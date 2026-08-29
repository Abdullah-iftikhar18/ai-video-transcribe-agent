"""
YouTube AI Video Search & Transcription Agent — Web Interface.

Clean, high-performance Red & Black YouTube-themed dashboard
for searching, transcribing, reading, and managing video transcripts.
"""

import json
import time
import sys
from pathlib import Path
import streamlit as st

# ── Ensure project root and src/ in sys.path ──────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── Bootstrap ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Transcribe Agent",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom YouTube Dark (Red & Black) CSS ────────────────────────────────────
st.markdown("""
<style>
  /* ── Typography: YouTube Roboto ────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700;900&display=swap');
  html, body, [class*="st-"] {
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  /* ── Page Canvas: True YouTube Dark ────────────────────────── */
  .stApp {
    background-color: #0f0f0f;
    color: #f1f1f1;
  }
  header[data-testid="stHeader"] {
    background-color: rgba(15, 15, 15, 0.95);
    backdrop-filter: blur(8px);
  }

  /* ── Sidebar: YouTube Elevated Black ───────────────────────── */
  section[data-testid="stSidebar"] {
    background-color: #121212;
    border-right: 1px solid #222222;
  }
  section[data-testid="stSidebar"] .stMarkdown h1,
  section[data-testid="stSidebar"] .stMarkdown h2,
  section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #ffffff;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  /* ── YouTube Accent Palette Tokens ─────────────────────────── */
  :root {
    --yt-red: #FF0000;
    --yt-red-dark: #CC0000;
    --yt-red-soft: rgba(255, 0, 0, 0.12);
    --yt-black: #0f0f0f;
    --yt-surface: #181818;
    --yt-surface-hover: #222222;
    --yt-chip: #272727;
    --yt-border: #282828;
    --yt-text: #f1f1f1;
    --yt-subtext: #aaaaaa;
    --yt-dim: #717171;
  }

  /* ── Cards & Containers ────────────────────────────────────── */
  .card {
    background: var(--yt-surface);
    border: 1px solid var(--yt-border);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color .15s ease;
  }
  .card:hover { border-color: #383838; }

  /* ── Tool execution pill ───────────────────────────────────── */
  .step-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #212121;
    border: 1px solid #333333;
    color: #ff4d4d;
    font-size: .78rem; font-weight: 600;
    padding: 4px 12px;
    border-radius: 6px;
    margin-bottom: .5rem;
  }
  .step-pill.result {
    background: rgba(46, 213, 115, 0.10);
    border-color: rgba(46, 213, 115, 0.3);
    color: #2ed573;
  }

  /* ── Chat Messages ─────────────────────────────────────────── */
  .user-msg {
    background: #272727;
    border: 1px solid #383838;
    color: #ffffff;
    padding: .85rem 1.25rem;
    border-radius: 16px 16px 4px 16px;
    max-width: 72%;
    margin-left: auto;
    margin-bottom: 1rem;
    font-size: .94rem;
    line-height: 1.55;
  }

  .agent-msg-box {
    background: #181818;
    border: 1px solid #282828;
    border-radius: 10px;
    padding: 1.35rem 1.6rem;
    margin-bottom: 1.4rem;
    color: #f1f1f1;
    font-size: .94rem;
    line-height: 1.65;
  }
  .agent-msg-box h1, .agent-msg-box h2, .agent-msg-box h3 {
    color: #ffffff;
    margin-top: .9rem;
    margin-bottom: .4rem;
  }
  .agent-msg-box hr {
    border-color: #282828;
    margin: 1.2rem 0;
  }

  /* ── Video Link Card (YouTube Player Style) ────────────────── */
  .yt-video-card {
    background: #1f1f1f;
    border: 1px solid #303030;
    border-left: 4px solid #FF0000;
    border-radius: 8px;
    padding: 12px 18px;
    margin-bottom: 14px;
    transition: background .15s ease;
  }
  .yt-video-card:hover { background: #242424; }
  .yt-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #FF0000;
    color: #ffffff;
    font-size: 0.7rem; font-weight: 800;
    padding: 2px 7px;
    border-radius: 4px;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .yt-video-title {
    font-size: 1.12rem; font-weight: 700;
    margin-bottom: 4px;
  }
  .yt-video-title a {
    color: #ffffff !important;
    text-decoration: none !important;
  }
  .yt-video-title a:hover { color: #ff4d4d !important; }
  .yt-video-meta {
    font-size: 0.83rem;
    color: #aaaaaa;
  }
  .yt-video-meta a {
    color: #ff6666 !important;
    text-decoration: none !important;
  }

  /* ── Stat chips (YouTube Studio Style) ─────────────────────── */
  .stat-row { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 1.4rem; }
  .stat-chip {
    background: #181818;
    border: 1px solid #272727;
    border-radius: 8px;
    padding: .75rem 1.2rem;
    flex: 1; min-width: 130px;
    text-align: center;
    transition: border-color .15s ease;
  }
  .stat-chip:hover { border-color: #383838; }
  .stat-chip .label {
    color: #aaaaaa;
    font-size: .72rem;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: .08em;
  }
  .stat-chip .value {
    color: #ffffff;
    font-size: 1.45rem;
    font-weight: 800;
    margin-top: 3px;
  }

  /* ── Knowledge Base Cards ──────────────────────────────────── */
  .kb-card {
    background: #181818;
    border: 1px solid #272727;
    border-radius: 8px;
    padding: 1rem 1.3rem;
    margin-bottom: .8rem;
    transition: border-color .15s ease, background .15s ease;
  }
  .kb-card:hover {
    border-color: #FF0000;
    background: #1c1c1c;
  }
  .kb-title {
    color: #ffffff;
    font-weight: 600;
    font-size: .98rem;
    margin-bottom: 4px;
  }
  .kb-meta {
    color: #aaaaaa;
    font-size: .8rem;
  }

  /* ── Inputs ────────────────────────────────────────────────── */
  .stTextInput > div > div > input {
    background: #121212 !important;
    border: 1px solid #333333 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    padding: .75rem 1.1rem !important;
    font-size: .94rem !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #FF0000 !important;
    box-shadow: 0 0 0 1px #FF0000 !important;
  }

  /* ── Primary Action Buttons (YouTube Red) ──────────────────── */
  .stButton > button {
    background: #FF0000 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: .92rem !important;
    padding: .55rem 1.6rem !important;
    letter-spacing: .02em !important;
    transition: background .15s ease !important;
  }
  .stButton > button:hover {
    background: #CC0000 !important;
    color: #ffffff !important;
  }

  /* ── Secondary / Utility Buttons ───────────────────────────── */
  .stButton > button[kind="secondary"] {
    background: #212121 !important;
    border: 1px solid #333333 !important;
    color: #f1f1f1 !important;
  }
  .stButton > button[kind="secondary"]:hover {
    background: #2a2a2a !important;
    border-color: #444444 !important;
  }

  /* ── Tabs (YouTube Navigation Bar) ─────────────────────────── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #282828;
    background: transparent;
  }
  .stTabs [data-baseweb="tab"] {
    color: #aaaaaa !important;
    font-weight: 500 !important;
    font-size: .94rem !important;
    padding: .65rem 1.4rem !important;
    border-bottom: 2px solid transparent !important;
  }
  .stTabs [aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 2px solid #FF0000 !important;
    font-weight: 700 !important;
  }

  /* ── Expander ──────────────────────────────────────────────── */
  .streamlit-expanderHeader {
    background-color: #181818 !important;
    color: #f1f1f1 !important;
    border: 1px solid #282828 !important;
    border-radius: 6px !important;
  }

  /* ── Clean Up Streamlit Chrome ─────────────────────────────── */
  #MainMenu, footer, .stDeployButton { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Lazy imports (after page config) ─────────────────────────────────────────
from src.ai_video_transcribe_agent.config import Config
from src.ai_video_transcribe_agent.agent import VideoTranscribeAgent
from src.ai_video_transcribe_agent.tools.knowledge_base import (
    list_knowledge_base_transcripts,
    clear_knowledge_base,
)


# ── Session state initialisation ─────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_steps" not in st.session_state:
    st.session_state.agent_steps = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# ── Helper: format tool names for display ────────────────────────────────────
TOOL_LABELS = {
    "search_youtube_videos": ("Search YouTube", "🔍"),
    "transcribe_video": ("Transcribe Audio", "🎙️"),
    "list_knowledge_base": ("Knowledge Base", "📚"),
}


def _tool_label(name: str) -> tuple[str, str]:
    return TOOL_LABELS.get(name, (name, "⚙️"))


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 12px;">
      <div style="background:#FF0000; color:#FFF; width:34px; height:24px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:bold; box-shadow: 0 2px 8px rgba(255,0,0,0.4);">▶</div>
      <span style="color:#FFF; font-size:1.15rem; font-weight:700; letter-spacing:-0.02em;">Agent Studio</span>
    </div>
    """, unsafe_allow_html=True)

    provider = st.radio(
        "Reasoning Engine",
        ["groq", "gemini"],
        index=0,
        horizontal=True,
        help="Groq = ultra-fast tool execution via Llama. Gemini = multimodal reasoning.",
    )

    st.markdown("---")
    st.markdown("### Workspace Management")
    st.caption("Clean up your active conversation or remove stored transcripts.")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.agent_steps = []
            st.rerun()

    with col_btn2:
        if st.button("Delete Files", use_container_width=True):
            clear_knowledge_base()
            st.session_state.pop("_reading", None)
            st.rerun()

    if st.button("🗑️ Reset All (Chat & Files)", use_container_width=True):
        clear_knowledge_base()
        st.session_state.chat_history = []
        st.session_state.agent_steps = []
        st.session_state.pop("_reading", None)
        st.success("All data and chat history erased!")
        time.sleep(0.3)
        st.rerun()


