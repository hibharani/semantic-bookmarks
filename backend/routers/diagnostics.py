from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from uuid import UUID

from database import get_db
from models import User, Bookmark, Embedding
from auth import get_current_user
from config import settings

router = APIRouter()


@router.get("/overview")
async def diagnostic_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overview of user's indexed content"""
    
    # Basic counts
    bookmark_count = db.query(Bookmark).filter(Bookmark.user_id == current_user.id).count()
    embedding_count = db.execute(text("""
        SELECT COUNT(e.id) as count
        FROM embeddings e
        JOIN bookmarks b ON e.bookmark_id = b.id
        WHERE b.user_id = :user_id
    """), {"user_id": str(current_user.id)}).scalar()
    
    # Content statistics
    content_stats = db.execute(text("""
        SELECT 
            COUNT(*) as total_bookmarks,
            COUNT(CASE WHEN content IS NOT NULL AND LENGTH(content) > 0 THEN 1 END) as with_content,
            COUNT(CASE WHEN title IS NOT NULL THEN 1 END) as with_title,
            COUNT(CASE WHEN description IS NOT NULL THEN 1 END) as with_description,
            AVG(LENGTH(COALESCE(content, ''))) as avg_content_length,
            MAX(LENGTH(COALESCE(content, ''))) as max_content_length,
            MIN(LENGTH(COALESCE(content, ''))) as min_content_length
        FROM bookmarks 
        WHERE user_id = :user_id
    """), {"user_id": str(current_user.id)}).fetchone()
    
    # Platform breakdown
    platform_stats = db.execute(text("""
        SELECT 
            COALESCE(platform, 'unknown') as platform,
            COUNT(*) as count
        FROM bookmarks 
        WHERE user_id = :user_id
        GROUP BY platform
        ORDER BY count DESC
    """), {"user_id": str(current_user.id)}).fetchall()
    
    # Recent processing activity
    recent_bookmarks = db.execute(text("""
        SELECT 
            b.id,
            b.title,
            b.url,
            b.platform,
            b.created_at,
            COUNT(e.id) as embedding_count,
            LENGTH(COALESCE(b.content, '')) as content_length
        FROM bookmarks b
        LEFT JOIN embeddings e ON b.id = e.bookmark_id
        WHERE b.user_id = :user_id
        GROUP BY b.id, b.title, b.url, b.platform, b.created_at, b.content
        ORDER BY b.created_at DESC
        LIMIT 10
    """), {"user_id": str(current_user.id)}).fetchall()
    
    return {
        "summary": {
            "total_bookmarks": bookmark_count,
            "total_embeddings": embedding_count,
            "embeddings_per_bookmark": round(embedding_count / max(bookmark_count, 1), 2)
        },
        "content_stats": {
            "total_bookmarks": content_stats.total_bookmarks,
            "with_content": content_stats.with_content,
            "with_title": content_stats.with_title,
            "with_description": content_stats.with_description,
            "content_coverage": round((content_stats.with_content / max(content_stats.total_bookmarks, 1)) * 100, 1),
            "avg_content_length": round(content_stats.avg_content_length or 0),
            "max_content_length": content_stats.max_content_length or 0,
            "min_content_length": content_stats.min_content_length or 0
        },
        "platforms": [
            {"platform": row.platform, "count": row.count}
            for row in platform_stats
        ],
        "recent_activity": [
            {
                "id": str(row.id),
                "title": row.title,
                "url": row.url,
                "platform": row.platform,
                "created_at": row.created_at.isoformat(),
                "embedding_count": row.embedding_count,
                "content_length": row.content_length
            }
            for row in recent_bookmarks
        ]
    }


