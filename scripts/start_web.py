#!/usr/bin/env python3
"""Start the web server for Render deployment."""

import os
import sys
import uvicorn

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    # Configure uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        # Disable reload in production
        reload=False,
    )