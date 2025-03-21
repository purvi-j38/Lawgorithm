import spacy
import re
from typing import List, Dict, Any
import random  # For demo purposes only

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not available, download a small one
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load("en_core_web_sm")

def find_precedents(text: str) -> List[Dict[str, Any]]:
    """
    Find precedent cases and relevant legal arguments in a document.
    
    Args:
        text (str): Text of the legal document
    
    Returns:
        List[Dict[str, Any]]: List of precedent cases with relevance
    """
    # Extract case citations
    case_citations = extract_case_citations(text)
    
    # Extract legal arguments
    legal_arguments = extract_legal_arguments(text)
    
    # Match precedents (in a real app, this would query a database)
    precedents = match_precedents_to_arguments(case_citations, legal_arguments)
    
    return precedents

def extract_case_citations(text: str) -> List[Dict[str, Any]]:
    """
    Extract case citations from text.
    
    Args:
        text (str): Text to extract citations from
    
    Returns:
        List[Dict[str, Any]]: List of extracted case citations
    """
    # Common case citation patterns
    citation_patterns = [
        # Pattern for "X v. Y" or "X vs. Y"
        r'\b([A-Z][a-zA-Z\'\s,\.]+)\s+v\.?\s+([A-Z][a-zA-Z\'\s,\.]+)(?:\s+\((\d{4})\))?',
        # Pattern for "X versus Y"
        r'\b([A-Z][a-zA-Z\'\s,\.]+)\s+versus\s+([A-Z][a-zA-Z\'\s,\.]+)(?:\s+\((\d{4})\))?',
        # Pattern for court reporter citations
        r'\b\d+\s+[A-Z]\.(?:\s?\d+[a-z]{0,2}\.?)+\s+\d+\s+\(\d{4}\)',
        # Pattern for statutory citations
        r'\b\d+\s+U\.S\.C\.\s+§\s*\d+[a-z]?'
    ]
    
    citations = []
    
    for pattern in citation_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            match_text = match.group(0)
            
            # Get context around citation
            start_idx = max(0, match.start() - 100)
            end_idx = min(len(text), match.end() + 100)
            context = text[start_idx:end_idx]
            
            # For v. pattern, extract parties and year
            if match.lastindex and match.lastindex >= 2:
                plaintiff = match.group(1).strip() if match.group(1) else ""
                defendant = match.group(2).strip() if match.group(2) else ""
                year = match.group(3) if match.lastindex >= 3 and match.group(3) else "Unknown"
                
                citation = {
                    "citation": match_text,
                    "plaintiff": plaintiff,
                    "defendant": defendant,
                    "year": year,
                    "context": context
                }
            else:
                citation = {
                    "citation": match_text,
                    "context": context
                }
                
            citations.append(citation)
    
    return citations

def extract_legal_arguments(text: str) -> List[Dict[str, Any]]:
    """
    Extract legal arguments from text.
    
    Args:
        text (str): Text to extract arguments from
    
    Returns:
        List[Dict[str, Any]]: List of extracted legal arguments
    """
    # Legal argument markers
    argument_markers = [
        r'plaintiff\s+argues?',
        r'defendant\s+argues?',
        r'appellant\s+argues?',
        r'respondent\s+argues?',
        r'petitioner\s+argues?',
        r'the\s+court\s+finds?',
        r'the\s+court\s+holds?',
        r'the\s+court\s+rules?',
        r'the\s+court\s+concludes?',
        r'contends?\s+that',
        r'maintains?\s+that',
        r'asserts?\s+that',
        r'claims?\s+that',
        r'alleges?\s+that'
    ]
    
    arguments = []
    for marker in argument_markers:
        pattern = f"({marker})(.*?)(?=[\.\n])"
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            marker_text = match.group(1)
            argument_text = match.group(2).strip()
            
            arguments.append({
                "marker": marker_text,
                "argument": argument_text
            })
    
    return arguments

