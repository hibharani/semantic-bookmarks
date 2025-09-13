from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models import User, Bookmark
from schemas import BookmarkCreate, BookmarkUpdate, Bookmark as BookmarkSchema
from auth import get_current_user
from workers.tasks import process_bookmark_content

router = APIRouter()


@router.post("/", response_model=BookmarkSchema)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bookmark"""
    # Create bookmark in database
    db_bookmark = Bookmark(
        user_id=current_user.id,
        url=bookmark_data.url,
        title=bookmark_data.title,
        description=bookmark_data.description,
        tags=bookmark_data.tags,
        is_public=bookmark_data.is_public
    )
    
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    
    # Queue content extraction and processing using Celery
    process_bookmark_content.delay(str(db_bookmark.id))
    
    return db_bookmark


@router.get("/", response_model=List[BookmarkSchema])
async def get_bookmarks(
    skip: int = 0,
    limit: int = 20,
    platform: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's bookmarks"""
    query = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)
    
    if platform:
        query = query.filter(Bookmark.platform == platform)
    
    bookmarks = query.offset(skip).limit(limit).all()
    return bookmarks


@router.get("/{bookmark_id}", response_model=BookmarkSchema)
async def get_bookmark(
    bookmark_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bookmark"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    return bookmark


@router.put("/{bookmark_id}", response_model=BookmarkSchema)
async def update_bookmark(
    bookmark_id: UUID,
    bookmark_data: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a bookmark"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    # Update fields
    update_data = bookmark_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bookmark, field, value)
    
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bookmark"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == current_user.id
    ).first()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark deleted successfully"}