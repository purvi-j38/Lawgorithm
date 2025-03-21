import re
import spacy
from typing import Dict, List, Optional

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not available, download a small one
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load("en_core_web_sm")

# Dictionary of common legal terms and their plain language explanations
LEGAL_TERMS = {
    "force majeure": "Unforeseeable circumstances that prevent fulfilling a contract",
    "habeas corpus": "A legal action to determine if someone's detention is lawful",
    "res judicata": "A matter that has been adjudicated and cannot be pursued further",
    "prima facie": "Based on first impression or accepted as correct until proven otherwise",
    "voir dire": "Preliminary examination of a witness or juror",
    "stare decisis": "Legal principle of determining points based on precedent",
    "mens rea": "The intention or knowledge of wrongdoing",
    "actus reus": "The action or conduct that is a constituent element of a crime",
    "pro se": "Representing oneself in court without an attorney",
    "de novo": "Starting anew, as if previous proceedings did not occur",
    "pro bono": "Legal work done for free or for the public good",
    "ex parte": "A legal proceeding brought by one person without the other party knowing",
    "amicus curiae": "Friend of the court; someone who offers information or insight to the court",
    "in camera": "In private, in a judge's chambers",
    "inter alia": "Among other things",
    "nunc pro tunc": "Now for then; retroactive legal change",
    "per curiam": "By the court as a whole rather than by a specific judge",
    "corpus delicti": "The facts that show a crime has been committed",
    "sua sponte": "Something done by a court's own initiative, without prompting",
    "res ipsa loquitur": "The thing speaks for itself; doctrine where negligence can be inferred",
    "subpoena duces tecum": "Order to produce documents or other evidence",
    "tort": "A wrongful act leading to civil legal liability",
    "writ of mandamus": "Court order to a government official to properly fulfill duties",
    "affidavit": "A written statement confirmed by oath for use as evidence",
    "estoppel": "Principle that prevents someone from arguing something contrary to a previous claim",
    "hearsay": "Evidence based on what someone has told the witness, not what they personally know",
    "jurisdiction": "Authority of a court to make legal decisions and judgments",
    "precedent": "A previous case that establishes a legal principle for similar future cases",
    "plaintiff": "Person who initiates a lawsuit",
    "defendant": "Person against whom legal action is brought",
    "appellant": "Person who appeals a lower court's decision",
    "respondent": "Person against whom an appeal is filed",
    "adjudicate": "To make an official decision or judgment about a legal matter",
    "injunction": "Court order requiring someone to do or stop doing something",
    "lien": "Legal right to keep possession of property until a debt is paid",
    "deposition": "Out-of-court testimony by a witness",
    "interrogatory": "Written questions sent to the opposing party in a lawsuit",
    "motion": "Formal request asking a judge to make a decision on a specific issue",
    "statute of limitations": "Time limit for filing a lawsuit",
    "burden of proof": "Obligation to prove one's case",
    "class action": "Lawsuit filed by a group of people with similar claims",
    "discovery": "Process where parties exchange information before trial",
    "bail": "Money paid for release from jail pending trial",
    "indictment": "Formal accusation that someone has committed a crime",
    "acquittal": "Judgment that a person is not guilty of a charge",
    "preponderance of evidence": "Standard of proof requiring that a claim is more likely true than not",
    "beyond reasonable doubt": "Standard of proof requiring that there is no reasonable doubt of guilt"
}

def translate_legal_jargon(text: str) -> str:
    """
    Translate legal jargon in text to plain language.
    
    Args:
        text (str): Legal text to translate
    
    Returns:
        str: Text with legal terms translated
    """
    # Process with spaCy for sentence segmentation
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    # Process each sentence
    translated_sentences = []
    for sentence in sentences:
        translated_sentence = translate_sentence(sentence)
        translated_sentences.append(translated_sentence)
    
    # Join and format the translated text
    translated_text = "\n\n".join(translated_sentences)
    
    # Add explanations of terms at the end
    term_explanations = get_term_explanations(text)
    if term_explanations:
        translated_text += "\n\n## Legal Terms Explained\n\n"
        for term, explanation in term_explanations.items():
            translated_text += f"- **{term}**: {explanation}\n"
    
    return translated_text

def translate_sentence(sentence: str) -> str:
    """
    Translate legal terms in a single sentence.
    
    Args:
        sentence (str): Sentence to translate
    
    Returns:
        str: Translated sentence
    """
    # Lowercase for case-insensitive matching
    sentence_lower = sentence.lower()
    
    # Find legal terms in the sentence
    terms_found = []
    for term in LEGAL_TERMS:
        # Look for exact matches of multi-word terms
        if term in sentence_lower:
            terms_found.append(term)
        # For single word terms, check word boundaries
        elif len(term.split()) == 1:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, sentence_lower):
                terms_found.append(term)
    
    # Translated sentence starts as the original
    translated = sentence
    
    # If terms found, highlight and explain them
    if terms_found:
        for term in sorted(terms_found, key=len, reverse=True):  # Process longest terms first
            # Find the term with proper case in the original sentence
            case_insensitive_pattern = re.compile(re.escape(term), re.IGNORECASE)
            match = case_insensitive_pattern.search(translated)
            if match:
                original_case_term = match.group(0)
                # Replace with highlighted term
                translated = case_insensitive_pattern.sub(f"**{original_case_term}**", translated, 1)
    
    return translated

