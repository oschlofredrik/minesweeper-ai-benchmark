"""Configuration for reasoning evaluation."""

import os

# Whether to use the LLM-based reasoning judge (requires GPT-4 API calls)
USE_REASONING_JUDGE = os.getenv("USE_REASONING_JUDGE", "false").lower() == "true"

# Model to use for reasoning evaluation
REASONING_JUDGE_MODEL = os.getenv("REASONING_JUDGE_MODEL", "gpt-4o")

# Temperature for reasoning judge (0 = deterministic)
REASONING_JUDGE_TEMPERATURE = float(os.getenv("REASONING_JUDGE_TEMPERATURE", "0.0"))