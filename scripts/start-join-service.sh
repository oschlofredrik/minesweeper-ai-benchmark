#!/bin/bash
# Start the Tilts join service on port 8001

echo "Starting Tilts join service on port 8001..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Export environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the join service
python -m uvicorn src.api.join_service:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    --log-level info