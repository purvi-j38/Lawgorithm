import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.timeline_generator import extract_timeline

def render_timeline_page():
    """Render the timeline page for the current document."""
    doc = st.session_state.current_document
    
    if not doc:
        st.warning("Please upload a document first.")
        return
    
    st.title(f"Timeline: {doc.filename}")
    
    # Check if we already have timeline data cached
    if doc.timeline:
        timeline_data = doc.timeline
    else:
        with st.spinner("Extracting timeline..."):
            # Extract timeline from the document
            timeline_data = extract_timeline(doc.content)
            # Cache the results
            doc.set_timeline(timeline_data)
    
    if timeline_data:
        st.subheader("Important Dates and Deadlines")
        
        # Create a DataFrame for display
        df = pd.DataFrame(timeline_data)
        
        # Display timeline in table format
        st.dataframe(df)
        
        # Visual timeline if we have dates that can be parsed
        st.subheader("Visual Timeline")
        
        try:
            # Try to create a visual timeline with Plotly
            # First, extract dates that can be converted to datetime
            dates = []
            events = []
            types = []
            
            for event in timeline_data:
                # Try different date formats
                date_formats = ['%m/%d/%Y', '%B %d, %Y', '%d %B %Y', '%Y-%m-%d']
                
                for fmt in date_formats:
                    try:
                        date = datetime.strptime(event['Date'], fmt)
                        dates.append(date)
                        events.append(event['Description'])
                        types.append(event['Type'])
                        break
                    except:
                        continue
            
            if dates:
                # Create a DataFrame for the timeline
                timeline_df = pd.DataFrame({
                    'Date': dates,
                    'Event': events,
                    'Type': types
                })
                
                # Sort by date
                timeline_df = timeline_df.sort_values('Date')
                
                # Create Plotly figure
                fig = px.timeline(
                    timeline_df, 
                    x_start='Date', 
                    y='Event',
                    color='Type',
                    title='Document Timeline'
                )
                
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Could not create visual timeline due to date format issues.")
                
        except Exception as e:
            st.error(f"Error creating visual timeline: {str(e)}")
            st.info("Visual timeline could not be generated.")
    else:
        st.info("No timeline information found in this document.")
    
    # Add option to manually add dates
    st.divider()
    
    st.subheader("Add Date Manually")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date_input = st.date_input("Date", datetime.now())
    
    with col2:
        event_type = st.selectbox("Type", ["Deadline", "Hearing", "Filing", "Other"])
    
    description = st.text_input("Description")
    
    if st.button("Add to Timeline"):
        if description:
            # Format the date
            date_str = date_input.strftime("%B %d, %Y")
            
            # Create new timeline entry
            new_entry = {
                "Date": date_str,
                "Type": event_type,
                "Description": description,
                "Context": "Manually added"
            }
            
            # Add to timeline
            if not doc.timeline:
                doc.timeline = []
            
            doc.timeline.append(new_entry)
            st.success("Date added to timeline!")
            st.rerun()
        else:
            st.error("Please enter a description")
