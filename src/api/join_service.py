"""Minimal join service for join.tilts.com - Kahoot.it style"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(
    title="Tilts Join",
    description="Simple join service for Tilts competitions",
    version="1.0.0",
)

# Configure CORS to allow main domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tilts.com", 
        "https://www.tilts.com",
        "http://localhost:8000",
        "http://localhost:3000",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static" / "join"
static_dir.mkdir(exist_ok=True, parents=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the minimal join page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Join - Tilts</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f7f7f7;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 48px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        
        .logo {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 48px;
            color: #111;
        }
        
        .subtitle {
            font-size: 18px;
            color: #666;
            margin-bottom: 32px;
            font-weight: 400;
        }
        
        .pin-input {
            width: 100%;
            padding: 24px;
            font-size: 32px;
            text-align: center;
            border: 2px solid #e0e0e0;
            border-radius: 4px;
            margin-bottom: 24px;
            letter-spacing: 8px;
            text-transform: uppercase;
            font-weight: 600;
            transition: border-color 0.2s ease;
        }
        
        .pin-input:focus {
            outline: none;
            border-color: #111;
        }
        
        .pin-input::placeholder {
            letter-spacing: normal;
            font-size: 20px;
            font-weight: 400;
            color: #999;
        }
        
        .join-button {
            width: 100%;
            padding: 20px;
            font-size: 20px;
            font-weight: 600;
            background: #111;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        
        .join-button:hover {
            background: #333;
        }
        
        .join-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .error {
            color: #dc2626;
            font-size: 14px;
            margin-top: 16px;
            display: none;
        }
        
        .footer {
            margin-top: 48px;
            font-size: 14px;
            color: #999;
        }
        
        .footer a {
            color: #666;
            text-decoration: none;
            transition: color 0.2s ease;
        }
        
        .footer a:hover {
            color: #111;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 32px 24px;
            }
            
            .logo {
                font-size: 28px;
                margin-bottom: 32px;
            }
            
            .pin-input {
                font-size: 24px;
                padding: 20px;
                letter-spacing: 4px;
            }
            
            .join-button {
                font-size: 18px;
                padding: 16px;
            }
        }
        
        /* Loading state */
        .loading {
            display: none;
            margin-top: 16px;
            color: #666;
            font-size: 14px;
        }
        
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #333;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="logo">Tilts</h1>
        <p class="subtitle">Enter game PIN</p>
        
        <form id="join-form" onsubmit="handleJoin(event)">
            <input 
                type="text" 
                id="game-pin" 
                class="pin-input" 
                placeholder="Game PIN" 
                maxlength="10" 
                autocomplete="off"
                autocorrect="off"
                autocapitalize="characters"
                inputmode="text"
                pattern="[A-Za-z0-9]*"
                required
            >
            <button type="submit" class="join-button" id="join-btn">
                Join
            </button>
        </form>
        
        <div class="error" id="error-message"></div>
        <div class="loading" id="loading">
            <span class="spinner"></span>
            Joining game...
        </div>
        
        <div class="footer">
            <a href="https://tilts.com">Create your own game at tilts.com</a>
        </div>
    </div>
    
    <script>
        // Auto-uppercase the input
        document.getElementById('game-pin').addEventListener('input', function(e) {
            e.target.value = e.target.value.toUpperCase();
        });
        
        // Focus on load
        window.addEventListener('load', function() {
            document.getElementById('game-pin').focus();
        });
        
        async function handleJoin(event) {
            event.preventDefault();
            
            const pin = document.getElementById('game-pin').value.trim();
            const errorEl = document.getElementById('error-message');
            const loadingEl = document.getElementById('loading');
            const joinBtn = document.getElementById('join-btn');
            
            if (!pin) {
                return;
            }
            
            // Hide error, show loading
            errorEl.style.display = 'none';
            loadingEl.style.display = 'block';
            joinBtn.disabled = true;
            joinBtn.textContent = 'Joining...';
            
            try {
                // Check if session exists
                const response = await fetch('/api/check/' + pin);
                const data = await response.json();
                
                if (response.ok && data.valid) {
                    // Redirect to main platform with join code
                    const mainUrl = window.location.hostname === 'localhost' 
                        ? 'http://localhost:8000' 
                        : 'https://tilts.com';
                    window.location.href = `${mainUrl}/join/${pin}`;
                } else {
                    throw new Error(data.message || 'Invalid game PIN');
                }
            } catch (error) {
                errorEl.textContent = error.message || 'Invalid game PIN. Please try again.';
                errorEl.style.display = 'block';
                loadingEl.style.display = 'none';
                joinBtn.disabled = false;
                joinBtn.textContent = 'Join';
                
                // Select all text for easy retry
                document.getElementById('game-pin').select();
            }
        }
    </script>
</body>
</html>
"""


@app.get("/api/check/{pin}")
async def check_pin(pin: str):
    """Check if a game PIN is valid"""
    import httpx
    import os
    
    pin = pin.upper().strip()
    
    if len(pin) < 4 or len(pin) > 10:
        raise HTTPException(status_code=404, detail="Invalid PIN format")
    
    # Check against main platform API
    main_api_url = os.getenv("MAIN_API_URL", "https://tilts.com")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{main_api_url}/api/sessions/check-join-code/{pin}",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "pin": pin,
                    "session_name": data.get("session_name", "Competition"),
                    "message": "PIN validated"
                }
            else:
                return {
                    "valid": False,
                    "pin": pin,
                    "message": "Invalid game PIN"
                }
                
    except Exception as e:
        # Fallback for development
        if os.getenv("ENV") == "development":
            return {
                "valid": True,
                "pin": pin,
                "message": "PIN validated (dev mode)"
            }
        else:
            raise HTTPException(status_code=503, detail="Unable to validate PIN")


@app.get("/api/join/{pin}")
async def join_redirect(pin: str):
    """Redirect to main platform with PIN"""
    return RedirectResponse(url=f"https://tilts.com/join/{pin}")


if __name__ == "__main__":
    import uvicorn
    # Run on different port than main app
    uvicorn.run(app, host="0.0.0.0", port=8001)