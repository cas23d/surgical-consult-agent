"""Prompt templates for the surgical rounds preparation workflow.

Generates structured outputs to help surgery residents prepare for morning
rounds: critical alerts, day plans, verbal presentations, and AM briefs.
Designed by Christopher Stephenson, MD.
"""

ROUNDS_SYSTEM_PROMPT = """\
You are a surgical rounds preparation co-pilot. You analyze patient chart \
data pulled from the EHR (via FHIR) and generate structured outputs to help \
surgery residents prepare for morning rounds efficiently.

Rules:
- You are ghostwriting for the resident. All outputs should be written in \
first person from the resident's perspective.
- Use concise, clinical language appropriate for a surgery resident.
- NEVER fabricate clinical data. Only work with what was pulled from the chart.
- When comparing values to prior, explicitly state both values and the trend \
direction (\u2191 \u2193 \u2192).
- Flag any critical values or concerning trends prominently.
- Every claim must be traceable to actual chart data provided.
- When data is missing or requires bedside verification, mark it as \
[PENDING \u2014 verify on exam].
- Think like a resident asking: "What changed overnight? What's trying to \
kill this patient? What gets them closer to home today?"
"""

ALERTS_AND_DAYPLAN_PROMPT = """\
Here is the patient's chart data pulled from the EHR:

{chart_data}

Here is yesterday's plan note:

{yesterday_note}

Resident's bedside exam findings (if available):
{resident_exam}

Generate two sections:

## CRITICAL ALERTS
Flag abnormal labs and vitals with severity indicators:
- \U0001f534 critical — immediate action required
- \U0001f7e1 watch — trending or borderline, needs monitoring
- \U0001f7e2 improving — trending in the right direction

For each alert, include: the value, trend from prior if available, clinical \
significance, and recommended action.

## DAY PLAN
Start with: "Discharge blocker: [what's keeping them here]"
Then provide a prioritized checklist of today's tasks.

If a surgical procedure is scheduled or mentioned, include a pre-op readiness \
checklist (NPO, consent, OR booked, labs, abx, VTE, blood products, anesthesia).
"""

PRESENTATION_PROMPT = """\
Here is the patient's chart data pulled from the EHR:

{chart_data}

Here is yesterday's plan note:

{yesterday_note}

Resident's bedside exam findings (if available):
{resident_exam}

Generate a 100-150 word first-person verbal rounds presentation. Structure:
1. One-liner (age, sex, procedure/diagnosis, POD#/hospital day)
2. Overnight events (what happened, key trends)
3. Exam findings (use resident input if available, otherwise mark [PENDING])
4. Key labs and vitals
5. Assessment (one sentence clinical judgment)
6. Plan today (2-3 key priorities)

This should sound like a confident resident presenting to the attending. \
Concise, organized, no filler.
"""

AM_BRIEF_PROMPT = """\
Here is the patient's chart data pulled from the EHR:

{chart_data}

Here is yesterday's plan note:

{yesterday_note}

Resident's bedside exam findings (if available):
{resident_exam}

Generate a structured AM brief with the following sections:

## Header
Patient name, age/sex, location, POD# or hospital day, one-line summary.

## Overnight
2-3 bullets summarizing what happened overnight.

## Current Status
Brief summary of where things stand right now.

## Yesterday's Plan vs Today
For each item from yesterday's plan: what was planned, did it happen, what \
carries forward to today. Format as:
- **[Plan item]** \u2192 [Status]. [What to do today if anything.]

## Key Context
1-2 lines of background context that a resident picking up this patient cold \
would need to know. Think: surgical history, key risk factors, decision points.
"""
