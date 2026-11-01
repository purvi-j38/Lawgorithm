"""
Legal Document NLP Analyzer
TextRank + TF-IDF + LSA + NER
Generates an executive, clear, high-stake legal summary without using any LLM.
"""

import re
import math
import sys
import subprocess
import numpy as np
import spacy
from typing import Dict, List, Tuple, Any
from collections import defaultdict

INDIAN_LEGAL_PATTERNS = {
    'IPC_SECTION':      r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?IPC',
    'BNS_SECTION':      r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?BNS',
    'CRPC_SECTION':     r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?Cr?PC',
    'CPC_SECTION':      r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?CPC',
    'CONSTITUTION':     r'Article\s+\d+(?:\([A-Za-z0-9]+\))?\s+of\s+the\s+Constitution(?:\s+of\s+India)?|Art\.\s*\d+',
    'EVIDENCE_ACT':     r'(?:Section|Sec\.?)\s*(\d+[A-Za-z]*)\s+(?:of\s+)?(?:the\s+)?(?:Indian\s+)?Evidence Act',
    'SCC_CITATION':     r'\(\d{4}\)\s+\d+\s+SCC\s+\d+',
    'AIR_CITATION':     r'AIR\s+\d{4}\s+SC\s+\d+',
    'FIR_NUMBER':       r'FIR\s+No\.?\s*([A-Z0-9/\-]+)',
    'CASE_NUMBER':      r'(?:Criminal\s+Appeal|Civil\s+Appeal|Writ\s+Petition|SLP)[.\s]+No\.?\s*[\d/]+(?:\s+of\s+\d{4})?',
}

STOP_WORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with','by',
    'from','is','are','was','were','be','been','being','have','has','had','do',
    'does','did','will','would','could','should','may','might','shall','that',
    'this','these','those','it','its','not','no','nor','as','if','so','yet',
    'both','either','neither','each','than','then','when','where','which','who',
    'whom','what','how','why','he','she','they','we','you','i','me','him','her',
    'them','us','my','your','his','their','our','said','also','any','all','such',
    'into','upon','under','above','before','after','during','through','between',
    'among','within','without','against','over','per','there','here','out','up',
    'down','off','thus','however','therefore','whereas','wherein','thereof',
    'therein','hereby','herein','hereof','thereto','therewith','therefrom',
    'thereby','shall','hereinafter','aforementioned','aforesaid','notwithstanding',
}

def _load_nlp():
    for model in ('en_core_web_md', 'en_core_web_sm'):
        try:
            return spacy.load(model)
        except OSError:
            continue
    subprocess.run([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
    return spacy.load('en_core_web_sm')

nlp = _load_nlp()

def _clean_text_line(text: str) -> str:
    t = re.sub(r'\s+', ' ', text).strip()
    return t

def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-]{2,}\b', text.lower())
    return [t for t in tokens if t not in STOP_WORDS]

def _compute_tfidf(sentences: List[str]) -> Tuple[np.ndarray, List[str]]:
    vocab: Dict[str, int] = {}
    doc_freq: Dict[str, int] = defaultdict(int)
    tokenized: List[List[str]] = []

    for sent in sentences:
        toks = _tokenize(sent)
        tokenized.append(toks)
        for tok in set(toks):
            if tok not in vocab:
                vocab[tok] = len(vocab)
            doc_freq[tok] += 1

    if not vocab:
        return np.zeros((len(sentences), 1)), []

    vocab_list = list(vocab)
    n = len(sentences)
    mat = np.zeros((n, len(vocab_list)))

    for i, toks in enumerate(tokenized):
        tf: Dict[str, int] = defaultdict(int)
        for tok in toks:
            tf[tok] += 1
        total = len(toks) or 1
        for tok, cnt in tf.items():
            if tok in vocab:
                idf = math.log((n + 1) / (doc_freq[tok] + 1)) + 1
                mat[i, vocab[tok]] = (cnt / total) * idf

    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return mat / norms, vocab_list

def get_top_terms(text: str, top_n: int = 15) -> List[Tuple[str, float]]:
    toks = _tokenize(text)
    if not toks:
        return []
    tf: Dict[str, int] = defaultdict(int)
    for t in toks:
        tf[t] += 1
    total = len(toks)
    scored = sorted(tf.items(), key=lambda x: x[1] / total, reverse=True)
    return scored[:top_n]

def textrank_sentences(sentences: List[str], top_n: int = 8) -> List[Tuple[int, str, float]]:
    if len(sentences) <= top_n:
        return [(i, s, 1.0) for i, s in enumerate(sentences)]

    mat, _ = _compute_tfidf(sentences)
    n = len(sentences)

    sim = mat @ mat.T
    np.fill_diagonal(sim, 0)

    row_sums = sim.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    sim /= row_sums

    d = 0.85
    scores = np.ones(n) / n
    for _ in range(35):
        scores = (1 - d) / n + d * (sim.T @ scores)

    top_idx = set(i for i, _ in sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_n])
    return [(i, sentences[i], float(scores[i])) for i in range(n) if i in top_idx]

