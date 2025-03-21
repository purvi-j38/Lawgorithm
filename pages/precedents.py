import streamlit as st
from utils.precedent_finder import find_precedents

def render_precedents_page():
    """Render the precedents page for the current document."""
    doc = st.session_state.current_document
    
    if not doc:
        st.warning("Please upload a document first.")
        return
    
    st.title(f"Precedent Cases: {doc.filename}")
    
    # Check if we already have precedent data cached
    if doc.precedents:
        precedents = doc.precedents
    else:
        with st.spinner("Finding precedent cases..."):
            # Find precedent cases
            precedents = find_precedents(doc.content)
            # Cache the results
            doc.set_precedents(precedents)
    
    if precedents:
        st.subheader("Relevant Precedent Cases")
        
        # Filter options
        st.sidebar.subheader("Filter Precedents")
        relevance_filter = st.sidebar.multiselect(
            "Relevance", 
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )
        
        # Filter precedents by relevance
        filtered_precedents = [p for p in precedents if p["relevance"] in relevance_filter]
        
        if not filtered_precedents:
            st.info("No precedents match the selected filters.")
        else:
            # Display precedents
            for i, case in enumerate(filtered_precedents):
                with st.expander(f"{case['case_name']} ({case['year']}) - {case['relevance']} Relevance"):
                    st.write(f"**Outcome**: {case['outcome']}")
                    st.write(f"**Key Points**:")
                    for point in case['key_points']:
                        st.write(f"- {point}")
                    
                    # Add options to save notes about this precedent
                    st.text_area(
                        "Your notes on this case:",
                        value=st.session_state.get(f"precedent_note_{i}", ""),
                        key=f"precedent_note_{i}",
                        on_change=save_precedent_note,
                        args=(i,)
                    )
    else:
        st.info("No relevant precedent cases found for this document.")
    
    # Option to manually add a precedent
    st.divider()
    
    st.subheader("Add Precedent Case Manually")
    
    case_name = st.text_input("Case Name")
    case_year = st.text_input("Year")
    
    col1, col2 = st.columns(2)
    
    with col1:
        relevance = st.selectbox("Relevance", ["High", "Medium", "Low"])
    
    with col2:
        outcome = st.text_input("Outcome")
    
    key_points = st.text_area("Key Points (one per line)")
    
    if st.button("Add Precedent"):
        if case_name and case_year and key_points:
            # Create new precedent
            new_precedent = {
                "case_name": case_name,
                "year": case_year,
                "relevance": relevance,
                "outcome": outcome,
                "key_points": [point.strip() for point in key_points.split('\n') if point.strip()]
            }
            
            # Add to precedents
            if not doc.precedents:
                doc.precedents = []
            
            doc.precedents.append(new_precedent)
            st.success("Precedent added!")
            st.rerun()
        else:
            st.error("Please fill in all required fields")

def save_precedent_note(index):
    """Save a note for a precedent case."""
    # This function is called when a note is changed
    # The note is already saved in session state by Streamlit
    st.success("Note saved!")
