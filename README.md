# Multi-Agent Research Assistant

A three-agent pipeline — **Researcher → Drafter → Critic** — that researches
a topic, drafts a report, and iterates on it until a critic agent approves.
Built for a weekend hackathon build.

## Why this project

Most hackathon LLM demos are a single chatbot. This one *visibly* shows
multiple agents handing work off and disagreeing with each other in real
time, which is far more memorable to judges than a single Q&A box.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=sk-...   # or use a .env loader of your choice
streamlit run app.py
```

## How it works

1. **Researcher agent** — uses Claude's web search tool to gather current,
   factual notes on the topic.
2. **Drafter agent** — turns those notes into a readable report.
3. **Critic agent** — checks the draft against the research notes. If it's
   not good enough, it sends specific feedback back to the Drafter. This
   loops up to 2 times, then stops (so a demo can never hang forever).

State is passed as a plain Python dict/dataclass between agent functions —
no LangGraph/CrewAI. This is a deliberate choice for a weekend build: it's
easier to debug live, and easier to explain to judges in Q&A ("here's
exactly what data moves between agents and why").

## Customizing for your hackathon theme

The pipeline is domain-agnostic — swap the topic for anything:
- Due-diligence briefs for a VC/startup theme
- Study guides for an edtech theme
- Policy briefs for a govtech/civic theme

Just retitle the app and adjust the system prompts in `agents.py` slightly
(e.g., "Critic" could check for legal accuracy, for cited sources, etc.)
to match your specific use case — a named use case beats a generic tool
in judging.

## Demo tips

- Pre-test 2-3 topics beforehand so you know the pipeline handles them
  well and roughly how long they take.
- Point out the moment (if it happens) where the Critic sends the draft
  back for revision — that's the "aha" moment for the audience.
- Have a screen-recorded backup demo in case live API calls are slow or
  flaky during judging.
- One slide with the 3-agent diagram (Researcher → Drafter → Critic, with
  the revision loop drawn as an arrow back) helps judges follow along.

## Known limitations (be ready to mention these if asked)

- No persistent memory between runs — each topic starts fresh.
- Web search quality depends on what's indexed; very niche or very recent
  topics may get thin research notes.
- Revision loop is capped at 2 rounds to keep demo time predictable.

## File structure

```
multi-agent-research/
├── agents.py          # Core orchestration logic (3 agents + pipeline)
├── app.py             # Streamlit UI
├── requirements.txt
├── .env.example
└── README.md
```
