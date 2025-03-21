import spacy
import re
import os
import json
from typing import List, Dict, Any

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not available, download a small one
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load("en_core_web_sm")

# Indian Legal Entity Patterns
indian_legal_patterns = {
    'IPC_SECTION': r'(?:Section|Sec\.|S\.)\s+(\d+(?:\w)?(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?Indian\s+Penal\s+Code',
    'CPC_SECTION': r'(?:Section|Sec\.|S\.)\s+(\d+(?:\w)?(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?Code\s+of\s+Civil\s+Procedure',
    'CRPC_SECTION': r'(?:Section|Sec\.|S\.)\s+(\d+(?:\w)?(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?Code\s+of\s+Criminal\s+Procedure',
    'CONSTITUTION': r'(?:Article|Art\.|A\.)\s+(\d+(?:\w)?(?:\(\d+\))?)\s+(?:of\s+)?(?:the\s+)?Constitution\s+of\s+India',
    'HIGH_COURT': r'((?:Bombay|Delhi|Calcutta|Madras|Allahabad|Karnataka|Gujarat|Patna|Punjab|Haryana|Rajasthan|Kerala|Orissa|Jharkhand|Chhattisgarh|Uttarakhand|Himachal Pradesh|Jammu|Kashmir|Sikkim|Manipur|Meghalaya|Tripura)\s+High\s+Court)',
    'SUPREME_COURT': r'Supreme\s+Court\s+of\s+India'
}

# Indian legal terms and explanations
indian_legal_terms = {
    'writ petition': 'A court petition for extraordinary review, seeking justice when fundamental rights are violated',
    'suo motu': 'Action taken by a court on its own initiative without any party requesting it',
    'cognizance': 'Formal recognition by a court that it has the power to deal with a particular case or matter',
    'vakalatnama': 'Document by which a litigant authorizes an advocate to represent them in court',
    'lok adalat': 'People\'s court where disputes are settled through compromise and conciliation',
    'habeas corpus': 'Legal remedy ensuring a person under arrest is brought before a court',
    'caveat': 'A notice given by someone that they have an interest in the matter and should be informed before action is taken',
    'anticipatory bail': 'Bail granted to a person who anticipates arrest for a non-bailable offense',
    'FIR': 'First Information Report, the document prepared by police when they receive information about a cognizable offense'
}

def summarize_document(text: str) -> str:
    """
    Generate a plain-language summary of a legal document with focus on Indian law.
    
    Args:
        text (str): The text of the legal document
    
    Returns:
        str: A simplified summary of the document
    """
    # Extract key sentences as baseline summary approach
    summary = extract_key_sentences(text)
    
    # Enhanced Indian legal entity extraction
    indian_legal_entities = extract_indian_legal_entities(text)
    
    # Extract standard named entities
    entities = extract_named_entities(text)
    
    # Add Indian legal entities to the standard entities
    for entity_type, entity_list in indian_legal_entities.items():
        if entity_list:
            if "LAW" not in entities:
                entities["LAW"] = []
            entities["LAW"].extend(entity_list)
    
    # Format the final summary with Indian law context
    formatted_summary = format_summary_indian_law(summary, entities, indian_legal_entities)
    
    return formatted_summary

