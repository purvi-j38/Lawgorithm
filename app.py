import streamlit as st
from streamlit_option_menu import option_menu
import tempfile
import time

# Import dark mode function from settings
from pages.settings import apply_dark_mode

# Set page configuration
st.set_page_config(
    page_title="LegalAI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'current_document' not in st.session_state:
    st.session_state.current_document = None
if 'document_history' not in st.session_state:
    st.session_state.document_history = []
if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Create a session-specific directory for temporary files
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

def login_page():
    """Display login page."""
    # Hide navigation elements before login
    hide_navigation_css = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp > header {display: none !important;}
    </style>
    """
    st.markdown(hide_navigation_css, unsafe_allow_html=True)
    
    st.title("Welcome to LegalAI Assistant")
    st.markdown("### Indian Legal Document Analysis Platform")
    
    # Display features section above login
    st.write("""
    **Features:**
    - 📄 Document Summarization - Get concise summaries of complex legal documents
    - ⏱️ Timeline Extraction - Automatically identify key dates and deadlines
    - ⚖️ Precedent Case Matching - Find relevant case law and legal precedents
    - 💬 Legal Terms Simplifier - Translate complex legal jargon to plain language
    - 💻 AI Chatbot - Ask questions about Indian law and your documents
    """)
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # Simple mock login - in a real app, this would validate against a database
            if username and password:
                st.session_state.user_logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Please enter username and password")
    
    with col2:
        st.subheader("Sign Up")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Sign Up"):
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            elif new_username and new_password:
                # In a real app, this would create a new user in the database
                st.success("Account created! Please login.")
            else:
                st.error("Please fill all fields")

def main_interface():
    """Display the main interface after login."""
    with st.sidebar:
        st.title("LegalAI Assistant")
        st.write(f"Welcome, {st.session_state.username}")
        
        selected_tab = option_menu(
            "Navigation",
            ["Home", "Summary", "Timeline", "Precedents", "Legal Terms Simplifier", "VERA", "Settings"],
            icons=["house", "file-text", "calendar", "search", "translate", "chat-dots", "gear"],
            menu_icon="list",
            default_index=0,
        )
        
        st.divider()
        st.subheader("Notes")
        
        if st.session_state.current_document:
            doc_id = st.session_state.current_document.id  
            if doc_id not in st.session_state.notes:
                st.session_state.notes[doc_id] = ""
            
            st.session_state.notes[doc_id] = st.text_area(
                "Your notes for this document:",
                value=st.session_state.notes[doc_id],
                height=200,
                key=f"notes_{doc_id}"
            )
        
        if st.button("Logout"):
            st.session_state.user_logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    # Main content area
    if selected_tab == "Home":
        home_page()
    elif selected_tab == "Summary" and st.session_state.current_document:
        summary_page()
    elif selected_tab == "Timeline" and st.session_state.current_document:
        timeline_page()
    elif selected_tab == "Precedents" and st.session_state.current_document:
        precedents_page()
    elif selected_tab == "Legal Terms Simplifier" and st.session_state.current_document:
        translator_page()
    elif selected_tab == "VERA":
        from utils.chatbot import render_chatbot_page
        render_chatbot_page()
    elif selected_tab == "Settings":
        settings_page()
    elif selected_tab != "Home" and selected_tab != "AI Chat":
        st.warning("Please upload a document first.")

def home_page():
    """Home page with document upload and history."""
    # Import and render home page
    from pages.home import render_home_page
    render_home_page()

def summary_page():
    """Page showing document summary."""
    # Import and render summary page
    from pages.summary import render_summary_page
    render_summary_page()

def timeline_page():
    """Page showing document timeline and deadlines."""
    # Import and render timeline page
    from pages.timeline import render_timeline_page
    render_timeline_page()

def precedents_page():
    """Page showing precedent cases and relevant legal arguments."""
    # Import and render precedents page
    from pages.precedents import render_precedents_page
    render_precedents_page()

def translator_page():
    """Page for translating legal jargon to plain language."""
    # Import and render translator page
    from pages.translator import render_translator_page
    render_translator_page()

def settings_page():
    """Settings page for user preferences."""
    # Import and render settings page
    from pages.settings import render_settings_page
    render_settings_page()

def main():
    """Main application flow."""
    if not st.session_state.get('app_loaded', False):
        st.markdown(
            """
            <div style='text-align: center; margin-top: 100px;'>
                <h1>⚖️ LegalAI Assistant</h1>
                <p>Your AI-powered Indian legal document analyzer</p>
                <h3>Simplifying Indian legal research and analysis</h3>
                <p style='font-size: 0.9em;'>Specialized in IPC, CPC, CrPC, BNS and Indian case law</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.session_state.app_loaded = True
        import time
        time.sleep(5)
        st.rerun()
    
    if not st.session_state.user_logged_in:
        login_page()
    else:
        main_interface()

if __name__ == "__main__":
    main()