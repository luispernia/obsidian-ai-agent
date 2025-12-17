import streamlit as st
from pathlib import Path
from src import config
from src.tagging.auto_tag import TagScanner, TagSuggester, TagCache, apply_changes

def render_tagger_tab():
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
