import spacy
import re
from transformers import pipeline
from typing import List, Dict, Any

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not available, download a small one
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load("en_core_web_sm")

# Initialize summarization pipeline from transformers
try:
    summarizer = pipeline("summarization")
except:
    # If there's an issue, provide an error message function
    def summarizer(text, max_length=130, min_length=30, do_sample=False):
        return [{"summary_text": "Summarization model could not be loaded. Please check your internet connection or install the required models."}]

def summarize_document(text: str) -> str:
    """
    Generate a plain-language summary of a legal document.
    
    Args:
        text (str): The text of the legal document
    
    Returns:
        str: A simplified summary of the document
    """
    # Check if text is too long for transformer model
    if len(text) > 1000:
        # Split text into chunks for processing
        chunks = split_text_into_chunks(text)
        summaries = []
        
        for chunk in chunks:
            if len(chunk) < 100:  # Skip very small chunks
                continue
                
            try:
                # Summarize each chunk
                summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            except Exception as e:
                print(f"Error summarizing chunk: {str(e)}")
                # If summarization fails, use basic extraction
                summaries.append(extract_key_sentences(chunk))
        
        # Combine summaries
        full_summary = " ".join(summaries)
    else:
        try:
            # Summarize short text directly
            summary = summarizer(text, max_length=100, min_length=30, do_sample=False)
            full_summary = summary[0]['summary_text']
        except Exception as e:
            print(f"Error summarizing text: {str(e)}")
            # If summarization fails, use basic extraction
            full_summary = extract_key_sentences(text)
    
    # Enhance summary with named entities
    entities = extract_named_entities(text)
    
    # Format the final summary
    formatted_summary = format_summary(full_summary, entities)
    
    return formatted_summary

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
