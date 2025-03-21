import os
import streamlit as st
from streamlit_option_menu import option_menu
import tempfile
import uuid
import pickle
import base64
from pathlib import Path

# Import utility modules
from utils.document_processor import process_document
from utils.nlp_analyzer import summarize_document
from utils.timeline_generator import extract_timeline
from utils.precedent_finder import find_precedents
from utils.translation import translate_legal_jargon
from models.legal_document import LegalDocument

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
    
def save_uploaded_file(uploaded_file):
    """Save an uploaded file to a temporary location and return the path."""
    file_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def login_page():
    """Display login page."""
    st.title("Welcome to LegalAI Assistant")
    st.markdown("### Indian Legal Document Analysis Platform")
    
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
    # Sidebar navigation
    with st.sidebar:
        st.title("LegalAI Assistant")
        st.write(f"Welcome, {st.session_state.username}")
        
        selected_tab = option_menu(
            "Navigation",
            ["Home", "Summary", "Timeline", "Precedents", "Legal Terms Simplifier", "Settings"],
            icons=["house", "file-text", "calendar", "search", "translate", "gear"],
            menu_icon="list",
            default_index=0,
        )
        
        st.divider()
        st.subheader("Notes")
        
        # Display and edit notes for the current document
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
    elif selected_tab == "Settings":
        settings_page()
    elif selected_tab != "Home":
        st.warning("Please upload a document first.")

def home_page():
    """Home page with document upload and history."""
    st.title("Document Upload")
    
    uploaded_file = st.file_uploader(
        "Upload a legal document (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        help="Upload the legal document you want to analyze"
    )
    
    if uploaded_file:
        with st.spinner("Processing document..."):
            # Save the uploaded file and process it
            file_path = save_uploaded_file(uploaded_file)
            
            # Process the document
            processed_text = process_document(file_path, uploaded_file.type)
            
            if processed_text:
                # Create a new document object
                doc = LegalDocument(
                    id=str(uuid.uuid4()),
                    filename=uploaded_file.name,
                    content=processed_text,
                    file_type=uploaded_file.type,
                    file_path=file_path
                )
                
                # Set as current document and add to history (avoid duplicates)
                st.session_state.current_document = doc
                
                # Check if document with same name exists in history
                duplicate = False
                for existing_doc in st.session_state.document_history:
                    if existing_doc.filename == doc.filename:
                        duplicate = True
                        break
                
                if not duplicate:
                    st.session_state.document_history.append(doc)
                
                st.success(f"Document '{uploaded_file.name}' processed successfully!")
                st.rerun()
            else:
                st.error("Failed to process the document. Please try again.")
    
    st.divider()
    
    # Display document history
    st.subheader("Document History")
    
    if not st.session_state.document_history:
        st.info("No documents in history. Upload a document to get started.")
    else:
        # Create a dictionary to store latest version of each document by filename
        unique_docs = {}
        for doc in st.session_state.document_history:
            unique_docs[doc.filename] = doc
        
        # Display only unique documents
        for i, (filename, doc) in enumerate(unique_docs.items()):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{filename}")
            with col2:
                st.write(f"Type: {doc.file_type}")
            with col3:
                if st.button("Open", key=f"open_{i}"):
                    st.session_state.current_document = doc
                    st.rerun()