def get_term_explanations(text: str) -> Dict[str, str]:
    """
    Get explanations for legal terms found in the text.
    
    Args:
        text (str): Text to find terms in
    
    Returns:
        Dict[str, str]: Dictionary of terms and their explanations
    """
    text_lower = text.lower()
    explanations = {}
    
    for term, explanation in LEGAL_TERMS.items():
        # Check for exact multi-word terms
        if term in text_lower:
            explanations[term] = explanation
        # For single word terms, check word boundaries
        elif len(term.split()) == 1:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                explanations[term] = explanation
    
    return explanations

def identify_legal_phrases(text: str) -> List[Dict[str, str]]:
    """
    Identify complex legal phrases in text that might need explanation.
    
    Args:
        text (str): Legal text to analyze
    
    Returns:
        List[Dict[str, str]]: List of legal phrases with context
    """
    # This would use more sophisticated NLP in a real application
    # Here we'll use simple pattern matching
    
    legal_phrases = []
    
    # Look for patterns like "pursuant to Section X" or "in accordance with"
    patterns = [
        r'pursuant to [\w\s\d\.]+',
        r'in accordance with [\w\s\d\.]+',
        r'notwithstanding [\w\s\d\.]+',
        r'hereinafter [\w\s\d\.]+',
        r'aforementioned [\w\s\d\.]+',
        r'subject to the provisions of [\w\s\d\.]+',
        r'without prejudice to [\w\s\d\.]+'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            phrase = match.group(0)
            
            # Get context around the phrase
            start_idx = max(0, match.start() - 50)
            end_idx = min(len(text), match.end() + 50)
            context = text[start_idx:end_idx]
            
            legal_phrases.append({
                "phrase": phrase,
                "context": context
            })
    
    return legal_phrases

def simplify_legal_document(text: str) -> str:
    """
    Simplify an entire legal document by translating jargon and breaking down complex sentences.
    
    Args:
        text (str): Legal document text
    
    Returns:
        str: Simplified document text
    """
    # Process with spaCy
    doc = nlp(text[:100000])  # Limit text size for processing
    
    # Break into paragraphs
    paragraphs = text.split('\n\n')
    simplified_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            simplified_paragraphs.append("")
            continue
            
        # Process the paragraph
        doc = nlp(paragraph)
        
        # Simplify each sentence
        simplified_sentences = []
        for sent in doc.sents:
            # Translate legal terms
            simplified = translate_sentence(sent.text)
            
            # Break down complex sentences (in a real app, would use more sophisticated methods)
            if len(sent) > 30:  # If sentence is long
                simplified = break_down_complex_sentence(simplified)
                
            simplified_sentences.append(simplified)
        
        # Join sentences and add to paragraphs
        simplified_paragraph = " ".join(simplified_sentences)
        simplified_paragraphs.append(simplified_paragraph)
    
    # Join paragraphs
    simplified_text = "\n\n".join(simplified_paragraphs)
    
    # Add glossary at the end
    term_explanations = get_term_explanations(text)
    if term_explanations:
        simplified_text += "\n\n## Legal Terms Glossary\n\n"
        for term, explanation in term_explanations.items():
            simplified_text += f"- **{term}**: {explanation}\n"
    
    return simplified_text

def break_down_complex_sentence(sentence: str) -> str:
    """
    Attempt to break down a complex legal sentence into simpler parts.
    
    Args:
        sentence (str): Complex sentence to simplify
    
    Returns:
        str: Simplified version, possibly broken into multiple sentences
    """
    # In a real app, this would use more sophisticated NLP techniques
    # For this demo, we'll use basic heuristics
    
    # Process with spaCy
    doc = nlp(sentence)
    
    # If sentence is short, just return it
    if len(doc) <= 30:
        return sentence
    
    # Look for common connectors to split on
    connectors = ['; ', ', however, ', ', nevertheless, ', ', moreover, ', ', furthermore, ']
    
    simplified = sentence
    for connector in connectors:
        if connector in simplified:
            parts = simplified.split(connector, 1)
            if len(parts) == 2:
                # Ensure first part ends with period if needed
                if not parts[0].rstrip().endswith('.'):
                    parts[0] = parts[0] + '.'
                # Ensure second part starts with capital letter
                if parts[1] and not parts[1].lstrip()[0].isupper():
                    parts[1] = parts[1][0].upper() + parts[1][1:]
                simplified = parts[0] + ' ' + parts[1]
                break
    
    return simplified
