"""Surgical Consult Agent — pulls patient data from EHR via FHIR,
analyzes the chart, and produces structured clinical outputs.

Built by Christopher Stephenson, MD
"""

import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from fhir_client import pull_full_chart, format_chart_for_ai
from prompts import (
    SYSTEM_PROMPT,
    TRIAGE_PROMPT,
    CONTEXT_PROMPT,
    PLAN_PROMPT,
    NOTE_PROMPT,
)

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"


def call_claude(system, user_message):
    """Send a message to Claude and return the response text."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def get_input(prompt=">> ", allow_empty=False):
    """Collect multi-line input. Empty line submits."""
    print(prompt, end="", flush=True)
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def run_consult():
    """Run the surgical consult workflow."""

    print_header("SURGICAL CONSULT AGENT")
    print("Paste the consult page info below.")
    print("Include the patient MRN and consult message.\n")

    # --- Input: consult page ---
    consult_message = get_input("Consult message >> ")

    # --- Load patient from FHIR ---
    # For demo, use the pre-loaded patient. In production, would search by MRN.
    demo_config = os.path.join(os.path.dirname(__file__), "demo_patient.json")
    if os.path.exists(demo_config):
        with open(demo_config) as f:
            config = json.load(f)
        patient_id = config["patient_id"]
    else:
        patient_id = input("Enter FHIR Patient ID: ").strip()

    print("\n⏳ Pulling patient chart from EHR...\n")
    chart_data = pull_full_chart(patient_id)
    chart_text = format_chart_for_ai(chart_data)

    print(chart_text)
    print_header("CHART DATA LOADED")

    # --- Stage 1: Triage ---
    print_header("TRIAGE ANALYSIS")
    print("Analyzing acuity and red flags...\n")

    triage = call_claude(
        system=SYSTEM_PROMPT,
        user_message=TRIAGE_PROMPT.format(
            consult_message=consult_message,
            chart_data=chart_text,
        ),
    )
    print(triage)

    # --- Stage 2: Treatment Context & Gaps ---
    print_header("TREATMENT CONTEXT & GAPS")
    print("Analyzing current management and missing info...\n")

    context = call_claude(
        system=SYSTEM_PROMPT,
        user_message=CONTEXT_PROMPT.format(
            consult_message=consult_message,
            chart_data=chart_text,
        ),
    )
    print(context)

    # --- Resident input ---
    print_header("YOUR INPUT")
    print("You've seen the triage and gaps analysis.")
    print("Add anything from your exam, patient interview, or corrections.")
    print("(Type your input, then press Enter twice to submit)\n")

    resident_input = get_input(">> ")

    # --- Stage 3: Assessment & Plan ---
    print_header("ASSESSMENT & PLAN")
    print("Generating evidence-based plan...\n")

    plan = call_claude(
        system=SYSTEM_PROMPT,
        user_message=PLAN_PROMPT.format(
            consult_message=consult_message,
            chart_data=chart_text,
            resident_input=resident_input,
        ),
    )
    print(plan)

    # --- Stage 4: Final Outputs ---
    print_header("GENERATING FINAL OUTPUTS")

    print("Any final corrections before generating the note?")
    print("(Press Enter twice to skip, or type corrections)\n")
    final_corrections = get_input(">> ")
    combined_input = resident_input
    if final_corrections:
        combined_input += "\n\nAdditional corrections:\n" + final_corrections

    note = call_claude(
        system=SYSTEM_PROMPT,
        user_message=NOTE_PROMPT.format(
            consult_message=consult_message,
            chart_data=chart_text,
            resident_input=combined_input,
        ),
    )
    print(note)

    print_header("CONSULT COMPLETE")


if __name__ == "__main__":
    run_consult()
