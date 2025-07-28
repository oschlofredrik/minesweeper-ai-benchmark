#!/bin/bash
# Setup script for Minesweeper AI Benchmark

echo "Setting up Minesweeper AI Benchmark..."

# Create necessary directories
mkdir -p data/tasks/interactive
mkdir -p data/tasks/static
mkdir -p data/results
mkdir -p data/cache

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please add your API keys"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate initial tasks
echo "Generating initial benchmark tasks..."
python -m src.cli.main generate-tasks --num-tasks 30

echo "Setup complete! You can now run:"
echo "  python -m src.cli.main evaluate --model gpt-4 --num-games 5"