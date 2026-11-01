import streamlit as st
import os
import shutil

def apply_dark_mode():
    """Apply dark mode CSS if enabled in settings."""
    if st.session_state.get('dark_mode', False):
        # Apply dark mode CSS
        dark_mode_css = """
        <style>
            .stApp {
                background-color: #111;
                color: #f0f0f0;
            }
            .stTextInput, .stNumberInput, .stSelectbox {
                background-color: #222;
                color: #f0f0f0;
                border-color: #444;
            }
            .stSidebar {
                background-color: #222;
            }
            .stButton button {
                background-color: #0078cc;
                color: white;
            }
            .stMarkdown, p, h1, h2, h3, h4, h5, h6 {
                color: #f0f0f0 !important;
            }
            div[data-testid="stExpander"] {
                background-color: #222;
                border-color: #444;
            }
            div[data-testid="stForm"] {
                background-color: #222;
                border-color: #444;
            }
        </style>
        """
        st.markdown(dark_mode_css, unsafe_allow_html=True)

def render_settings_page():
    """Render the settings page."""
    st.title("Settings")
    
    st.subheader("User Preferences")
    
    # In a real app, these settings would be saved to a database or local storage
    col1, col2 = st.columns(2)
    
    with col1:
        # Dark mode setting
        dark_mode = st.toggle(
            "Dark Mode",
            value=st.session_state.get('dark_mode', False),
            key='dark_mode',
            on_change=apply_dark_mode
        )
        
        # History items setting
        history_items = st.number_input(
            "Number of items in history",
            min_value=5,
            max_value=50,
            value=st.session_state.get('history_items', 10),
            key='history_items'
        )
    
    with col2:
        # Default export format
        export_format = st.selectbox(
            "Default Export Format",
            options=["PDF", "DOCX", "TXT"],
            index=["PDF", "DOCX", "TXT"].index(st.session_state.get('export_format', "PDF")),
            key='export_format'
        )
        
        # Language setting
        language_options = ["English", "Hindi", "Bengali", "Marathi", "Tamil", "Telugu", "Gujarati", "Kannada", "Malayalam", "Punjabi", "Urdu"]
        current_language = st.session_state.get('language', "English")
        
        # Make sure current_language is valid
        if current_language not in language_options:
            current_language = "English"
            
        language = st.selectbox(
            "Language",
            options=language_options,
            index=language_options.index(current_language),
            key='language'
        )
        
        # Apply language change
        if language != st.session_state.get('previous_language', "English"):
            st.session_state.previous_language = language
            
            # Here we would add translations in a real multilingual app
            # For the hackathon demo, we'll just show a notification
            st.info(f"Language changed to {language}. In a production app, all UI text would be translated.")
            
            # Keep this value in session state
            st.session_state.language = language
    
    st.divider()
    
    st.subheader("Document Management")
    
    # Clear document history
    if st.button("Clear Document History"):
        confirm = st.checkbox("I understand this will remove all documents from history")
        if confirm and st.button("Confirm Clear History"):
            # Clear document history
            st.session_state.document_history = []
            st.session_state.current_document = None
            
            # Clear temp files
            if 'temp_dir' in st.session_state and os.path.exists(st.session_state.temp_dir):
                try:
                    shutil.rmtree(st.session_state.temp_dir)
                    st.session_state.temp_dir = os.path.join(os.getcwd(), "temp_files")
                    os.makedirs(st.session_state.temp_dir, exist_ok=True)
                except Exception as e:
                    st.error(f"Error clearing temporary files: {str(e)}")
            
            st.success("Document history cleared!")
            st.rerun()
    
    st.divider()
    
    st.subheader("Account")
    
    # Change password option
    if st.button("Change Password"):
        st.text_input("Current Password", type="password", key="current_pw")
        new_pw = st.text_input("New Password", type="password", key="new_pw")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_pw")
        
        if st.button("Update Password"):
            if new_pw != confirm_pw:
                st.error("New passwords don't match!")
            elif not new_pw:
                st.error("Password cannot be empty")
            else:
                # In a real app, this would update the password in a database
                st.success("Password updated successfully!")
    
    # Delete account option
    if st.button("Delete Account"):
        st.warning("This action cannot be undone!")
        confirm = st.checkbox("I understand this action cannot be undone")
        if confirm and st.button("Confirm Delete"):
            # In a real app, this would delete the user's account from a database
            st.session_state.user_logged_in = False
            st.session_state.username = ""
            st.success("Account deleted. Redirecting to login...")
            st.rerun()

    st.divider()
    
    st.subheader("About")
    st.write("""
    **LegalAI Assistant** v1.0
    
    An AI-powered tool for legal document analysis, designed to help lawyers save time and improve accuracy.
    
    **Features:**
    - Document summarization
    - Timeline extraction
    - Precedent case matching
    - Legal jargon translation
    - AI Chatbot
    
    **Libraries Used:**
    - Streamlit
    - spaCy
    - PyPDF2/pdf2image
    - pytesseract
    - and more... definitely
    """)