def summary_page():
    """Page showing document summary."""
    doc = st.session_state.current_document
    
    st.title(f"Summary: {doc.filename}")
    
    # Document view and summary side by side
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Original Document")
        st.text_area("Document Content", value=doc.content[:1000] + "...", height=500, disabled=True)
    
    with col2:
        st.subheader("Document Summary")
        
        with st.spinner("Generating summary..."):
            # Generate the summary
            summary = summarize_document(doc.content)
            st.markdown(summary)
    
    # Export options
    st.divider()
    export_options = st.columns([1, 1, 1, 3])
    
    with export_options[0]:
        if st.button("Export as PDF"):
            # In a real app, this would generate a PDF
            st.info("PDF export feature will be implemented here")
    
    with export_options[1]:
        if st.button("Export as DOCX"):
            # In a real app, this would generate a DOCX
            st.info("DOCX export feature will be implemented here")
    
    with export_options[2]:
        if st.button("Export as TXT"):
            # Create a download link for the text
            text_content = f"SUMMARY: {doc.filename}\n\n{summary}\n\nOriginal Document:\n{doc.content}"
            b64 = base64.b64encode(text_content.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="{doc.filename}_summary.txt">Download TXT</a>'
            st.markdown(href, unsafe_allow_html=True)

def timeline_page():
    """Page showing document timeline and deadlines."""
    doc = st.session_state.current_document
    
    st.title(f"Timeline: {doc.filename}")
    
    with st.spinner("Extracting timeline..."):
        # Extract timeline from the document
        timeline_data = extract_timeline(doc.content)
        
        if timeline_data:
            st.subheader("Important Dates and Deadlines")
            
            # Display timeline in table format
            st.table(timeline_data)
            
            # Visual timeline
            st.subheader("Visual Timeline")
            # In a real app, this would create a visual timeline with Plotly or similar
            st.info("Visual timeline will be displayed here using Plotly")
        else:
            st.info("No timeline information found in this document.")

def precedents_page():
    """Page showing precedent cases and relevant legal arguments."""
    doc = st.session_state.current_document
    
    st.title(f"Precedent Cases: {doc.filename}")
    
    with st.spinner("Finding precedent cases..."):
        # Find precedent cases
        precedents = find_precedents(doc.content)
        
        if precedents:
            st.subheader("Relevant Precedent Cases")
            
            for case in precedents:
                with st.expander(f"{case['case_name']} ({case['year']})"):
                    st.write(f"**Relevance**: {case['relevance']}")
                    st.write(f"**Outcome**: {case['outcome']}")
                    st.write(f"**Key Points**:")
                    for point in case['key_points']:
                        st.write(f"- {point}")
        else:
            st.info("No relevant precedent cases found for this document.")

def translator_page():
    """Page for translating legal jargon to plain language."""
    doc = st.session_state.current_document
    
    st.title(f"Legal Terms Simplifier: {doc.filename}")
    
    # Select text to translate
    st.subheader("Select Text to Translate")
    text_to_translate = st.text_area(
        "Enter or paste legal text to translate:",
        value="",
        height=200
    )
    
    if st.button("Translate") and text_to_translate:
        with st.spinner("Translating..."):
            # Translate the text
            translated_text = translate_legal_jargon(text_to_translate)
            
            st.subheader("Plain Language Translation")
            st.markdown(translated_text)
    
    # Common legal terms glossary
    st.divider()
    st.subheader("Common Legal Terms Glossary")
    
    tab1, tab2 = st.tabs(["Indian Legal Terms", "General Legal Terms"])
    
    with tab1:
        st.markdown("""
        - **Writ petition**: A court petition for extraordinary review, seeking justice when fundamental rights are violated
        - **Suo motu**: Action taken by a court on its own initiative without any party requesting it
        - **Vakalatnama**: Document by which a litigant authorizes an advocate to represent them in court
        - **Lok adalat**: People's court where disputes are settled through compromise and conciliation
        - **FIR**: First Information Report, the document prepared by police when they receive information about a cognizable offense
        - **IPC**: Indian Penal Code, the main criminal code of India
        - **CPC**: Code of Civil Procedure, the procedural law related to civil proceedings in India
        - **CrPC**: Code of Criminal Procedure, the main legislation on procedure for administration of criminal law in India
        - **PIL**: Public Interest Litigation, court case filed to protect the public interest
        - **Anticipatory bail**: Bail granted to a person who anticipates arrest for a non-bailable offense
        """)
        
    with tab2:
        st.markdown("""
        - **Force majeure**: Unforeseeable circumstances that prevent fulfilling a contract
        - **Habeas corpus**: A legal action to determine if someone's detention is lawful
        - **Res judicata**: A matter that has been adjudicated and cannot be pursued further
        - **Prima facie**: Based on first impression or accepted as correct until proven otherwise
        - **Voir dire**: Preliminary examination of a witness or juror
        - **Stare decisis**: Legal principle of determining points based on precedent
        - **Mens rea**: The intention or knowledge of wrongdoing
        - **Actus reus**: The action or conduct that is a constituent element of a crime
        """)

def settings_page():
    """Settings page for user preferences."""
    st.title("Settings")
    
    st.subheader("User Preferences")
    
    # In a real app, these settings would be saved to a database or local storage
    col1, col2 = st.columns(2)
    
    with col1:
        st.toggle("Enable Email Notifications", value=False)
        
        # Get dark mode from session state or default to False
        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = False
            
        # Create toggle that updates session state
        dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
        
        # Update session state if toggle changes
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            # Apply dark mode theme
            if dark_mode:
                st.markdown("""
                <style>
                    .stApp {
                        background-color: #1E1E1E;
                        color: #FFFFFF;
                    }
                    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, span, div {
                        color: #FFFFFF !important;
                    }
                    .stTextArea > div > div > textarea {
                        background-color: #2D2D2D;
                        color: #FFFFFF;
                    }
                    .stButton > button {
                        background-color: #0E6EF9;
                        color: #FFFFFF;
                    }
                    .stSidebar {
                        background-color: #252525;
                    }
                </style>
                """, unsafe_allow_html=True)
            else:
                # Reset to light mode (let Streamlit handle default styling)
                st.rerun()
        
        st.number_input("Number of items in history", min_value=5, max_value=50, value=10)
    
    with col2:
        st.selectbox("Default Export Format", options=["PDF", "DOCX", "TXT"], index=0)
        
        # Updated language options to include Indian languages
        st.selectbox("Language", options=[
            "English", 
            "Hindi", 
            "Bengali", 
            "Marathi", 
            "Tamil", 
            "Telugu", 
            "Kannada", 
            "Malayalam", 
            "Gujarati", 
            "Punjabi"
        ], index=0)
    
    st.divider()
    
    st.subheader("Account")
    if st.button("Change Password"):
        st.info("Password change functionality would be implemented here")
    
    if st.button("Delete Account"):
        confirm = st.checkbox("I understand this action cannot be undone")
        if confirm and st.button("Confirm Delete"):
            st.warning("Account deletion would be implemented here")

# Main app flow
def main():
    """Main application flow."""
    # Display short splash screen on first load
    if not st.session_state.get('app_loaded', False):
        st.markdown(
            """
            <div style='text-align: center; margin-top: 100px;'>
                <h1>⚖️ LegalAI Assistant</h1>
                <p>Your AI-powered Indian legal document analyzer</p>
                <h3>Simplifying Indian legal research and analysis</h3>
                <p style='font-size: 0.9em;'>Specialized in IPC, CPC, CrPC and Indian case law</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.session_state.app_loaded = True
        import time
        time.sleep(1)
        st.rerun()
    
    # Flow control based on login state
    if not st.session_state.user_logged_in:
        login_page()
    else:
        main_interface()

if __name__ == "__main__":
    main()