def lsa_topics(sentences: List[str], n_topics: int = 4) -> List[Dict[str, Any]]:
    if len(sentences) < 3:
        return []

    mat, vocab = _compute_tfidf(sentences)
    if mat.shape[1] < n_topics:
        return []

    try:
        U, S, Vt = np.linalg.svd(mat, full_matrices=False)
    except np.linalg.LinAlgError:
        return []

    topics = []
    for k in range(min(n_topics, len(S))):
        if S[k] < 0.01:
            continue
        top_term_idx = np.argsort(np.abs(Vt[k]))[::-1][:5]
        top_terms = [vocab[i] for i in top_term_idx if i < len(vocab)]
        sent_scores = np.abs(U[:, k]) * S[k]
        rep_idx = int(np.argmax(sent_scores))
        rep_sent = sentences[rep_idx] if rep_idx < len(sentences) else ''
        topics.append({
            'terms': top_terms,
            'representative': rep_sent,
            'weight': float(S[k]),
        })
    return topics

def extract_entities(text: str) -> Dict[str, List[str]]:
    doc = nlp(text[:80000])
    entities: Dict[str, List[str]] = {
        'parties': [], 'courts': [], 'judges': [],
        'dates': [], 'locations': [],
    }
    seen: Dict[str, set] = defaultdict(set)

    for ent in doc.ents:
        txt = ent.text.strip()
        if not txt or len(txt) < 3:
            continue
        key = txt.lower()

        if ent.label_ == 'PERSON':
            if key not in seen['PERSON']:
                seen['PERSON'].add(key)
                ctx = doc[max(0, ent.start - 3):ent.end + 3].text.lower()
                if any(w in ctx for w in ['justice', ' j.', 'judge', "hon'ble", 'honourable']):
                    entities['judges'].append(txt)
                else:
                    entities['parties'].append(txt)
        elif ent.label_ == 'ORG':
            if key not in seen['ORG']:
                seen['ORG'].add(key)
                if any(w in txt.lower() for w in ['court', 'tribunal', 'bench', 'commission', 'police']):
                    entities['courts'].append(txt)
        elif ent.label_ == 'DATE':
            if key not in seen['DATE']:
                seen['DATE'].add(key)
                entities['dates'].append(txt)
        elif ent.label_ == 'GPE':
            if key not in seen['GPE']:
                seen['GPE'].add(key)
                entities['locations'].append(txt)

    for k in entities:
        entities[k] = entities[k][:6]
    return entities

def extract_legal_references(text: str) -> Dict[str, List[str]]:
    refs: Dict[str, List[str]] = {}
    for name, pattern in INDIAN_LEGAL_PATTERNS.items():
        raw = re.findall(pattern, text, re.IGNORECASE)
        cleaned = []
        for m in raw:
            val = ' '.join(m) if isinstance(m, tuple) else str(m)
            val = val.strip()
            if val and val not in cleaned:
                cleaned.append(val)
        if cleaned:
            refs[name] = cleaned[:5]
    return refs

OUTCOME_KEYWORDS = {
    'allowed', 'dismissed', 'convicted', 'acquitted', 'granted',
    'rejected', 'upheld', 'overruled', 'affirmed', 'reversed',
    'remanded', 'quashed', 'set aside', 'confirmed', 'modified',
    'sentenced', 'penalty', 'compensation', 'directed', 'ordered'
}

def extract_outcome(text: str) -> str:
    tail = text[-12000:]
    doc = nlp(tail)
    candidates = []
    for sent in doc.sents:
        s = sent.text.strip()
        score = sum(1 for kw in OUTCOME_KEYWORDS if kw in s.lower())
        if score >= 1 and 30 < len(s) < 400:
            candidates.append((score, s))
    if not candidates:
        return 'The exact final order or outcome was not explicitly specified in the text.'
    candidates.sort(key=lambda x: x[0], reverse=True)
    return ' '.join(s for _, s in candidates[:2])

