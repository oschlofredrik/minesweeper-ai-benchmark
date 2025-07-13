#!/bin/bash
# Quick benchmark runner

MODEL=${1:-gpt-4}
GAMES=${2:-10}

echo "Running benchmark for $MODEL with $GAMES games..."

python -m src.cli.main evaluate \
    --model $MODEL \
    --num-games $GAMES \
    --difficulty expert \
    --verbose \
    --output data/results/${MODEL}_$(date +%Y%m%d_%H%M%S).json

echo "Benchmark complete!"