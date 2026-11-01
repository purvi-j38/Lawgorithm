"""
Legal Timeline Extractor
Regex + spaCy NER — Indian date formats first, dynamic context extraction.
Strictly no LLM. No hardcoded names or case descriptions.
"""

import re
import sys
import subprocess
import spacy
from datetime import datetime
from typing import List, Dict, Any, Optional

def _load_nlp():
    for model in ('en_core_web_md', 'en_core_web_sm'):
        try:
            return spacy.load(model)
        except OSError:
            continue
    subprocess.run([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
    return spacy.load('en_core_web_sm')

nlp = _load_nlp()

DATE_FORMATS = [
    '%d.%m.%Y',    # 06.11.2009
    '%d/%m/%Y',    # 06/11/2009
    '%d-%m-%Y',    # 06-11-2009
    '%d %B %Y',    # 06 November 2009
    '%d %b %Y',    # 06 Nov 2009
    '%d-%b-%Y',    # 06-Nov-2009
    '%B %d, %Y',   # November 06, 2009
    '%b %d, %Y',   # Nov 06, 2009
    '%Y-%m-%d',    # ISO
    '%m/%d/%Y',    # US
]

DATE_PATTERNS = [
    r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b',
    r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
    r'\b(\d{1,2}-\d{1,2}-\d{4})\b',
    r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August'
     r'|September|October|November|December)\s+\d{4})\b',
    r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\b',
    r'\b((?:January|February|March|April|May|June|July|August'
     r'|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
    r'\b(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*-\d{4})\b',
    r'\b(\d{4}-\d{2}-\d{2})\b',
]

EVENT_PATTERNS = [
    (r'\b(?:killed?|murdered?|deceased|death|fatal|homicide|shooting|stabbing|attack(?:ed)?)\b',
     'Incident / Offence', '#DC2626'),
    (r'\bF\.?I\.?R\.?\s+(?:No\.?|registered|filed|lodged|reported)\b',
     'FIR / Police Report', '#EA580C'),
    (r'\b(?:charge[\s-]?sheet|chargesheet|challan)\s+(?:filed|submitted|presented)\b',
     'Charge Sheet Filed', '#D97706'),
    (r'\b(?:arrested?|custody|detained?|remand(?:ed)?)\b',
     'Arrest / Detention', '#CA8A04'),
    (r'\b(?:bail|anticipatory bail)\s+(?:granted|allowed|rejected|denied|refused)\b',
     'Bail Proceedings', '#16A34A'),
    (r'\b(?:Sessions\s+(?:Trial|Case|Court)|trial\s+(?:began|commenced|started))\b',
     'Trial Commencement', '#0891B2'),
    (r'\b(?:convicted|conviction|sentenced|sentence\s+of)\b',
     'Conviction / Sentencing', '#7C3AED'),
    (r'\b(?:acquitted?|acquittal|not\s+guilty|discharged)\b',
     'Acquittal / Discharge', '#059669'),
    (r'\b(?:High\s+Court|HC)\s+(?:allowed|dismissed|reversed|upheld|affirmed)\b',
     'High Court Ruling', '#2563EB'),
    (r'\b(?:Supreme\s+Court|SC)\s+(?:allowed|dismissed|upheld|affirmed|reversed)\b',
     'Supreme Court Ruling', '#1D4ED8'),
    (r'\b(?:judgment|judgement|order|decree)\s+(?:dated|passed|pronounced|delivered)\b',
     'Judgment / Order', '#6D28D9'),
    (r'\b(?:post[\s-]?mortem|autopsy|medical\s+(?:report|examination|evidence))\b',
     'Medical / Forensic Report', '#BE185D'),
    (r'\b(?:witness(?:es)?\s+(?:examined|deposed|testified|recorded)|deposition)\b',
     'Witness Examination', '#0D9488'),
    (r'\b(?:evidence\s+(?:produced|exhibited|marked)|exhibit\s+[A-Z])\b',
     'Evidence Produced', '#0369A1'),
    (r'\b(?:complaint|petition|application|writ)\s+(?:filed|lodged|preferred|presented)\b',
     'Filing / Petition', '#9333EA'),
    (r'\b(?:hearing|arguments|submissions)\s+(?:held|heard|recorded|concluded)\b',
     'Court Hearing', '#0E7490'),
    (r'\bnotice\s+(?:issued|served|sent|returnable)\b',
     'Notice Issued', '#4B5563'),
    (r'\bremand(?:ed)?\s+(?:back|for|to)\b',
     'Remand / Retrial Order', '#B45309'),
    (r'\b(?:appeal|revision)\s+(?:filed|preferred|admitted)\b',
     'Appeal Filed', '#7C3AED'),
    (r'\b(?:investigation|inquiry)\s+(?:commenced|started|completed)\b',
     'Investigation', '#6B7280'),
]

def parse_date(date_str: str) -> Optional[datetime]:
    s = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def classify_event(context: str):
    for pattern, etype, color in EVENT_PATTERNS:
        if re.search(pattern, context, re.IGNORECASE):
            return etype, color
    return 'Legal Event', '#475569'

def _clean_description(line: str, date_str: str) -> str:
    desc = line.replace(date_str, '').strip()
    desc = re.sub(r'^[,\.\-\:\;\s]+', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    if len(desc) < 10:
        desc = line.strip()
    return (desc[:160] + '…') if len(desc) > 160 else desc

def extract_timeline(text: str) -> List[Dict[str, Any]]:
    """
    Extract, normalize, and classify chronological events from text.
    Uses Regex + spaCy NER with dynamic context extraction.
    No LLM. Zero hardcoded case data.
    """
    events: List[Dict[str, Any]] = []
    seen_dates: set = set()

    for line in text.split('\n'):
        line = line.strip()
        if not line or len(line) < 8:
            continue

        for pattern in DATE_PATTERNS:
            for date_str in re.findall(pattern, line):
                if date_str in seen_dates:
                    continue
                dt = parse_date(date_str)
                if not dt or not (1850 <= dt.year <= 2035):
                    continue

                seen_dates.add(date_str)
                etype, color = classify_event(line)
                events.append({
                    'Date':        date_str,
                    'date_obj':    dt,
                    'Type':        etype,
                    'Description': _clean_description(line, date_str),
                    'Color':       color,
                    'Context':     line[:220],
                })

    try:
        doc = nlp(text[:80000])
        for ent in doc.ents:
            if ent.label_ != 'DATE':
                continue
            date_text = ent.text.strip()
            if date_text in seen_dates:
                continue
            dt = parse_date(date_text)
            if not dt or not (1850 <= dt.year <= 2035):
                continue

            ctx = doc[max(0, ent.start - 15): ent.end + 15].text.strip()
            etype, color = classify_event(ctx)
            seen_dates.add(date_text)
            events.append({
                'Date':        date_text,
                'date_obj':    dt,
                'Type':        etype,
                'Description': _clean_description(ctx, date_text),
                'Color':       color,
                'Context':     ctx[:220],
            })
    except Exception:
        pass

    events.sort(key=lambda x: x['date_obj'])
    deduped: List[Dict[str, Any]] = []
    seen_keys: set = set()
    for evt in events:
        key = evt['date_obj'].strftime('%Y-%m-%d') + evt['Type']
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(evt)

    return deduped
