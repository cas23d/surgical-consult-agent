# Surgical Consult Agent + Rounds Prep

**[Live Demo](https://surgical-consult-agent.vercel.app/)**

An AI-powered clinical decision support system built by a surgery resident for surgery residents. Two complementary workflows — surgical consults and morning rounds — demonstrating how clinical expertise and AI can combine to solve real workflow problems.

---

## What's New (February 2026)

The demo is now **fully interactive with a live backend**:

✅ **Live Flask API** — Real-time streaming responses from Claude
✅ **Editable Inputs** — Modify exam findings and watch AI re-analyze in real-time
✅ **Session History** — Consults saved to Supabase, accessible across visits
✅ **Mobile Responsive** — Optimized for desktop, tablet, and mobile
✅ **Production-Ready** — Error handling, logging, type hints, CORS support

---

## Quick Start

### Option 1: Try the Interactive Demo Online

Visit: https://cas23d.github.io/surgical-consult-agent/

Click a case to see the agent in action. (Note: Static demo — for full interactivity with editable inputs, deploy locally.)

### Option 2: Run Locally (Full Interactive Features)

**Prerequisites:**
- Python 3.10+
- Anthropic API key
- Supabase credentials (free account available)

**Setup (5 minutes):**

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your Anthropic API key and Supabase URL/key

# Start Flask backend (Terminal 1)
python api.py

# Serve frontend (Terminal 2)
cd web
python -m http.server 8000

# Open browser to http://localhost:8000/index.html
```

Full deployment guide in [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Architecture

```
Web Frontend                Flask Backend               External Services
(HTML/CSS/JS)              (Python/Anthropic)          (Claude API, Supabase)
     │                             │                           │
     ├─ app.js (interactive)       │                           │
     ├─ index.html                 ├─ /api/consult/* (streaming)
     ├─ style.css                  ├─ /api/session (persistence)
     └─ cases/ (demo data)         ├─ Session management ─────→ Supabase
                                   └─ Error handling, logging    (PostgreSQL)
                                                          ─────→ Anthropic
                                                           Claude API
```

---

## API Endpoints

### Session Management
```
POST   /api/session                    Create or retrieve user session
GET    /api/session/history            Get user's recent consults
```

### Consult Workflow (Streaming)
```
POST   /api/consult/triage             Generate triage analysis
POST   /api/consult/context            Generate gaps analysis
POST   /api/consult/plan               Generate assessment & plan
POST   /api/consult/note               Generate final consult note
```

All consult endpoints return `text/event-stream` for real-time display.

### Data Persistence
```
POST   /api/consult/save               Save completed consult to database
```

---

## Key Features

### 1. Real-Time Interaction
Edit the "Resident Exam Findings" textarea — the AI re-analyzes with your input in real-time.

### 2. Session Persistence
Browser stores a unique session ID. Your consult history is saved, so you can return and see previous work.

### 3. Streaming Responses
Outputs appear progressively in real-time, not in bulk. Users can start reading immediately.

### 4. Mobile Responsive
Layouts adapt from two-panel (desktop) to stacked (mobile). Fully functional on phones and tablets.

### 5. Clinical by Design
- No frameworks, no abstractions — raw Claude API calls
- Handles real surgical workflows under fatigue
- Designed for "hour 28" (worst case), not best case
- Guideline citations, not generic summaries

---

## Design Philosophy

**Core Principle:** Systems must work at hour 28 of a shift, when cognitive reserve is exhausted.

**Seven Design Principles:**
1. **Cognitive Load Reduction** — System tracks state; user's brain is free to think
2. **Complexity Embedding** — Complex logic hidden; simple user interface
3. **Multi-Output Efficiency** — One input → multiple structured outputs
4. **Verification Loops** — AI output validated at decision points before use
5. **Context Awareness** — Auto-pull data from screen; minimize manual entry
6. **Delimiter-Based Parsing** — Structured outputs enable automation
7. **Design for Worst Moment** — If it works only when alert, it fails when needed

---

## File Structure

```
.
├── api.py                          # Flask backend with API endpoints
├── consult_agent.py                # CLI surgical consult workflow
├── rounds_agent.py                 # CLI morning rounds workflow
├── fhir_client.py                  # FHIR R4 EHR data pulling
├── prompts.py                      # Claude system & stage prompts
├── rounds_prompts.py               # Rounds workflow prompts
│
├── web/
│   ├── index.html                  # Surgical consult demo UI
│   ├── rounds.html                 # Rounds prep demo UI
│   ├── app.js                      # Interactive consult app
│   ├── rounds-app.js               # Interactive rounds app
│   ├── style.css                   # Shared styles (responsive)
│   ├── cases/                      # Demo case JSON files
│   └── rounds-cases/               # Rounds demo patients
│
├── DEPLOYMENT.md                   # Setup & production deployment guide
├── VIDEO_GUIDE.md                  # How to record demo video
├── TESTIMONIALS_GUIDE.md           # Getting clinical validation
└── README.md                       # This file
```

---

## Workflows

### Surgical Consult Agent

**Use Case:** New consult arrives. Resident needs to answer: "Is this patient sick?"

**Stages:**
1. **Triage** — Red flags, sepsis criteria, end-organ dysfunction
2. **Context & Gaps** — What's been done, what's missing
3. **Assessment & Plan** — Evidence-based recommendations (guideline citations)
4. **Final Note** — Copy-paste-ready consult note + staffing summary

**Input:** Consult message + patient chart data + resident exam findings
**Output:** Structured analysis → final EMR-ready note

### Rounds Prep (CLI Ready)

```bash
python rounds_agent.py
```

**Use Case:** AM chart check for existing patients.

**Stages:**
1. **Alerts & Day Plan** — Critical labs flagged by severity
2. **Presentation** — 100-word attending presentation
3. **AM Brief** — Overnight summary vs. yesterday's plan

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Anthropic Claude (Sonnet 4) |
| **Backend** | Python 3.10+, Flask |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | Supabase (PostgreSQL) |
| **EHR Integration** | FHIR R4 (HAPI FHIR) |
| **Deployment** | Docker, Heroku, Vercel, AWS |

---

## Development

### Code Quality
- ✅ Type hints on all functions
- ✅ Comprehensive error handling
- ✅ Logging throughout (structured)
- ✅ Input validation on API endpoints
- ✅ CORS headers for cross-origin requests
- ✅ Streaming responses for real-time display

### Database (Supabase)
- `consult_sessions` — User session tracking
- `consult_history` — Saved consults with metadata
- RLS policies for data access control
- Indexes for query performance

---

## Next Steps for Hiring Impact

### 1. Record a Video Demo (2-3 min)
See [VIDEO_GUIDE.md](VIDEO_GUIDE.md) for:
- Detailed script
- Recording setup
- Sharing & embedding
- What makes it compelling to hiring managers

### 2. Get Clinical Testimonials
See [TESTIMONIALS_GUIDE.md](TESTIMONIALS_GUIDE.md) for:
- Who to ask
- How to request
- Where to display
- Why testimonials matter

### 3. Deploy Live Backend
See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Local development setup
- Docker deployment
- Heroku/Vercel production
- Performance optimization

---

## Requirements

- **Runtime:** Python 3.10+
- **API Keys:** Anthropic, Supabase
- **Browser:** Chrome 60+, Firefox 55+, Safari 10+ (for streaming support)
- **Network:** Internet connection for Claude API and Supabase

## License

Personal portfolio project. Not for clinical use without proper validation, regulatory approval, and HIPAA compliance infrastructure.

---

## Contact

**Christopher Stephenson, MD**

- Email: christopherstephenson8@gmail.com
- Phone: (317) 938-7424
- LinkedIn: [christopher-stephenson-md](https://www.linkedin.com/in/christopher-stephenson-md)
- GitHub: [cas23d](https://github.com/cas23d)

---

## Credentials

- **MD** — University of Nebraska Medical Center (2022)
- **PGY-4 Surgery** — Prisma Health / University of South Carolina
- **AOA** — Alpha Omega Alpha (top quartile)
- **Honors** — Big Ten Medal of Honor, NCAA All-American
- **Clinical Focus** — Trauma, surgical oncology, minimally invasive, robotic surgery
- **AI Experience** — 2 years building clinical workflows with Claude and LLMs
