from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import SearchQuery, SearchResult
from auth import get_current_user
from services.semantic_search import SemanticSearchService

router = APIRouter()


@router.post("/", response_model=SearchResult)
async def search_bookmarks(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search bookmarks using semantic and keyword search"""
    search_service = SemanticSearchService(db)
    results = await search_service.search(
        query=search_query.query,
        user_id=current_user.id,
        limit=search_query.limit,
        mode=search_query.mode
    )
    
    return results


@router.get("/suggestions")
async def get_search_suggestions(
    q: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search query suggestions based on user's bookmarks"""
    search_service = SearchService(db)
    suggestions = await search_service.get_suggestions(q, current_user.id)
    
    return {"suggestions": suggestions}