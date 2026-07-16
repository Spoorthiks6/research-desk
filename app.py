"""
Streamlit UI for the Research -> Draft -> Critic multi-agent pipeline.

Visual concept: a lab notebook / editorial desk. The Researcher's notes
look like typewritten field notes, the Drafter's output is a manuscript
page, and the Critic's feedback appears as literal red-pen marginalia.
An approved report gets a rotated ink-stamp treatment.

Includes a Day/Night toggle - both modes are driven by the same CSS
variables, so any element using var(--ink) etc. stays correct in either
mode automatically.

Run with: streamlit run app.py
"""

import streamlit as st
from agents_groq import run_pipeline

st.set_page_config(page_title="Research Desk", layout="wide", page_icon="📋")

if "mode" not in st.session_state:
    st.session_state.mode = "Day"

mode = st.session_state.mode

if mode == "Day":
    paper = "#EDE6D3"
    paper_dark = "#E3DAC2"
    ink = "#21221D"
    steel = "#1F3A5C"
    rule = "#C7BEA6"
    redpen = "#A32F1D"
    stamp = "#2E5233"
    surface_text = "#EDE6D3"
else:
    paper = "#1B1C1A"
    paper_dark = "#2A2B28"
    ink = "#F3F1E7"
    steel = "#A8BED1"
    rule = "#4D5158"
    redpen = "#F16A5A"
    stamp = "#8BC3A9"
    surface_text = "#F3F1E7"

# ---------------------------------------------------------------------
# Design tokens + global styling
# ---------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Newsreader:ital,wght@0,400;0,500;1,400&family=Space+Mono:wght@400;700&family=Caveat:wght@500;700&display=swap');

:root {
  --paper: """ + paper + """;
  --paper-dark: """ + paper_dark + """;
  --ink: """ + ink + """;
  --redpen: """ + redpen + """;
  --stamp: """ + stamp + """;
  --steel: """ + steel + """;
  --rule: """ + rule + """;
  --surface-text: """ + surface_text + """;
}

/* Base canvas */
.stApp {
  background: var(--paper);
  color: var(--ink);
}

/* Native Streamlit text elements: forced to the mode-aware ink color.
   These are wired to var(--ink) (not a static config.toml color) so
   they stay correct in BOTH Day and Night mode automatically. */
.stApp label, .stApp p,
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"] p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
h1, h2, h3, h4, h5, h6 {
  color: var(--ink) !important;
}

.stSelectbox > div > div > div,
.stSelectbox button,
.stSelectbox [role="button"],
.stRadio > div > label,
.stRadio [role="radio"] {
  background: var(--paper-dark) !important;
  color: var(--ink) !important;
  border: 1px solid var(--rule) !important;
}
.stSelectbox [role="option"] {
  background: var(--paper) !important;
  color: var(--ink) !important;
}
.stRadio [role="radio"] {
  background: var(--paper-dark) !important;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

/* Title block */
.desk-title {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 2.6rem;
  color: var(--ink);
  letter-spacing: -0.01em;
  margin-bottom: 0.1rem;
}
.desk-subtitle {
  font-family: 'Space Mono', monospace;
  font-size: 0.85rem;
  color: var(--steel);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 1.6rem;
}

/* Relay / station line */
.station-line {
  display: flex;
  align-items: center;
  margin: 1.4rem 0 2rem 0;
}
.station-node {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: 'Space Mono', monospace;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  color: var(--ink);
  opacity: 0.45;
}
.station-node.active {
  opacity: 1;
}
.station-plate {
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 1.5px solid var(--ink);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700;
  background: var(--paper);
  color: var(--ink);
}
.station-node.active .station-plate {
  background: var(--redpen);
  border-color: var(--redpen);
  color: var(--surface-text);
  animation: pulse 1.4s ease-in-out infinite;
}
.station-node.done .station-plate {
  background: var(--stamp);
  border-color: var(--stamp);
  color: var(--surface-text);
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(163,47,29,0.35); }
  50% { box-shadow: 0 0 0 6px rgba(163,47,29,0); }
}
.station-rule {
  flex: 1;
  height: 1px;
  background: var(--rule);
  margin: 0 0.8rem;
}

