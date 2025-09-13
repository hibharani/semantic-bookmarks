from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# User schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Bookmark schemas
class BookmarkBase(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False


class BookmarkCreate(BookmarkBase):
    pass


class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class Bookmark(BookmarkBase):
    id: UUID
    user_id: UUID
    content: Optional[str] = None
    platform: Optional[str] = None
    meta_data: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    relevance_score: Optional[float] = None  # For search results
    
    class Config:
        from_attributes = True


# Search schemas
class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=20, le=100)
    mode: str = Field(default="smart", pattern="^(precise|smart)$")
    platform: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchResult(BaseModel):
    bookmarks: List[Bookmark]
    total: int
    query: str


# Processing schemas
class ProcessingStatus(BaseModel):
    bookmark_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    message: Optional[str] = None
    progress: Optional[int] = None  # 0-100