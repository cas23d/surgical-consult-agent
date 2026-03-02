# Surgical Consult Agent + Rounds Prep

Two clinical AI workflows built on the same FHIR infrastructure — demonstrating how a single EHR integration can power multiple resident-facing tools.

| | Surgical Consult Agent | Rounds Prep |
|---|---|---|
| **Use case** | New consult arrives | AM chart check, existing patients |
| **Clinical question** | "Is this patient sick?" | "What changed? What's the plan?" |
| **Data source** | FHIR R4 (same) | FHIR R4 (same) |
| **Outputs** | Triage, gaps, plan, consult note | Alerts, day plan, presentation, AM brief |
| **User input** | Consult message + exam | Exam findings only |

## Surgical Consult Agent

A CLI-based AI agent that guides surgery residents through a structured consult workflow using Claude. Pulls patient data from the EHR via FHIR, analyzes the clinical picture, and generates a complete surgical consult workup — triage, gap analysis, evidence-based plan, and documentation.

```bash
python consult_agent.py
```

### Workflow Stages
1. **Triage** — "Is this patient sick or not sick?" Surfaces red flags, checks sepsis criteria, flags end-organ dysfunction.
2. **Gaps** — What's been done, what's missing, what information do we still need?
3. **Plan** — Evidence-based assessment with guideline citations.
4. **Final Note** — Copy-paste-ready consult note, staffing summary, follow-up tasks.

## Rounds Prep

An AI-powered morning chart check for surgery residents. Pulls overnight data from the EHR, compares against yesterday's plan, flags critical changes, and generates structured outputs for rounds.

```bash
python rounds_agent.py
```

### Workflow Stages
1. **Alerts & Day Plan** — Critical lab/vital flags (color-coded by severity), discharge blockers, prioritized task list.
2. **Presentation** — 100-150 word first-person verbal presentation for the attending.
3. **AM Brief** — Structured brief with overnight summary, yesterday's plan vs today, key context.

### Demo Patients
- Harold Whitaker (68M) — ICU, POD#1 Hartmann for perforated diverticulitis
- Maria Santos (45F) — Floor, POD#0 lap chole, discharge candidate
- Eugene Morales (72M) — ICU, ischemic colitis day 2, non-operative management

## Setup

```bash
git clone https://github.com/cas23d/surgical-consult-agent.git
cd surgical-consult-agent
pip install -r requirements.txt
cp .env.example .env
# Add your Anthropic API key to .env
```

### Upload demo patients to HAPI FHIR
```bash
python setup_demo_patient.py      # Consult workflow patient
python setup_rounds_patients.py   # Rounds workflow patients (3)
```

## Web Demo

The interactive web demo is deployed via GitHub Pages. Both workflows share the same design system — dark clinical aesthetic, split-panel layout, typing effect for AI outputs.

- **Consult Agent**: `web/index.html`
- **Rounds Prep**: `web/rounds.html`

Pre-baked case data in `web/cases/` and `web/rounds-cases/` — fully static, no backend required.

## Design Principles

- **No frameworks** — Raw Anthropic API calls. No LangChain, no abstractions. Every API call is visible and understandable.
- **FHIR R4 for everything** — Both workflows share `fhir_client.py`. Same functions, same data model, different clinical questions.
- **Designed for messy reality** — Residents are tired and busy. The agent handles shorthand, incomplete data, and missing information gracefully.
- **Clinician-in-the-loop** — The agent surfaces what the resident might miss. It doesn't make decisions. The only manual input that matters is the bedside exam — the one thing AI can't do.

## Architecture

```
FHIR R4 (HAPI FHIR)
      │
      ├── fhir_client.py (shared)
      │
      ├── Consult Workflow
      │     ├── prompts.py
      │     ├── consult_agent.py
      │     └── web/index.html + app.js
      │
      └── Rounds Workflow
            ├── rounds_prompts.py
            ├── rounds_agent.py
            └── web/rounds.html + rounds-app.js
```

## Requirements

- Python 3.10+
- Anthropic API key

## Built By

Christopher Stephenson, MD
