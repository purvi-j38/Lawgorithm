"""
Timeline Page — professional chronological visualization.
Uses utils/timeline_generator.py (regex + NER, no LLM, no hardcoded names).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.timeline_generator import extract_timeline

_CSS = """
<style>
.law-header {
    border-left: 4px solid #1a3a5c;
    padding: 0.5rem 1rem;
    margin-bottom: 1.2rem;
    background: linear-gradient(90deg, #f0f4f8 0%, #fff 100%);
    border-radius: 0 6px 6px 0;
}
.law-header h2 { margin: 0; color: #1a3a5c; }
.law-header p  { margin: 0; color: #6b7280; font-size: 0.82rem; }
.tl-empty {
    text-align: center; padding: 3rem; color: #9ca3af;
    background: #f8fafc; border-radius: 8px; border: 1px dashed #e2e8f0;
}
</style>
"""


def _build_figure(events_df: pd.DataFrame) -> go.Figure:
    """Build a clean, non-overlapping Plotly timeline figure."""
    fig = go.Figure()
    n = len(events_df)

    # Alternating y positions so labels never overlap
    y_vals   = [1.10 if i % 2 == 0 else 0.90 for i in range(n)]
    t_pos    = ["top center" if i % 2 == 0 else "bottom center" for i in range(n)]
    conn_y   = [1.10 if i % 2 == 0 else 0.90 for i in range(n)]

    # Connector lines from marker to axis
    for i in range(n):
        fig.add_shape(
            type="line",
            x0=events_df["date_obj"].iloc[i],
            x1=events_df["date_obj"].iloc[i],
            y0=1.0,
            y1=conn_y[i],
            line=dict(color="#94a3b8", width=1, dash="dot"),
        )

    # Central axis line
    fig.add_shape(
        type="line",
        x0=events_df["date_obj"].min(),
        x1=events_df["date_obj"].max(),
        y0=1.0, y1=1.0,
        line=dict(color="#1a3a5c", width=2.5),
    )

    # One trace per event type for legend
    for etype in events_df["Type"].unique():
        sub = events_df[events_df["Type"] == etype].copy()
        sub_idx = list(sub.index)

        fig.add_trace(go.Scatter(
            x=sub["date_obj"],
            y=[y_vals[i] for i in sub_idx],
            mode="markers+text",
            name=etype,
            marker=dict(
                size=13,
                color=sub.iloc[0]["Color"],
                symbol="circle",
                line=dict(width=2, color="white"),
            ),
            text=sub["Date"],
            textposition=[t_pos[i] for i in sub_idx],
            textfont=dict(size=9, color="#374151"),
            hovertext=sub.apply(
                lambda r: f"<b>{r['Type']}</b><br>{r['Date']}<br>{r['Description']}", axis=1
            ),
            hoverinfo="text",
        ))

    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="white",
        font=dict(family="Georgia, 'Times New Roman', serif", size=11),
        xaxis=dict(
            title="",
            showgrid=False,
            type="date",
            tickformat="%b %Y",
            tickfont=dict(size=10),
            rangeslider=dict(visible=True, thickness=0.04, bgcolor="#f0f4f8"),
        ),
        yaxis=dict(
            visible=False,
            range=[0.72, 1.28],
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    return fig


def render_timeline_page():
    doc = st.session_state.current_document
    if not doc:
        st.warning("Please upload a document first.")
        return

    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="law-header">
        <h2>⏱ Case Timeline</h2>
        <p>Chronological reconstruction using Regex + NER — no LLM, no hardcoded data</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Process ───────────────────────────────────────────────────────────────
    if not doc.timeline:
        with st.spinner("Reconstructing case chronology…"):
            doc.timeline = extract_timeline(doc.content)

    valid = [e for e in (doc.timeline or []) if "date_obj" in e]

    if not valid:
        st.markdown("""
        <div class="tl-empty">
            <h4>No dated events found</h4>
            <p>The document may not contain recognisable date strings,<br>
            or all dates are in an unrecognised format.<br>
            You can add events manually below.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        events_df = (
            pd.DataFrame(valid)
            .sort_values("date_obj")
            .reset_index(drop=True)
        )

        # ── Stats bar ─────────────────────────────────────────────────────────
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Events Found", len(events_df))
        s2.metric("Event Types", events_df["Type"].nunique())
        span = events_df["date_obj"].max() - events_df["date_obj"].min()
        s3.metric("Time Span", f"{span.days // 365}y {(span.days % 365) // 30}m" if span.days > 30 else f"{span.days}d")
        s4.metric("Earliest", events_df["date_obj"].min().strftime("%d %b %Y"))

        st.divider()

        # ── Chart ─────────────────────────────────────────────────────────────
        fig = _build_figure(events_df)
        st.plotly_chart(fig, use_container_width=True)

        # ── Chronology table ──────────────────────────────────────────────────
        st.markdown("### 📋 Detailed Chronology")

        events_df["Formatted Date"] = events_df["date_obj"].dt.strftime("%d %b %Y")
        display = events_df[["Formatted Date", "Type", "Description"]].copy()
        display.columns = ["Date", "Event Type", "Description"]

        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Date":       st.column_config.TextColumn("Date",       width="small"),
                "Event Type": st.column_config.TextColumn("Event Type", width="medium"),
                "Description":st.column_config.TextColumn("Description",width="large"),
            },
        )

        # Filter sidebar
        with st.sidebar.expander("Filter Timeline", expanded=False):
            all_types = sorted(events_df["Type"].unique())
            selected_types = st.multiselect(
                "Event types", all_types, default=all_types, key="tl_filter"
            )
            if selected_types != all_types:
                filtered = events_df[events_df["Type"].isin(selected_types)]
                if not filtered.empty:
                    st.write(f"Showing {len(filtered)} of {len(events_df)} events")

    # ── Manual entry ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### ➕ Add Event Manually")

    with st.form("add_tl_event"):
        c1, c2 = st.columns(2)
        with c1:
            evt_date = st.date_input("Event Date", datetime.today())
        with c2:
            evt_type = st.selectbox("Event Type", [
                "FIR / Police Report",
                "Arrest / Detention",
                "Bail Proceedings",
                "Trial Commencement",
                "Court Hearing",
                "Witness Examination",
                "Judgment / Order",
                "High Court Ruling",
                "Supreme Court Ruling",
                "Appeal Filed",
                "Conviction / Sentencing",
                "Acquittal / Discharge",
                "Other Legal Event",
            ])
        evt_desc = st.text_input("Description", placeholder="Brief description of the event")

        if st.form_submit_button("Add Event", type="primary"):
            if not doc.timeline:
                doc.timeline = []
            doc.timeline.append({
                "Date":        evt_date.strftime("%d %B %Y"),
                "date_obj":    datetime(evt_date.year, evt_date.month, evt_date.day),
                "Type":        evt_type,
                "Description": evt_desc or evt_type,
                "Color":       "#6B7280",
                "Context":     "Manually added event",
            })
            st.success("Event added to timeline.")
            st.rerun()
