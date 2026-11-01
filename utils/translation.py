"""
Legal Language Simplifier
TF-IDF term ranking + NER + exact legal dictionary matching.
Strictly no LLM — lightning fast and fully local.
"""

import re
import math
import sys
import subprocess
import spacy
from typing import Dict, List, Tuple
from collections import defaultdict

def _load_nlp():
    for model in ('en_core_web_md', 'en_core_web_sm'):
        try:
            return spacy.load(model)
        except OSError:
            continue
    subprocess.run([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
    return spacy.load('en_core_web_sm')

nlp = _load_nlp()

LEGAL_TERMS: Dict[str, Tuple[str, str]] = {
    "force majeure":        ("Force Majeure",        "An unforeseeable event (flood, war, pandemic) that excuses a party from contractual obligations."),
    "habeas corpus":        ("Habeas Corpus",         "A writ requiring that a detained person be brought before a judge to determine if the detention is lawful."),
    "res judicata":         ("Res Judicata",          "Once a court has finally decided a case, the same parties cannot re-litigate the same dispute."),
    "prima facie":          ("Prima Facie",           "On the face of it — evidence sufficient to establish a fact unless rebutted."),
    "voir dire":            ("Voir Dire",             "Preliminary examination of a witness or juror to determine competency or admissibility."),
    "stare decisis":        ("Stare Decisis",         "Courts must follow earlier judicial decisions (precedents) when deciding similar cases."),
    "mens rea":             ("Mens Rea",              "Guilty mind — the criminal intent or knowledge required for most offences."),
    "actus reus":           ("Actus Reus",            "The guilty act — the physical conduct that constitutes the criminal offence."),
    "pro se":               ("Pro Se",                "Representing oneself in court without a lawyer."),
    "de novo":              ("De Novo",               "A fresh hearing as if no prior proceedings occurred; used in appellate review."),
    "pro bono":             ("Pro Bono",              "Legal work performed free of charge, usually in the public interest."),
    "ex parte":             ("Ex Parte",              "A court proceeding or order made without notice to or in the absence of the other party."),
    "amicus curiae":        ("Amicus Curiae",         "Friend of the court — a non-party that submits information to assist the court."),
    "in camera":            ("In Camera",             "Proceedings held in private (judge's chambers), not open to the public."),
    "inter alia":           ("Inter Alia",            "Among other things — indicates the list is not exhaustive."),
    "nunc pro tunc":        ("Nunc Pro Tunc",         "Now for then — a retroactive court order correcting a prior record."),
    "per curiam":           ("Per Curiam",            "A judgment by the court as a whole, not attributed to any single judge."),
    "corpus delicti":       ("Corpus Delicti",        "The body of the crime — the facts that prove a crime has been committed."),
    "sua sponte":           ("Sua Sponte",            "On the court's own initiative, without any party requesting action."),
    "res ipsa loquitur":    ("Res Ipsa Loquitur",     "The thing speaks for itself — negligence may be inferred from the nature of the event."),
    "subpoena duces tecum": ("Subpoena Duces Tecum",  "Court order compelling production of documents or other evidence."),
    "writ of mandamus":     ("Writ of Mandamus",      "Court order requiring a public official or body to perform a statutory duty."),
    "estoppel":             ("Estoppel",              "A party is barred from asserting something contrary to what was previously claimed or agreed upon."),
    "locus standi":         ("Locus Standi",          "The legal right of a person to bring an action before a court."),
    "ratio decidendi":      ("Ratio Decidendi",       "The binding legal reason or principle on which the court's decision is based."),
    "obiter dicta":         ("Obiter Dicta",          "Remarks made by a judge in passing — persuasive but not binding precedent."),
    "sub judice":           ("Sub Judice",            "The matter is currently under judicial consideration and may not be publicly discussed."),
    "ex officio":           ("Ex Officio",            "By virtue of holding a particular office or position."),
    "writ petition":        ("Writ Petition",         "Petition to High Court or Supreme Court for extraordinary relief when fundamental rights are violated."),
    "suo motu":             ("Suo Motu",              "Action taken by a court on its own initiative without a complaint from any party."),
    "cognizance":           ("Cognizance",            "Formal recognition by a court or magistrate of its authority to deal with a matter."),
    "vakalatnama":          ("Vakalatnama",           "Document by which a litigant authorises an advocate to appear on their behalf."),
    "lok adalat":           ("Lok Adalat",            "People's Court under the Legal Services Authorities Act — disputes settled through compromise."),
    "caveat":               ("Caveat",                "A notice ensuring the filer is heard before any court order is passed against them."),
    "anticipatory bail":    ("Anticipatory Bail",     "Bail granted in advance to protect a person from arrest for a non-bailable offence."),
    "fir":                  ("FIR (First Information Report)", "Document prepared by police on receiving information about a cognizable offence; initiates investigation."),
    "panchnama":            ("Panchnama",             "Memorandum of observation prepared in the presence of independent witnesses during a police search or seizure."),
    "crpc":                 ("CrPC",                  "Code of Criminal Procedure — governs the procedural aspects of criminal justice in India."),
    "cpc":                  ("CPC",                   "Code of Civil Procedure — governs procedure for civil litigation in Indian courts."),
    "ipc":                  ("IPC (Indian Penal Code)", "India's main criminal code defining offences and prescribing punishments (applicable pre-July 2024)."),
    "bns":                  ("BNS (Bharatiya Nyaya Sanhita)", "New criminal code that replaced the IPC from 1 July 2024."),
    "pil":                  ("PIL (Public Interest Litigation)", "Litigation filed by any citizen to protect a public interest; relaxed locus standi rules."),
    "adr":                  ("ADR (Alternative Dispute Resolution)", "Resolving disputes outside courts: arbitration, mediation, conciliation, Lok Adalat."),
    "preventive detention": ("Preventive Detention",  "Detention without trial to prevent a person from committing a future harmful act."),
    "fundamental rights":   ("Fundamental Rights",    "Basic constitutional rights guaranteed by Part III of the Constitution to all citizens."),
    "directive principles": ("Directive Principles",  "Non-justiciable guidelines in Part IV of the Constitution directing state governance."),
    "legal aid":            ("Legal Aid",             "Free legal assistance under the Legal Services Authorities Act to eligible persons."),
    "special leave petition": ("SLP (Special Leave Petition)", "Discretionary petition to the Supreme Court under Article 136 to appeal any court's order."),
    "slp":                  ("SLP (Special Leave Petition)", "Discretionary petition to the Supreme Court under Article 136 to appeal any court's order."),
    "review petition":      ("Review Petition",       "Application asking the same court to reconsider its own judgment."),
    "curative petition":    ("Curative Petition",     "Last judicial remedy — lies before the Supreme Court after a review petition is dismissed."),
    "bail":                 ("Bail",                  "Temporary release of an accused from custody on surety or bond, pending trial."),
    "cognizable offence":   ("Cognizable Offence",    "An offence for which police may arrest without a warrant and investigate without a magistrate's order."),
    "non-cognizable offence": ("Non-Cognizable Offence", "An offence requiring a magistrate's authority before police can arrest or investigate."),
    "bailable offence":     ("Bailable Offence",      "An offence where the accused has a right to bail."),
    "non-bailable offence": ("Non-Bailable Offence",  "An offence where bail is at the court's discretion, not a right."),
    "remand":               ("Remand",                "Court order sending the accused back to custody (police or judicial) pending investigation or trial."),
    "acquittal":            ("Acquittal",             "Formal finding that the accused is not guilty; results in release."),
    "conviction":           ("Conviction",            "Formal finding that the accused is guilty of the charge."),
    "injunction":           ("Injunction",            "Court order restraining a party from doing (prohibitory) or compelling them to do (mandatory) a specific act."),
    "affidavit":            ("Affidavit",             "A written statement of facts sworn or affirmed before an authorised officer."),
    "decree":               ("Decree",                "Final expression of a civil court's adjudication of the parties' rights."),
    "interlocutory":        ("Interlocutory Order",   "An order made during proceedings that does not finally dispose of the case."),
    "stay":                 ("Stay Order",            "Order temporarily suspending proceedings or enforcement of a decree, pending appeal."),
    "jurisdiction":         ("Jurisdiction",          "A court's authority to hear and decide a case — limited by territory, subject matter, and pecuniary value."),
    "charge sheet":         ("Charge Sheet",          "Document filed by police in court after investigation, naming the accused and the charges."),
    "contempt of court":    ("Contempt of Court",     "Disobedience or disrespect to a court, or conduct that interferes with the administration of justice."),
    "limitation":           ("Limitation Period",     "Time limit within which a suit or appeal must be filed, prescribed by the Limitation Act, 1963."),
    "cause of action":      ("Cause of Action",       "The set of facts giving a person a legal right to seek judicial redress."),
    "transfer petition":    ("Transfer Petition",     "Petition seeking transfer of a case from one court/state to another."),
}

LEGAL_PHRASES: List[Tuple[str, str]] = [
    (r'pursuant to (?:Section|Article|Order|Rule)[\w\s\.]+',
     '**Pursuant to [provision]** — In accordance with / as required by that provision'),
    (r'notwithstanding (?:anything|the provisions|Section|any)[\w\s\.]+',
     '**Notwithstanding** — Despite / regardless of the stated provision'),
    (r'without prejudice to',
     '**Without Prejudice** — Without affecting any existing legal rights or claims'),
    (r'subject to (?:the provisions|Section)[\w\s\.]+',
     '**Subject to [provision]** — Conditioned upon / limited by that provision'),
    (r'save (?:and except|as (?:otherwise|provided))',
     '**Save and Except** — Except for / other than the stated cases'),
    (r'in so far as',
     '**In So Far As** — To the extent that'),
    (r'hereinafter (?:referred to as|called)',
     '**Hereinafter referred to as** — From this point in the document, will be called'),
    (r'aforementioned|aforesaid',
     '**Aforementioned / Aforesaid** — Previously mentioned / referred to above in this document'),
    (r'without derogating from',
     '**Without Derogating From** — Without diminishing or limiting'),
    (r'mutatis mutandis',
     '**Mutatis Mutandis** — With the necessary changes having been made; with like changes'),
]

def _tfidf_rank(text: str, terms: List[str]) -> List[Tuple[str, float]]:
    text_lower = text.lower()
    total = len(text_lower.split()) or 1
    scored = []
    for term in terms:
        cnt = len(re.findall(r'\b' + re.escape(term) + r'\b', text_lower))
        if cnt == 0:
            continue
        tf = cnt / total
        idf = 1 + math.log(1 / (cnt + 1))
        scored.append((term, tf * idf * cnt))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

def _find_terms(text: str) -> Dict[str, Tuple[str, str]]:
    text_lower = text.lower()
    found = {}
    for key, (display, expl) in LEGAL_TERMS.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, text_lower):
            found[key] = (display, expl)
    return found

def translate_legal_jargon(text: str) -> str:
    """
    Identify and explain legal terms in a passage using exact matching + TF-IDF ranking.
    No LLM.
    """
    if not text.strip():
        return '_No text provided._'

    found = _find_terms(text)
    if not found:
        return text + '\n\n---\n\n_No recognised legal terms found in this passage._'

    ranked = _tfidf_rank(text, list(found.keys()))

    lines = [text, '\n\n---\n\n## 📖 Legal Terms Identified & Explained\n']
    for term_key, _ in ranked[:25]:
        display, expl = found[term_key]
        lines.append(f'**{display}**\n{expl}\n')

    phrase_hits = []
    for phrase_pattern, phrase_expl in LEGAL_PHRASES:
        if re.search(phrase_pattern, text, re.IGNORECASE):
            phrase_hits.append(f'- {phrase_expl}')
    if phrase_hits:
        lines.append('\n## 📌 Structural Legal Phrases Detected\n')
        lines.extend(phrase_hits)

    return '\n'.join(lines)

def simplify_legal_document(text: str) -> str:
    """
    Comprehensive document analysis:
    - NER entity preservation
    - TF-IDF ranked legal terms glossary
    - Legal phrase breakdown
    Strictly no LLM.
    """
    if not text.strip():
        return '_No text provided._'

    doc_spacy = nlp(text[:80000])
    ents: Dict[str, List[str]] = defaultdict(list)
    seen: set = set()
    for ent in doc_spacy.ents:
        if ent.label_ in ('PERSON', 'ORG', 'DATE', 'GPE', 'LAW'):
            k = ent.text.strip().lower()
            if k not in seen and len(k) > 1:
                seen.add(k)
                ents[ent.label_].append(ent.text.strip())

    found = _find_terms(text)
    ranked = _tfidf_rank(text, list(found.keys()))

    sections = []

    glance = []
    if ents.get('ORG'):
        glance.append(f"**Courts / Organizations:** {', '.join(ents['ORG'][:5])}")
    if ents.get('PERSON'):
        glance.append(f"**Persons / Parties:** {', '.join(ents['PERSON'][:6])}")
    if ents.get('DATE'):
        glance.append(f"**Key Dates:** {', '.join(ents['DATE'][:6])}")
    if ents.get('GPE'):
        glance.append(f"**Jurisdictions:** {', '.join(ents['GPE'][:4])}")
    if glance:
        sections.append('## 🔍 Document At a Glance (NER Extraction)\n\n' + '\n\n'.join(glance))

    if ranked:
        term_lines = []
        for term_key, _ in ranked[:30]:
            display, expl = found[term_key]
            term_lines.append(f'**{display}**\n> {expl}')
        sections.append('## 📖 Legal Jargon in Plain Language (TF-IDF Ranked)\n\n' + '\n\n'.join(term_lines))

    phrase_hits = []
    for phrase_pattern, phrase_expl in LEGAL_PHRASES:
        if re.search(phrase_pattern, text, re.IGNORECASE):
            phrase_hits.append(f'- {phrase_expl}')
    if phrase_hits:
        sections.append('## 📌 Structural Legal Phrases Simplified\n\n' + '\n'.join(phrase_hits))

    if not sections:
        sections.append('_No recognised legal terms or patterns found in this document._')

    return '\n\n---\n\n'.join(sections)
