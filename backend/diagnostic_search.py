#!/usr/bin/env python3
"""
Search Diagnostic Tool
This script tests each component of the search system separately to identify issues.
"""

import asyncio
import sys
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from datetime import datetime
from uuid import UUID

# Import our modules
from config import settings
from models import Bookmark, Embedding, User
from services.search import SearchService
from services.embeddings import EmbeddingService
from schemas import SearchResult

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.END}")

class SearchDiagnostic:
    def __init__(self):
        # Create database connection
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        self.search_service = SearchService(self.db)
        self.embedding_service = EmbeddingService()

    def test_database_connection(self):
        """Test database connectivity"""
        print_header("1. DATABASE CONNECTION TEST")
        try:
            result = self.db.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                print_success("Database connection successful")
                return True
        except Exception as e:
            print_error(f"Database connection failed: {e}")
            return False

    def test_data_availability(self):
        """Test if we have users, bookmarks, and embeddings"""
        print_header("2. DATA AVAILABILITY TEST")
        
        # Check users
        user_count = self.db.query(User).count()
        print_info(f"Users in database: {user_count}")
        
        if user_count == 0:
            print_error("No users found")
            return None, False
            
        # Get first user
        user = self.db.query(User).first()
        print_success(f"Test user found: {user.email}")
        
        # Check bookmarks
        bookmark_count = self.db.query(Bookmark).filter(Bookmark.user_id == user.id).count()
        print_info(f"Bookmarks for user: {bookmark_count}")
        
        if bookmark_count == 0:
            print_error("No bookmarks found for user")
            return user, False
        
        # Check embeddings
        embedding_count = self.db.query(Embedding).count()
        print_info(f"Total embeddings: {embedding_count}")
        
        # Show sample bookmark data
        bookmark = self.db.query(Bookmark).filter(Bookmark.user_id == user.id).first()
        print_info(f"Sample bookmark: {bookmark.title[:50]}...")
        print_info(f"Content length: {len(bookmark.content or '')} characters")
        
        return user, bookmark_count > 0

    def test_openai_connection(self):
        """Test OpenAI API connectivity"""
        print_header("3. OPENAI API TEST")
        try:
            # Test with a simple query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            embedding = loop.run_until_complete(
                self.embedding_service.generate_query_embedding("test query")
            )
            loop.close()
            
            if embedding and len(embedding) > 0:
                print_success(f"OpenAI API working - embedding dimension: {len(embedding)}")
                return True
            else:
                print_error("OpenAI API returned empty embedding")
                return False
        except Exception as e:
            print_error(f"OpenAI API failed: {e}")
            return False

    def test_postgresql_search(self, user_id, query="jules"):
        """Test PostgreSQL full-text search directly"""
        print_header("4. POSTGRESQL FULL-TEXT SEARCH TEST")
        
        try:
            sql = """
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
            LIMIT 10
            """
            
            result = self.db.execute(text(sql), {
                "query": query,
                "user_id": str(user_id)
            }).fetchall()
            
            if result:
                print_success(f"PostgreSQL search found {len(result)} results for '{query}'")
                for row in result:
                    print_info(f"  - {row.title[:50]}... (rank: {row.rank:.4f})")
                return True
            else:
                print_error(f"PostgreSQL search found no results for '{query}'")
                return False
                
        except Exception as e:
            print_error(f"PostgreSQL search failed: {e}")
            return False

    def test_semantic_search(self, user_id, query="coding assistant"):
        """Test semantic search with embeddings"""
        print_header("5. SEMANTIC SEARCH TEST")
        
        try:
            # First check if we have embeddings
            embedding_count = self.db.execute(text("""
                SELECT COUNT(*) as count
                FROM embeddings e
                JOIN bookmarks b ON e.bookmark_id = b.id
                WHERE b.user_id = :user_id
            """), {"user_id": str(user_id)}).fetchone()
            
            if embedding_count.count == 0:
                print_warning("No embeddings found for user's bookmarks")
                return False
                
            print_info(f"Found {embedding_count.count} embeddings for user's bookmarks")
            
            # Test semantic search
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            query_embedding = loop.run_until_complete(
                self.embedding_service.generate_query_embedding(query)
            )
            loop.close()
            
            if not query_embedding:
                print_error("Failed to generate query embedding")
                return False
                
            # Test semantic similarity search
            sql = """
            SELECT 
                b.title,
                b.id,
                MIN(e.embedding <=> :query_embedding::vector) as distance
            FROM bookmarks b
            JOIN embeddings e ON b.id = e.bookmark_id
            WHERE b.user_id = :user_id
            GROUP BY b.id, b.title
            ORDER BY distance
            LIMIT 5
            """
            
            result = self.db.execute(text(sql), {
                "query_embedding": query_embedding,
                "user_id": str(user_id)
            }).fetchall()
            
            if result:
                print_success(f"Semantic search found {len(result)} results for '{query}'")
                for row in result:
                    print_info(f"  - {row.title[:50]}... (distance: {row.distance:.4f})")
                return True
            else:
                print_error(f"Semantic search found no results for '{query}'")
                return False
                
        except Exception as e:
            print_error(f"Semantic search failed: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def test_hybrid_search_service(self, user_id, query="jules"):
        """Test the actual search service used by the API"""
        print_header("6. HYBRID SEARCH SERVICE TEST")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.search_service.search(
                    query=query,
                    user_id=UUID(str(user_id)),
                    limit=10
                )
            )
            loop.close()
            
            if result and result.bookmarks:
                print_success(f"Hybrid search found {len(result.bookmarks)} results for '{query}'")
                print_info(f"Total results: {result.total}")
                for bookmark in result.bookmarks[:3]:
                    print_info(f"  - {bookmark.title[:50]}...")
                return True
            else:
                print_error(f"Hybrid search found no results for '{query}'")
                return False
                
        except Exception as e:
            print_error(f"Hybrid search service failed: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def test_search_suggestions(self, user_id, query="ju"):
        """Test search suggestions"""
        print_header("7. SEARCH SUGGESTIONS TEST")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            suggestions = loop.run_until_complete(
                self.search_service.get_suggestions(query, UUID(str(user_id)))
            )
            loop.close()
            
            if suggestions:
                print_success(f"Found {len(suggestions)} suggestions for '{query}'")
                for suggestion in suggestions:
                    print_info(f"  - {suggestion}")
                return True
            else:
                print_warning(f"No suggestions found for '{query}'")
                return False
                
        except Exception as e:
            print_error(f"Search suggestions failed: {e}")
            return False

    def run_full_diagnostic(self):
        """Run all diagnostic tests"""
        print(f"{Colors.BOLD}{Colors.WHITE}")
        print("🔍 SEMANTIC BOOKMARKS SEARCH DIAGNOSTIC TOOL")
        print("=" * 60)
        print(f"{Colors.END}")
        
        results = []
        
        # Test 1: Database
        results.append(self.test_database_connection())
        
        # Test 2: Data availability
        user, has_bookmarks = self.test_data_availability()
        results.append(has_bookmarks)
        
        if not user or not has_bookmarks:
            print_error("Cannot continue without user data and bookmarks")
            return
            
        # Test 3: OpenAI
        results.append(self.test_openai_connection())
        
        # Test 4: PostgreSQL search
        results.append(self.test_postgresql_search(user.id))
        
        # Test 5: Semantic search
        results.append(self.test_semantic_search(user.id))
        
        # Test 6: Hybrid search service
        results.append(self.test_hybrid_search_service(user.id))
        
        # Test 7: Search suggestions
        results.append(self.test_search_suggestions(user.id))
        
        # Summary
        print_header("DIAGNOSTIC SUMMARY")
        passed = sum(1 for r in results if r)
        total = len(results)
        
        if passed == total:
            print_success(f"All tests passed ({passed}/{total})")
        else:
            print_error(f"Some tests failed ({passed}/{total})")
            
        test_names = [
            "Database Connection",
            "Data Availability", 
            "OpenAI API",
            "PostgreSQL Search",
            "Semantic Search",
            "Hybrid Search Service",
            "Search Suggestions"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✓" if result else "✗"
            color = Colors.GREEN if result else Colors.RED
            print(f"{color}{status} {name}{Colors.END}")

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

def main():
    diagnostic = SearchDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()