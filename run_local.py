#!/usr/bin/env python3
"""
Local runner that loads environment variables before running CLI commands.
This ensures API keys from .env are available to the application.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Run the CLI with all arguments passed through
if __name__ == "__main__":
    # Import after loading env vars
    from src.cli.main import cli
    cli()