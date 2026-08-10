# Surgical Consult Agent

**[Open the portfolio demo](https://surgical-consult-agent.vercel.app/)**

A clinician-designed portfolio prototype exploring how AI could reduce the cognitive load of surgical consult preparation.

I built this project with AI-assisted development: I defined the clinical workflow and safety boundaries, directed coding agents through implementation and debugging, tested the outputs against realistic scenarios, and deployed the result for review.

## What the demo shows

- A staged consult workflow: triage, information gaps, draft assessment and plan, and documentation
- Human-in-the-loop inputs for bedside findings and corrections
- A readable Python and JavaScript implementation that product and engineering teams can inspect

## What is live, simulated, and experimental

| Component | Status |
|---|---|
| Hosted patient cases | Fictional, synthetic JSON data |
| Hosted workflow outputs | Pre-generated examples for consistent review |
| FHIR R4 ingestion | Working prototype against the public HAPI FHIR test server; not connected to a production EHR |
| Model-backed analysis | Implemented as a Vercel serverless function; disabled by default on the public deployment |
| Clinical validation | Not completed |
| HIPAA and production infrastructure | Not implemented |

The hosted application is a product and workflow demonstration. It is not a medical device, does not provide medical advice, and must not be used for patient care.

## Product premise

Clinical workflows often fail at the point where information is fragmented across notes, labs, imaging, orders, and bedside findings. This prototype tests a simple interaction model:

1. Assemble the available chart context.
2. Surface acuity, contradictions, and missing information.
3. Accept clinician examination findings and corrections.
4. Produce reviewable draft outputs for the clinician to verify and revise.

The clinician remains responsible for the assessment, recommendations, documentation, and escalation decisions.

## Architecture

```text
Hosted portfolio demo                 Optional controlled model path
HTML / CSS / JavaScript               Vercel serverless Python function
        |                                        |
        +-- synthetic case JSON                  +-- stage-specific prompts
        +-- pre-generated outputs                +-- Anthropic API

FHIR prototype
Python client -> HAPI FHIR public test server -> normalized chart context
```

## Repository map

```text
api/consult.py              Optional model-backed analysis endpoint
consult_agent.py            Command-line consult workflow
fhir_client.py              FHIR R4 retrieval and normalization
prompts.py                  Consult-stage prompts and safety instructions
web/                        Hosted portfolio interface and synthetic cases
setup_demo_patient.py       Synthetic HAPI FHIR data utility
```

## Run the static demo locally

```bash
cd web
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Run a controlled model-backed evaluation

Install the Python dependencies and set the required environment variables:

```bash
python -m pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_MODEL="your-enabled-model"
export ENABLE_PUBLIC_AI="true"
```

The public deployment intentionally leaves `ENABLE_PUBLIC_AI` unset. Anyone enabling the endpoint is responsible for authentication, rate limiting, cost controls, privacy review, and appropriate data-handling infrastructure.

## Known limitations and next steps

- The synthetic cases are demonstrations, not a clinical validation set.
- Generated recommendations and citations require independent clinician verification.
- The FHIR adapter covers a limited subset of R4 resources and has not been tested against vendor-specific production implementations.
- Production use would require access controls, audit logging, monitoring, evaluation datasets, PHI-safe infrastructure, and organizational legal, privacy, security, and regulatory review.
- The highest-value next step is structured evaluation with clinicians and product teams, including failure-mode logging rather than testimonial-only feedback.

## About the builder

Christopher Stephenson, MD is a practicing physician and clinical AI product builder. He uses AI-assisted development to translate clinical workflow problems into working prototypes, while owning the clinical reasoning, product requirements, and evaluation criteria.

- [LinkedIn](https://www.linkedin.com/in/christopher-stephenson-md)
- [GitHub profile](https://github.com/cas23d)

## Use and attribution

Personal portfolio project. All fictional names, identifiers, and clinical records in the hosted demo are synthetic. No real patient data is included.
