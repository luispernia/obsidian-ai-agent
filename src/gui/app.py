import streamlit as st
import sys
import os
import uuid
import time
from pathlib import Path

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.rag.query import query_rag
from src.daily_report.reporter import generate_summary
from src.tagging.auto_tag import TagScanner, TagSuggester, TagCache, apply_changes
from src import config
from src.gui.storage import ChatManager, ReportManager

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

# --- TAB 1: RAG CHAT ---
with tab_chat:
    col_hist, col_chat = st.columns([1, 3])
    
    # --- Check for New Chat Creation ---
    if "messages" not in st.session_state:
         st.session_state.messages = []

    # Left: History
    with col_hist:
        st.subheader("History")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.active_chat_id = None
            st.session_state.messages = []
            st.rerun()
            
        search_query = st.text_input("Search Chats", placeholder="Filter...")
        
        chats = st.session_state.chat_manager.list_chats()
        if search_query:
            chats = [c for c in chats if search_query.lower() in c["title"].lower()]
            
        st.markdown("---")
        for chat in chats:
            label = f"{'📌 ' if chat['pinned'] else ''}{chat['title']}"
            if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                st.session_state.active_chat_id = chat['id']
                loaded = st.session_state.chat_manager.load_chat(chat['id'])
                if loaded:
                    st.session_state.messages = loaded['messages']
                st.rerun()

    # Right: Chat Interface
    with col_chat:
        if st.session_state.active_chat_id:
             # Header Actions for Active Chat
             c1, c2, c3 = st.columns([6, 1, 1])
             with c2:
                 if st.button("📌", help="Toggle Pin"):
                     st.session_state.chat_manager.toggle_pin(st.session_state.active_chat_id)
                     st.rerun()
             with c3:
                 if st.button("🗑️", help="Delete Chat"):
                     st.session_state.chat_manager.delete_chat(st.session_state.active_chat_id)
                     st.session_state.active_chat_id = None
                     st.session_state.messages = []
                     st.rerun()

        # Display Chat
        container = st.container(height=600)
        for message in st.session_state.messages:
            with container.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input
        if prompt := st.chat_input("Ask something about your notes..."):
            with container.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Thinking..."):
                try:
                    response = query_rag(prompt)
                except Exception as e:
                    response = f"Error: {e}"

            with container.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Save Chat
            if not st.session_state.active_chat_id:
                st.session_state.active_chat_id = str(uuid.uuid4())
                # Generate simple title from first prompt
                title = (prompt[:30] + '..') if len(prompt) > 30 else prompt
            else:
                # Keep existing title
                # (Ideally we'd read it, but for now we just pass None to keep existing)
                title = None 
                
            st.session_state.chat_manager.save_chat(
                st.session_state.active_chat_id, 
                st.session_state.messages,
                title=title
            )
            # Rerun only if we just created a new ID so the UI updates
            if title: 
                 st.rerun()


# --- TAB 2: REPORTS ---
with tab_report:
    col_rep_list, col_rep_view = st.columns([1, 3])
    
    with col_rep_list:
        st.subheader("Reports")
        
        # Generator
        with st.expander("Generate New Report"):
            rep_name = st.text_input("Filename (Optional)", placeholder="MyReport.md")
            if st.button("Generate Now", use_container_width=True):
                with st.spinner("Analyzing git changes..."):
                     filename = rep_name if rep_name and rep_name.strip() else f"Report_{time.strftime('%Y-%m-%d_%H-%M')}.md"
                     if not filename.endswith(".md"): filename += ".md"
                     
                     path = generate_summary(output_filename=filename)
                     if path:
                         st.success("Done!")
                         st.session_state.active_report_path = Path(path).name
                         time.sleep(1)
                         st.rerun()
                     else:
                         st.error("Generation failed (no changes?)")

        st.markdown("---")
        
        search_rep = st.text_input("Search Reports", placeholder="Filter...")
        reports = st.session_state.report_manager.list_reports()
        if search_rep:
            reports = [r for r in reports if search_rep.lower() in r["filename"].lower()]
            
        for rep in reports:
            label = f"{'📌 ' if rep['pinned'] else ''}{rep['filename']}"
            if st.button(label, key=f"rep_{rep['filename']}", use_container_width=True):
                st.session_state.active_report_path = rep["filename"]
                st.rerun()

    with col_rep_view:
        if st.session_state.active_report_path:
            active_rep = st.session_state.active_report_path
            
            r1, r2, r3 = st.columns([6, 1, 1])
            with r1:
                st.subheader(active_rep)
            with r2:
                 if st.button("📌", key="pin_rep", help="Toggle Pin"):
                     st.session_state.report_manager.toggle_pin(active_rep)
                     st.rerun()
            with r3:
                 if st.button("🗑️", key="del_rep", help="Delete Report"):
                     st.session_state.report_manager.delete_report(active_rep)
                     st.session_state.active_report_path = None
                     st.rerun()
            
            content = st.session_state.report_manager.get_report_content(active_rep)
            st.markdown(content)
        else:
            st.info("Select a report to view or generate a new one.")

