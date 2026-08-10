"""Controlled CLI for the surgical consult portfolio prototype.

Built by Christopher Stephenson, MD
"""

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


def call_claude(system: str, user_message: str) -> str:
    """Send a controlled evaluation request and return the text block."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL")
    if not api_key or not model:
        raise RuntimeError("ANTHROPIC_API_KEY and ANTHROPIC_MODEL are required")

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return next(b.text for b in response.content if b.type == "text")
    except Exception:
        logger.error("Model request failed")
        raise


def get_input(prompt: str = ">> ") -> str:
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
    print("Use fictional or appropriately authorized test data only.")
    print("Enter a consult message and a patient ID from the configured FHIR test server.\n")

    try:
        # --- Input: consult page ---
        consult_message = get_input("Consult message >> ")
        if not consult_message:
            logger.warning("No consult message provided")
            print("Error: Consult message cannot be empty")
            return

        patient_id = input("Enter FHIR Patient ID: ").strip()
        if not patient_id:
            logger.warning("No patient ID provided")
            print("Error: Patient ID cannot be empty")
            return

        print("\nPulling synthetic chart context from the configured FHIR server...\n")
        chart_data = pull_full_chart(patient_id)
        chart_text = format_chart_for_ai(chart_data)

        print(chart_text)
        print_header("CHART DATA LOADED")
    except Exception:
        logger.error("Consult setup failed")
        print("Error: unable to load the synthetic consult context")
        return

    try:
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
        print("Generating draft considerations for clinician review...\n")

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

        print_header("DRAFT COMPLETE - CLINICIAN VERIFICATION REQUIRED")
        logger.info("Consult workflow completed successfully")
    except Exception:
        logger.error("Consult workflow failed")
        print("\nError: the draft workflow could not be completed")
        raise


if __name__ == "__main__":
    run_consult()
