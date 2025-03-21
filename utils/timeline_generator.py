import re
import spacy
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Load spaCy model for NER
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load("en_core_web_sm")

def extract_timeline(text: str) -> List[Dict[str, Any]]:
    """
    Extract dates, deadlines, and events from a legal document.
    
    Args:
        text (str): Text of the legal document
    
    Returns:
        List[Dict[str, Any]]: List of timeline events with date, description, and source
    """
    # Process the text with spaCy
    doc = nlp(text[:100000])  # Limit text size for processing
    
    # Extract dates using spaCy's named entity recognition
    date_entities = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            # Get the context - words before and after the date
            start_context = max(0, ent.start - 10)
            end_context = min(len(doc), ent.end + 10)
            context = doc[start_context:end_context].text
            
            # Skip dates that are likely not relevant (e.g., historical references)
            if is_historical_reference(context):
                continue
                
            # Try to determine if this is a deadline
            is_deadline = is_deadline_date(context)
            
            # Add to our list
            date_entities.append({
                "date": ent.text,
                "context": context,
                "is_deadline": is_deadline
            })
    
    # Also use regex patterns to catch additional date formats
    regex_dates = extract_dates_with_regex(text)
    for regex_date in regex_dates:
        if not any(date["date"] == regex_date["date"] for date in date_entities):
            date_entities.append(regex_date)
    
    # Process the extracted dates to format and categorize them
    timeline_events = process_dates(date_entities)
    
    # Sort by date
    timeline_events = sort_timeline_events(timeline_events)
    
    return timeline_events

def extract_dates_with_regex(text: str) -> List[Dict[str, Any]]:
    """
    Extract dates using regex patterns to complement spaCy NER.
    
    Args:
        text (str): Text to extract dates from
    
    Returns:
        List[Dict[str, Any]]: List of extracted dates with context
    """
    date_patterns = [
        # MM/DD/YYYY
        r'(\b\d{1,2}/\d{1,2}/\d{2,4}\b)',
        # Month DD, YYYY
        r'(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b)',
        # DD Month YYYY
        r'(\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b)',
        # YYYY-MM-DD
        r'(\b\d{4}-\d{1,2}-\d{1,2}\b)',
        # Within X days/weeks/months
        r'within\s+(\d+)\s+(days?|weeks?|months?)',
        # By date certain
        r'by\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        # No later than
        r'no\s+later\s+than\s+((?:\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}))'
    ]
    
    dates = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            # Get the date text
            date_text = match.group(0)
            
            # Get context around the match
            start_idx = max(0, match.start() - 50)
            end_idx = min(len(text), match.end() + 50)
            context = text[start_idx:end_idx]
            
            # Check if this appears to be a deadline
            is_deadline = is_deadline_date(context)
            
            dates.append({
                "date": date_text,
                "context": context,
                "is_deadline": is_deadline
            })
    
    return dates

def is_deadline_date(context: str) -> bool:
    """
    Determine if a date context suggests it's a deadline.
    
    Args:
        context (str): The text context around a date
    
    Returns:
        bool: True if the date appears to be a deadline
    """
    deadline_keywords = [
        'due', 'deadline', 'by', 'before', 'no later than',
        'must', 'shall', 'required', 'submit', 'file',
        'respond', 'reply', 'within', 'motion'
    ]
    
    # Convert to lowercase for case-insensitive matching
    context_lower = context.lower()
    
    return any(keyword in context_lower for keyword in deadline_keywords)

def is_historical_reference(context: str) -> bool:
    """
    Check if a date mention is likely a historical reference.
    
    Args:
        context (str): The text context around a date
    
    Returns:
        bool: True if the date appears to be a historical reference
    """
    historical_keywords = [
        'historically', 'previously', 'in the past', 'formerly',
        'originally', 'ancient', 'history', 'precedent',
        'landmark', 'traditional', 'convention of'
    ]
    
    # Convert to lowercase for case-insensitive matching
    context_lower = context.lower()
    
    return any(keyword in context_lower for keyword in historical_keywords)