# --- TAB 3: AUTO-TAGGER ---
with tab_tagger:
    st.header("Smart Auto-Tagging")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        target_folder = st.text_input("Target Folder (optional, relative to Vault root)", placeholder="e.g., Drafts")
    with col2:
        force_scan = st.checkbox("Force Scan All", help="Ignore cache and rescan all files")

    if st.button("Start Scan"):
        st.write("Initializing Scanner...")
        
        # Setup similar to main() in auto_tag.py
        scanner = TagScanner(config.VAULT_ABS_PATH)
        scanner.build_index()
        top_tags = scanner.get_top_tags(50)
        
        suggester = TagSuggester()
        cache = TagCache()
        
        if not suggester.llm:
            st.error("LLM not initialized. Check provider settings.")
            st.stop()
            
        # Determine files
        if target_folder:
            target_dir = Path(config.VAULT_ABS_PATH) / target_folder
            if not target_dir.exists():
                st.error(f"Folder '{target_folder}' does not exist.")
                st.stop()
            files = list(target_dir.rglob("*.md"))
        else:
            files = scanner.get_all_markdown_files()
            
        st.info(f"Found {len(files)} files to scan.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        changes_preview = []
        
        for i, file_path in enumerate(files):
            progress = (i + 1) / len(files)
            progress_bar.progress(progress)
            status_text.text(f"Processing {file_path.name}...")
            
            if not force_scan and not cache.should_process(file_path):
                continue

            current_tags = scanner.parse_tags_from_file(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                continue

            result = suggester.analyze_note(content, current_tags, top_tags)
            
            if result:
                suggested_topics = set(result.get('topic_tags', []))
                maturity_tag = result.get('maturity_tag')
                maintenance_tag = result.get('maintenance_tag')
                
                new_tag_set = set(suggested_topics)
                if maturity_tag: new_tag_set.add(maturity_tag)
                if maintenance_tag: new_tag_set.add(maintenance_tag)
                
                added = new_tag_set - current_tags
                removed = current_tags - new_tag_set
                
                if added or removed:
                    changes_preview.append({
                        "file": file_path,
                        "current": current_tags,
                        "suggested": new_tag_set,
                        "added": added,
                        "removed": removed,
                        "content": content # needed for apply
                    })

        status_text.text("Scan complete.")
        
        if not changes_preview:
            st.success("No changes suggested.")
        else:
            st.subheader(f"Suggested Changes ({len(changes_preview)})")
            
            # Store changes in session state to persist for the "Apply" button
            st.session_state.tag_changes = changes_preview
            
    # Display and Apply Changes
    if "tag_changes" in st.session_state and st.session_state.tag_changes:
        
        for change in st.session_state.tag_changes:
            with st.expander(f"{change['file'].name}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Current Tags**")
                    st.write(change['current'])
                with col_b:
                    st.markdown("**Suggested Tags**")
                    st.write(change['suggested'])
                
                st.markdown(f"**Added:** {', '.join(change['added'])}")
                st.markdown(f"**Removed:** {', '.join(change['removed'])}")

        if st.button("Apply All Changes"):
            progress_bar_apply = st.progress(0)
            
            for i, change in enumerate(st.session_state.tag_changes):
                apply_changes(change['file'], change['suggested'], change['content'])
                
                # Update cache
                # We need to instantiate cache again or keep it
                # For simplicity, just instantiate a temp one to update
                temp_cache = TagCache() 
                temp_cache.update(change['file'])
                
                progress_bar_apply.progress((i + 1) / len(st.session_state.tag_changes))
            
            st.success("All changes applied!")
            st.session_state.tag_changes = [] # Clear
