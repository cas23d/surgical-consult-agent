# Surgical Consult Agent + Rounds Prep

**[Live Demo](https://surgical-consult-agent.vercel.app/)**

An AI-powered clinical decision support system built by a surgery resident for surgery residents. Two complementary workflows — surgical consults and morning rounds — demonstrating how clinical expertise and AI can combine to solve real workflow problems.

---

## Try It

Visit: **https://surgical-consult-agent.vercel.app/**

1. Click a case to see the agent in action — chart data loads on the left, AI analysis on the right
2. Edit the resident exam findings in the textarea
3. Hit **"Re-analyze with Live AI"** to have Claude re-analyze the case in real-time based on your input

---

## Architecture

```
Static Frontend (Vercel)          Serverless API (Vercel)        External
  HTML/CSS/JS                      Python                        Services
       |                               |                            |
       +-- app.js                      +-- /api/consult (POST)      |
       +-- index.html                  |   Calls Claude with        |
       +-- rounds.html                 |   case data + stage     -> Anthropic
       +-- style.css                   |   Returns AI analysis      Claude API
       +-- cases/*.json (static demo)  |
       +-- rounds-cases/*.json         |
```

**Two modes:**
- **Static demo** — Pre-built case data loads instantly (free, no API cost)
- **Live AI** — Sends case data to Claude via serverless function, returns fresh analysis

---

## Workflows

### Surgical Consult Agent

**Use case:** New consult arrives. Resident needs to answer: "Is this patient sick?"

**Stages:**
1. **Triage** — Red flags, sepsis criteria, end-organ dysfunction
2. **Context & Gaps** — What's been done, what's missing
3. **Assessment & Plan** — Evidence-based recommendations with guideline citations
4. **Final Note** — Copy-paste-ready consult note + staffing summary

### Rounds Prep

**Use case:** AM chart check for existing patients.

**Stages:**
1. **Alerts & Day Plan** — Critical labs flagged by severity
2. **Presentation** — 100-word attending presentation
3. **AM Brief** — Overnight summary vs. yesterday's plan

---

## Design Philosophy

**Core Principle:** Systems must work at hour 28 of a shift, when cognitive reserve is exhausted.

1. **Cognitive Load Reduction** — System tracks state; user's brain is free to think
2. **Complexity Embedding** — Complex logic hidden; simple user interface
3. **Multi-Output Efficiency** — One input -> multiple structured outputs
4. **Verification Loops** — AI output validated at decision points before use
5. **Context Awareness** — Auto-pull data from screen; minimize manual entry
6. **Delimiter-Based Parsing** — Structured outputs enable automation
7. **Design for Worst Moment** — If it works only when alert, it fails when needed

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Anthropic Claude (Sonnet 4) |
| **Backend** | Vercel Serverless Functions (Python) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **EHR Integration** | FHIR R4 (HAPI FHIR) |
| **Deployment** | Vercel |

---

## File Structure

```
.
├── api/
│   └── consult.py                 # Vercel serverless function (Claude API)
├── consult_agent.py               # CLI surgical consult workflow
├── rounds_agent.py                # CLI morning rounds workflow
├── fhir_client.py                 # FHIR R4 EHR data pulling
├── prompts.py                     # Claude system & stage prompts
├── rounds_prompts.py              # Rounds workflow prompts
│
├── web/
│   ├── index.html                 # Surgical consult demo UI
│   ├── rounds.html                # Rounds prep demo UI
│   ├── app.js                     # Interactive consult app + live AI
│   ├── rounds-app.js              # Interactive rounds app
│   ├── style.css                  # Shared styles
│   ├── cases/                     # Demo case JSON files
│   └── rounds-cases/              # Rounds demo patients
│
├── vercel.json                    # Vercel deployment config
└── README.md
```

---

## License

Personal portfolio project. Not for clinical use without proper validation, regulatory approval, and HIPAA compliance infrastructure.

---

## Contact

**Christopher Stephenson, MD**

- Email: christopherstephenson8@gmail.com
- LinkedIn: [christopher-stephenson-md](https://www.linkedin.com/in/christopher-stephenson-md)
- GitHub: [cas23d](https://github.com/cas23d)
