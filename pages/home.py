import streamlit as st
import os
import tempfile
import uuid
from utils.document_processor import process_document
from models.legal_document import LegalDocument

def render_home_page():
    """Render the home page with document upload functionality."""
    st.title("Document Upload")
    
    uploaded_file = st.file_uploader(
        "Upload a legal document (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        help="Upload the legal document you want to analyze"
    )
    
    if uploaded_file:
        with st.spinner("Processing document..."):
            # Save the uploaded file
            temp_dir = st.session_state.get('temp_dir', tempfile.mkdtemp())
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
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
                
                # Set as current document and add to history
                st.session_state.current_document = doc
                if 'document_history' not in st.session_state:
                    st.session_state.document_history = []
                st.session_state.document_history.append(doc)
                
                st.success(f"Document '{uploaded_file.name}' processed successfully!")
                st.rerun()
            else:
                st.error("Failed to process the document. Please try again.")
    
    st.divider()
    
    # Display document history
    st.subheader("Document History")
    
    if not st.session_state.get('document_history', []):
        st.info("No documents in history. Upload a document to get started.")
    else:
        for i, doc in enumerate(reversed(st.session_state.document_history)):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{doc.filename}")
            with col2:
                st.write(f"Type: {doc.file_type}")
            with col3:
                if st.button("Open", key=f"open_{i}"):
                    st.session_state.current_document = doc
                    st.rerun()