_REF_LABELS = {
    'IPC_SECTION':  'Indian Penal Code (IPC)',
    'BNS_SECTION':  'Bharatiya Nyaya Sanhita (BNS)',
    'CRPC_SECTION': 'Code of Criminal Procedure (CrPC)',
    'CPC_SECTION':  'Code of Civil Procedure (CPC)',
    'CONSTITUTION': 'Constitution of India',
    'EVIDENCE_ACT': 'Indian Evidence Act',
    'SCC_CITATION': 'SCC Citations',
    'AIR_CITATION': 'AIR Citations',
    'FIR_NUMBER':   'FIR Records',
    'CASE_NUMBER':  'Case Identification',
}

def _build_readable_summary(sentences, topics, entities, legal_refs, key_terms, outcome) -> str:
    lines = []

    lines.append("### 📌 Executive Summary")
    # Top 3 most coherent TextRank sentences
    exec_paras = [s for _, s, _ in sentences[:3]]
    lines.append("\n\n".join(exec_paras))

    lines.append("\n---\n")
    lines.append("### ⚖️ Final Outcome & Judicial Decision")
    lines.append(f"> {outcome}")

    lines.append("\n---\n")
    lines.append("### 👥 Case Identity & Key Parties (NER)")
    p_info = []
    if entities.get('parties'):
        p_info.append(f"- **Key Parties / Individuals:** {', '.join(entities['parties'])}")
    if entities.get('judges'):
        p_info.append(f"- **Bench / Presiding Judges:** {', '.join(entities['judges'])}")
    if entities.get('courts'):
        p_info.append(f"- **Courts / Authorities:** {', '.join(entities['courts'])}")
    if entities.get('locations'):
        p_info.append(f"- **Jurisdiction:** {', '.join(entities['locations'])}")
    if entities.get('dates'):
        p_info.append(f"- **Important Dates Mentioned:** {', '.join(entities['dates'][:4])}")
    lines.append("\n".join(p_info) if p_info else "No distinct parties could be automatically indexed.")

    if legal_refs:
        lines.append("\n---\n")
        lines.append("### 📜 Statutory Provisions & Legal Citations")
        ref_bullets = []
        for key, vals in legal_refs.items():
            label = _REF_LABELS.get(key, key)
            ref_bullets.append(f"- **{label}:** {', '.join(vals)}")
        lines.append("\n".join(ref_bullets))

    # Core Facts & Arguments from TextRank sentences 4 onwards
    core_facts = [s for _, s, _ in sentences[3:8] if len(s) > 40]
    if core_facts:
        lines.append("\n---\n")
        lines.append("### 🔍 Key Facts & Findings (TextRank)")
        for f in core_facts:
            lines.append(f"- {f}")

    if topics:
        lines.append("\n---\n")
        lines.append("### 💡 Core Legal Concepts Identified (LSA Topics)")
        for i, t in enumerate(topics[:3], 1):
            terms_str = ", ".join(t['terms']).title()
            rep = t['representative']
            if len(rep) > 180:
                rep = rep[:180] + "..."
            lines.append(f"- **Topic {i} ({terms_str}):** {rep}")

    if key_terms:
        lines.append("\n---\n")
        lines.append("### 🏷️ Critical Legal Terms (TF-IDF)")
        terms_badge = " ".join([f"`{term}`" for term in key_terms[:8]])
        lines.append(terms_badge)

    return "\n".join(lines)

def summarize_document(text: str) -> str:
    """
    Generate clean, coherent, highly professional legal summary.
    Powered strictly by TextRank, TF-IDF, LSA, and NER. No LLM.
    """
    cleaned = _clean_text_line(text)
    doc_spacy = nlp(cleaned[:100000])
    
    # Filter high quality legal sentences
    sentences = []
    for s in doc_spacy.sents:
        sent_text = s.text.strip()
        if 40 < len(sent_text) < 450:
            sentences.append(sent_text)

    if not sentences:
        return "Unable to parse clear sentences from this document."

    n_top = max(5, min(10, len(sentences) // 6))
    top_sents = sorted(textrank_sentences(sentences, top_n=n_top), key=lambda x: x[0])

    topics = lsa_topics(sentences[:250], n_topics=3)
    entities = extract_entities(cleaned)
    legal_refs = extract_legal_references(cleaned)
    key_terms = [t for t, _ in get_top_terms(cleaned, 15) if len(t) > 3]
    outcome = extract_outcome(cleaned)

    return _build_readable_summary(top_sents, topics, entities, legal_refs, key_terms, outcome)
