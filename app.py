"""
AI Video Search & Transcription Agent — Streamlit Web Interface.

A clean, professional dashboard for interacting with the multi-tool
AI agent, browsing the knowledge base, and reading saved transcripts.
"""

import json
import time
import streamlit as st
from pathlib import Path

# ── Bootstrap ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Video Transcription Agent",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Fonts ─────────────────────────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }

  /* ── Page chrome ───────────────────────────────────────────── */
  .stApp { background: #0a0a0f; }
  header[data-testid="stHeader"] { background: transparent; }

  /* ── Sidebar ───────────────────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1019 0%, #12121f 100%);
    border-right: 1px solid rgba(255,255,255,.06);
  }
  section[data-testid="stSidebar"] .stMarkdown h1,
  section[data-testid="stSidebar"] .stMarkdown h2,
  section[data-testid="stSidebar"] .stMarkdown h3 { color: #e2e2e8; }

  /* ── Accent colour tokens ──────────────────────────────────── */
  :root {
    --accent: #6c63ff;
    --accent-soft: rgba(108,99,255,.12);
    --surface: #14141f;
    --surface-raised: #1a1a2e;
    --border: rgba(255,255,255,.07);
    --text-primary: #e8e8ed;
    --text-secondary: #8888a0;
  }

  /* ── Cards ─────────────────────────────────────────────────── */
  .card {
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color .2s;
  }
  .card:hover { border-color: rgba(108,99,255,.35); }

  /* ── Tool-step timeline ────────────────────────────────────── */
  .step-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: .78rem; font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: .5rem;
  }
  .step-pill.result { background: rgba(52,211,153,.10); color: #34d399; }

  /* ── Chat bubbles ──────────────────────────────────────────── */
  .user-msg {
    background: linear-gradient(135deg, #6c63ff 0%, #5548d9 100%);
    color: #fff;
    padding: .85rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 72%;
    margin-left: auto;
    margin-bottom: .75rem;
    font-size: .92rem;
    line-height: 1.5;
  }
  .agent-msg {
    background: var(--surface-raised);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: .85rem 1.2rem;
    border-radius: 18px 18px 18px 4px;
    max-width: 85%;
    margin-bottom: .75rem;
    font-size: .92rem;
    line-height: 1.6;
  }

  /* ── Stat chips ────────────────────────────────────────────── */
  .stat-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1.2rem; }
  .stat-chip {
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: .6rem 1rem;
    flex: 1; min-width: 130px;
    text-align: center;
  }
  .stat-chip .label { color: var(--text-secondary); font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; }
  .stat-chip .value { color: var(--text-primary); font-size: 1.35rem; font-weight: 700; margin-top: 2px; }

  /* ── KB file cards ──────────────────────────────────────────── */
  .kb-card {
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: .75rem;
    cursor: pointer;
    transition: all .2s;
  }
  .kb-card:hover { border-color: var(--accent); transform: translateY(-1px); }
  .kb-title { color: var(--text-primary); font-weight: 600; font-size: .95rem; margin-bottom: 4px; }
  .kb-meta { color: var(--text-secondary); font-size: .78rem; }

  /* ── Hide Streamlit defaults ───────────────────────────────── */
  #MainMenu, footer, .stDeployButton { display: none !important; }

  /* ── Text input styling ────────────────────────────────────── */
  .stTextInput > div > div > input {
    background: var(--surface-raised) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
    padding: .7rem 1rem !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-soft) !important;
  }

  /* ── Button styling ────────────────────────────────────────── */
  .stButton > button {
    background: linear-gradient(135deg, #6c63ff 0%, #5548d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: .55rem 1.6rem !important;
    transition: opacity .2s !important;
  }
  .stButton > button:hover { opacity: .88 !important; }

  /* ── Expander styling ──────────────────────────────────────── */
  .streamlit-expanderHeader { color: var(--text-primary) !important; font-weight: 500 !important; }

  /* ── Tabs ───────────────────────────────────────────────────── */
  .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid var(--border); }
  .stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    padding: .6rem 1.2rem !important;
    border-bottom: 2px solid transparent;
  }
  .stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Lazy imports (after page config) ─────────────────────────────────────────
from src.ai_video_transcribe_agent.config import Config
from src.ai_video_transcribe_agent.agent import VideoTranscribeAgent
from src.ai_video_transcribe_agent.tools.knowledge_base import list_knowledge_base_transcripts


# ── Session state initialisation ─────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_steps" not in st.session_state:
    st.session_state.agent_steps = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# ── Helper: format tool names for display ────────────────────────────────────