def process_dates(date_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process extracted date entities into structured timeline events.
    
    Args:
        date_entities (List[Dict[str, Any]]): Raw extracted date entities
    
    Returns:
        List[Dict[str, Any]]: Processed timeline events
    """
    timeline_events = []
    
    for date_entity in date_entities:
        date_text = date_entity["date"]
        context = date_entity["context"]
        is_deadline = date_entity["is_deadline"]
        
        # Determine event type
        event_type = "Deadline" if is_deadline else "Date"
        
        # Extract a description from the context
        description = extract_description_from_context(context, date_text)
        
        # Attempt to parse the date for sorting
        parsed_date = None
        try:
            parsed_date = parse_date_string(date_text)
        except:
            # If parsing fails, keep the original text
            pass
        
        timeline_events.append({
            "Date": date_text,
            "Type": event_type,
            "Description": description,
            "Context": context,
            "Parsed_Date": parsed_date
        })
    
    return timeline_events

def extract_description_from_context(context: str, date_text: str) -> str:
    """
    Extract a meaningful description from the context around a date.
    
    Args:
        context (str): Text context around the date
        date_text (str): The date text to exclude from description
    
    Returns:
        str: Extracted description
    """
    # Remove the date from the context
    description = context.replace(date_text, "")
    
    # Split into sentences
    sentences = re.split(r'[.!?]', description)
    
    # Find the sentence most likely to contain the action
    best_sentence = ""
    max_score = -1
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        # Score the sentence based on action words
        action_words = ['file', 'submit', 'respond', 'due', 'deadline', 'hearing', 'trial']
        score = sum(1 for word in action_words if word.lower() in sentence.lower())
        
        if score > max_score:
            max_score = score
            best_sentence = sentence
    
    # If no good sentence found, just clean up the context
    if max_score <= 0:
        # Just take the middle part of the context
        words = description.split()
        if len(words) > 10:
            best_sentence = " ".join(words[len(words)//4:3*len(words)//4])
        else:
            best_sentence = description
    
    # Clean up the description
    best_sentence = re.sub(r'\s+', ' ', best_sentence).strip()
    
    return best_sentence

def parse_date_string(date_string: str) -> datetime:
    """
    Attempt to parse a date string into a datetime object.
    
    Args:
        date_string (str): Date string to parse
    
    Returns:
        datetime: Parsed datetime object
    """
    # List of date formats to try
    date_formats = [
        '%m/%d/%Y',
        '%m/%d/%y',
        '%B %d, %Y',
        '%d %B %Y',
        '%Y-%m-%d',
        '%Y/%m/%d'
    ]
    
    # Handle special case for "within X days/weeks/months"
    within_match = re.match(r'within\s+(\d+)\s+(days?|weeks?|months?)', date_string)
    if within_match:
        # Just return current date as a placeholder - in a real app would calculate future date
        return datetime.now()
    
    # Try each format
    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            continue
    
    # If all formats fail, raise an exception
    raise ValueError(f"Unable to parse date: {date_string}")

def sort_timeline_events(timeline_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort timeline events by date.
    
    Args:
        timeline_events (List[Dict[str, Any]]): List of timeline events
    
    Returns:
        List[Dict[str, Any]]: Sorted timeline events
    """
    # Separate events with parsed dates from those without
    events_with_dates = [event for event in timeline_events if event.get("Parsed_Date")]
    events_without_dates = [event for event in timeline_events if not event.get("Parsed_Date")]
    
    # Sort events with dates
    sorted_events = sorted(events_with_dates, key=lambda x: x["Parsed_Date"])
    
    # Append events without parsed dates at the end
    sorted_events.extend(events_without_dates)
    
    # Remove the parsed_date field from the output
    for event in sorted_events:
        if "Parsed_Date" in event:
            del event["Parsed_Date"]
    
    return sorted_events
