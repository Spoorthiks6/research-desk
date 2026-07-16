

import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS
from dataclasses import dataclass, field
from typing import Callable, Optional

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

_api_key = os.environ.get("GROQ_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GROQ_API_KEY not found. Get a free key at "
        "https://console.groq.com/keys and add it to .env as "
        "GROQ_API_KEY=your-key-here (no quotes)."
    )

MODEL = "llama-3.3-70b-versatile"  # strong free-tier model on Groq
MAX_CRITIC_LOOPS = 2  # cap revision loops so the demo can't hang

client = Groq(api_key=_api_key)


@dataclass
class PipelineState:
    topic: str
    research_notes: str = ""
    draft: str = ""
    critique: str = ""
    revision_count: int = 0
    log: list = field(default_factory=list)


def _call_groq(system: str, user_message: str) -> str:
    """Single call wrapper. Keeps API surface in one place."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1500,
    )
    return (response.choices[0].message.content or "").strip()


def _web_search(query: str, max_results: int = 6) -> str:
    """Free DuckDuckGo search, no API key required."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return f"(search failed: {e})"

    if not results:
        return "(no search results found)"

    formatted = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        formatted.append(f"- {title}: {body} [source: {href}]")
    return "\n".join(formatted)


RESEARCHER_SYSTEM = """You are a Research Agent. You will be given raw web
search results on a topic. Your job is to turn them into a clean, factual
briefing document: bullet points, key facts, numbers, and source names.
Do not draft a report or give opinions. Flag anything uncertain or
disputed, or where the search results seem thin. Be concise: aim for
under 400 words."""


def run_researcher(topic: str, on_chunk: Optional[Callable[[str], None]] = None) -> str:
    raw_results = _web_search(topic)
    notes = _call_groq(
        RESEARCHER_SYSTEM,
        f"Topic: {topic}\n\nRaw search results:\n{raw_results}",
    )
    if on_chunk:
        on_chunk(notes)
    return notes



def run_drafter(topic: str, research_notes: str, prior_critique: str = "",
                 on_chunk: Optional[Callable[[str], None]] = None) -> str:
    user_msg = f"Topic: {topic}\n\nResearch notes:\n{research_notes}"
    if prior_critique:
        user_msg += f"\n\nRevise your previous draft based on this critique:\n{prior_critique}"
    draft = _call_groq(DRAFTER_SYSTEM, user_msg)
    if on_chunk:
        on_chunk(draft)
    return draft



def run_critic(topic: str, research_notes: str, draft: str,
                on_chunk: Optional[Callable[[str], None]] = None) -> str:
    user_msg = (
        f"Topic: {topic}\n\nResearch notes:\n{research_notes}\n\nDraft:\n{draft}"
    )
    critique = _call_groq(CRITIC_SYSTEM, user_msg)
    if on_chunk:
        on_chunk(critique)
    return critique

def run_pipeline(topic: str, callbacks: dict = None) -> PipelineState:
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
