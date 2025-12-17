import streamlit as st
import time
import os
from pathlib import Path
from src import config
from src.daily_report.reporter import generate_report_content
from src.daily_report.git_manager import GitManager

def render_report_tab():
    report_manager = st.session_state.report_manager
    
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
                     
                     content = generate_report_content()
                     
                     if content:
                         # Save to file
                         report_path = os.path.join(config.REPORTS_ABS_PATH, filename)
                         with open(report_path, 'w') as f:
                             f.write(content)
                             
                         # Auto-Commit
                         try:
                             git_mgr = GitManager()
                             git_mgr.commit_all(f"Report: {filename}")
                             st.success("Report saved and committed!")
                         except Exception as commit_err:
                             st.warning(f"Report saved, but git commit failed: {commit_err}")
                         
                         st.session_state.active_report_path = filename
                         time.sleep(1)
                         st.rerun()
                     else:
                         st.error("Report generation returned no content.")

        st.markdown("---")
        
        search_rep = st.text_input("Search Reports", placeholder="Filter...")
        reports = report_manager.list_reports()
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
            st.info("Select a report to view or generate a new one.")
