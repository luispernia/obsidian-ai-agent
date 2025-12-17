import streamlit as st
import time
import os
import yaml
from datetime import datetime
from src import config
from src.daily_report.reporter import generate_report_content
from src.daily_report.git_manager import GitManager

def render_report_tab():
    report_manager = st.session_state.report_manager
    
    # Initialize session state for draft if not exists
    if "draft_report_data" not in st.session_state:
        st.session_state.draft_report_data = None
    
    col_rep_list, col_rep_view = st.columns([1, 3])
    
    with col_rep_list:
        st.subheader("Reports")
        
        # Generator / Drafter
        with st.expander("Create New Report", expanded=not st.session_state.draft_report_data):
            if st.session_state.draft_report_data is None:
                st.info("Generate a draft based on recent git changes.")
                if st.button("Draft Report", use_container_width=True):
                    with st.spinner("Analyzing changes & generating draft..."):
                         data = generate_report_content()
                         if data:
                             st.session_state.draft_report_data = data
                             st.rerun()
                         else:
                             st.error("No content generated. Check logs or git changes.")
            else:
                st.success("Draft Generated!")
                if st.button("Discard Draft", use_container_width=True):
                    st.session_state.draft_report_data = None
                    st.rerun()

        st.markdown("---")
        
        search_rep = st.text_input("Search Reports", placeholder="Filter...")
        reports = report_manager.list_reports()
        if search_rep:
            reports = [r for r in reports if search_rep.lower() in r["filename"].lower()]
            
        for rep in reports:
            label = f"{'📌 ' if rep['pinned'] else ''}{rep['filename']}"
            if st.button(label, key=f"rep_{rep['filename']}", use_container_width=True):
                st.session_state.active_report_path = rep["filename"]
                st.session_state.draft_report_data = None # Switch to view mode
                st.rerun()

    with col_rep_view:
        # If we have a draft, show the Review UI
        if st.session_state.draft_report_data:
            st.subheader("📝 Review & Save Draft")
            
            draft = st.session_state.draft_report_data
            
            # Metadata Editors
            c1, c2 = st.columns(2)
            with c1:
                topic = st.text_input("Topic / Title", value=draft.get("topic", "Daily Report"))
            with c2:
                # Join tags list purely for display/edit
                tags_val = draft.get("tags", [])
                if isinstance(tags_val, list):
                    tags_str = ", ".join(tags_val)
                else:
                    tags_str = str(tags_val)
                tags_input = st.text_input("Tags (comma separated)", value=tags_str)
            
            # Preview Filename
            safe_topic = "".join([c if c.isalnum() or c == '-' else '-' for c in topic.strip().replace(' ', '-')])
            date_str = datetime.now().strftime('%Y-%m-%d')
            preview_filename = f"{date_str}-{safe_topic}.md"
            st.caption(f"💾 Will save as: `{preview_filename}`")
            
            # Content Preview / Edit
            summary_content = st.text_area("Report Content (Markdown)", value=draft.get("summary", ""), height=400)
            
            if st.button("✅ Save & Commit", use_container_width=True):
                # Process Tags
                final_tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                
                # Construct Frontmatter
                frontmatter = {
                    "tags": final_tags,
                    "creation-date": datetime.now().strftime('%Y-%m-%dT%H:%M'),
                    "topic": topic
                }
                
                # We need to manually dump YAML to string to ensure format
                # Using safe_dump usually works well
                fm_str = yaml.dump(frontmatter, sort_keys=False)
                
                final_file_content = f"---\n{fm_str}---\n\n{summary_content}"
                
                # Save
                report_path = os.path.join(config.REPORTS_ABS_PATH, preview_filename)
                
                try:
                    with open(report_path, 'w') as f:
                        f.write(final_file_content)
                    
                    # Commit
                    git_mgr = GitManager()
                    git_mgr.commit_all(f"Report: {topic}")
                    
                    st.success(f"Saved to {preview_filename}!")
                    
                    # Cleanup & Switch to View
                    st.session_state.draft_report_data = None
                    st.session_state.active_report_path = preview_filename
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error saving/committing: {e}")

        # Otherwise show the active report viewer
        elif st.session_state.active_report_path:
            active_rep = st.session_state.active_report_path
            
            r1, r2, r3 = st.columns([6, 1, 1])
            with r1:
                st.subheader(active_rep)
            with r2:
                if st.button("📌", key="pin_rep", help="Toggle Pin"):
                    report_manager.toggle_pin(active_rep)
                    st.rerun()
            with r3:
                if st.button("🗑️", key="del_rep", help="Delete Report"):
                    report_manager.delete_report(active_rep)
                    st.session_state.active_report_path = None
                    st.rerun()
            
            content = report_manager.get_report_content(active_rep)
            st.markdown(content)
        else:
            st.info("👈 Select a report to view or create a new one.")
