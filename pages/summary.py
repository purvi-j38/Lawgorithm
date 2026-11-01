import streamlit as st
import base64
import io
import os
import sys
from utils.nlp_analyzer import summarize_document

def render_summary_page():
    """Render the summary page for the current document."""
    doc = st.session_state.current_document
    
    if not doc:
        st.warning("Please upload a document first.")
        return
    
    st.title(f"Summary: {doc.filename}")
    
    # Document view and summary side by side
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Original Document")
        st.text_area("Document Content", value=doc.content[:5000] + "..." if len(doc.content) > 5000 else doc.content, height=500, disabled=True)
    
    with col2:
        st.subheader("Document Summary")
        
        if doc.summary:
            # Use cached summary if available
            st.markdown(doc.summary)
        else:
            with st.spinner("Generating summary..."):
                # Generate the summary
                summary = summarize_document(doc.content)
                # Cache the summary in the document
                doc.generate_summary(summary)
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
            if doc.summary:
                text_content = f"SUMMARY: {doc.filename}\n\n{doc.summary}\n\nOriginal Document:\n{doc.content}"
                b64 = base64.b64encode(text_content.encode()).decode()
                href = f'<a href="data:file/txt;base64,{b64}" download="{doc.filename}_summary.txt">Download TXT</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.warning("Generate a summary first")
