#!/usr/bin/env python3
"""Test imports to debug the issue."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    
    print("1. Importing logging_config...")
    from src.core.logging_config import get_logger
    print("✅ logging_config imported successfully")
    
    print("\n2. Importing game_registry...")
    from src.games.registry import game_registry, register_builtin_games
    print("✅ game_registry imported successfully")
    
    print("\n3. Importing competition_runner...")
    from src.api.competition_runner import run_competition
    print("✅ competition_runner imported successfully")
    
    print("\n4. Testing competition_runner imports...")
    from src.api.competition_runner import CompetitionRunner
    print("✅ CompetitionRunner class imported successfully")
    
    print("\nAll imports successful!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()