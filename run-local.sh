#!/bin/bash

# Local Development Setup Script
echo "🚀 Minesweeper AI Benchmark - Local Development"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! pip show fastapi &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
    echo "Press Enter to continue after adding keys..."
    read
fi

# Create necessary directories
mkdir -p data/tasks data/results data/logs

# Export environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Start the server
echo ""
echo "Starting local server..."
echo "Server will be available at: http://localhost:8000"
echo "API docs available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Run the FastAPI server with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000