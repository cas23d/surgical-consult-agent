"""Vercel serverless function for live AI consult analysis.

Receives case data + stage name, calls Claude, returns the result.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Add project root to path so we can import prompts.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from prompts import SYSTEM_PROMPT, TRIAGE_PROMPT, CONTEXT_PROMPT, PLAN_PROMPT, NOTE_PROMPT

PUBLIC_AI_ENABLED = os.environ.get("ENABLE_PUBLIC_AI", "").lower() in {"1", "true", "yes"}
ALLOWED_ORIGIN = os.environ.get(
    "ALLOWED_ORIGIN", "https://surgical-consult-agent.vercel.app"
).rstrip("/")
MAX_BODY_BYTES = 100_000
MAX_CONSULT_CHARS = 2_000
MAX_CHART_CHARS = 60_000
MAX_RESIDENT_INPUT_CHARS = 4_000
MODEL = os.environ.get("ANTHROPIC_MODEL")

STAGE_PROMPTS = {
    "triage": TRIAGE_PROMPT,
    "context": CONTEXT_PROMPT,
    "plan": PLAN_PROMPT,
    "note": NOTE_PROMPT,
}


class handler(BaseHTTPRequestHandler):

    def _allowed_origin(self):
        origin = self.headers.get("Origin", "").rstrip("/")
        if origin == ALLOWED_ORIGIN:
            return origin
        if os.environ.get("VERCEL_ENV") != "production" and origin in {
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        }:
            return origin
        return None

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        origin = self._allowed_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        origin = self._allowed_origin()
        if not origin:
            self._send_json(403, {"error": "Origin not allowed"})
            return
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if not PUBLIC_AI_ENABLED:
            self._send_json(403, {"error": "Public model execution is disabled"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length"})
            return

        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "Request body is missing or too large"})
            return

        try:
            body = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON"})
            return

        if not isinstance(body, dict):
            self._send_json(400, {"error": "Request body must be a JSON object"})
            return

        stage = body.get("stage")
        consult_message = body.get("consult_message", "")
        chart_data = body.get("chart_data", "")
        resident_input = body.get("resident_input", "")

        if stage not in STAGE_PROMPTS:
            self._send_json(400, {"error": f"Invalid stage: {stage}"})
            return

        if not consult_message or not chart_data:
            self._send_json(400, {"error": "consult_message and chart_data are required"})
            return

        fields = (consult_message, chart_data, resident_input)
        if not all(isinstance(value, str) for value in fields):
            self._send_json(400, {"error": "Clinical inputs must be strings"})
            return

        if (
            len(consult_message) > MAX_CONSULT_CHARS
            or len(chart_data) > MAX_CHART_CHARS
            or len(resident_input) > MAX_RESIDENT_INPUT_CHARS
        ):
            self._send_json(413, {"error": "One or more clinical inputs are too large"})
            return

        prompt_template = STAGE_PROMPTS[stage]

        if stage in ("plan", "note"):
            user_message = prompt_template.format(
                consult_message=consult_message,
                chart_data=chart_data,
                resident_input=resident_input,
            )
        else:
            user_message = prompt_template.format(
                consult_message=consult_message,
                chart_data=chart_data,
            )

        try:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key or not MODEL:
                self._send_json(503, {"error": "Model service is not configured"})
                return
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=MODEL,
                max_tokens=8192,
                output_config={"effort": "low"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            self._send_json(200, {"text": text})
        except Exception:
            self._send_json(502, {"error": "Model service request failed"})
