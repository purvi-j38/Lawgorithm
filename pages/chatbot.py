import streamlit as st
from utils.chatbot import legal_chatbot

def render_chatbot_page():
    """Render the AI chatbot page for legal assistance."""
    st.title("Legal AI Assistant")
    
    # Initialize chat history in session state if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize the current document for context
    if st.session_state.current_document:
        legal_chatbot.set_document_context(st.session_state.current_document)
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask a question about Indian law or the current document..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get response from chatbot
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = legal_chatbot.get_response(user_input)
                st.write(response)
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Option to clear chat history
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            legal_chatbot.clear_conversation_history()
            st.rerun()
    
    # Display information about the chatbot's capabilities
    with st.expander("About Legal AI Assistant"):
        st.markdown("""
        **Legal AI Assistant** can help you with:
        
        - Understanding legal documents
        - Explaining Indian legal terms and concepts
        - Finding key information in your documents
        - Answering questions about Indian law, including:
          - Indian Penal Code (IPC)
          - Code of Criminal Procedure (CrPC)
          - Code of Civil Procedure (CPC)
          - Bharatiya Nyaya Sanhita (BNS)
          - Constitutional provisions
          
        Note: This assistant provides general information, not personalized legal advice.
        Always consult a qualified legal professional for specific legal matters.
        """)