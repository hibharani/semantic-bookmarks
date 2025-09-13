from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pgvector.sqlalchemy import Vector
import asyncio

from models import Bookmark, Embedding, SearchLog, User
from schemas import SearchResult, Bookmark as BookmarkSchema
from services.embeddings import EmbeddingService


class SearchService:
    """Service for semantic and keyword search"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def search(
        self,
        query: str,
        user_id: UUID,
        limit: int = 20,
        platform: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> SearchResult:
        """Perform hybrid search (semantic + keyword)"""
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_query_embedding(query)
        
        # Build base query
        base_conditions = [
            "b.user_id = %(user_id)s"
        ]
        params = {"user_id": str(user_id), "query": query, "limit": limit}
        
        # Add filters
        if platform:
            base_conditions.append("b.platform = %(platform)s")
            params["platform"] = platform
        
        if tags:
            base_conditions.append("b.tags && %(tags)s")
            params["tags"] = tags
        
        if date_from:
            base_conditions.append("b.created_at >= %(date_from)s")
            params["date_from"] = date_from
        
        if date_to:
            base_conditions.append("b.created_at <= %(date_to)s")
            params["date_to"] = date_to
        
        base_where = " AND ".join(base_conditions)
        
        # Hybrid search query
        if query_embedding:
            search_sql = """
            WITH semantic_search AS (
                SELECT 
                    b.id,
                    b.user_id,
                    b.url,
                    b.title,
                    b.description,
                    b.content,
                    b.platform,
                    b.metadata as meta_data,
                    b.tags,
                    b.is_public,
                    b.created_at,
                    b.updated_at,
                    MIN(e.embedding <=> %(query_embedding)s::vector) as semantic_distance,
                    0.0 as keyword_score
                FROM bookmarks b
                JOIN embeddings e ON b.id = e.bookmark_id
                WHERE {base_where}
                GROUP BY b.id, b.user_id, b.url, b.title, b.description, b.content, 
                         b.platform, b.metadata as meta_data, b.tags, b.is_public, b.created_at, b.updated_at
                ORDER BY semantic_distance
                LIMIT %(limit)s
            ),
            keyword_search AS (
                SELECT 
                    b.id,
                    b.user_id,
                    b.url,
                    b.title,
                    b.description,
                    b.content,
                    b.platform,
                    b.metadata as meta_data,
                    b.tags,
                    b.is_public,
                    b.created_at,
                    b.updated_at,
                    1.0 as semantic_distance,
                    ts_rank(
                        to_tsvector('english', 
                            COALESCE(b.title, '') || ' ' || 
                            COALESCE(b.description, '') || ' ' || 
                            COALESCE(b.content, '')
                        ),
                        plainto_tsquery('english', %(query)s)
                    ) as keyword_score
                FROM bookmarks b
                WHERE {base_where}
                AND to_tsvector('english', 
                    COALESCE(b.title, '') || ' ' || 
                    COALESCE(b.description, '') || ' ' || 
                    COALESCE(b.content, '')
                ) @@ plainto_tsquery('english', %(query)s)
                ORDER BY keyword_score DESC
                LIMIT %(limit)s
            ),
            combined_results AS (
                SELECT *, 
                       CASE 
                           WHEN semantic_distance < 0.5 THEN semantic_distance * 0.7 + keyword_score * 0.3
                           ELSE semantic_distance * 0.3 + keyword_score * 0.7
                       END as combined_score
                FROM (
                    SELECT * FROM semantic_search
                    UNION ALL
                    SELECT * FROM keyword_search
                ) all_results
            )
            SELECT DISTINCT ON (id) *
            FROM combined_results
            ORDER BY id, combined_score
            LIMIT %(limit)s
            """.format(base_where=base_where)
            
            params["query_embedding"] = query_embedding
        else:
            # Fallback to keyword-only search if embedding fails
            search_sql = """
            SELECT 
                b.id,
                b.user_id,
                b.url,
                b.title,
                b.description,
                b.content,
                b.platform,
                b.metadata as meta_data,
                b.tags,
                b.is_public,
                b.created_at,
                b.updated_at,
                ts_rank(
                    to_tsvector('english', 
                        COALESCE(b.title, '') || ' ' || 
                        COALESCE(b.description, '') || ' ' || 
                        COALESCE(b.content, '')
                    ),
                    plainto_tsquery('english', %(query)s)
                ) as keyword_score
            FROM bookmarks b
            WHERE {base_where}
            AND to_tsvector('english', 
                COALESCE(b.title, '') || ' ' || 
                COALESCE(b.description, '') || ' ' || 
                COALESCE(b.content, '')
            ) @@ plainto_tsquery('english', %(query)s)
            ORDER BY keyword_score DESC
            LIMIT %(limit)s
            """.format(base_where=base_where)
        
        # Execute search
        result = self.db.execute(text(search_sql), params)
        bookmarks_data = result.fetchall()
        
        # Convert to Pydantic models
        bookmarks = []
        for row in bookmarks_data:
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
                'updated_at': row.updated_at
            }
            bookmarks.append(BookmarkSchema(**bookmark_dict))
        
        # Log search
        search_log = SearchLog(
            user_id=user_id,
            query=query,
            results_count=len(bookmarks)
        )
        self.db.add(search_log)
        self.db.commit()
        
        return SearchResult(
            bookmarks=bookmarks,
            total=len(bookmarks),
            query=query
        )
    
    async def get_suggestions(self, query: str, user_id: UUID, limit: int = 5) -> List[str]:
        """Get search query suggestions based on user's bookmarks"""
        # Simple implementation - get common words from titles and tags
        sql = """
        WITH words AS (
            SELECT unnest(string_to_array(lower(title), ' ')) as word
            FROM bookmarks 
            WHERE user_id = %(user_id)s 
            AND title IS NOT NULL
            AND lower(title) LIKE %(query_pattern)s
        )
        SELECT 
            word,
            COUNT(*) as frequency
        FROM words
        WHERE LENGTH(word) > 2
        GROUP BY word
        ORDER BY frequency DESC, word
        LIMIT %(limit)s
        """
        
        params = {
            "user_id": str(user_id),
            "query_pattern": f"%{query.lower()}%",
            "limit": limit
        }
        
        result = self.db.execute(text(sql), params)
        suggestions = [row.word for row in result.fetchall()]
        
        return suggestions
    
    async def find_similar_bookmarks(self, bookmark_id: UUID, limit: int = 5) -> List[BookmarkSchema]:
        """Find bookmarks similar to the given bookmark"""
        # Get embeddings for the given bookmark
        bookmark = self.db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
        if not bookmark:
            return []
        
        sql = """
        WITH bookmark_embeddings AS (
            SELECT embedding
            FROM embeddings 
            WHERE bookmark_id = %(bookmark_id)s
            LIMIT 1
        )
        SELECT 
            b.id,
            b.user_id,
            b.url,
            b.title,
            b.description,
            b.content,
            b.platform,
            b.metadata as meta_data,
            b.tags,
            b.is_public,
            b.created_at,
            b.updated_at,
            AVG(e.embedding <=> be.embedding) as similarity
        FROM bookmarks b
        JOIN embeddings e ON b.id = e.bookmark_id
        CROSS JOIN bookmark_embeddings be
        WHERE b.user_id = %(user_id)s 
        AND b.id != %(bookmark_id)s
        GROUP BY b.id, b.user_id, b.url, b.title, b.description, b.content, 
                 b.platform, b.metadata as meta_data, b.tags, b.is_public, b.created_at, b.updated_at
        ORDER BY similarity
        LIMIT %(limit)s
        """
        
        params = {
            "bookmark_id": str(bookmark_id),
            "user_id": str(bookmark.user_id),
            "limit": limit
        }
        
        result = self.db.execute(text(sql), params)
        bookmarks_data = result.fetchall()
        
        bookmarks = []
        for row in bookmarks_data:
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
                'updated_at': row.updated_at
            }
            bookmarks.append(BookmarkSchema(**bookmark_dict))
        
        return bookmarks