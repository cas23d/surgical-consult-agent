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

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-5"

STAGE_PROMPTS = {
    "triage": TRIAGE_PROMPT,
    "context": CONTEXT_PROMPT,
    "plan": PLAN_PROMPT,
    "note": NOTE_PROMPT,
}


class handler(BaseHTTPRequestHandler):

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length))

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
            response = client.messages.create(
                model=MODEL,
                max_tokens=8192,
                output_config={"effort": "low"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            self._send_json(200, {"text": text})
        except Exception as e:
            self._send_json(500, {"error": str(e)})
