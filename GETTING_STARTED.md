# Getting Started with Semantic Bookmarks

A smart bookmarking tool that uses semantic search to help you find saved content even with different keywords.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd semantic-bookmarks
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

3. **Configure environment:**
   - Edit `.env` file and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Restart services:**
   ```bash
   docker-compose restart
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8080
   - API Documentation: http://localhost:8080/docs

## 📖 How to Use

### 1. Create an Account
- Go to http://localhost:3000/auth/register
- Sign up with your email and password
- You'll be automatically logged in

### 2. Add Your First Bookmark
- Click the "Add Bookmark" button
- Paste any URL (YouTube, Twitter, websites, PDFs, etc.)
- Optionally add title, description, and tags
- Click "Add Bookmark"

The system will automatically:
- Extract content from the URL
- Generate embeddings for semantic search
- Index the content for future search

### 3. Search Your Bookmarks
- Use the search bar with natural language
- Examples:
  - "JavaScript tutorial videos"
  - "Machine learning papers from 2023"
  - "Recipes with chicken"
  - "Frontend development tips"

The search combines:
- **Semantic similarity**: Finds content with similar meaning
- **Keyword matching**: Traditional text search
- **Hybrid ranking**: Best of both approaches

### 4. Supported Platforms

- **YouTube**: Extracts titles, descriptions, transcripts
- **Twitter/X**: Gets tweet content and metadata
- **PDFs**: Extracts full text content
- **General Websites**: Article content using readability
- **GitHub**: Repository information
- **Reddit**: Post and comment content

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Database Management
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d semantic_bookmarks

# View logs
docker-compose logs backend
docker-compose logs worker
```

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `JWT_SECRET`: Secret for JWT tokens
- `YOUTUBE_API_KEY`: YouTube API key (optional)
- `TWITTER_BEARER_TOKEN`: Twitter API bearer token (optional)

### Adding New Content Extractors

1. Create a new extractor class in `backend/services/extractors.py`
2. Extend the `ContentExtractor` base class
3. Add platform detection in `ContentExtractorFactory`
4. Test with your target URLs

## 📊 Features

### Semantic Search
- Uses OpenAI embeddings (text-embedding-3-small)
- Chunks large content for better search
- Combines semantic and keyword search
- Personalized ranking based on user's content

### Content Processing
- Automatic content extraction
- Background processing with Celery
- Platform-specific optimizations
- Metadata preservation

### User Experience
- Fast, responsive React frontend
- Real-time search suggestions
- Bookmark organization with tags
- Mobile-friendly design

## 🔍 Search Tips

1. **Natural Language**: Use full sentences
   - "Show me videos about React hooks"
   - "Find articles about database optimization"

2. **Concepts**: Search by concepts, not just keywords
   - "Authentication patterns" instead of just "auth"
   - "Performance optimization" instead of just "speed"

3. **Combine Filters**: Use platform and tag filters
   - Search "machine learning" + filter by "youtube"
   - Search "recipes" + filter by tag "vegetarian"

## 🚨 Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   docker-compose down
   docker-compose up --build
   ```

2. **Database connection errors**
   - Check if PostgreSQL container is running
   - Verify DATABASE_URL in .env

3. **Content extraction failing**
   - Check worker logs: `docker-compose logs worker`
   - Verify OpenAI API key is correct

4. **Search not working**
   - Ensure embeddings are generated (check worker logs)
   - Verify OpenAI API key and quota

### Getting Help

1. Check logs: `docker-compose logs [service-name]`
2. Inspect containers: `docker-compose ps`
3. Reset database: `docker-compose down -v && docker-compose up`

## 🎯 Next Steps

- Set up monitoring and logging
- Add more content extractors
- Implement bookmark sharing
- Add browser extension
- Set up automated backups