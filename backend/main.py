from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base
from routers import auth, bookmarks, search, diagnostics
from config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Semantic Bookmarks API",
    description="Smart bookmarking tool with semantic search",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://frontend-nu-sable-67.vercel.app",
        "https://frontend-2vbuc4zk1-hibharanis-projects.vercel.app",
        "https://frontend-nr8et587u-hibharanis-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])


@app.get("/")
async def root():
    return {"message": "Semantic Bookmarks API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}