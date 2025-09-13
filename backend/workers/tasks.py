import re
import asyncio
from uuid import UUID
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from workers.celery import celery_app
from models import Bookmark, Embedding
from services.extractors import ContentExtractorFactory
from services.embeddings import EmbeddingService
from config import settings

# Create database session for workers
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True)
def process_bookmark_content(self, bookmark_id: str):
    """Extract content from bookmark URL and generate embeddings"""
    db = SessionLocal()
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Starting content extraction'})
        
        # Get bookmark
        bookmark = db.query(Bookmark).filter(Bookmark.id == UUID(bookmark_id)).first()
        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")
        
        # Detect platform and extract content
        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Extracting content'})
        
        extractor_factory = ContentExtractorFactory()
        extractor = extractor_factory.get_extractor(bookmark.url)
        
        extracted_data = extractor.extract(bookmark.url)
        
        # Update bookmark with extracted data
        bookmark.title = extracted_data.get('title') or bookmark.title
        bookmark.description = extracted_data.get('description') or bookmark.description
        bookmark.content = extracted_data.get('content', '')
        bookmark.platform = extracted_data.get('platform')
        bookmark.meta_data = extracted_data.get('meta_data', {})
        
        db.commit()
        
        # Generate and store embeddings
        self.update_state(state='PROGRESS', meta={'current': 70, 'total': 100, 'status': 'Generating embeddings'})
        
        embedding_service = EmbeddingService()
        # Run async function in sync context
        asyncio.run(embedding_service.generate_and_store_embeddings(db, bookmark))
        
        self.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'Completed'})
        
        return {
            'bookmark_id': bookmark_id,
            'status': 'completed',
            'title': bookmark.title,
            'platform': bookmark.platform
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
    finally:
        db.close()


@celery_app.task
def generate_embeddings(bookmark_id: str):
    """Generate embeddings for bookmark content"""
    db = SessionLocal()
    try:
        bookmark = db.query(Bookmark).filter(Bookmark.id == UUID(bookmark_id)).first()
        if not bookmark:
            raise ValueError(f"Bookmark {bookmark_id} not found")
        
        embedding_service = EmbeddingService()
        # Run async function in sync context
        asyncio.run(embedding_service.generate_and_store_embeddings(db, bookmark))
        
        return {'bookmark_id': bookmark_id, 'status': 'completed'}
        
    except Exception as e:
        raise
    finally:
        db.close()