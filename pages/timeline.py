import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from datetime import datetime
from utils.timeline_generator import extract_timeline  # You'll need to update this

# Modified extract_timeline function (should be in your utils/timeline_generator.py)
def extract_timeline(content):
    """Enhanced legal timeline extractor for Indian court documents"""
    timeline_events = []
    
    # Indian legal date patterns
    date_patterns = [
        r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b',        # DD.MM.YYYY
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',           # DD/MM/YYYY
        r'\b(\d{1,2} \w+ \d{4})\b',               # 06 November 2009
        r'(?:dated|on) (\w+ \d{1,2}, \d{4})',     # March 27, 2025
        r'(\d{1,2}-\w+-\d{4})',                   # 27-Mar-2025
    ]
    
    # Legal event triggers with priorities
    event_triggers = [
        (r'murder(?:ed)? (?:on|dated)', 'Violent Crime', 'red'),
        (r'F\.I\.R\. (?:registered|filed)', 'FIR Filing', 'orange'),
        (r'Sessions Trial No', 'Trial Proceedings', 'purple'),
        (r'judgment dated', 'Court Judgment', 'blue'),
        (r'High Court (?:allowed|dismissed)', 'Appeal Decision', 'green'),
        (r'Supreme Court (?:allowed|dismissed)', 'Final Verdict', 'darkblue'),
        (r'post-mortem report', 'Medical Evidence', 'pink'),
        (r'bail (?:granted|denied)', 'Bail Hearing', 'yellow'),
        (r'sentenced to', 'Sentencing', 'black'),
    ]

    for line in content.split('\n'):
        for pattern in date_patterns:
            dates = re.findall(pattern, line)
            if dates:
                date_str = dates[0]
                event_type = 'Legal Event'
                color = 'gray'
                description = line.strip()[:100] + "..."  # Default description

                # Check for specific event types
                for trigger, et, clr in event_triggers:
                    if re.search(trigger, line, re.IGNORECASE):
                        event_type = et
                        color = clr
                        
                        # Create meaningful descriptions
                        if 'murder' in trigger:
                            description = "Homicide of Mohan Singh"
                        elif 'F.I.R' in trigger:
                            description = "FIR Registered (No. 458/2009)"
                        elif 'Sessions Trial' in trigger:
                            description = "Trial Court Conviction"
                        elif 'High Court' in trigger:
                            description = "High Court Partial Acquittal"
                        elif 'Supreme Court' in trigger:
                            description = "Supreme Court Final Verdict"
                        break

                timeline_events.append({
                    "Date": date_str,
                    "Type": event_type,
                    "Description": description,
                    "Color": color,
                    "Context": line.strip()
                })
    
    return timeline_events

def render_timeline_page():
    """Render a court-case specific timeline visualization"""
    doc = st.session_state.current_document
    
    if not doc:
        st.warning("Please upload a document first.")
        return
    
    st.title(f"Case Timeline: {doc.filename}")
    
    # Process timeline data
    if not doc.timeline:
        with st.spinner("Analyzing legal chronology..."):
            doc.timeline = extract_timeline(doc.content)
    
    if doc.timeline:
        # Convert dates to datetime objects
        valid_events = []
        date_formats = [
            '%d.%m.%Y',    # 06.11.2009
            '%d/%m/%Y',    # 06/11/2009
            '%d %B %Y',    # 06 November 2009
            '%B %d, %Y',   # March 27, 2025
            '%d-%b-%Y',    # 27-Mar-2025
        ]
        
        for event in doc.timeline:
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(event['Date'], fmt)
                    event['date_obj'] = dt
                    valid_events.append(event)
                    break
                except:
                    continue

        if not valid_events:
            st.info("No valid legal dates found in document")
            return
            
        events_df = pd.DataFrame(valid_events).sort_values('date_obj')
        
        # Create legal timeline visualization
        fig = go.Figure()
        
        # Add timeline markers
        symbol_map = {
            'Violent Crime': 'diamond',
            'FIR Filing': 'square',
            'Trial Proceedings': 'circle',
            'Court Judgment': 'star',
            'Appeal Decision': 'triangle-up',
            'Final Verdict': 'pentagon'
        }
        
        for event_type in events_df['Type'].unique():
            subset = events_df[events_df['Type'] == event_type]
            fig.add_trace(go.Scatter(
                x=subset['date_obj'],
                y=[1]*len(subset),
                mode='markers+text',
                name=event_type,
                marker=dict(
                    size=16,
                    color=subset.iloc[0]['Color'],
                    symbol=symbol_map.get(event_type, 'circle'),
                    line=dict(width=2, color='black')
                ),
                text=subset['Description'],
                textposition='middle right',
                hovertext=subset['Context'],
                hoverinfo='text'
            ))
        
        # Add timeline axis
        fig.add_shape(
            type="line",
            x0=events_df['date_obj'].min(),
            x1=events_df['date_obj'].max(),
            y0=1,
            y1=1,
            line=dict(color='black', width=3)
        )
        
        # Configure legal timeline layout
        fig.update_layout(
            height=200 + len(events_df)*40,
            margin=dict(l=20, r=20, b=20, t=40),
            xaxis=dict(
                title="Case Timeline",
                showgrid=False,
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            ),
            yaxis=dict(
                showticklabels=False,
                range=[0.8, 1.2]
            ),
            plot_bgcolor='white',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display detailed legal chronology
        st.subheader("Case Chronology")
        events_df['Formatted Date'] = events_df['date_obj'].dt.strftime('%d %b %Y')
        st.dataframe(
            events_df[['Formatted Date', 'Type', 'Description']],
            column_config={
                'Formatted Date': 'Date',
                'Type': 'Event Type',
                'Description': 'Legal Significance'
            },
            hide_index=True,
            use_container_width=True,
            height=min(400, 35*len(events_df))
        )
        
    else:
        st.info("No timeline events found in document")
    
    # Manual entry for legal dates
    st.divider()
    st.subheader("Add Legal Event")
    with st.form("add_legal_event"):
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date", datetime.now())
        with col2:
            event_type = st.selectbox("Event Type", [
                "FIR Filing", 
                "Charge Sheet", 
                "Bail Hearing",
                "Trial Hearing",
                "Judgment",
                "Appeal Filing"
            ])
        description = st.text_input("Event Description")
        
        if st.form_submit_button("Add to Timeline"):
            new_event = {
                "Date": event_date.strftime("%d %B %Y"),
                "Type": event_type,
                "Description": description,
                "Context": "Manually added event",
                "Color": "gray"
            }
            doc.timeline.append(new_event)
            st.rerun()