def extract_indian_legal_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract Indian legal entities using regex patterns.
    
    Args:
        text (str): Text to extract entities from
    
    Returns:
        Dict[str, List[str]]: Dictionary of Indian legal entity types to lists of entities
    """
    entities = {
        "IPC_SECTION": [],
        "CPC_SECTION": [],
        "CRPC_SECTION": [],
        "CONSTITUTION": [],
        "HIGH_COURT": [],
        "SUPREME_COURT": []
    }
    
    # Extract entities using patterns
    for entity_type, pattern in indian_legal_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            entities[entity_type] = list(set(matches))  # Remove duplicates
    
    return entities

def format_summary_indian_law(summary: str, entities: Dict[str, List[str]], 
                             indian_entities: Dict[str, List[str]]) -> str:
    """
    Format the summary with Indian law-specific entity information.
    
    Args:
        summary (str): The base summary text
        entities (Dict[str, List[str]]): Dictionary of extracted entities
        indian_entities (Dict[str, List[str]]): Dictionary of Indian legal entities
        
    Returns:
        str: Formatted summary with entity information tailored for Indian law
    """
    formatted_text = "## Summary\n\n" + summary + "\n\n"
    
    # Add Indian legal references section
    has_indian_refs = any(indian_entities.values())
    if has_indian_refs:
        formatted_text += "## Indian Legal References\n\n"
        
        if indian_entities.get("IPC_SECTION"):
            formatted_text += "**Indian Penal Code**: " + ", ".join(indian_entities["IPC_SECTION"][:5]) + "\n\n"
            
        if indian_entities.get("CPC_SECTION"):
            formatted_text += "**Civil Procedure Code**: " + ", ".join(indian_entities["CPC_SECTION"][:5]) + "\n\n"
            
        if indian_entities.get("CRPC_SECTION"):
            formatted_text += "**Criminal Procedure Code**: " + ", ".join(indian_entities["CRPC_SECTION"][:5]) + "\n\n"
            
        if indian_entities.get("CONSTITUTION"):
            formatted_text += "**Constitutional Articles**: " + ", ".join(indian_entities["CONSTITUTION"][:5]) + "\n\n"
            
        if indian_entities.get("HIGH_COURT") or indian_entities.get("SUPREME_COURT"):
            courts = indian_entities.get("HIGH_COURT", []) + indian_entities.get("SUPREME_COURT", [])
            formatted_text += "**Courts Referenced**: " + ", ".join(courts[:5]) + "\n\n"
    
    # Add key entities section if entities exist
    has_entities = any(entities.values())
    if has_entities:
        formatted_text += "## Key Entities\n\n"
        
        if entities.get("PERSON"):
            formatted_text += "**People**: " + ", ".join(entities["PERSON"][:5]) + "\n\n"
            
        if entities.get("ORG"):
            formatted_text += "**Organizations**: " + ", ".join(entities["ORG"][:5]) + "\n\n"
            
        if entities.get("GPE"):
            formatted_text += "**Locations**: " + ", ".join(entities["GPE"][:5]) + "\n\n"
            
        if entities.get("LAW"):
            formatted_text += "**Legal References**: " + ", ".join(entities["LAW"][:5]) + "\n\n"
            
        if entities.get("DATE"):
            formatted_text += "**Dates**: " + ", ".join(entities["DATE"][:5]) + "\n\n"
    
    # Add disclaimer
    formatted_text += "---\n\n*Note: This summary is generated automatically and may not capture all nuances of the legal document. Always refer to the original document for critical decisions.*"
    
    return formatted_text

def split_text_into_chunks(text: str, chunk_size: int = 500) -> List[str]:
    """
    Split text into manageable chunks for processing.
    
    Args:
        text (str): The text to split
        chunk_size (int): Maximum size of each chunk
    
    Returns:
        List[str]: List of text chunks
    """
    # Split by paragraphs first
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If adding this paragraph exceeds chunk size, save current chunk and start new one
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n" + para
            else:
                current_chunk = para
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def extract_key_sentences(text: str) -> str:
    """
    Extract key sentences from text as a basic summarization method.
    
    Args:
        text (str): Text to extract key sentences from
    
    Returns:
        str: Extracted key sentences joined as a summary
    """
    doc = nlp(text)
    
    # Get sentences
    sentences = [sent.text.strip() for sent in doc.sents]
    
    # Basic heuristic: take first 2 sentences and then every 5th sentence
    key_sentences = sentences[:2]
    if len(sentences) > 5:
        key_sentences.extend([sentences[i] for i in range(4, len(sentences), 5) if i < len(sentences)])
    
    return " ".join(key_sentences)

def extract_named_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text.
    
    Args:
        text (str): Text to extract named entities from
    
    Returns:
        Dict[str, List[str]]: Dictionary of entity types to lists of entities
    """
    doc = nlp(text[:5000])  # Limit text size for processing
    
    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],  # Geopolitical entities
        "LAW": [],
        "DATE": []
    }
    
    # Extract standard spaCy entities
    for ent in doc.ents:
        if ent.label_ in entities:
            # Avoid duplicates
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
    
    # Extract potential legal references
    legal_references = extract_legal_references(text)
    if legal_references:
        entities["LAW"] = list(set(entities.get("LAW", []) + legal_references))
    
    return entities

def extract_legal_references(text: str) -> List[str]:
    """
    Extract potential legal references using regex patterns.
    
    Args:
        text (str): Text to extract references from
    
    Returns:
        List[str]: List of extracted legal references
    """
    # Patterns for common legal references
    patterns = [
        r'\b\d+\s+U\.S\.C\.\s+§\s*\d+\b',  # US Code
        r'\b\d+\s+CFR\s+§*\s*\d+\b',       # Code of Federal Regulations
        r'\b\d+\s+Fed\.\s*Reg\.\s*\d+\b',  # Federal Register
        r'\bPublic\s+Law\s+\d+-\d+\b',      # Public Law
        r'\b\w+\s+v\.\s+\w+\b'             # Case names
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        references.extend(matches)
    
    return list(set(references))  # Remove duplicates

def format_summary(summary: str, entities: Dict[str, List[str]]) -> str:
    """
    Format the summary with additional entity information.
    
    Args:
        summary (str): The base summary text
        entities (Dict[str, List[str]]): Dictionary of extracted entities
    
    Returns:
        str: Formatted summary with entity information
    """
    formatted_text = "## Summary\n\n" + summary + "\n\n"
    
    # Add key entities section if entities exist
    has_entities = any(entities.values())
    if has_entities:
        formatted_text += "## Key Entities\n\n"
        
        if entities.get("PERSON"):
            formatted_text += "**People**: " + ", ".join(entities["PERSON"][:5]) + "\n\n"
            
        if entities.get("ORG"):
            formatted_text += "**Organizations**: " + ", ".join(entities["ORG"][:5]) + "\n\n"
            
        if entities.get("GPE"):
            formatted_text += "**Locations**: " + ", ".join(entities["GPE"][:5]) + "\n\n"
            
        if entities.get("LAW"):
            formatted_text += "**Legal References**: " + ", ".join(entities["LAW"][:5]) + "\n\n"
            
        if entities.get("DATE"):
            formatted_text += "**Dates**: " + ", ".join(entities["DATE"][:5]) + "\n\n"
    
    # Add disclaimer
    formatted_text += "---\n\n*Note: This summary is generated automatically and may not capture all nuances of the legal document. Always refer to the original document for critical decisions.*"
    
    return formatted_text