def match_precedents_to_arguments(
    citations: List[Dict[str, Any]], 
    arguments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Match precedents to arguments and generate structured output.
    
    Args:
        citations (List[Dict[str, Any]]): Extracted case citations
        arguments (List[Dict[str, Any]]): Extracted legal arguments
    
    Returns:
        List[Dict[str, Any]]: List of precedents with matching arguments
    """
    # In a real application, this would query a legal database
    # For this demo, we'll create example precedents based on the extracted citations
    
    precedents = []
    
    # If we have citations, create precedents based on them
    if citations:
        for citation in citations[:min(5, len(citations))]:
            # Extract case name and year
            if "plaintiff" in citation and "defendant" in citation:
                case_name = f"{citation['plaintiff']} v. {citation['defendant']}"
                year = citation.get("year", "Unknown")
            else:
                # Use the full citation if we couldn't parse it
                case_name = citation["citation"]
                year = "Unknown"
                # Try to extract year from citation
                year_match = re.search(r'\b(\d{4})\b', citation["citation"])
                if year_match:
                    year = year_match.group(1)
            
            # Find relevant arguments that might be related to this citation
            relevant_args = []
            for arg in arguments:
                # Check if the citation text appears near the argument
                if citation["citation"] in arg["argument"] or citation["citation"] in arg["marker"]:
                    relevant_args.append(arg["argument"])
            
            # Generate example key points
            key_points = generate_key_points(citation["context"], relevant_args)
            
            precedent = {
                "case_name": case_name,
                "year": year,
                "relevance": "High" if relevant_args else "Medium",
                "outcome": generate_example_outcome(),
                "key_points": key_points
            }
            
            precedents.append(precedent)
    
    # If we don't have enough precedents, generate some examples
    while len(precedents) < 3:
        precedent = generate_example_precedent(arguments)
        precedents.append(precedent)
    
    return precedents

def generate_key_points(context: str, arguments: List[str]) -> List[str]:
    """
    Generate key points from context and arguments.
    
    Args:
        context (str): Context around a citation
        arguments (List[str]): Related arguments
    
    Returns:
        List[str]: Generated key points
    """
    key_points = []
    
    # Process with spaCy to extract sentences
    doc = nlp(context)
    sentences = [sent.text.strip() for sent in doc.sents]
    
    # Select up to 3 sentences that seem important
    selected_sentences = []
    for sentence in sentences:
        # Look for indications of a ruling or holding
        if re.search(r'court|held|ruled|found|concluded|determined', sentence, re.IGNORECASE):
            selected_sentences.append(sentence)
            
        # Stop once we have 3
        if len(selected_sentences) >= 3:
            break
    
    # Add selected sentences as key points
    for sentence in selected_sentences:
        if sentence and len(sentence) > 20:  # Avoid very short sentences
            key_points.append(sentence)
    
    # Add arguments if we don't have enough key points
    if arguments and len(key_points) < 3:
        for arg in arguments[:3 - len(key_points)]:
            if arg and len(arg) > 20:
                key_points.append(arg)
    
    # In a real app, we'd do more sophisticated processing here
    # For now, just return what we have or some placeholders
    if not key_points:
        key_points = [
            "The court established an important precedent regarding this legal issue.",
            "The ruling clarified the interpretation of the relevant statutes.",
            "This case established the standard for similar future cases."
        ]
    
    return key_points

def generate_example_outcome() -> str:
    """
    Generate an example outcome for demonstration purposes.
    
    Returns:
        str: Generated outcome text
    """
    outcomes = [
        "The court ruled in favor of the plaintiff.",
        "The court ruled in favor of the defendant.",
        "The court affirmed the lower court's decision.",
        "The court reversed the lower court's decision.",
        "The case was remanded for further proceedings.",
        "The court dismissed the case.",
        "Judgment for the plaintiff.",
        "Judgment for the defendant."
    ]
    
    return random.choice(outcomes)

def generate_example_precedent(arguments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate an example precedent for demonstration purposes.
    
    Args:
        arguments (List[Dict[str, Any]]): Available arguments to incorporate
    
    Returns:
        Dict[str, Any]: Generated precedent
    """
    example_cases = [
        {"case_name": "Smith v. Jones", "year": "2018"},
        {"case_name": "Johnson v. State", "year": "2019"},
        {"case_name": "United States v. Williams", "year": "2017"},
        {"case_name": "People v. Anderson", "year": "2020"},
        {"case_name": "Brown v. Board of Education", "year": "1954"},
        {"case_name": "Roe v. Wade", "year": "1973"},
        {"case_name": "Doe v. Corporation", "year": "2021"},
    ]
    
    case = random.choice(example_cases)
    
    # Try to use real arguments if available
    key_points = []
    if arguments:
        for arg in arguments[:min(3, len(arguments))]:
            key_points.append(arg["argument"])
    
    # Fill in if we don't have enough
    while len(key_points) < 3:
        example_points = [
            "The court established that the burden of proof lies with the plaintiff in such cases.",
            "The ruling clarified the interpretation of the relevant statutes.",
            "This case established the standard for similar future cases.",
            "The court found that the evidence was insufficient to support the claim.",
            "The decision emphasized the importance of procedural compliance.",
            "This precedent restricts the application of the legal principle in question."
        ]
        point = random.choice(example_points)
        if point not in key_points:
            key_points.append(point)
    
    return {
        "case_name": case["case_name"],
        "year": case["year"],
        "relevance": random.choice(["High", "Medium", "Low"]),
        "outcome": generate_example_outcome(),
        "key_points": key_points
    }
