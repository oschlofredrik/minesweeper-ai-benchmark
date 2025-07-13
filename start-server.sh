#!/bin/bash

# Activate virtual environment and start server
cd /Users/fredrikevjenekli/minesweeper-benchmark
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

echo "Starting Minesweeper AI Benchmark server..."
echo "Server will be available at: http://localhost:8000"
echo ""

# Run server
exec uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000