TOOL_LABELS = {
    "search_youtube_videos": ("Search Videos", "🔍"),
    "transcribe_video": ("Transcribe", "🎙️"),
    "list_knowledge_base": ("Knowledge Base", "📚"),
}


def _tool_label(name: str) -> tuple[str, str]:
    return TOOL_LABELS.get(name, (name, "⚙️"))


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ◎ Agent Config")
    st.caption("Adjust agent behaviour and inspect API status.")

    provider = st.radio(
        "LLM Provider",
        ["groq", "gemini"],
        index=0,
        horizontal=True,
        help="Groq = fast tool-calling via Llama. Gemini = auto function calling.",
    )

    st.markdown("---")
    st.markdown("### API Key Status")
    key_status = Config.validate_keys()
    for svc, ok in key_status.items():
        icon = "●" if ok else "○"
        colour = "#34d399" if ok else "#f87171"
        st.markdown(
            f'<span style="color:{colour};font-weight:600">{icon}</span>&ensp;'
            f'<span style="color:var(--text-primary);font-size:.88rem">{svc.upper()}</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Quick prompts")
    prompts = [
        "Find a short video on Python decorators and transcribe it",
        "What transcripts are in my knowledge base?",
    ]
    for p in prompts:
        if st.button(p, key=f"qp_{hash(p)}", use_container_width=True):
            st.session_state["_prefill"] = p
            st.rerun()


# ── Main area: Tabs ──────────────────────────────────────────────────────────
tab_agent, tab_kb = st.tabs(["Agent", "Knowledge Base"])

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1 — Agent Chat
# ═════════════════════════════════════════════════════════════════════════════
with tab_agent:
    # Header
    st.markdown(
        '<h1 style="color:#e8e8ed;font-size:1.65rem;font-weight:700;margin-bottom:0">'
        "Video Transcription Agent</h1>"
        '<p style="color:#8888a0;font-size:.88rem;margin-top:4px;margin-bottom:1.5rem">'
        "Search YouTube, transcribe audio with Gemini, and build your knowledge base — all through natural language.</p>",
        unsafe_allow_html=True,
    )

    # ── Stat chips ───────────────────────────────────────────────────────────
    kb = list_knowledge_base_transcripts()
    total_transcripts = kb.get("total_transcripts", 0)
    total_msgs = len(st.session_state.chat_history)

    stat_html = f"""
    <div class="stat-row">
      <div class="stat-chip"><div class="label">Transcripts</div><div class="value">{total_transcripts}</div></div>
      <div class="stat-chip"><div class="label">Messages</div><div class="value">{total_msgs}</div></div>
      <div class="stat-chip"><div class="label">Provider</div><div class="value" style="font-size:1rem">{provider.upper()}</div></div>
    </div>
    """
    st.markdown(stat_html, unsafe_allow_html=True)

    # ── Scrollable chat history ──────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for entry in st.session_state.chat_history:
            if entry["role"] == "user":
                st.markdown(f'<div class="user-msg">{entry["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="agent-msg">{entry["content"]}</div>', unsafe_allow_html=True)

                # Inline tool steps (collapsible)
                steps = entry.get("steps", [])
                if steps:
                    with st.expander(f"Tool execution trace  ({len(steps)} steps)"):
                        for s in steps:
                            if s["type"] == "tool_call":
                                label, icon = _tool_label(s["tool_name"])
                                st.markdown(
                                    f'<div class="step-pill">{icon} {label}</div>',
                                    unsafe_allow_html=True,
                                )
                                st.code(json.dumps(s["arguments"], indent=2), language="json")
                            elif s["type"] == "tool_result":
                                label, icon = _tool_label(s["tool_name"])
                                result = s.get("result", {})
                                success = result.get("success", False)
                                badge = "✓" if success else "✗"
                                st.markdown(
                                    f'<div class="step-pill result">{badge} {label} returned</div>',
                                    unsafe_allow_html=True,
                                )
                                # Show a compact summary of the result
                                preview = json.dumps(result, indent=2, default=str)
                                if len(preview) > 600:
                                    preview = preview[:600] + "\n  …"
                                st.code(preview, language="json")

    # ── Input area ───────────────────────────────────────────────────────────
    prefill = st.session_state.pop("_prefill", "")

    with st.form("chat_form", clear_on_submit=True):
        col_in, col_btn = st.columns([6, 1])
        with col_in:
            user_input = st.text_input(
                "Message",
                value=prefill,
                placeholder="Ask the agent anything — e.g. 'Transcribe a video about async Python'",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Send", use_container_width=True)

    # ── Agent execution ──────────────────────────────────────────────────────
    if submitted and user_input.strip():
        prompt_text = user_input.strip()
        st.session_state.chat_history.append({"role": "user", "content": prompt_text})

        collected_steps: list[dict] = []

        with st.status("Agent is working...", expanded=True) as status_box:
            def _on_step(event_type: str, data: dict):
                collected_steps.append({"type": event_type, **data})
                if event_type == "tool_call":
                    tool = data.get("tool_name", "")
                    args = data.get("arguments", {})
                    if tool == "search_youtube_videos":
                        status_box.write(f"🔍 **Searching YouTube** for: `{args.get('query', '')}`...")
                    elif tool == "transcribe_video":
                        status_box.write(f"🎙️ **Extracting audio & transcribing with Gemini**: `{args.get('video_url', '')}`...")
                    elif tool == "list_knowledge_base":
                        status_box.write("📚 **Checking local Knowledge Base**...")
                    else:
                        status_box.write(f"⚙️ Running `{tool}`...")
                elif event_type == "tool_result":
                    tool = data.get("tool_name", "")
                    res = data.get("result", {})
                    if res.get("success"):
                        if tool == "search_youtube_videos":
                            found = len(res.get("results", []))
                            status_box.write(f"✅ Found {found} video(s).")
                        elif tool == "transcribe_video":
                            status_box.write(f"✅ Transcribed: **{res.get('title', 'Video')}**")
                        else:
                            status_box.write(f"✅ Finished `{tool}`.")
                    else:
                        status_box.write(f"⚠️ {res.get('error', 'Notice')}")

            try:
                agent = VideoTranscribeAgent(provider=provider, step_callback=_on_step)
                response = agent.run(prompt_text)
                status_box.update(label="Done!", state="complete", expanded=False)
            except Exception as exc:
                response = f"**Error:** {exc}"
                status_box.update(label="Error occurred", state="error")

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "steps": collected_steps,
        })
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2 — Knowledge Base Browser
# ═════════════════════════════════════════════════════════════════════════════
with tab_kb:
    st.markdown(
        '<h2 style="color:#e8e8ed;font-size:1.35rem;font-weight:700;margin-bottom:.25rem">'
        "Knowledge Base</h2>"
        '<p style="color:#8888a0;font-size:.85rem;margin-bottom:1.2rem">'
        "Browse, read, and download your saved video transcripts.</p>",
        unsafe_allow_html=True,
    )

    kb_data = list_knowledge_base_transcripts()
    items = kb_data.get("transcripts", [])

    if not items:
        st.info("No transcripts saved yet. Use the Agent tab to search and transcribe a video.")
    else:
        # Search filter
        search_q = st.text_input("Filter transcripts", placeholder="Type to filter by title or channel…", label_visibility="collapsed")

        filtered = items
        if search_q:
            sq = search_q.lower()
            filtered = [i for i in items if sq in i.get("title", "").lower() or sq in i.get("channel", "").lower()]

        st.caption(f"Showing {len(filtered)} of {len(items)} transcripts")

        for item in filtered:
            title = item.get("title", "Untitled")
            channel = item.get("channel", "Unknown")
            date = item.get("transcribed_at", "")
            url = item.get("video_url", "")
            fname = item.get("file_name", "")

            col_info, col_actions = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f'<div class="kb-card">'
                    f'<div class="kb-title">{title}</div>'
                    f'<div class="kb-meta">{channel}  ·  {date}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_actions:
                # Read button
                if st.button("Read", key=f"read_{fname}", use_container_width=True):
                    st.session_state["_reading"] = fname

        # ── Reading pane ─────────────────────────────────────────────────────
        reading = st.session_state.get("_reading")
        if reading:
            md_name = reading.replace(".json", ".md")
            md_path = Config.TRANSCRIPTS_DIR / md_name
            if md_path.exists():
                st.markdown("---")
                st.markdown(
                    f'<h3 style="color:#e8e8ed;font-weight:600;margin-bottom:.5rem">📄 {md_name}</h3>',
                    unsafe_allow_html=True,
                )
                content = md_path.read_text(encoding="utf-8")
                st.markdown(content)

                st.download_button(
                    "Download Markdown",
                    data=content,
                    file_name=md_name,
                    mime="text/markdown",
                    use_container_width=True,
                )

                if st.button("Close", key="close_reader"):
                    del st.session_state["_reading"]
                    st.rerun()
            else:
                st.warning(f"File not found: {md_path}")