# ── Main area: Tabs ──────────────────────────────────────────────────────────
tab_agent, tab_kb = st.tabs(["Agent Chat", "Knowledge Base"])

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1 — Agent Chat
# ═════════════════════════════════════════════════════════════════════════════
with tab_agent:
    # Header: YouTube Logo + Title
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 6px; margin-top: 4px;">
          <div style="background: #FF0000; color: #FFFFFF; width: 42px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: bold; box-shadow: 0 2px 10px rgba(255, 0, 0, 0.45);">▶</div>
          <h1 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 800; margin: 0; letter-spacing: -0.02em;">YouTube Transcribe Agent</h1>
        </div>
        <p style="color: #aaaaaa; font-size: 0.9rem; margin-top: 2px; margin-bottom: 1.4rem;">
          Autonomous AI agent with SerpApi YouTube Search, Gemini Multimodal Transcription, and local Knowledge Base indexing.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ── Stat chips (YouTube Studio style) ────────────────────────────────────
    kb = list_knowledge_base_transcripts()
    total_transcripts = kb.get("total_transcripts", 0)
    total_msgs = len(st.session_state.chat_history)

    stat_html = f"""
    <div class="stat-row">
      <div class="stat-chip"><div class="label">Saved Transcripts</div><div class="value">{total_transcripts}</div></div>
      <div class="stat-chip"><div class="label">Messages</div><div class="value">{total_msgs}</div></div>
      <div class="stat-chip"><div class="label">Model Provider</div><div class="value" style="font-size:1.15rem; color:#FF4D4D;">{provider.upper()}</div></div>
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
                with st.container():
                    steps = entry.get("steps", [])

                    # 1. YouTube Video Source Card (if a video was transcribed)
                    for s in steps:
                        if s.get("type") == "tool_result" and s.get("tool_name") == "transcribe_video":
                            res = s.get("result", {})
                            v_url = res.get("video_url")
                            v_title = res.get("title", "Source Video")
                            v_chan = res.get("channel", "YouTube")
                            if v_url:
                                st.markdown(f"""
                                <div class="yt-video-card">
                                  <div class="yt-badge">▶ YOUTUBE VIDEO</div>
                                  <div class="yt-video-title"><a href="{v_url}" target="_blank">{v_title} ↗</a></div>
                                  <div class="yt-video-meta">Channel: {v_chan} &bull; <a href="{v_url}" target="_blank">{v_url}</a></div>
                                </div>
                                """, unsafe_allow_html=True)
                                break

                    # 2. Main Agent Response (Summary + Key Takeaways + Full Transcript)
                    st.markdown(f'<div class="agent-msg-box">', unsafe_allow_html=True)
                    st.markdown(entry["content"])

                    # 3. Guaranteed Full Transcript in front if not already in message content
                    for s in steps:
                        if s.get("type") == "tool_result" and s.get("tool_name") == "transcribe_video":
                            res = s.get("result", {})
                            transcript_text = res.get("transcript", "")
                            if transcript_text and "Full Transcript" not in entry["content"]:
                                st.markdown("---")
                                st.markdown("### 🎙️ Full Video Transcript")
                                st.markdown(transcript_text)
                    st.markdown("</div>", unsafe_allow_html=True)

                    # 4. Collapsible tool execution trace
                    if steps:
                        with st.expander(f"Tool Execution Trace ({len(steps)} steps)"):
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
                                        f'<div class="step-pill result">{badge} {label} completed</div>',
                                        unsafe_allow_html=True,
                                    )
                                    preview = json.dumps(result, indent=2, default=str)
                                    if len(preview) > 600:
                                        preview = preview[:600] + "\n  …"
                                    st.code(preview, language="json")

                    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # ── Input Area ───────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        col_in, col_btn = st.columns([6, 1])
        with col_in:
            user_input = st.text_input(
                "Message",
                placeholder="Ask to find a video or paste a YouTube URL (e.g. 'Find a 5-minute video on Docker and transcribe it')",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Send", use_container_width=True)

    # ── Agent Execution with Live Real-time Status ────────────────────────────
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
                        status_box.write(f"🔍 **Searching YouTube** via SerpApi for: `{args.get('query', '')}`...")
                    elif tool == "transcribe_video":
                        status_box.write(f"🎙️ **Downloading audio & transcribing with Gemini**: `{args.get('video_url', '')}`...")
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
                            status_box.write(f"✅ Found {found} relevant YouTube video(s).")
                        elif tool == "transcribe_video":
                            status_box.write(f"✅ Transcribed: **{res.get('title', 'Video')}**")
                        else:
                            status_box.write(f"✅ Finished `{tool}`.")
                    else:
                        status_box.write(f"⚠️ {res.get('error', 'Notice')}")

            try:
                agent = VideoTranscribeAgent(provider=provider, step_callback=_on_step)
                response = agent.run(prompt_text)
                status_box.update(label="Complete!", state="complete", expanded=False)
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
    kb_data = list_knowledge_base_transcripts()
    items = kb_data.get("transcripts", [])

    col_kb_title, col_kb_clear = st.columns([4, 2])
    with col_kb_title:
        st.markdown(
            '<h2 style="color:#ffffff;font-size:1.35rem;font-weight:700;margin-bottom:.25rem">'
            "Saved Knowledge Base</h2>"
            '<p style="color:#aaaaaa;font-size:.85rem;margin-bottom:1.2rem">'
            "Browse, read, and download all transcribed YouTube videos.</p>",
            unsafe_allow_html=True,
        )
    with col_kb_clear:
        if items:
            if st.button("🗑️ Delete All Transcripts", key="kb_del_all_btn", use_container_width=True):
                clear_knowledge_base()
                st.session_state.pop("_reading", None)
                st.rerun()

    if not items:
        st.info("No transcripts saved yet. Use the Agent tab to search and transcribe any YouTube video.")
    else:
        # Search filter
        search_q = st.text_input("Filter transcripts", placeholder="Type to filter by video title or channel…", label_visibility="collapsed")

        filtered = items
        if search_q:
            sq = search_q.lower()
            filtered = [i for i in items if sq in i.get("title", "").lower() or sq in i.get("channel", "").lower()]

        st.caption(f"Showing {len(filtered)} of {len(items)} saved transcriptions")

        for item in filtered:
            title = item.get("title", "Untitled Video")
            channel = item.get("channel", "Unknown Channel")
            date = item.get("transcribed_at", "")
            fname = item.get("file_name", "")

            col_info, col_actions = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f'<div class="kb-card">'
                    f'<div class="kb-title">▶ {title}</div>'
                    f'<div class="kb-meta">{channel} &bull; Transcribed on {date}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_actions:
                if st.button("Read", key=f"read_{fname}", use_container_width=True):
                    st.session_state["_reading"] = fname

        # ── Reading Pane ─────────────────────────────────────────────────────
        reading = st.session_state.get("_reading")
        if reading:
            md_name = reading.replace(".json", ".md")
            md_path = Config.TRANSCRIPTS_DIR / md_name
            if md_path.exists():
                st.markdown("---")
                st.markdown(
                    f'<h3 style="color:#ffffff;font-weight:700;margin-bottom:.5rem">📄 {md_name}</h3>',
                    unsafe_allow_html=True,
                )
                content = md_path.read_text(encoding="utf-8")
                st.markdown(content)

                col_d, col_c = st.columns([3, 1])
                with col_d:
                    st.download_button(
                        "Download Markdown File",
                        data=content,
                        file_name=md_name,
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with col_c:
                    if st.button("Close Document", key="close_reader", use_container_width=True):
                        del st.session_state["_reading"]
                        st.rerun()
            else:
                st.warning(f"File not found: {md_path}")
