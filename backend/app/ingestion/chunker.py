"""
Kalag Text Chunking
Intelligent chunking for RAG retrieval
"""

from typing import List, Dict, Any, Optional
import re


class TextChunker:
    """
    Intelligent text chunking for RAG.
    
    Strategies:
    1. Semantic chunking - split on paragraph/section boundaries
    2. Overlap - maintain context between chunks
    3. Size limits - stay within embedding model limits
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Full text to chunk
            metadata: Base metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with content and metadata
        """
        if not text.strip():
            return []
        
        # First try semantic splitting (paragraphs, sections)
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > self.chunk_size:
                # Save current chunk if it meets minimum
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "start_char": current_start,
                        "end_char": current_start + len(current_chunk),
                        "chunk_index": len(chunks),
                        **(metadata or {})
                    })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text + para + "\n\n"
                current_start = current_start + len(current_chunk) - len(overlap_text)
            else:
                current_chunk += para + "\n\n"
        
        # Don't forget the last chunk
        if len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "content": current_chunk.strip(),
                "start_char": current_start,
                "end_char": current_start + len(current_chunk),
                "chunk_index": len(chunks),
                **(metadata or {})
            })
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs on double newlines."""
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        
        # Split on multiple newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from end of chunk."""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to break at sentence boundary
        overlap_region = text[-self.chunk_overlap:]
        sentence_end = overlap_region.find('. ')
        
        if sentence_end != -1:
            return overlap_region[sentence_end + 2:]
        
        # Fall back to word boundary
        word_break = overlap_region.find(' ')
        if word_break != -1:
            return overlap_region[word_break + 1:]
        
        return overlap_region
    
    def chunk_with_pages(
        self,
        pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk text while preserving page number references.
        
        Args:
            pages: List of dicts with 'page_number' and 'text'
            
        Returns:
            Chunks with page_numbers field
        """
        all_chunks = []
        
        for page in pages:
            page_chunks = self.chunk_text(
                page.get("text", ""),
                metadata={"page_number": page["page_number"]}
            )
            all_chunks.extend(page_chunks)
        
        # Re-index chunks
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_index"] = i
        
        return all_chunks


def estimate_token_count(text: str) -> int:
    """
    Rough token count estimation.
    More accurate than character count for LLM context limits.
    """
    # Rough approximation: 1 token ≈ 4 characters for English
    return len(text) // 4
