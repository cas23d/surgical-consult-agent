# Surgical Consult Agent

A CLI-based AI agent that guides surgery residents through a structured 5-stage consult workflow using Claude. The AI drives the conversation — you just answer the questions.

## How It Works

The agent implements a state-machine architecture with five stages:

1. **Consult Lock** — AI asks for the reason for consult (e.g., "R/O SBO")
2. **Guided Data Capture** — AI generates a context-aware checklist based on consult type; resident provides clinical data in freeform
3. **Synthesis** — AI generates a draft EMR note and staffing summary from collected data
4. **Active Verification** — AI highlights 2-3 critical decision points for the resident to confirm or correct
5. **Finalization** — AI outputs a clean, copy-paste-ready EMR note, staffing summary, and ranked follow-up tasks

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/surgical-consult-agent.git
cd surgical-consult-agent
pip install -r requirements.txt
cp .env.example .env
# Add your Anthropic API key to .env
```

## Usage

```bash
python consult_agent.py
```

Walk through the prompts — the agent guides you through each stage.

## Design Principles

- **No frameworks** — Raw Anthropic API calls. No LangChain, no abstractions. Every API call is visible and understandable.
- **State-machine architecture** — Each stage has a defined input, output, and transition. The workflow is deterministic even though the AI responses are generative.
- **Conversation history managed manually** — Messages are appended to a list and passed to the API. This is the fundamental pattern all agent frameworks abstract away.
- **Designed for messy input** — Residents are tired and busy. The agent accepts shorthand, bullet points, whatever format and organizes it.

## Architecture

```
User input → [Stage 1: Lock consult type]
           → [Stage 2: Generate checklist → collect data]
           → [Stage 3: Synthesize note + staffing summary]
           → [Stage 4: Verify critical decision points]
           → [Stage 5: Finalize outputs]
           → EMR note + staffing summary + follow-up tasks
```

State is passed between stages via a simple Python dict — no database, no persistence layer. The entire workflow runs in a single session.

## Requirements

- Python 3.10+
- Anthropic API key

## Built By

Christopher Stephenson, MD
