"""Surgical Consult Agent — pulls patient data from EHR via FHIR,
analyzes the chart, and produces structured clinical outputs.

Built by Christopher Stephenson, MD
"""

import json
import os
import logging
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-5"


def call_claude(system: str, user_message: str) -> str:
    """Send a message to Claude and return the response text."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Error calling Claude API: {str(e)}")
        raise


def get_input(prompt: str = ">> ", allow_empty: bool = False) -> str:
    """Collect multi-line input. Empty line submits."""
    print(prompt, end="", flush=True)
    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except KeyboardInterrupt:
        logger.info("User cancelled input")
        return ""
    except EOFError:
        logger.info("End of input")
        return ""
    return "\n".join(lines)


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def run_consult() -> None:
    """Run the surgical consult workflow."""

    print_header("SURGICAL CONSULT AGENT")
    print("Paste the consult page info below.")
    print("Include the patient MRN and consult message.\n")

    try:
        # --- Input: consult page ---
        consult_message = get_input("Consult message >> ")
        if not consult_message:
            logger.warning("No consult message provided")
            print("Error: Consult message cannot be empty")
            return

        # --- Load patient from FHIR ---
        demo_config = os.path.join(os.path.dirname(__file__), "demo_patient.json")
        patient_id = None
        if os.path.exists(demo_config):
            try:
                with open(demo_config) as f:
                    config = json.load(f)
                patient_id = config.get("patient_id")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading demo_patient.json: {str(e)}")

        if not patient_id:
            patient_id = input("Enter FHIR Patient ID: ").strip()
            if not patient_id:
                logger.warning("No patient ID provided")
                print("Error: Patient ID cannot be empty")
                return

        print("\n⏳ Pulling patient chart from EHR...\n")
        chart_data = pull_full_chart(patient_id)
        chart_text = format_chart_for_ai(chart_data)

        print(chart_text)
        print_header("CHART DATA LOADED")
    except Exception as e:
        logger.error(f"Error in consult setup: {str(e)}")
        print(f"Error: {str(e)}")
        return

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
        logger.info("Consult workflow completed successfully")
    except Exception as e:
        logger.error(f"Error in consult workflow: {str(e)}")
        print(f"\nError during consult: {str(e)}")
        raise


if __name__ == "__main__":
    run_consult()
