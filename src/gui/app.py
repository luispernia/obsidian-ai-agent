import streamlit as st
import sys
import os

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src import config
from src.gui.storage import ChatManager, ReportManager
from src.gui.tabs.chat import render_chat_tab
from src.gui.tabs.report import render_report_tab
from src.gui.tabs.tagger import render_tagger_tab

st.set_page_config(page_title="Obsidian AI Agent", page_icon="🧠", layout="wide")

st.title("🧠 Obsidian AI Agent")

# Sidebar for config/status
with st.sidebar:
    st.header("Configuration")
    st.text(f"Provider: {os.getenv('AI_PROVIDER', 'Not Set')}")
    st.text(f"Vault: {config.VAULT_ABS_PATH}")
    
    if st.button("Refresh Config"):
        st.experimental_rerun()

# Initialize Managers
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()
if "report_manager" not in st.session_state:
    st.session_state.report_manager = ReportManager()

# Initialize Session State for Active Items
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "active_report_path" not in st.session_state:
    st.session_state.active_report_path = None

# Tabs
tab_chat, tab_report, tab_tagger = st.tabs(["💬 Chat (RAG)", "📅 Reports", "🏷️ Auto-Tagger"])

with tab_chat:
    render_chat_tab()

with tab_report:
    render_report_tab()

with tab_tagger:
    render_tagger_tab()


