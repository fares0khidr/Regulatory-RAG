import base64
import html
from datetime import datetime
from pathlib import Path

import streamlit as st

# ----------------------------------------------------------------------------
# LOGO
# Drop your logo file at ./assets/logo.png (any image format works, just
# update the path below) before running the app. It will automatically be
# used both in the sidebar brand row and as the assistant's chat avatar.
LOGO_PATH = Path("./logo.jpeg")


def get_logo_data_uri():
    """Return a base64 data: URI for the logo, or None if the file is missing."""
    if LOGO_PATH.exists():
        ext = LOGO_PATH.suffix.lstrip(".") or "png"
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f"data:image/{ext};base64,{encoded}"
    return None


LOGO_URI = get_logo_data_uri()

from backend import answer_from_backend, backend_collection, backend_collection_count

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="REG RAG — Regulatory AI",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# STYLING (dark theme, red accent — Vodafone-red #E60000 used only as an
# accent color, not as any reproduction of the Vodafone logo/brand assets)
# ----------------------------------------------------------------------------
ACCENT = "#E60000"

st.markdown(
    f"""
    <style>
        /* ---- global ---- */
        .stApp {{
            background-color: #0e0e10;
            color: #eaeaea;
        }}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Hide the menu/deploy/status clutter inside the toolbar, but leave
           the toolbar itself alone — the "reopen sidebar" arrow
           (stExpandSidebarButton) lives inside it, and hiding the whole
           toolbar was hiding that arrow too, making a collapsed sidebar
           impossible to reopen. */
        [data-testid="stMainMenu"] {{visibility: hidden;}}
        [data-testid="stAppDeployButton"] {{display: none;}}
        [data-testid="stStatusWidget"] {{display: none;}}
        [data-testid="stToolbarActions"] {{display: none;}}

        header[data-testid="stHeader"] {{
            background-color: #0e0e10 !important;
        }}
        [data-testid="stExpandSidebarButton"] {{
            color: #eaeaea !important;
        }}
        [data-testid="stExpandSidebarButton"] svg {{
            fill: #eaeaea !important;
        }}

        /* ---- sidebar ---- */
        section[data-testid="stSidebar"] {{
            background-color: #131315;
            border-right: 1px solid #2a2a2d;
        }}
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 1rem;
        }}

        /* brand row */
        .brand-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 4px 20px 4px;
            margin-bottom: 6px;
            border-bottom: 1px solid #2a2a2d;
        }}
        .brand-logo {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
            overflow: hidden;
            padding: 4px;
            box-sizing: border-box;
        }}
        .brand-text-title {{
            font-weight: 700;
            font-size: 17px;
            color: #fff;
            line-height: 1.1;
        }}
        .brand-text-sub {{
            font-size: 11px;
            letter-spacing: 1px;
            color: #9a9a9d;
        }}

        /* sidebar buttons (new conversation + history items) */
        section[data-testid="stSidebar"] div.stButton {{
            margin-bottom: 8px;
        }}
        div.stButton > button {{
            width: 100%;
            border-radius: 8px;
            border: 1px solid {ACCENT};
            background-color: transparent;
            color: {ACCENT};
            font-weight: 600;
            padding: 0.6rem 0.75rem;
            text-align: left;
            white-space: pre-line;
            line-height: 1.5;
            transition: all 0.15s ease;
        }}
        div.stButton > button:hover {{
            background-color: {ACCENT};
            color: white;
            border-color: {ACCENT};
        }}
        section[data-testid="stSidebar"] .section-label:first-of-type {{
            margin-top: 4px;
        }}

        /* section labels e.g. TODAY / YESTERDAY */
        .section-label {{
            font-size: 11px;
            letter-spacing: 1.5px;
            color: #7a7a7d;
            margin: 18px 0 6px 4px;
            font-weight: 600;
        }}

        /* top bar */
        .topbar-title {{
            font-weight: 700;
            font-size: 18px;
            color: #fff;
        }}
        .docs-indexed {{
            font-size: 12px;
            color: {ACCENT};
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: {ACCENT};
            display: inline-block;
        }}
        /* chat bubbles */
        .user-bubble {{
            background: {ACCENT};
            color: white;
            padding: 12px 16px;
            border-radius: 14px 14px 2px 14px;
            max-width: 65%;
            margin-left: auto;
            font-size: 14.5px;
            line-height: 1.5;
        }}
        .assistant-bubble {{
            background: #1a1a1d;
            border: 1px solid #2a2a2d;
            color: #eaeaea;
            padding: 16px 18px;
            border-radius: 14px 14px 14px 2px;
            max-width: 75%;
            font-size: 14.5px;
            line-height: 1.6;
        }}
        .msg-row {{
            display: flex;
            gap: 10px;
            margin-bottom: 22px;
            align-items: flex-start;
        }}
        .msg-time {{
            font-size: 10.5px;
            color: #6a6a6d;
            margin-top: 4px;
            text-align: right;
        }}
        .avatar {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            flex-shrink: 0;
            overflow: hidden;
            padding: 3px;
            box-sizing: border-box;
        }}

        /* ---- bottom chat-input bar ---- */
        [data-testid="stBottom"] {{
            background-color: #0e0e10 !important;
        }}
        [data-testid="stBottomBlockContainer"] {{
            background-color: #0e0e10 !important;
        }}
        [data-testid="stChatInput"] {{
            background-color: #1a1a1d !important;
            border: 1px solid #2a2a2d !important;
            border-radius: 10px !important;
        }}
        /* the actual input surface is nested baseweb divs that ship their own
           white background — force every layer inside the box transparent
           so the dark background above shows through */
        [data-testid="stChatInput"] * {{
            background-color: transparent !important;
            border-color: transparent !important;
            box-shadow: none !important;
        }}
        [data-testid="stChatInput"] textarea {{
            color: #eaeaea !important;
            caret-color: #eaeaea !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{
            color: #7a7a7d !important;
        }}
        [data-testid="stChatInputSubmitButton"] {{
            background-color: {ACCENT} !important;
        }}
        [data-testid="stChatInputSubmitButton"] svg {{
            fill: white !important;
        }}

        /* footer hint */
        .footer-hint {{
            text-align: center;
            font-size: 11px;
            color: #6a6a6d;
            letter-spacing: 0.5px;
            margin-top: 6px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------------
# Conversations remain frontend-only in memory; answers and source metadata come
# from the connected Chroma/Gemini backend above.
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if (
    "active_conversation" not in st.session_state
    or st.session_state.active_conversation not in st.session_state.conversations
):
    first_id = "c1"
    st.session_state.conversations[first_id] = {
        "title": "New conversation",
        "preview": "",
        "group": "TODAY",
        "messages": [],
    }
    st.session_state.active_conversation = first_id

if "docs_indexed" not in st.session_state:
    st.session_state.docs_indexed = backend_collection_count

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    logo_html = (
        f'<img src="{LOGO_URI}" style="width:100%;height:100%;object-fit:contain;" />'
        if LOGO_URI
        else '<span style="color:{ACCENT_PLACEHOLDER};font-weight:700;font-size:18px;">R</span>'
    ).replace("{ACCENT_PLACEHOLDER}", ACCENT)

    st.markdown(
        f"""
        <div class="brand-row">
            <div class="brand-logo">{logo_html}</div>
            <div>
                <div class="brand-text-title">REG RAG</div>
                <div class="brand-text-sub">REGULATORY AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # No logo file found at ./assets/logo.png yet? Drop one there and rerun —
    # it will replace the placeholder "R" above and the chat avatar below.

    if st.button("＋ New conversation", use_container_width=True):
        new_id = f"c{len(st.session_state.conversations) + 1}"
        st.session_state.conversations[new_id] = {
            "title": "New conversation",
            "preview": "Empty",
            "group": "TODAY",
            "messages": [],
        }
        st.session_state.active_conversation = new_id
        st.rerun()

    # group conversations for display, preserving insertion order
    groups = {}
    for cid, convo in st.session_state.conversations.items():
        groups.setdefault(convo["group"], []).append((cid, convo))

    for group_name, items in groups.items():
        st.markdown(f'<div class="section-label">{group_name}</div>', unsafe_allow_html=True)
        for cid, convo in items:
            label = f"{convo['title']}\n{convo['preview']}"
            if st.button(label, key=f"hist_{cid}", use_container_width=True):
                st.session_state.active_conversation = cid
                st.rerun()

# ----------------------------------------------------------------------------
# TOP BAR
# ----------------------------------------------------------------------------
active = st.session_state.conversations[st.session_state.active_conversation]

top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.markdown(
        f'<div class="topbar-title">{active["title"] if active["messages"] else "New conversation"}</div>',
        unsafe_allow_html=True,
    )
with top_col2:
    st.markdown(
        f'<div class="docs-indexed" style="justify-content:flex-end;">'
        f'<span class="dot"></span> {st.session_state.docs_indexed} DOCS INDEXED</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr style="border-color:#2a2a2d;margin-top:0;">', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# CHAT HISTORY DISPLAY
# ----------------------------------------------------------------------------
_avatar_html = (
    f'<img src="{LOGO_URI}" style="width:100%;height:100%;object-fit:contain;" />'
    if LOGO_URI
    else f'<span style="color:{ACCENT};font-weight:700;font-size:13px;">R</span>'
)

for msg in active["messages"]:
    if msg["role"] == "user":
        col_l, col_r = st.columns([1, 3])
        with col_r:
            st.markdown(
                    f'<div class="user-bubble">{html.escape(msg["text"])}</div>'
                f'<div class="msg-time">{msg["time"]}</div>',
                unsafe_allow_html=True,
            )
    else:
        col_l, col_r = st.columns([3, 1])
        with col_l:
            sources = msg.get("sources", [])
            sources_html = ""
            if sources:
                source_items = "".join(
                    f'<li>{html.escape(str(source["source"]))} — page '
                    f'{html.escape(str(source["page"]))}</li>'
                    for source in sources
                )
                sources_html = (
                    '<details class="sources-details">'
                    '<summary>Sources</summary>'
                    f'<ul>{source_items}</ul></details>'
                )
            st.markdown(
                f'''
                <div class="msg-row">
                    <div class="avatar">{_avatar_html}</div>
                    <div>
                        <div class="assistant-bubble">{html.escape(msg["text"]).replace(chr(10), "<br>")}</div>
                        {sources_html}
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

if not active["messages"]:
    st.markdown(
        '<div style="text-align:center; color:#6a6a6d; margin-top:80px; font-size:14px;">'
        "Ask about regulations, obligations, or compliance timelines to get started."
        "</div>",
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------
# CHAT INPUT
# ----------------------------------------------------------------------------
user_input = st.chat_input("Ask about regulations, obligations, compliance timelines...")

if user_input:
    now = datetime.now().strftime("%H:%M")
    active["messages"].append({"role": "user", "text": user_input, "time": now})
    active["preview"] = user_input[:55]
    if active["title"] == "New conversation":
        active["title"] = user_input[:40]

    try:
        answer_text, sources = answer_from_backend(user_input)
    except Exception as error:
        answer_text = (
            "The regulatory backend is not available. "
            f"Check the environment and backend setup. Details: {error}"
        )
        sources = []

    active["messages"].append({
        "role": "assistant",
        "text": answer_text,
        "time": now,
        "sources": sources,
    })
    st.rerun()

st.markdown(
    '<div class="footer-hint">SHIFT+ENTER FOR NEW LINE &nbsp;·&nbsp; ANSWERS GROUNDED IN INDEXED DOCUMENTS</div>',
    unsafe_allow_html=True,
 )