/* Cards */
.desk-card {
  background: var(--paper-dark);
  border: 1px solid var(--rule);
  border-radius: 2px;
  padding: 1.1rem 1.2rem;
  min-height: 120px;
}
.desk-card-label {
  font-family: 'Space Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--steel);
  margin-bottom: 0.6rem;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 0.4rem;
}
.desk-placeholder {
  color: var(--ink);
  opacity: 0.4;
  font-family: 'Newsreader', serif;
  font-style: italic;
}

/* Researcher: typewritten field notes */
.field-notes {
  font-family: 'Space Mono', monospace;
  font-size: 0.85rem;
  line-height: 1.55;
  color: var(--ink);
  white-space: pre-wrap;
}

/* Drafter: manuscript page */
.manuscript {
  font-family: 'Newsreader', serif;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--ink);
}
.manuscript h1, .manuscript h2, .manuscript h3 {
  font-family: 'Fraunces', serif;
  color: var(--ink) !important;
}

/* Critic: red-pen marginalia */
.marginalia {
  font-family: 'Caveat', cursive;
  font-size: 1.35rem;
  line-height: 1.35;
  color: var(--redpen) !important;
  transform: rotate(-0.4deg);
}
.verdict-approved {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  color: var(--stamp) !important;
  border: 2px solid var(--stamp);
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 3px;
  transform: rotate(-3deg);
  margin-bottom: 0.5rem;
  letter-spacing: 0.03em;
}
.verdict-revise {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  color: var(--redpen) !important;
  border: 2px dashed var(--redpen);
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 3px;
  transform: rotate(-3deg);
  margin-bottom: 0.5rem;
  letter-spacing: 0.03em;
}

/* Final report stamp */
.final-report {
  background: var(--paper-dark);
  border: 1px solid var(--rule);
  padding: 2rem 2.4rem;
  position: relative;
  font-family: 'Newsreader', serif;
  font-size: 1.05rem;
  line-height: 1.65;
  color: var(--ink);
  margin-top: 1rem;
}
.final-report h1, .final-report h2, .final-report h3 {
  font-family: 'Fraunces', serif;
  color: var(--ink) !important;
}
.stamp {
  position: absolute;
  top: 1.6rem;
  right: 2rem;
  font-family: 'Space Mono', monospace;
  font-weight: 700;
  font-size: 1rem;
  color: var(--stamp) !important;
  border: 3px solid var(--stamp);
  padding: 0.3rem 0.9rem;
  border-radius: 4px;
  transform: rotate(-9deg);
  letter-spacing: 0.06em;
  opacity: 0.85;
}

/* Input + button */
.stTextInput input {
  font-family: 'Newsreader', serif;
  font-size: 1.05rem;
  background: var(--paper-dark) !important;
  border: 1px solid var(--rule) !important;
  color: var(--ink) !important;
}
.stTextInput input::placeholder {
  color: var(--steel) !important;
  opacity: 1 !important;
}
.stButton button {
  font-family: 'Space Mono', monospace;
  background: var(--ink) !important;
  color: var(--paper) !important;
  border: none !important;
  letter-spacing: 0.04em;
  border-radius: 2px !important;
}
.stButton button * {
  color: var(--paper) !important;
}
.stButton button:hover {
  background: var(--redpen) !important;
}
.stButton button:hover * {
  color: var(--surface-text) !important;
}

