"""Join service endpoint - Kahoot-style PIN entry page"""
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(self.get_join_html().encode())
    
    def get_join_html(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Join - Tilts</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%23111'/%3E%3Ctext x='50' y='50' text-anchor='middle' dy='.35em' fill='white' font-family='system-ui' font-size='40' font-weight='bold'%3ET%3C/text%3E%3C/svg%3E">
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
        
        .pin-input.error {
            border-color: #e53e3e;
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
            transition: all 0.2s ease;
        }
        
        .join-button:hover:not(:disabled) {
            background: #333;
        }
        
        .join-button:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        
        .error-message {
            color: #e53e3e;
            margin-top: 16px;
            font-size: 14px;
            display: none;
        }
        
        .info {
            margin-top: 48px;
            font-size: 14px;
            color: #888;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 32px 24px;
            }
            
            .logo {
                font-size: 28px;
                margin-bottom: 32px;
            }
            
            .subtitle {
                font-size: 16px;
                margin-bottom: 24px;
            }
            
            .pin-input {
                font-size: 24px;
                padding: 20px;
                letter-spacing: 4px;
            }
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
                id="pin-input" 
                class="pin-input" 
                placeholder="ABCD" 
                maxlength="4"
                pattern="[A-Za-z0-9]{4}"
                required
                autocomplete="off"
                autocorrect="off"
                autocapitalize="off"
                spellcheck="false"
            >
            
            <button type="submit" class="join-button" id="join-btn">
                Join
            </button>
            
            <div class="error-message" id="error-msg">
                Invalid PIN. Please try again.
            </div>
        </form>
        
        <p class="info">
            Ask your host for the game PIN
        </p>
    </div>
    
    <script>
        // Auto-uppercase input
        const input = document.getElementById('pin-input');
        const errorMsg = document.getElementById('error-msg');
        const joinBtn = document.getElementById('join-btn');
        
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
            // Clear error state when typing
            input.classList.remove('error');
            errorMsg.style.display = 'none';
            
            // Enable/disable button based on length
            joinBtn.disabled = e.target.value.length !== 4;
        });
        
        // Auto-focus on load
        input.focus();
        
        async function handleJoin(event) {
            event.preventDefault();
            
            const pin = input.value;
            if (pin.length !== 4) return;
            
            joinBtn.disabled = true;
            joinBtn.textContent = 'Joining...';
            
            try {
                // Redirect to main platform with join code
                // Remove the /join from the URL to get the main platform URL
                const currentUrl = new URL(window.location.href);
                currentUrl.pathname = '/';
                currentUrl.search = '?join=' + pin;
                
                window.location.href = currentUrl.toString();
            } catch (error) {
                // Show error
                input.classList.add('error');
                errorMsg.style.display = 'block';
                joinBtn.disabled = false;
                joinBtn.textContent = 'Join';
                input.select();
            }
        }
    </script>
</body>
</html>"""