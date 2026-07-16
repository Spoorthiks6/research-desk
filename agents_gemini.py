"""
Multi-agent Research -> Draft -> Critic pipeline.

Uses Google Gemini (free tier via Google AI Studio) instead of a paid API.
Get a free key at: https://aistudio.google.com/apikey  (no credit card needed)

Design:
- Each agent is just a function that calls the Gemini API with a specific
  system prompt and returns text. No framework, no magic.
- State is passed explicitly between functions (a plain dataclass), so it's
  easy to debug, log, and explain in a demo/Q&A.
- The Researcher agent gets Gemini's built-in Google Search grounding tool.
  Drafter and Critic are pure text-in/text-out reasoning steps.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from dataclasses import dataclass, field
from typing import Callable, Optional

# Load .env from this file's own directory, regardless of where the
# process was launched from.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GEMINI_API_KEY not found. Get a free key at "
        "https://aistudio.google.com/apikey and add it to .env as "
        "GEMINI_API_KEY=your-key-here (no quotes)."
    )

MODEL = "gemini-flash-latest"  # Google-maintained alias, auto-tracks current stable Flash
MAX_CRITIC_LOOPS = 2  # cap revision loops so the demo can't hang

client = genai.Client(api_key=_api_key)


@dataclass
class PipelineState:
    topic: str
    research_notes: str = ""
    draft: str = ""
    critique: str = ""
    revision_count: int = 0
    log: list = field(default_factory=list)


def _call_gemini(system: str, user_message: str, use_search: bool = False) -> str:
    """Single call wrapper. Keeps API surface in one place."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=[types.Tool(google_search=types.GoogleSearch())] if use_search else None,
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=config,
    )
    return (response.text or "").strip()


# ---------------------------------------------------------------------
# Agent 1: Researcher
# ---------------------------------------------------------------------
RESEARCHER_SYSTEM = """You are a Research Agent. Your only job is to gather
accurate, current, well-organized information on the given topic using web
search. Do not draft a report or give opinions - just produce a clean,
factual briefing document with bullet points, key facts, numbers, and
source names. Flag anything uncertain or disputed. Be concise: aim for
under 400 words."""


def run_researcher(topic: str, on_chunk: Optional[Callable[[str], None]] = None) -> str:
    notes = _call_gemini(RESEARCHER_SYSTEM, f"Research topic: {topic}", use_search=True)
    if on_chunk:
        on_chunk(notes)
    return notes


# ---------------------------------------------------------------------
# Agent 2: Drafter
# ---------------------------------------------------------------------
DRAFTER_SYSTEM = """You are a Drafting Agent. You take research notes and
turn them into a clear, well-structured report for a general audience.
Use short paragraphs and headers where useful. Do not invent facts beyond
what's in the research notes. If the notes are thin on a point, say so
briefly rather than fabricating detail. Aim for under 500 words unless the
topic clearly needs more."""


def run_drafter(topic: str, research_notes: str, prior_critique: str = "",
                 on_chunk: Optional[Callable[[str], None]] = None) -> str:
    user_msg = f"Topic: {topic}\n\nResearch notes:\n{research_notes}"
    if prior_critique:
        user_msg += f"\n\nRevise your previous draft based on this critique:\n{prior_critique}"
    draft = _call_gemini(DRAFTER_SYSTEM, user_msg)
    if on_chunk:
        on_chunk(draft)
    return draft


# ---------------------------------------------------------------------
# Agent 3: Critic
# ---------------------------------------------------------------------
CRITIC_SYSTEM = """You are a Critic Agent. Review the draft report against
the research notes for accuracy, clarity, and completeness. Be specific
and constructive. If the draft is genuinely solid, say APPROVED as the
first word of your response and briefly say why. If it needs work, say
REVISE as the first word, then give 2-4 concrete, actionable points the
Drafting Agent should fix. Keep it under 200 words."""


def run_critic(topic: str, research_notes: str, draft: str,
                on_chunk: Optional[Callable[[str], None]] = None) -> str:
    user_msg = (
        f"Topic: {topic}\n\nResearch notes:\n{research_notes}\n\nDraft:\n{draft}"
    )
    critique = _call_gemini(CRITIC_SYSTEM, user_msg)
    if on_chunk:
        on_chunk(critique)
    return critique


# ---------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------
def run_pipeline(topic: str, callbacks: dict = None) -> PipelineState:
    """
    callbacks: optional dict with keys 'on_research', 'on_draft', 'on_critique'
    each a function(text) used to stream output to a UI as it's produced.
    """
    callbacks = callbacks or {}
    state = PipelineState(topic=topic)

    state.research_notes = run_researcher(topic, callbacks.get("on_research"))
    state.log.append(("research", state.research_notes))

    state.draft = run_drafter(topic, state.research_notes,
                               on_chunk=callbacks.get("on_draft"))
    state.log.append(("draft", state.draft))

    for i in range(MAX_CRITIC_LOOPS):
        state.critique = run_critic(topic, state.research_notes, state.draft,
                                     on_chunk=callbacks.get("on_critique"))
        state.log.append(("critique", state.critique))

        if state.critique.strip().upper().startswith("APPROVED"):
            break

        state.revision_count += 1
        state.draft = run_drafter(topic, state.research_notes,
                                   prior_critique=state.critique,
                                   on_chunk=callbacks.get("on_draft"))
        state.log.append(("draft_revision", state.draft))

    return state
