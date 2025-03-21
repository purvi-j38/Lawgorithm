import re
import math
from typing import List, Dict, Any, Tuple
import numpy as np

class RAGPipeline:
    """
    A simple RAG (Retrieval Augmented Generation) pipeline for legal documents.
    This is a basic implementation that would typically use embeddings and semantic search.
    """
    
    def __init__(self):
        """Initialize the RAG pipeline."""
        self.documents = []
        self.chunks = []
        self.index = {}  # Term frequency index
        
    def add_document(self, doc_id: str, content: str) -> None:
        """
        Add a document to the RAG pipeline.
        
        Args:
            doc_id (str): Unique identifier for the document
            content (str): Text content of the document
        """
        self.documents.append({"id": doc_id, "content": content})
        
        # Process the document into chunks
        chunks = self._chunk_document(doc_id, content)
        self.chunks.extend(chunks)
        
        # Update the index
        self._update_index(chunks)
    
    def _chunk_document(self, doc_id: str, content: str, chunk_size: int = 200) -> List[Dict[str, Any]]:
        """
        Split a document into smaller chunks for retrieval.
        
        Args:
            doc_id (str): Document identifier
            content (str): Document content
            chunk_size (int): Target size of each chunk in words
            
        Returns:
            List[Dict[str, Any]]: List of document chunks
        """
        # Split content into paragraphs
        paragraphs = [p for p in content.split('\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            # Split paragraph into words
            words = para.split()
            para_size = len(words)
            
            # If paragraph itself is bigger than chunk_size, split it
            if para_size > chunk_size:
                for i in range(0, para_size, chunk_size):
                    sub_para = ' '.join(words[i:i+chunk_size])
                    chunks.append({
                        "doc_id": doc_id,
                        "content": sub_para,
                        "index": len(chunks)
                    })
            # If adding paragraph would exceed chunk_size, create a new chunk
            elif current_size + para_size > chunk_size and current_chunk:
                chunks.append({
                    "doc_id": doc_id,
                    "content": ' '.join(current_chunk),
                    "index": len(chunks)
                })
                current_chunk = [para]
                current_size = para_size
            # Otherwise add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append({
                "doc_id": doc_id,
                "content": ' '.join(current_chunk),
                "index": len(chunks)
            })
        
        return chunks
    
    def _update_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Update the term frequency index with new chunks.
        
        Args:
            chunks (List[Dict[str, Any]]): List of document chunks to index
        """
        for chunk in chunks:
            content = chunk["content"].lower()
            # Tokenize and clean
            words = re.findall(r'\b\w+\b', content)
            
            # Count term frequencies
            term_freq = {}
            for word in words:
                if len(word) > 2:  # Skip very short words
                    term_freq[word] = term_freq.get(word, 0) + 1
            
            # Update global index
            for term, freq in term_freq.items():
                if term not in self.index:
                    self.index[term] = []
                self.index[term].append((chunk["index"], freq))
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query (str): User query
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: List of relevant document chunks
        """
        if not self.chunks:
            return []
            
        # Tokenize and clean query
        query = query.lower()
        query_terms = re.findall(r'\b\w+\b', query)
        query_terms = [term for term in query_terms if len(term) > 2]
        
        if not query_terms:
            return []
        
        # Compute TF-IDF scores for each chunk
        chunk_scores = {}
        
        for term in query_terms:
            if term in self.index:
                idf = math.log(len(self.chunks) / (1 + len(self.index[term])))
                for chunk_idx, term_freq in self.index[term]:
                    if chunk_idx not in chunk_scores:
                        chunk_scores[chunk_idx] = 0
                    # TF-IDF score
                    chunk_scores[chunk_idx] += term_freq * idf
        
        # Sort chunks by score
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top-k chunks
        results = []
        for chunk_idx, score in sorted_chunks[:top_k]:
            chunk = self.chunks[chunk_idx]
            results.append({
                "doc_id": chunk["doc_id"],
                "content": chunk["content"],
                "score": score
            })
        
        return results
    
    def generate_response(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the query and retrieved chunks.
        
        Args:
            query (str): User query
            retrieved_chunks (List[Dict[str, Any]]): Retrieved document chunks
            
        Returns:
            str: Generated response
        """
        if not retrieved_chunks:
            return "I couldn't find any relevant information in the document. Could you please rephrase your question?"
        
        # Extract content from chunks
        context = "\n".join([chunk["content"] for chunk in retrieved_chunks])
        
        # Simple rule-based response generation
        response = "Based on the document, "
        
        # Check query type
        if "what" in query.lower() or "define" in query.lower() or "explain" in query.lower():
            # Extract a relevant sentence from context
            sentences = context.split('.')
            for sentence in sentences:
                cleaned_sentence = sentence.strip().lower()
                if any(term in cleaned_sentence for term in query.lower().split()):
                    return f"Based on the document, {sentence.strip()}."
                    
        elif "when" in query.lower() or "date" in query.lower() or "time" in query.lower():
            # Look for dates in the context
            date_pattern = r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b'
            dates = re.findall(date_pattern, context, re.IGNORECASE)
            if dates:
                return f"Based on the document, relevant dates include: {', '.join(dates)}."
                
        elif "where" in query.lower() or "location" in query.lower() or "place" in query.lower():
            # A simple approach - in practice would use named entity recognition
            places = ['court', 'tribunal', 'office', 'delhi', 'mumbai', 'kolkata', 'chennai', 'bangalore']
            for place in places:
                if place in context.lower():
                    return f"Based on the document, it appears to involve {place}."
        
        # Default to returning the most relevant chunk
        return f"Based on the document: {retrieved_chunks[0]['content']}"
    
    def query(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a query through the RAG pipeline.
        
        Args:
            query (str): User query
            
        Returns:
            Tuple[str, List[Dict[str, Any]]]: Generated response and retrieved chunks
        """
        # Retrieve relevant chunks
        retrieved_chunks = self.retrieve(query)
        
        # Generate response
        response = self.generate_response(query, retrieved_chunks)
        
        return response, retrieved_chunks

# Initialize a global RAG pipeline
rag_pipeline = RAGPipeline()