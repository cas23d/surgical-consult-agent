"""Flask API backend for the Surgical Consult Agent web demo.

Exposes the consult workflow as REST endpoints with streaming responses.
Integrates with Supabase for session persistence.
"""

import os
import json
import logging
from datetime import datetime
from typing import Generator
from functools import wraps

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from anthropic import Anthropic
import supabase
import uuid

from fhir_client import pull_full_chart, format_chart_for_ai
from prompts import (
    SYSTEM_PROMPT,
    TRIAGE_PROMPT,
    CONTEXT_PROMPT,
    PLAN_PROMPT,
    NOTE_PROMPT,
)

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"

sb_url = os.getenv("VITE_SUPABASE_URL")
sb_key = os.getenv("VITE_SUPABASE_ANON_KEY")
sb = supabase.create_client(sb_url, sb_key)


def get_or_create_session(session_id: str = None) -> str:
    """Get or create a consult session."""
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        response = sb.table("consult_sessions").select("*").eq("session_id", session_id).execute()

        if not response.data:
            sb.table("consult_sessions").insert({
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Using existing session: {session_id}")
    except Exception as e:
        logger.error(f"Error managing session: {str(e)}")

    return session_id


def call_claude_stream(system: str, user_message: str) -> Generator[str, None, None]:
    """Call Claude API and stream responses."""
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        logger.error(f"Error calling Claude: {str(e)}")
        yield f"\n\n**ERROR**: {str(e)}"


def save_consult_to_db(
    session_id: str,
    patient_name: str,
    consult_message: str,
    resident_input: str,
    triage: str,
    context: str,
    plan: str,
    final_note: str,
) -> bool:
    """Save a completed consult to Supabase."""
    try:
        session_record = sb.table("consult_sessions").select("id").eq("session_id", session_id).execute()

        if not session_record.data:
            logger.warning(f"Session not found: {session_id}")
            return False

        session_uuid = session_record.data[0]["id"]

        sb.table("consult_history").insert({
            "session_id": session_uuid,
            "patient_name": patient_name,
            "consult_message": consult_message,
            "resident_input": resident_input,
            "triage_output": triage,
            "context_output": context,
            "plan_output": plan,
            "final_note": final_note,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        logger.info(f"Saved consult to database for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving consult to database: {str(e)}")
        return False


def get_session_history(session_id: str) -> list:
    """Retrieve consult history for a session."""
    try:
        session_record = sb.table("consult_sessions").select("id").eq("session_id", session_id).execute()

        if not session_record.data:
            return []

        session_uuid = session_record.data[0]["id"]
        history = sb.table("consult_history").select("*").eq("session_id", session_uuid).order("created_at", desc=True).execute()

        return [
            {
                "id": h["id"],
                "patient_name": h["patient_name"],
                "consult_message": h["consult_message"],
                "created_at": h["created_at"],
            }
            for h in history.data
        ]
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}")
        return []


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Surgical Consult Agent API is running"}), 200


@app.route("/api/session", methods=["POST"])
def create_session():
    """Create or retrieve a session."""
    data = request.get_json() or {}
    session_id = data.get("session_id")

    session_id = get_or_create_session(session_id)

    return jsonify({
        "session_id": session_id,
        "message": "Session created or retrieved"
    }), 200


@app.route("/api/session/history", methods=["GET"])
def session_history():
    """Get consult history for a session."""
    session_id = request.args.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    history = get_session_history(session_id)

    return jsonify({"history": history}), 200


@app.route("/api/consult/triage", methods=["POST"])
def triage():
    """Generate triage analysis."""
    data = request.get_json() or {}
    consult_message = data.get("consult_message", "")
    chart_data = data.get("chart_data", "")

    if not consult_message or not chart_data:
        return jsonify({"error": "consult_message and chart_data required"}), 400

    def generate():
        for text in call_claude_stream(
            system=SYSTEM_PROMPT,
            user_message=TRIAGE_PROMPT.format(
                consult_message=consult_message,
                chart_data=chart_data,
            ),
        ):
            yield text

    return Response(generate(), mimetype="text/event-stream"), 200


@app.route("/api/consult/context", methods=["POST"])
def context():
    """Generate context and gaps analysis."""
    data = request.get_json() or {}
    consult_message = data.get("consult_message", "")
    chart_data = data.get("chart_data", "")

    if not consult_message or not chart_data:
        return jsonify({"error": "consult_message and chart_data required"}), 400

    def generate():
        for text in call_claude_stream(
            system=SYSTEM_PROMPT,
            user_message=CONTEXT_PROMPT.format(
                consult_message=consult_message,
                chart_data=chart_data,
            ),
        ):
            yield text

    return Response(generate(), mimetype="text/event-stream"), 200


@app.route("/api/consult/plan", methods=["POST"])
def plan():
    """Generate assessment and plan."""
    data = request.get_json() or {}
    consult_message = data.get("consult_message", "")
    chart_data = data.get("chart_data", "")
    resident_input = data.get("resident_input", "")

    if not consult_message or not chart_data:
        return jsonify({"error": "consult_message and chart_data required"}), 400

    def generate():
        for text in call_claude_stream(
            system=SYSTEM_PROMPT,
            user_message=PLAN_PROMPT.format(
                consult_message=consult_message,
                chart_data=chart_data,
                resident_input=resident_input,
            ),
        ):
            yield text

    return Response(generate(), mimetype="text/event-stream"), 200


@app.route("/api/consult/note", methods=["POST"])
def note():
    """Generate final consult note."""
    data = request.get_json() or {}
    consult_message = data.get("consult_message", "")
    chart_data = data.get("chart_data", "")
    resident_input = data.get("resident_input", "")

    if not consult_message or not chart_data:
        return jsonify({"error": "consult_message and chart_data required"}), 400

    def generate():
        for text in call_claude_stream(
            system=SYSTEM_PROMPT,
            user_message=NOTE_PROMPT.format(
                consult_message=consult_message,
                chart_data=chart_data,
                resident_input=resident_input,
            ),
        ):
            yield text

    return Response(generate(), mimetype="text/event-stream"), 200


@app.route("/api/consult/save", methods=["POST"])
def save_consult():
    """Save a completed consult to the database."""
    data = request.get_json() or {}

    required = ["session_id", "patient_name", "consult_message", "resident_input", "triage", "context", "plan", "final_note"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing required fields: {', '.join(required)}"}), 400

    success = save_consult_to_db(
        session_id=data["session_id"],
        patient_name=data["patient_name"],
        consult_message=data["consult_message"],
        resident_input=data["resident_input"],
        triage=data["triage"],
        context=data["context"],
        plan=data["plan"],
        final_note=data["final_note"],
    )

    if success:
        return jsonify({"message": "Consult saved successfully"}), 200
    else:
        return jsonify({"error": "Failed to save consult"}), 500


@app.errorhandler(400)
def bad_request(e):
    """Handle 400 errors."""
    logger.warning(f"Bad request: {str(e)}")
    return jsonify({"error": str(e)}), 400


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Surgical Consult Agent API")
    app.run(debug=os.getenv("FLASK_ENV") == "development", port=5000)
