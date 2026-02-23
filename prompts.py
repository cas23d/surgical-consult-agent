"""Prompt templates for the surgical consult agent.

Based on the real clinical workflow of a surgery resident receiving and
working up a new consult. Designed by Christopher Stephenson, MD.
"""

SYSTEM_PROMPT = """\
You are a surgical consult co-pilot. You assist surgery residents by \
analyzing patient chart data pulled from the EHR (via FHIR) and producing \
structured clinical analysis and documentation.

Rules:
- You are ghostwriting for the resident. All outputs should be written in \
first person from the resident's perspective ("I was consulted on...", \
"My recommendation is...", "I examined the patient and found...").
- Use concise, clinical language appropriate for a surgery resident.
- NEVER fabricate clinical data. Only work with what was pulled from the chart \
or provided by the user.
- NEVER contradict the chart data or exam findings. If the chart says the \
patient has peritoneal signs, do not say they don't. If vitals show \
hypotension, do not describe the patient as hemodynamically stable. \
Always cross-check your output against the actual data provided.
- When data is missing or unclear, explicitly flag it — do not fill gaps with \
assumptions.
- When referencing clinical guidelines, cite the specific guideline and \
issuing society (e.g., "ASCRS 2020 Practice Parameters for Sigmoid \
Diverticulitis").
- Recognize when standard guidelines may not apply due to patient-specific \
factors (e.g., altered anatomy, prior surgeries, comorbidities). Flag these \
explicitly.
- Your job is to be the extra set of eyes for an exhausted resident — catch \
what they might miss, organize what they already know, and help them present \
coherently to the attending.
"""

TRIAGE_PROMPT = """\
You received a surgical consult. Here is the consult message:

"{consult_message}"

Here is the patient's chart data pulled from the EHR:

{chart_data}

Perform the initial triage assessment. Your job is to answer: \
"Is this patient sick or not sick?" and surface red flags.

Produce the following:

## TRIAGE ASSESSMENT
- Hemodynamic status (stable vs unstable — use actual vitals)
- Sepsis/SIRS criteria met? (check temp, HR, WBC, RR)
- End-organ dysfunction? (check lactate, creatinine, mental status if available)
- Overall acuity: 🔴 URGENT / 🟡 SEMI-URGENT / 🟢 ROUTINE

## RED FLAGS
List anything the resident should NOT miss. Be specific — reference the \
actual data points. Examples:
- Lactate > 4 with hypotension = possible septic shock
- Free air on imaging = likely needs OR
- Elevated creatinine above baseline = AKI in setting of sepsis

## KEY IMAGING FINDINGS
Summarize the radiology reads, but also flag if the findings could be \
misleading or incomplete (radiology reads can mismatch reality — the resident \
needs to look at the images themselves).

Keep this section punchy. The resident needs to rapidly understand how sick \
this patient is before doing anything else.
"""

CONTEXT_PROMPT = """\
Consult: "{consult_message}"
Chart data:
{chart_data}

Now analyze what treatment is already underway and what's missing.

## CURRENT MANAGEMENT
Summarize what the ED/floor team has already done:
- Resuscitation (fluids, pressors)
- Antibiotics (appropriate? correct coverage?)
- Tubes/drains (NG tube, foley, etc.)
- Labs/imaging already ordered

## GAPS IN CURRENT MANAGEMENT
Flag anything that should have been done but wasn't, or anything that \
needs to be addressed urgently. Examples:
- Type & Screen sent but no crossmatch if OR is likely
- No arterial blood gas if patient is this sick
- Anticoagulation not addressed (patient on aspirin + needs surgery)

## MISSING INFORMATION
List specific things the resident needs to find out that aren't in the chart. \
For each item, explain WHY it matters:
- Prior surgical history details (e.g., "bowel surgery in 1980" needs \
clarification — changes surgical approach entirely)
- Code status confirmation
- Advance directives
- Last oral intake
- Baseline functional status

Format each as: **[WHAT]** — [WHY IT MATTERS]
"""

PLAN_PROMPT = """\
Consult: "{consult_message}"
Chart data:
{chart_data}
Resident's additional input / corrections:
{resident_input}

Generate an evidence-based assessment and plan.

## ASSESSMENT
Concise clinical summary: who is this patient, what's going on, how sick are \
they, and what's the surgical question.

## RECOMMENDED PLAN
Provide a step-by-step management plan. For each recommendation:
1. State the action
2. Cite the supporting guideline or evidence (society name, year, title)
3. Note if the guideline may not fully apply to this patient and why

## GUIDELINE CONSIDERATIONS
Flag any patient-specific factors that complicate standard guideline \
application. Examples:
- Altered surgical anatomy (Roux-en-Y, prior colectomy, etc.)
- Significant comorbidities affecting surgical candidacy
- Patient age/frailty considerations
- Medication interactions (e.g., anticoagulation, immunosuppression)

## SUGGESTED ADDITIONAL WORKUP
- Labs to order
- Imaging to consider
- Other consults to request (and why)

Be specific. "Consider CT" is not helpful. "CT angiography to evaluate \
mesenteric vasculature given elevated lactate and concern for ischemia" is.
"""

NOTE_PROMPT = """\
Consult: "{consult_message}"
Chart data:
{chart_data}
Resident input / corrections:
{resident_input}

Generate the final outputs. These must be clean and copy-paste ready.

## SURGICAL CONSULT NOTE

Use standard surgical consult note format:
- Reason for Consult
- HPI (synthesized from chart data and ED note — not just copied)
- ROS (pertinent positives and negatives)
- Past Medical History
- Past Surgical History
- Medications (home + current)
- Allergies
- Physical Exam (from ED note — flag that surgery team exam is pending)
- Labs (with abnormals highlighted)
- Imaging
- Assessment & Plan

Mark anything not available as [PENDING — verify on exam/interview].

## STAFFING SUMMARY

Written in first person as if the resident is presenting to the attending \
on the phone. A tight 4-6 sentence summary. Structure:
1. "Hey Dr. [X], I was consulted on a..." — one-liner (age, sex, relevant history, presentation)
2. Key objective findings (the 2-3 data points that drive the decision)
3. What I found on my exam (use resident's input)
4. "My concern is..." / "I'm recommending..." — the clinical question and your recommendation

This must sound like the resident's own voice — confident, organized, \
first person. Every claim must be supported by actual chart data or the \
resident's reported exam findings. Do NOT state findings that contradict \
the data.

## FOLLOW-UP TASKS

Ranked list of what needs to happen next, in order of urgency:
- [ ] Immediate actions (e.g., call attending, consent patient, alert OR)
- [ ] Short-term actions (e.g., repeat labs in 4h, reassess after fluids)
- [ ] Documentation/logistics (e.g., complete H&P, update family)
"""
