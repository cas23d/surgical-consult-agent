"""Prompt templates for a clinician-supervised surgical consult prototype.

The prompts are product artifacts, not validated clinical protocols.
"""

SYSTEM_PROMPT = """\
You are generating draft outputs for a clinician-supervised portfolio prototype.

Safety and evidence rules:
- Never present the output as medical advice, a final diagnosis, a final order, or autonomous clinical decision-making.
- Use only the supplied chart context and explicit clinician input. Never invent history, examination findings, medications, orders, procedures, or test results.
- Distinguish chart facts, clinician-entered facts, reasonable inferences, and missing information.
- If an item is absent, say it is not visible in the supplied context; do not claim it was not done.
- Do not diagnose septic shock from hypotension or lactate alone. State what additional criteria or response-to-resuscitation data are required.
- Do not invent citations. Name a guideline and year only when confident; otherwise mark the reference for verification.
- Avoid prescribing a specific operation, reconstruction, dose, transfusion quantity, or imaging protocol when patient-specific context is incomplete.
- Make uncertainty and human-review checkpoints explicit.
- Label every output: SYNTHETIC DEMO - REQUIRES CLINICIAN VERIFICATION.
- Use concise language suitable for review by a surgical clinician.
"""

TRIAGE_PROMPT = """\
Consult message:
{consult_message}

Supplied chart context:
{chart_data}

Draft a rapid acuity assessment for clinician review.

Include:
## ACUITY ASSESSMENT
- Objective instability and organ-hypoperfusion signals
- A risk-oriented sepsis assessment without using SIRS as the diagnostic definition
- Overall urgency

## IMMEDIATE RED FLAGS
- Specific findings from the supplied context
- Important alternative explanations where appropriate

## DEFINITION CHECK
- Any diagnostic label that cannot yet be established and what is missing

## CLINICIAN CHECKPOINT
- The bedside findings and actions that must be verified immediately
"""

CONTEXT_PROMPT = """\
Consult message:
{consult_message}

Supplied chart context:
{chart_data}

Compare what is documented with what a clinician would need to verify.

Include:
## DOCUMENTED IN THE SNAPSHOT
- Findings and treatments explicitly visible in the supplied context

## URGENT ITEMS TO VERIFY
- Time-sensitive care or escalation that is not visible or is ambiguous
- Phrase these as verification questions, not claims that care was omitted

## MISSING DECISION CONTEXT
- Missing history, medications, baseline function, goals, examination, and operational details
- Explain briefly why each item matters
"""

PLAN_PROMPT = """\
Consult message:
{consult_message}

Supplied chart context:
{chart_data}

Clinician-entered findings or corrections:
{resident_input}

Generate a draft assessment and prioritized considerations for attending review.

Include:
## WORKING ASSESSMENT
- Concise synthesis with uncertainty preserved

## DRAFT PRIORITIES FOR ATTENDING REVIEW
- Resuscitation, reassessment, diagnostics, escalation, and source-control considerations
- Avoid a definitive procedure or reconstruction when the context is incomplete

## REFERENCES TO VERIFY
- Relevant society guidance only when confident in the title and year
- Explain what the reference supports and what still requires patient-specific judgment
"""

NOTE_PROMPT = """\
Consult message:
{consult_message}

Supplied chart context:
{chart_data}

Clinician-entered findings or corrections:
{resident_input}

Generate three clearly labeled draft artifacts:

## SURGICAL CONSULT NOTE
- Reason for consult
- History from supplied context
- Examination, explicitly attributed to the source
- Pertinent laboratory and imaging findings
- Working assessment with uncertainty
- Draft plan for attending review
- Mark unavailable information as [PENDING - VERIFY]

## STAFFING SUMMARY
- A concise verbal summary
- Do not put unverified findings into the clinician's voice

## VERIFICATION TASKS
- A prioritized checklist of facts, actions, and decisions that must be confirmed

End with: This draft must not be copied into a medical record without clinician review and correction.
"""