@router.get("/bookmark/{bookmark_id}")
async def diagnostic_bookmark_detail(
    bookmark_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific bookmark's indexing"""
    
    # Get bookmark with embeddings
    bookmark_data = db.execute(text("""
        SELECT 
            b.id,
            b.url,
            b.title,
            b.description,
            b.content,
            b.platform,
            b.metadata,
            b.tags,
            b.created_at,
            b.updated_at
        FROM bookmarks b
        WHERE b.id = :bookmark_id AND b.user_id = :user_id
    """), {
        "bookmark_id": bookmark_id,
        "user_id": str(current_user.id)
    }).fetchone()
    
    if not bookmark_data:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    # Get embeddings for this bookmark
    embeddings_data = db.execute(text("""
        SELECT 
            e.id,
            e.content_chunk,
            e.chunk_index,
            array_length(e.embedding, 1) as embedding_dimension
        FROM embeddings e
        WHERE e.bookmark_id = :bookmark_id
        ORDER BY e.chunk_index
    """), {"bookmark_id": bookmark_id}).fetchall()
    
    # Get processing stats
    processing_stats = {
        "total_chunks": len(embeddings_data),
        "total_characters": len(bookmark_data.content or ""),
        "avg_chunk_size": round(sum(len(e.content_chunk or "") for e in embeddings_data) / max(len(embeddings_data), 1)),
        "embedding_dimension": embeddings_data[0].embedding_dimension if embeddings_data else 0
    }
    
    return {
        "bookmark": {
            "id": str(bookmark_data.id),
            "url": bookmark_data.url,
            "title": bookmark_data.title,
            "description": bookmark_data.description,
            "content": bookmark_data.content,
            "platform": bookmark_data.platform,
            "metadata": bookmark_data.metadata,
            "tags": bookmark_data.tags,
            "created_at": bookmark_data.created_at.isoformat(),
            "updated_at": bookmark_data.updated_at.isoformat()
        },
        "processing": processing_stats,
        "embeddings": [
            {
                "id": str(e.id),
                "chunk_index": e.chunk_index,
                "content_chunk": e.content_chunk,
                "chunk_length": len(e.content_chunk or ""),
                "embedding_dimension": e.embedding_dimension
            }
            for e in embeddings_data
        ]
    }


@router.get("/search-test")
async def diagnostic_search_test(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test search functionality with detailed results"""
    
    from services.search import SearchService
    import asyncio
    
    search_service = SearchService(db)
    
    try:
        # Perform search
        results = await search_service.search(
            query=query,
            user_id=current_user.id,
            limit=10
        )
        
        # Also test individual components
        # Test PostgreSQL full-text search
        pg_results = db.execute(text("""
            SELECT 
                b.id,
                b.title,
                ts_rank(
                    to_tsvector('english', 
                        COALESCE(b.title, '') || ' ' || 
                        COALESCE(b.description, '') || ' ' || 
                        COALESCE(b.content, '')
                    ),
                    plainto_tsquery('english', :query)
                ) as rank
            FROM bookmarks b
            WHERE b.user_id = :user_id
            AND to_tsvector('english', 
                COALESCE(b.title, '') || ' ' || 
                COALESCE(b.description, '') || ' ' || 
                COALESCE(b.content, '')
            ) @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT 5
        """), {
            "query": query,
            "user_id": str(current_user.id)
        }).fetchall()
        
        return {
            "query": query,
            "hybrid_search": {
                "total_results": results.total,
                "results": [
                    {
                        "id": str(b.id),
                        "title": b.title,
                        "url": b.url,
                        "platform": b.platform
                    }
                    for b in results.bookmarks
                ]
            },
            "postgresql_search": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "rank": float(row.rank)
                }
                for row in pg_results
            ]
        }
        
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "hybrid_search": {"error": True},
            "postgresql_search": {"error": True}
        }


@router.get("/system-info")
async def diagnostic_system_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system configuration and status"""
    
    # Check OpenAI API key status
    openai_status = "configured" if settings.openai_api_key and len(settings.openai_api_key) > 20 else "missing"
    
    # Check database extensions
    pg_extensions = db.execute(text("""
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('vector', 'pgvector')
    """)).fetchall()
    
    # Check indexes
    search_indexes = db.execute(text("""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = 'bookmarks'
        AND indexname LIKE '%fts%'
    """)).fetchall()
    
    return {
        "configuration": {
            "openai_api_key": openai_status,
            "database_url": settings.database_url.split("@")[1] if "@" in settings.database_url else "configured",
            "redis_url": settings.redis_url,
            "debug_mode": settings.debug
        },
        "database": {
            "extensions": [
                {"name": ext.extname, "version": ext.extversion}
                for ext in pg_extensions
            ],
            "search_indexes": [
                {"name": idx.indexname, "definition": idx.indexdef[:100] + "..."}
                for idx in search_indexes
            ]
        }
    }