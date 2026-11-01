# utils/nlp_analyzer.py

import spacy
import re
import sys
import subprocess
from typing import Dict, List

INDIAN_LEGAL_PATTERNS = {
    'IPC_SECTION': r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?IPC',
    'CRPC_SECTION': r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?Cr?PC',
    'CONSTITUTION': r'Article\s+\d+\s+of\s+the\s+Constitution|Art\.?\s+\d+',
    'EVIDENCE_ACT_SECTION': r'(?:Section|Sec\.?|S\.?)\s*(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+)?Evidence Act',
    'EXHIBIT_REF': r'Exhibit\s+([A-Z0-9\-]+)',
    'FIR_NUMBER': r'FIR\s+No\.?\s*([A-Z0-9/\-]+)'
}

def load_legal_model():
    try:
        nlp = spacy.load("en_core_web_md")
    except OSError:
        print("Downloading en_core_web_md model...")
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_md"], check=True)
            nlp = spacy.load("en_core_web_md")
        except Exception as e:
            print(f"Model download failed: {e}, using small model")
            nlp = spacy.load("en_core_web_sm")
    return nlp

nlp = load_legal_model()

def summarize_document(text: str) -> str:
    clean_text = _preprocess_text(text)
    return _format_summary(
        overview=_generate_overview_summary(clean_text),
        references=_extract_legal_references(clean_text),
        entities=_extract_entities(clean_text),
        outcome=_extract_final_outcome(clean_text),
        evidence=_analyze_evidence(clean_text)
    )

def _preprocess_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:150000]

def _extract_entities(text: str) -> Dict:
    doc = nlp(text)
    return {
        'parties': list(set([ent.text for ent in doc.ents if ent.label_ in ('PERSON', 'ORG')]))[:5],
        'courts': list(set([ent.text for ent in doc.ents if 'court' in ent.text.lower()]))[:3],
        'locations': list(set([ent.text for ent in doc.ents if ent.label_ == 'GPE']))[:3],
        'dates': list(set([ent.text for ent in doc.ents if ent.label_ == 'DATE']))[:3]
    }

def _extract_legal_references(text: str) -> Dict:
    return {
        k: list(set(re.findall(v, text, re.IGNORECASE)))[:5]
        for k, v in INDIAN_LEGAL_PATTERNS.items()
        if k in ['IPC_SECTION', 'CRPC_SECTION', 'CONSTITUTION']
    }

def _analyze_evidence(text: str) -> Dict:
    return {
        'exhibits': list(set(re.findall(INDIAN_LEGAL_PATTERNS['EXHIBIT_REF'], text, re.IGNORECASE)))[:5],
        'fir_numbers': list(set(re.findall(INDIAN_LEGAL_PATTERNS['FIR_NUMBER'], text, re.IGNORECASE)))[:3],
        'evidence_sections': list(set(re.findall(
            INDIAN_LEGAL_PATTERNS['EVIDENCE_ACT_SECTION'], text, re.IGNORECASE
        )))[:3]
    }

def _extract_final_outcome(text: str) -> str:
    doc = nlp(text)
    outcomes = [
        sent.text.strip() for sent in doc.sents
        if any(keyword in sent.text.lower() 
               for keyword in {'allowed', 'dismissed', 'convicted', 'acquitted', 'granted', 'rejected'})
    ]
    return ". ".join(outcomes[-2:]) if outcomes else "Case outcome not explicitly stated"

def _generate_overview_summary(text: str) -> str:
    doc = nlp(text)
    parties = list(set([ent.text for ent in doc.ents if ent.label_ in ('PERSON', 'ORG')]))[:5]
    issues = []
    events = []

    for sent in doc.sents:
        s = sent.text.strip()
        if any(w in s.lower() for w in ['petition', 'filed', 'appeal', 'challenged', 'dispute', 'alleged', 'accused']):
            issues.append(s)
        elif any(w in s.lower() for w in ['incident', 'occurred', 'arrested', 'investigation', 'facts']):
            events.append(s)
        if len(issues) >= 2 and len(events) >= 2:
            break

    summary_parts = []

    if parties:
        summary_parts.append(f"The case involves the following parties: {', '.join(parties)}.")

    if issues:
        summary_parts.append("The case was filed in relation to the following issues: " + " ".join(issues[:2]))

    if events:
        summary_parts.append("The key facts and events in the case include: " + " ".join(events[:2]))

    if not (parties or issues or events):
        # fallback
        summary_parts.append("This case concerns a legal dispute. Detailed context could not be extracted.")

    return " ".join(summary_parts)

def _format_summary(overview: str, references: Dict, 
                   entities: Dict, outcome: str, evidence: Dict) -> str:
    sections = []
    
    # Case Overview
    sections.append(f"## Case Overview\n{overview}")
    
    # Final Outcome
    sections.append(f"## Final Outcome\n{outcome}")
    
    # Evidence Analysis
    evidence_lines = []
    if evidence['exhibits']:
        evidence_lines.append(f"- Exhibits: {', '.join(evidence['exhibits'])}")
    if evidence['fir_numbers']:
        evidence_lines.append(f"- FIR Numbers: {', '.join(evidence['fir_numbers'])}")
    if evidence['evidence_sections']:
        evidence_lines.append(f"- Evidence Act Sections: {', '.join(evidence['evidence_sections'])}")
    if evidence_lines:
        sections.append("## Evidence Analysis\n" + "\n".join(evidence_lines))
    
    # Legal References
    ref_lines = []
    for ref_type, values in references.items():
        if values:
            clean_name = ref_type.replace('_', ' ').title()
            ref_lines.append(f"- {clean_name}: {', '.join(values)}")
    if ref_lines:
        sections.append("## Legal References\n" + "\n".join(ref_lines))
    
    # Key Entities
    entity_lines = []
    for entity_type, values in entities.items():
        if values:
            entity_lines.append(f"- {entity_type.title()}: {', '.join(values)}")
    if entity_lines:
        sections.append("## Key Entities\n" + "\n".join(entity_lines))
    
    return "\n\n".join(sections)
