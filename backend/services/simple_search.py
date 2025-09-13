from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from models import Bookmark
from schemas import SearchResult, Bookmark as BookmarkSchema


class SimpleSearchService:
    """Simple working search service to test functionality"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(self, query: str, user_id: UUID, limit: int = 20) -> SearchResult:
        """Simple keyword search using ORM"""
        
        # Use ORM query and extract key terms for better matching
        query_terms = query.lower().split()
        key_terms = []
        
        # Extract meaningful terms from natural language queries
        for term in query_terms:
            if len(term) > 2 and term not in ['the', 'and', 'for', 'to', 'of', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must']:
                key_terms.append(term)
        
        # If no key terms, use the original query
        if not key_terms:
            key_terms = [query.lower()]
        
        # Build query to match any of the key terms
        conditions = []
        for term in key_terms:
            conditions.append(
                Bookmark.title.ilike(f'%{term}%') | 
                Bookmark.description.ilike(f'%{term}%') |
                Bookmark.content.ilike(f'%{term}%')
            )
        
        # Combine conditions with OR
        final_condition = conditions[0]
        for condition in conditions[1:]:
            final_condition = final_condition | condition
        
        bookmarks_query = self.db.query(Bookmark).filter(
            Bookmark.user_id == user_id
        ).filter(final_condition).limit(limit)
        
        bookmarks_data = bookmarks_query.all()
        
        # Convert to Pydantic models
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
            }
            bookmarks.append(BookmarkSchema(**bookmark_dict))
        
        return SearchResult(
            bookmarks=bookmarks,
            total=len(bookmarks),
            query=query
        )