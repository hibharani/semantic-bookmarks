#!/bin/bash

# Semantic Bookmarks Setup Script
echo "🔖 Setting up Semantic Bookmarks..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OpenAI API key before starting the services."
fi

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📖 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📝 Next steps:"
    echo "1. Edit .env file and add your OpenAI API key"
    echo "2. Restart services: docker-compose restart"
    echo "3. Create an account at http://localhost:3000/auth/register"
    echo "4. Start bookmarking!"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
fi