"""Rounds Prep Agent — pulls patient data from EHR via FHIR,
analyzes the chart, and produces structured rounds preparation outputs.

Built by Christopher Stephenson, MD
"""

import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from fhir_client import pull_full_chart, format_chart_for_ai
from rounds_prompts import (
    ROUNDS_SYSTEM_PROMPT,
    ALERTS_AND_DAYPLAN_PROMPT,
    PRESENTATION_PROMPT,
    AM_BRIEF_PROMPT,
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


def get_input(prompt=">> ", allow_empty=True):
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


def run_rounds():
    """Run the rounds preparation workflow."""

    print_header("ROUNDS PREP AGENT")

    # --- Load patient list ---
    patients_file = os.path.join(os.path.dirname(__file__), "rounds_patients.json")
    if not os.path.exists(patients_file):
        print("No rounds_patients.json found. Run setup_rounds_patients.py first.")
        return

    with open(patients_file) as f:
        patients = json.load(f)

    print("Patient List:")
    for i, p in enumerate(patients, 1):
        print(f"  {i}. {p['name']} (MRN: {p['mrn']})")
    print()

    # --- Select patient ---
    choice = input("Select patient (1-3): ").strip()
    try:
        idx = int(choice) - 1
        patient = patients[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    patient_id = patient["patient_id"]
    print(f"\nSelected: {patient['name']}")

    # --- Pull chart from FHIR ---
    print("\n\u23f3 Pulling patient chart from EHR...\n")
    chart_data = pull_full_chart(patient_id)
    chart_text = format_chart_for_ai(chart_data)

    print(chart_text)
    print_header("CHART DATA LOADED")

    # --- Extract yesterday's note ---
    yesterday_note = "No prior note available."
    for note in chart_data.get("notes", []):
        if "progress" in note.get("type", "").lower() or "consult" in note.get("type", "").lower():
            yesterday_note = note["text"]
            break

    # --- Stage 1: Alerts & Day Plan ---
    print_header("ALERTS & DAY PLAN")
    print("Analyzing critical values and generating day plan...\n")

    alerts = call_claude(
        system=ROUNDS_SYSTEM_PROMPT,
        user_message=ALERTS_AND_DAYPLAN_PROMPT.format(
            chart_data=chart_text,
            yesterday_note=yesterday_note,
            resident_exam="[PENDING \u2014 verify on exam]",
        ),
    )
    print(alerts)

    # --- Optional exam input ---
    print_header("EXAM FINDINGS")
    print("Add your bedside exam findings (or press Enter twice to skip):\n")
    resident_exam = get_input(">> ")
    if not resident_exam:
        resident_exam = "[PENDING \u2014 verify on exam]"

    # --- Stage 2: Presentation ---
    print_header("ROUNDS PRESENTATION")
    print("Generating verbal presentation...\n")

    presentation = call_claude(
        system=ROUNDS_SYSTEM_PROMPT,
        user_message=PRESENTATION_PROMPT.format(
            chart_data=chart_text,
            yesterday_note=yesterday_note,
            resident_exam=resident_exam,
        ),
    )
    print(presentation)

    # --- Stage 3: AM Brief ---
    print_header("AM BRIEF")
    print("Generating structured AM brief...\n")

    am_brief = call_claude(
        system=ROUNDS_SYSTEM_PROMPT,
        user_message=AM_BRIEF_PROMPT.format(
            chart_data=chart_text,
            yesterday_note=yesterday_note,
            resident_exam=resident_exam,
        ),
    )
    print(am_brief)

    print_header("ROUNDS PREP COMPLETE")


if __name__ == "__main__":
    run_rounds()
