#!/usr/bin/env python3
"""Quick health check for the refactored platform."""

import requests
import sys

def check_health():
    """Check if the platform is healthy."""
    base_url = "https://minesweeper-ai-benchmark.onrender.com"
    
    print("🔍 Checking platform health...\n")
    
    checks = [
        ("API Health", f"{base_url}/health"),
        ("Games List", f"{base_url}/api/games"),
        ("Leaderboard", f"{base_url}/api/leaderboard"),
        ("Sessions Debug", f"{base_url}/api/sessions/debug"),
    ]
    
    all_good = True
    
    for name, url in checks:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_good = False
    
    if all_good:
        print("\n✨ All checks passed! Platform is healthy.")
    else:
        print("\n⚠️  Some checks failed. Please investigate.")
        sys.exit(1)

if __name__ == "__main__":
    check_health()