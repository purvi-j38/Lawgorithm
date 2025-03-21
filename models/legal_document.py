from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class LegalDocument:
    """
    Class representing a legal document.
    """
    id: str  # Unique identifier
    filename: str  # Original filename
    content: str  # Full text content
    file_type: str  # MIME type or extension
    file_path: str  # Path to stored file
    
    # Optional fields that may be populated through analysis
    summary: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    precedents: Optional[List[Dict[str, Any]]] = None
    entities: Optional[Dict[str, List[str]]] = None
    upload_date: datetime = None
    
    def __post_init__(self):
        """Initialize any fields that weren't provided."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.upload_date:
            self.upload_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the document to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the document
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "content": self.content[:1000] + "..." if len(self.content) > 1000 else self.content,  # Truncate for storage
            "file_type": self.file_type,
            "file_path": self.file_path,
            "summary": self.summary,
            "timeline": self.timeline,
            "precedents": self.precedents,
            "entities": self.entities,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegalDocument':
        """
        Create a document from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of a document
        
        Returns:
            LegalDocument: New document instance
        """
        # Convert upload_date from string to datetime if present
        if 'upload_date' in data and data['upload_date']:
            data['upload_date'] = datetime.fromisoformat(data['upload_date'])
        
        return cls(**data)
    
    def generate_summary(self, summary_text: str) -> None:
        """
        Set the document summary.
        
        Args:
            summary_text (str): Generated summary text
        """
        self.summary = summary_text
    
    def set_timeline(self, timeline_data: List[Dict[str, Any]]) -> None:
        """
        Set the document timeline.
        
        Args:
            timeline_data (List[Dict[str, Any]]): Timeline data
        """
        self.timeline = timeline_data
    
    def set_precedents(self, precedent_data: List[Dict[str, Any]]) -> None:
        """
        Set the document precedents.
        
        Args:
            precedent_data (List[Dict[str, Any]]): Precedent data
        """
        self.precedents = precedent_data
    
    def set_entities(self, entity_data: Dict[str, List[str]]) -> None:
        """
        Set the document entities.
        
        Args:
            entity_data (Dict[str, List[str]]): Entity data
        """
        self.entities = entity_data
