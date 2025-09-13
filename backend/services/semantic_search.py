from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from models import Bookmark
from schemas import SearchResult, Bookmark as BookmarkSchema
from services.embeddings import EmbeddingService


class SemanticSearchService:
    """
    Semantic search service using OpenAI embeddings and PostgreSQL pgvector.
    
    Supports two search modes:
    - Smart: Adaptive threshold based on best match quality
    - Precise: Fixed threshold for high-relevance results only (60%+)
    
    Uses cosine distance for vector similarity and converts to 0-100 relevance scores.
    """
    
    # Search mode thresholds (lower distance = higher relevance)
    PRECISE_THRESHOLD = 0.4  # Only show 60%+ relevance (distance < 0.4)
    
    # Smart mode adaptive thresholds
    SMART_EXCELLENT_BOUNDARY = 0.3  # If best match < 0.3, be very strict
    SMART_GOOD_BOUNDARY = 0.6       # If best match 0.3-0.6, be moderate
    SMART_STRICT_THRESHOLD = 0.5    # Very strict threshold
    SMART_MODERATE_THRESHOLD = 0.7  # Moderate threshold  
    SMART_LENIENT_THRESHOLD = 0.8   # Lenient threshold
    
    def __init__(self, db: Session):
        """Initialize semantic search service with database session."""
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def search(self, query: str, user_id: UUID, limit: int = 20, mode: str = "smart") -> SearchResult:
        """
        Perform semantic search using vector similarity.
        
        Args:
            query: Natural language search query
            user_id: User performing the search  
            limit: Maximum number of results to return
            mode: Search mode ("smart" or "precise")
            
        Returns:
            SearchResult with bookmarks and metadata
        """
        # Step 1: Generate query embedding using OpenAI
        query_embedding = await self.embedding_service.generate_query_embedding(query)
        
        if not query_embedding:
            # Fallback to keyword search if embedding generation fails
            return await self._keyword_fallback(query, user_id, limit)
        
        # Step 2: Determine similarity threshold based on search mode
        threshold = await self._get_search_threshold(mode, query_embedding, user_id)
        
        # Step 3: Execute vector similarity search
        bookmarks_data = await self._execute_vector_search(query_embedding, user_id, threshold, limit)
        
        # Step 4: Convert results to Pydantic models with relevance scores
        bookmarks = self._convert_to_bookmark_schemas(bookmarks_data)
        
        return SearchResult(
            bookmarks=bookmarks,
            total=len(bookmarks),
            query=query
        )
    
    async def _get_search_threshold(self, mode: str, query_embedding: List[float], user_id: UUID) -> float:
        """
        Determine the similarity threshold based on search mode.
        
        Args:
            mode: "precise" or "smart"
            query_embedding: Query vector for smart mode calculation
            user_id: User ID for finding best match
            
        Returns:
            Distance threshold (lower = more strict)
        """
        if mode == "precise":
            return self.PRECISE_THRESHOLD
        else:
            # Smart mode: adapt based on best match quality
            best_distance = await self._get_best_match_distance(query_embedding, user_id)
            return self._calculate_adaptive_threshold(best_distance)
    
    async def _execute_vector_search(self, query_embedding: List[float], user_id: UUID, threshold: float, limit: int) -> List:
        """
        Execute the vector similarity search against PostgreSQL.
        
        Uses direct string interpolation to avoid SQLAlchemy parameter binding issues
        with vector types.
        
        Args:
            query_embedding: OpenAI embedding vector
            user_id: User to search bookmarks for
            threshold: Distance threshold for filtering
            limit: Maximum results
            
        Returns:
            Raw database rows with distance scores
        """
        # Convert embedding to PostgreSQL array format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Vector similarity search using pgvector cosine distance (<=>)
        sql = f"""
        SELECT 
            b.id, b.user_id, b.url, b.title, b.description, b.content, 
            b.platform, b.metadata as meta_data, b.tags, b.is_public, 
            b.created_at, b.updated_at,
            MIN(e.embedding <=> '{embedding_str}'::vector) as distance
        FROM bookmarks b
        JOIN embeddings e ON b.id = e.bookmark_id
        WHERE b.user_id = '{str(user_id)}'
        GROUP BY b.id, b.user_id, b.url, b.title, b.description, b.content, 
                 b.platform, b.metadata, b.tags, b.is_public, b.created_at, b.updated_at
        HAVING MIN(e.embedding <=> '{embedding_str}'::vector) < {threshold}
        ORDER BY distance
        LIMIT {limit}
        """
        
        result = self.db.execute(text(sql))
        return result.fetchall()
    
    def _convert_to_bookmark_schemas(self, bookmarks_data: List) -> List[BookmarkSchema]:
        """
        Convert raw database rows to Pydantic bookmark schemas.
        
        Calculates relevance scores from cosine distances.
        
        Args:
            bookmarks_data: Raw database rows
            
        Returns:
            List of BookmarkSchema objects with relevance scores
        """
        bookmarks = []
        for row in bookmarks_data:
            # Convert cosine distance to relevance score (0-100 scale)
            # Distance 0.0 = 100% relevance, Distance 1.0 = 0% relevance
            relevance_score = max(0, (1 - row.distance) * 100) if hasattr(row, 'distance') else None
            
            bookmark_dict = {
                'id': row.id,
                'user_id': row.user_id,
                'url': row.url,
                'title': row.title,
                'description': row.description,
                'content': row.content,
                'platform': row.platform,
                'meta_data': row.meta_data or {},
                'tags': row.tags or [],
                'is_public': row.is_public,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'relevance_score': relevance_score
            }
            bookmarks.append(BookmarkSchema(**bookmark_dict))
        
        return bookmarks
    
    async def _get_best_match_distance(self, query_embedding: List[float], user_id: UUID) -> float:
        """
        Get the distance of the best matching bookmark for adaptive threshold calculation.
        
        Args:
            query_embedding: Query vector
            user_id: User ID
            
        Returns:
            Minimum distance found, or 1.0 if no bookmarks exist
        """
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        sql = f"""
        SELECT MIN(e.embedding <=> '{embedding_str}'::vector) as min_distance
        FROM bookmarks b
        JOIN embeddings e ON b.id = e.bookmark_id
        WHERE b.user_id = '{str(user_id)}'
        """
        
        result = self.db.execute(text(sql))
        row = result.fetchone()
        return row.min_distance if row and row.min_distance is not None else 1.0
    
    def _calculate_adaptive_threshold(self, best_distance: float) -> float:
        """
        Calculate adaptive threshold for smart mode based on best match quality.
        
        Logic:
        - Excellent match (< 0.3): Be very strict, only show similar quality
        - Good match (0.3-0.6): Be moderate, show good matches  
        - Poor match (> 0.6): Be lenient, help user find something relevant
        
        Args:
            best_distance: Distance of the best matching bookmark
            
        Returns:
            Threshold for filtering results
        """
        if best_distance < self.SMART_EXCELLENT_BOUNDARY:
            return self.SMART_STRICT_THRESHOLD    # Very strict - only show excellent matches
        elif best_distance < self.SMART_GOOD_BOUNDARY:
            return self.SMART_MODERATE_THRESHOLD  # Moderate - show good matches
        else:
            return self.SMART_LENIENT_THRESHOLD   # Lenient - help user find something
    
    async def _keyword_fallback(self, query: str, user_id: UUID, limit: int) -> SearchResult:
        """
        Fallback to keyword search when embedding generation fails.
        
        Uses SQLAlchemy ORM with ILIKE for case-insensitive substring matching
        across title, description, and content fields.
        
        Args:
            query: Search query string
            user_id: User ID
            limit: Maximum results
            
        Returns:
            SearchResult with keyword-matched bookmarks (no relevance scores)
        """
        # Use ORM for simple keyword matching
        bookmarks_query = self.db.query(Bookmark).filter(
            Bookmark.user_id == user_id
        ).filter(
            # Case-insensitive substring search across text fields
            Bookmark.title.ilike(f'%{query}%') | 
            Bookmark.description.ilike(f'%{query}%') |
            Bookmark.content.ilike(f'%{query}%')
        ).limit(limit)
        
        bookmarks_data = bookmarks_query.all()
        
        # Convert to schemas without relevance scores (fallback mode)
        bookmarks = []
        for bookmark in bookmarks_data:
            bookmark_dict = {
                'id': bookmark.id,
                'user_id': bookmark.user_id,
                'url': bookmark.url,
                'title': bookmark.title,
                'description': bookmark.description,
                'content': bookmark.content,
                'platform': bookmark.platform,
                'meta_data': bookmark.meta_data or {},
                'tags': bookmark.tags or [],
                'is_public': bookmark.is_public,
                'created_at': bookmark.created_at,
                'updated_at': bookmark.updated_at
                # Note: No relevance_score for keyword fallback
            }
            bookmarks.append(BookmarkSchema(**bookmark_dict))
        
        return SearchResult(
            bookmarks=bookmarks,
            total=len(bookmarks),
            query=query
        )