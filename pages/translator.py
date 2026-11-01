import streamlit as st
from utils.translation import translate_legal_jargon, simplify_legal_document, LEGAL_TERMS

_CARD_CSS = """
<style>
.law-header {
    border-left: 4px solid #1a3a5c;
    padding: 0.6rem 1rem;
    margin-bottom: 1.5rem;
    background: linear-gradient(90deg, #f0f4f8 0%, #fff 100%);
    border-radius: 0 6px 6px 0;
}
.law-header h2 { margin:0; color:#1a3a5c; font-family:Georgia,serif; }
.law-header p  { margin:0; color:#64748b; font-size:0.85rem; }
</style>
"""

def render_translator_page():
    doc = st.session_state.current_document
    if not doc:
        st.warning("Please upload a document first.")
        return

    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="law-header">
        <h2>⚖️ Legal Terms Simplifier</h2>
        <p>TF-IDF Ranking · Named Entity Preservation · Exact Legal Mapping · Instant Execution</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📄 Analyse Passage", "📋 Simplify Document", "📚 Complete Glossary"])

    with tab1:
        st.markdown("##### Select or enter a passage to decode complex legalese")

        source = st.radio(
            "Text source",
            ["Extract from document", "Enter manually"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if source == "Extract from document":
            max_pos = max(0, len(doc.content) - 2000)
            pos = st.slider(
                "Scroll through document",
                min_value=0, max_value=max_pos, value=0, step=500,
                format="char %d",
            )
            excerpt = doc.content[pos : pos + 2000]
            text_in = st.text_area(
                "Passage (editable)", value=excerpt, height=230,
                label_visibility="visible",
            )
        else:
            text_in = st.text_area(
                "Paste legal passage:",
                height=230,
                placeholder="e.g. The appellant filed an application under Section 438 CrPC seeking anticipatory bail...",
            )

        if st.button("🔍 Identify & Explain Terms", type="primary", use_container_width=True):
            if text_in.strip():
                with st.spinner("Decoding legal terminology…"):
                    result = translate_legal_jargon(text_in)
                st.divider()
                st.markdown(result)
            else:
                st.warning("Please enter text to analyse.")

    with tab2:
        char_count = len(doc.content)
        limit = 35000

        col1, col2 = st.columns(2)
        col1.metric("Document Character Count", f"{char_count:,}")
        col2.metric("Characters In Scope", f"{min(char_count, limit):,}")

        if char_count > limit:
            st.info(f"Large document: processing first {limit:,} characters for high efficiency.")

        st.markdown(
            "Performs NER to preserve names, courts and dates, then extracts all legal terms "
            "ranked by document TF-IDF relevance with plain-language definitions."
        )

        if st.button("📋 Simplify Full Document", type="primary", use_container_width=True):
            with st.spinner("Extracting entities & ranking jargon…"):
                result = simplify_legal_document(doc.content[:limit])
            st.divider()
            st.markdown(result)

    with tab3:
        st.markdown(f"##### Indian & Common Law Legal Glossary ({len(LEGAL_TERMS)} Terms)")

        search = st.text_input(
            "Filter terms",
            placeholder="Type to search (e.g. bail, cognizance, fir, res judicata, mandamus)...",
            label_visibility="collapsed",
        )

        sq = search.lower().strip()
        filtered = {
            k: v for k, v in LEGAL_TERMS.items()
            if not sq or sq in k or sq in v[0].lower() or sq in v[1].lower()
        }

        st.caption(f"Showing {len(filtered)} of {len(LEGAL_TERMS)} catalogued terms")

        items = list(filtered.items())
        mid = (len(items) + 1) // 2
        col_a, col_b = st.columns(2)

        for col, chunk in zip([col_a, col_b], [items[:mid], items[mid:]]):
            with col:
                for key, (display, expl) in chunk:
                    with st.expander(f"**{display}**"):
                        st.write(expl)
