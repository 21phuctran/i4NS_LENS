#!/bin/bash

# i4NS LENS Quick Start Script
# This script helps you get started quickly

set -e

echo "========================================"
echo "i4NS LENS - Quick Start"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create data directories
echo "Creating data directories..."
mkdir -p data/doctrines data/mission_logs data/vector_store logs
echo "✅ Data directories created"
echo ""

# Check for doctrine documents
if [ -z "$(ls -A data/doctrines 2>/dev/null)" ]; then
    echo "⚠️  No doctrine documents found in data/doctrines/"
    echo ""
    read -p "Would you like to create a sample doctrine document? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating sample doctrine..."
        # We'll create it via Docker if needed, or user can add manually
        echo "Sample doctrine will be created on first run."
    else
        echo "Please add your doctrine PDFs or text files to data/doctrines/"
        echo "before running the application."
    fi
    echo ""
fi

# Build and start
echo "Building and starting i4NS LENS..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up --build -d

echo ""
echo "========================================"
echo "✅ i4NS LENS is starting!"
echo "========================================"
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check health
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Services are healthy"
    echo ""
    echo "🎉 i4NS LENS is ready!"
    echo ""
    echo "Access the application at:"
    echo "  👉 Frontend: http://localhost:8000"
    echo "  👉 API Docs: http://localhost:8000/docs"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop:"
    echo "  docker-compose down"
else
    echo "⚠️  Services may still be starting..."
    echo "   Check status with: docker-compose logs -f"
    echo ""
    echo "   Access at: http://localhost:8000"
fi

echo ""
echo "For more information, see README.md and SETUP.md"
