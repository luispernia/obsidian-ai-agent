import streamlit as st
import uuid
from src.rag.query import query_rag

def render_chat_tab():
    chat_manager = st.session_state.chat_manager
    
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
        
        chats = chat_manager.list_chats()
        if search_query:
            chats = [c for c in chats if search_query.lower() in c["title"].lower()]
            
        st.markdown("---")
        for chat in chats:
            label = f"{'📌 ' if chat['pinned'] else ''}{chat['title']}"
            if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                st.session_state.active_chat_id = chat['id']
                loaded = chat_manager.load_chat(chat['id'])
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
                     chat_manager.toggle_pin(st.session_state.active_chat_id)
                     st.rerun()
             with c3:
                 if st.button("🗑️", help="Delete Chat"):
                     chat_manager.delete_chat(st.session_state.active_chat_id)
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
                title = None 
                
            chat_manager.save_chat(
                st.session_state.active_chat_id, 
                st.session_state.messages,
                title=title
            )
            
            if title: 
                 st.rerun()
