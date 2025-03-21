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
    Extract case citations from text with focus on Indian law cases.
    
    Args:
        text (str): Text to extract citations from
    
    Returns:
        List[Dict[str, Any]]: List of extracted case citations
    """
    # Common case citation patterns - general
    general_citation_patterns = [
        # Pattern for "X v. Y" or "X vs. Y"
        r'\b([A-Z][a-zA-Z\'\s,\.]+)\s+v\.?\s+([A-Z][a-zA-Z\'\s,\.]+)(?:\s+\((\d{4})\))?',
        # Pattern for "X versus Y"
        r'\b([A-Z][a-zA-Z\'\s,\.]+)\s+versus\s+([A-Z][a-zA-Z\'\s,\.]+)(?:\s+\((\d{4})\))?',
    ]
    
    # Indian law specific citation patterns
    indian_citation_patterns = [
        # Supreme Court Reports (SCR)
        r'\b(\d+)\s+SCR\s+(\d+)(?:\s+\((\d{4})\))?',
        # Supreme Court Cases (SCC)
        r'\b(\d+)\s+SCC\s+(\d+)(?:\s+\((\d{4})\))?',
        # All India Reporter (AIR)
        r'\bAIR\s+(\d{4})\s+SC\s+(\d+)',
        r'\bAIR\s+(\d{4})\s+([A-Z][a-z]+)\s+(\d+)',
        # Indian Law Reports (ILR)
        r'\bILR\s+(\d{4})\s+([A-Z][a-z]+)\s+(\d+)',
        # Judgments Today (JT)
        r'\b(\d+)\s+JT\s+\((\d+)\)\s+(\d+)',
        # Scale
        r'\b(\d{4})\s+SCALE\s+(\d+)',
        # Criminal Law Journal (Cri LJ)
        r'\b(\d{4})\s+Cri\s*LJ\s+(\d+)',
        # Weekly Criminal Reports (WCR)
        r'\b(\d{4})\s+WCR\s+(\d+)',
        # Consumer Protection Judgments (CPJ)
        r'\b(\d{4})\s+CPJ\s+(\d+)',
        # Indian statutory citations
        r'\bSection\s+(\d+(?:\w)?)\s+of\s+the\s+([A-Za-z\s]+)',
        r'\bArticle\s+(\d+(?:\w)?)\s+of\s+the\s+Constitution\s+of\s+India'
    ]
    
    all_patterns = general_citation_patterns + indian_citation_patterns
    citations = []
    
    for pattern in all_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            match_text = match.group(0)
            
            # Get context around citation
            start_idx = max(0, match.start() - 100)
            end_idx = min(len(text), match.end() + 100)
            context = text[start_idx:end_idx]
            
            # For v. pattern and general cases, extract parties and year
            if match.lastindex and match.lastindex >= 2:
                # Handle different citation formats
                if "SCR" in match_text or "SCC" in match_text:
                    volume = match.group(1)
                    page = match.group(2)
                    year = match.group(3) if match.lastindex >= 3 and match.group(3) else "Unknown"
                    citation = {
                        "citation": match_text,
                        "reporter": "SCR" if "SCR" in match_text else "SCC",
                        "volume": volume,
                        "page": page,
                        "year": year,
                        "context": context,
                        "court": "Supreme Court of India"
                    }
                elif "AIR" in match_text:
                    year = match.group(1)
                    court = match.group(2) if match.lastindex >= 2 else "SC"
                    page = match.group(3) if match.lastindex >= 3 else match.group(2)
                    citation = {
                        "citation": match_text,
                        "reporter": "AIR",
                        "year": year,
                        "court": "Supreme Court" if court == "SC" else f"{court} High Court",
                        "page": page,
                        "context": context
                    }
                elif "Section" in match_text or "Article" in match_text:
                    section = match.group(1)
                    law_name = match.group(2)
                    citation = {
                        "citation": match_text,
                        "type": "statutory",
                        "section": section,
                        "law": law_name,
                        "context": context
                    }
                elif "v" in match_text or "versus" in match_text:
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
                    # Generic handler for other formats
                    citation = {
                        "citation": match_text,
                        "context": context
                    }
            else:
                citation = {
                    "citation": match_text,
                    "context": context
                }
            
            # Add court type inference for Indian cases
            if "citation" in citation and "court" not in citation:
                if "SC" in citation["citation"]:
                    citation["court"] = "Supreme Court of India"
                elif any(hc in citation["citation"] for hc in ["Bom", "Del", "Cal", "Mad", "All", "Kar", "Guj", "Pat"]):
                    # Extract High Court name
                    hc_match = re.search(r'(Bom|Del|Cal|Mad|All|Kar|Guj|Pat)', citation["citation"])
                    if hc_match:
                        hc_code = hc_match.group(1)
                        hc_map = {
                            "Bom": "Bombay", "Del": "Delhi", "Cal": "Calcutta", "Mad": "Madras",
                            "All": "Allahabad", "Kar": "Karnataka", "Guj": "Gujarat", "Pat": "Patna"
                        }
                        citation["court"] = f"{hc_map.get(hc_code, hc_code)} High Court"
            
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
    Generate an example precedent for demonstration purposes with focus on Indian law cases.
    
    Args:
        arguments (List[Dict[str, Any]]): Available arguments to incorporate
    
    Returns:
        Dict[str, Any]: Generated precedent
    """
    # Landmark Indian law cases
    indian_cases = [
        {"case_name": "Kesavananda Bharati v. State of Kerala", "year": "1973", "court": "Supreme Court of India"},
        {"case_name": "Maneka Gandhi v. Union of India", "year": "1978", "court": "Supreme Court of India"},
        {"case_name": "Vishaka v. State of Rajasthan", "year": "1997", "court": "Supreme Court of India"},
        {"case_name": "Mohd. Ahmed Khan v. Shah Bano Begum", "year": "1985", "court": "Supreme Court of India"},
        {"case_name": "Indra Sawhney v. Union of India", "year": "1992", "court": "Supreme Court of India"},
        {"case_name": "Olga Tellis v. Bombay Municipal Corporation", "year": "1985", "court": "Supreme Court of India"},
        {"case_name": "M.C. Mehta v. Union of India", "year": "1987", "court": "Supreme Court of India"},
        {"case_name": "Justice K.S. Puttaswamy v. Union of India", "year": "2017", "court": "Supreme Court of India"},
        {"case_name": "Navtej Singh Johar v. Union of India", "year": "2018", "court": "Supreme Court of India"},
        {"case_name": "Indian Hotel & Restaurant Association v. State of Maharashtra", "year": "2019", "court": "Supreme Court of India"},
        {"case_name": "Common Cause v. Union of India", "year": "2018", "court": "Supreme Court of India"},
        {"case_name": "Shreya Singhal v. Union of India", "year": "2015", "court": "Supreme Court of India"}
    ]
    
    case = random.choice(indian_cases)
    
    # Try to use real arguments if available
    key_points = []
    if arguments:
        for arg in arguments[:min(3, len(arguments))]:
            key_points.append(arg["argument"])
    
    # Fill in if we don't have enough
    while len(key_points) < 3:
        # Indian law specific example points
        indian_example_points = [
            "The court reaffirmed the basic structure doctrine of the Indian Constitution.",
            "The ruling established that fundamental rights must be interpreted in light of Directive Principles of State Policy.",
            "This case expanded the interpretation of Article 21 to include the right to live with dignity.",
            "The court found that personal laws must conform to constitutional principles.",
            "The decision emphasized the importance of adherence to due process in administrative actions.",
            "This precedent established guidelines for protection of women in the workplace.",
            "The court held that environmental protection is part of the right to life under Article 21.",
            "The judgment recognized the right to privacy as a fundamental right under the Indian Constitution.",
            "The court established the proportionality test for restrictions on fundamental rights.",
            "This ruling decriminalized consensual acts between adults of the same gender.",
            "The decision emphasized the constitutional value of secularism in governance.",
            "The court applied the principle of reasonable classification under Article 14 equality provisions."
        ]
        
        point = random.choice(indian_example_points)
        if point not in key_points:
            key_points.append(point)
    
    return {
        "case_name": case["case_name"],
        "year": case["year"],
        "court": case["court"],
        "relevance": random.choice(["High", "Medium", "Low"]),
        "outcome": generate_example_outcome(),
        "key_points": key_points
    }
