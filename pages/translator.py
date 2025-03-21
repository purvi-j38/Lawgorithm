import streamlit as st
from utils.translation import translate_legal_jargon, simplify_legal_document

def render_translator_page():
    """Render the legal jargon translator page."""
    doc = st.session_state.current_document
    
    if not doc:
        st.warning("Please upload a document first.")
        return
    
    st.title(f"Legal Jargon Translator: {doc.filename}")
    
    # Tabs for different translation modes
    tab1, tab2 = st.tabs(["Translate Selection", "Simplify Document"])
    
    with tab1:
        # Select text to translate
        st.subheader("Select Text to Translate")
        
        # Option to select from document or enter manually
        selection_method = st.radio(
            "Text Source",
            ["Extract from Document", "Enter Manually"]
        )
        
        if selection_method == "Extract from Document":
            # Show the document and let user select a portion
            st.write("Document Content (select a portion to translate):")
            
            # Display a small portion of the document at a time to make selection manageable
            start_pos = st.slider("Document Position", 0, max(0, len(doc.content) - 1000), 0)
            excerpt = doc.content[start_pos:start_pos + 1000]
            
            text_to_translate = st.text_area(
                "Selected Text:",
                value=excerpt,
                height=200
            )
        else:
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
    
    with tab2:
        st.subheader("Simplify Entire Document")
        st.write("This will attempt to translate the entire document into plain language.")
        st.warning("Processing large documents may take some time.")
        
        if st.button("Simplify Document"):
            with st.spinner("Simplifying document..."):
                # For very large documents, only process a portion
                if len(doc.content) > 20000:
                    st.info("Document is large, processing first 20,000 characters only.")
                    text_to_process = doc.content[:20000]
                else:
                    text_to_process = doc.content
                
                simplified_text = simplify_legal_document(text_to_process)
                
                st.subheader("Simplified Document")
                st.markdown(simplified_text)
    
    # Common legal terms glossary
    st.divider()
    st.subheader("Common Legal Terms Glossary")
    
    with st.expander("View Glossary"):
        st.markdown("""
        - **Force majeure**: Unforeseeable circumstances that prevent fulfilling a contract
        - **Habeas corpus**: A legal action to determine if someone's detention is lawful
        - **Res judicata**: A matter that has been adjudicated and cannot be pursued further
        - **Prima facie**: Based on first impression or accepted as correct until proven otherwise
        - **Voir dire**: Preliminary examination of a witness or juror
        - **Stare decisis**: Legal principle of determining points based on precedent
        - **Mens rea**: The intention or knowledge of wrongdoing
        - **Actus reus**: The action or conduct that is a constituent element of a crime
        - **Pro se**: Representing oneself in court without an attorney
        - **De novo**: Starting anew, as if previous proceedings did not occur
        - **Pro bono**: Legal work done for free or for the public good
        - **Ex parte**: A legal proceeding brought by one person without the other party knowing
        - **Amicus curiae**: Friend of the court; someone who offers information or insight to the court
        - **In camera**: In private, in a judge's chambers
        - **Inter alia**: Among other things
        """)
