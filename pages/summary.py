import streamlit as st
import base64
from utils.nlp_analyzer import summarize_document

_CSS = """
<style>
.law-header {
    border-left: 4px solid #1a3a5c;
    padding: 0.6rem 1rem;
    margin-bottom: 1.2rem;
    background: linear-gradient(90deg, #f0f4f8 0%, #fff 100%);
    border-radius: 0 6px 6px 0;
}
.law-header h2 { margin:0; color:#1a3a5c; font-family:Georgia,serif; }
.law-header p  { margin:0; color:#64748b; font-size:0.85rem; }
</style>
"""

def render_summary_page():
    doc = st.session_state.current_document
    if not doc:
        st.warning("Please upload a document first.")
        return

    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="law-header">
        <h2>📄 Executive Legal Brief & Analysis</h2>
        <p>TextRank · TF-IDF · LSA Latent Semantic Topics · NER Entity Extraction &nbsp;|&nbsp; High-Stake Law Firm Standard</p>
    </div>
    """, unsafe_allow_html=True)

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Document", doc.filename[:22] + ("…" if len(doc.filename) > 22 else ""))
    mc2.metric("Characters", f"{len(doc.content):,}")
    mc3.metric("Word Count (approx.)", f"{len(doc.content.split()):,}")
    mc4.metric("Date Uploaded", doc.upload_date.strftime("%d %b %Y") if doc.upload_date else "—")

    st.divider()

    col_doc, col_report = st.columns([1, 1], gap="large")

    with col_doc:
        st.markdown("#### 📃 Primary Record")

        chars_per_page = 2500
        total_pages = max(1, (len(doc.content) + chars_per_page - 1) // chars_per_page)
        page = st.number_input(
            f"Segment Viewer ({total_pages} page(s) total)",
            min_value=1, max_value=total_pages, value=1, step=1,
        )
        start = (page - 1) * chars_per_page
        excerpt = doc.content[start : start + chars_per_page]

        st.text_area(
            "document_view",
            value=excerpt,
            height=530,
            disabled=True,
            label_visibility="collapsed",
        )
        st.caption(
            f"Viewing characters {start:,} – {min(start + chars_per_page, len(doc.content)):,} "
            f"of {len(doc.content):,}"
        )

    with col_report:
        st.markdown("#### ⚖️ Law Firm Analytical Brief")

        if doc.summary:
            st.markdown(doc.summary)
        else:
            with st.spinner("Executing TextRank, TF-IDF, LSA and NER pipelines..."):
                summary = summarize_document(doc.content)
                doc.generate_summary(summary)
            st.markdown(doc.summary)

    st.divider()
    st.markdown("#### 💾 Export Brief")

    ecol1, ecol2, ecol3 = st.columns([1, 1, 2])

    with ecol1:
        if doc.summary:
            header = (
                f"LEGAL DOCUMENT EXECUTIVE BRIEF\n"
                f"File: {doc.filename}\n"
                f"Analysis Timestamp: {doc.upload_date.strftime('%d %B %Y') if doc.upload_date else 'N/A'}\n"
                f"{'=' * 65}\n\n"
            )
            txt = header + doc.summary
            b64 = base64.b64encode(txt.encode("utf-8")).decode()
            st.markdown(
                f'<a href="data:text/plain;base64,{b64}" '
                f'download="{doc.filename}_legal_brief.txt" style="text-decoration:none;">'
                f'<button style="background:#1a3a5c;color:white;border:none;padding:'
                f'0.5rem 1.4rem;border-radius:6px;cursor:pointer;font-size:0.9rem;font-weight:bold;">'
                f'⬇ Download Plain Text Brief</button></a>',
                unsafe_allow_html=True,
            )

    with ecol2:
        if st.button("🔄 Re-analyse Document", use_container_width=True):
            doc.summary = None
            st.rerun()
