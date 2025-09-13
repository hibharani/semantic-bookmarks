from openai import OpenAI
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models import Bookmark, Embedding
from config import settings

# OpenAI client will be initialized dynamically to ensure fresh API key loading
def get_openai_client():
    """Get OpenAI client with fresh settings"""
    from config import settings
    return OpenAI(api_key=settings.openai_api_key)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self.model = "text-embedding-3-small"
        self.dimension = 1536
        self.chunk_size = 512  # tokens
        self.chunk_overlap = 50  # tokens
    
    async def generate_and_store_embeddings(self, db: Session, bookmark: Bookmark):
        """Generate embeddings for bookmark content and store in database"""
        # Combine title, description, and content for embedding
        text_to_embed = self._prepare_text_for_embedding(bookmark)
        
        if not text_to_embed.strip():
            return
        
        # Split into chunks if text is too long
        chunks = self._chunk_text(text_to_embed)
        
        # Delete existing embeddings for this bookmark
        db.query(Embedding).filter(Embedding.bookmark_id == bookmark.id).delete()
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            try:
                client = get_openai_client()
                response = client.embeddings.create(
                    model=self.model,
                    input=chunk
                )
                
                embedding_vector = response.data[0].embedding
                
                # Store embedding in database
                db_embedding = Embedding(
                    bookmark_id=bookmark.id,
                    content_chunk=chunk,
                    embedding=embedding_vector,
                    chunk_index=i
                )
                
                db.add(db_embedding)
                
            except Exception as e:
                print(f"Error generating embedding for chunk {i}: {e}")
                continue
        
        db.commit()
    
    def _prepare_text_for_embedding(self, bookmark: Bookmark) -> str:
        """Prepare text from bookmark for embedding"""
        parts = []
        
        if bookmark.title:
            parts.append(f"Title: {bookmark.title}")
        
        if bookmark.description:
            parts.append(f"Description: {bookmark.description}")
        
        if bookmark.content:
            # Clean content
            cleaned_content = self._clean_text(bookmark.content)
            parts.append(f"Content: {cleaned_content}")
        
        if bookmark.tags:
            parts.append(f"Tags: {', '.join(bookmark.tags)}")
        
        return '\n'.join(parts)
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
        
        return text.strip()
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding"""
        # Simple word-based chunking (in production, use proper tokenization)
        words = text.split()
        chunks = []
        
        # Approximate tokens as words * 1.3 (rough estimate)
        words_per_chunk = int(self.chunk_size / 1.3)
        overlap_words = int(self.chunk_overlap / 1.3)
        
        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            if chunk_words:  # Only add non-empty chunks
                chunks.append(' '.join(chunk_words))
        
        return chunks if chunks else [text]  # Return original text if chunking fails
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        try:
            client = get_openai_client()
            response = client.embeddings.create(
                model=self.model,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []