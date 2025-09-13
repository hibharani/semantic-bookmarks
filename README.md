# Semantic Bookmarks

A smart bookmarking tool that uses semantic search to help you find saved content even with different keywords.

## Features

- Support for multiple platforms (YouTube, Twitter/X, Reddit, PDFs, websites)
- Semantic search using OpenAI embeddings
- Content extraction and indexing
- User authentication and management

## Tech Stack

- **Backend**: FastAPI + PostgreSQL + pgvector
- **Frontend**: Next.js + React
- **Search**: OpenAI embeddings + hybrid search
- **Content Extraction**: Playwright, yt-dlp, platform-specific APIs

## Project Structure

```
semantic-bookmarks/
├── backend/           # FastAPI application
├── frontend/          # Next.js application
├── workers/           # Background content extraction
├── database/          # Database migrations and schemas
└── docker-compose.yml # Development environment
```

## Getting Started

1. Clone the repository
2. Set up environment variables
3. Run with Docker: `docker-compose up`
4. Access frontend at `http://localhost:3000`