/* Kebab menu (mode switcher) */
.desk-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
[data-testid="stPopover"] button {
  background: transparent !important;
  border: 1px solid var(--rule) !important;
  color: var(--ink) !important;
  border-radius: 4px !important;
  font-family: 'Space Mono', monospace;
  padding: 0.25rem 0.7rem !important;
  min-height: 0 !important;
  line-height: 1.2 !important;
}
[data-testid="stPopover"] button:hover {
  background: var(--paper-dark) !important;
  border-color: var(--ink) !important;
}
[data-testid="stPopoverBody"] {
  background: var(--paper-dark) !important;
  border: 1px solid var(--rule) !important;
}
[data-testid="stPopoverBody"] * {
  color: var(--ink) !important;
  font-family: 'Newsreader', serif !important;
}
.menu-label {
  font-family: 'Space Mono', monospace !important;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--steel) !important;
  margin-bottom: 0.4rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--paper-dark);
  border-right: 1px solid var(--rule);
}
[data-testid="stSidebar"] * {
  font-family: 'Newsreader', serif;
  color: var(--ink) !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
title_col, menu_col = st.columns([12, 1])

with title_col:
    st.markdown('<div class="desk-title">The Research Desk</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="desk-subtitle">Researcher &rarr; Drafter &rarr; Critic &middot; a three-hand pipeline</div>',
        unsafe_allow_html=True,
    )

with menu_col:
    with st.popover("⋮", use_container_width=True):
        st.markdown('<div class="menu-label">Color mode</div>', unsafe_allow_html=True)
        chosen_mode = st.radio(
            "Color mode",
            ["Day", "Night"],
            index=["Day", "Night"].index(st.session_state.mode),
            label_visibility="collapsed",
            key="mode_radio",
        )
        if chosen_mode != st.session_state.mode:
            st.session_state.mode = chosen_mode
            st.rerun()

with st.sidebar:
    st.markdown("#### How it works")
    st.markdown(
        """
        **01 · Researcher** pulls facts from the web into raw field notes.

        **02 · Drafter** turns those notes into a readable manuscript.

        **03 · Critic** marks it up in red pen. If it's not ready, the
        marked-up draft goes back to the Drafter — up to two rounds.
        """
    )
    st.divider()
    st.caption("Set GROQ_API_KEY in your .env file before running (free key: console.groq.com/keys).")

topic = st.text_input(
    "Topic for the desk to research",
    placeholder="e.g. Impact of on-device LLMs on mobile app design in 2026",
)
run_button = st.button("Send to the desk →", type="primary")

station_line = st.empty()


def render_stations(active: int, done: set):
    labels = ["RESEARCH", "DRAFT", "REVIEW"]
    nodes = []
    for i, label in enumerate(labels, start=1):
        cls = "station-node"
        if i in done:
            cls += " done"
        elif i == active:
            cls += " active"
        nodes.append(
            f'<div class="{cls}"><div class="station-plate">{i:02d}</div>{label}</div>'
        )
    rule = '<div class="station-rule"></div>'
    html = '<div class="station-line">' + rule.join(nodes) + "</div>"
    station_line.markdown(html, unsafe_allow_html=True)


render_stations(0, set())

col1, col2, col3 = st.columns(3)
research_box = col1.empty()
draft_box = col2.empty()
critique_box = col3.empty()


def render_card(placeholder, label, body_html):
    placeholder.markdown(
        f'<div class="desk-card"><div class="desk-card-label">{label}</div>{body_html}</div>',
        unsafe_allow_html=True,
    )


render_card(research_box, "01 · Field Notes", '<span class="desk-placeholder">Waiting...</span>')
render_card(draft_box, "02 · Manuscript", '<span class="desk-placeholder">Waiting...</span>')
render_card(critique_box, "03 · Red Pen", '<span class="desk-placeholder">Waiting...</span>')

status = st.empty()
final_box = st.empty()

if run_button:
    if not topic.strip():
        st.warning("Give the desk a topic first.")
    else:
        done_stations = set()
        draft_round = {"n": 0}

        def on_research(text):
            render_stations(1, done_stations)
            render_card(research_box, "01 · Field Notes", f'<div class="field-notes">{text}</div>')
            done_stations.add(1)
            render_stations(2, done_stations)

        def on_draft(text):
            round_label = "Manuscript" if draft_round["n"] == 0 else f"Revision {draft_round['n']}"
            draft_round["n"] += 1
            render_card(draft_box, f"02 · {round_label}", f'<div class="manuscript">{text}</div>')

        def on_critique(text):
            approved = text.strip().upper().startswith("APPROVED")
            verdict_html = (
                '<div class="verdict-approved">✓ APPROVED</div>'
                if approved else
                '<div class="verdict-revise">↺ REVISE</div>'
            )
            render_card(
                critique_box, "03 · Red Pen",
                f'{verdict_html}<div class="marginalia">{text}</div>'
            )
            if approved:
                done_stations.add(2)
                done_stations.add(3)
                render_stations(3, done_stations)

        render_stations(1, done_stations)
        status.info("The desk is working \u2014 roughly 20\u201360s depending on revisions.")

        try:
            result = run_pipeline(
                topic,
                callbacks={
                    "on_research": on_research,
                    "on_draft": on_draft,
                    "on_critique": on_critique,
                },
            )
            status.success(f"Filed \u2014 {result.revision_count} revision round(s) before approval.")

            stamp_html = '<div class="stamp">APPROVED</div>' if result.critique.strip().upper().startswith("APPROVED") else ""
            final_box.markdown(
                f'<div class="final-report">{stamp_html}<h2>Final Report</h2>{result.draft}</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            status.error(f"The desk hit a snag: {e}")