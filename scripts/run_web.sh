#!/bin/bash
# Run the web interface

echo "Starting Minesweeper AI Benchmark Web Interface..."
echo "The interface will be available at http://localhost:8000"
echo ""

# Run with uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000