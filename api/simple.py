import json

def handler(request, response):
    """Vercel Python runtime handler."""
    # Minimal working endpoint
    data = {"status": "ok", "message": "Simple endpoint works", "method": request.method}
    
    response.status_code = 200
    response.headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    return json.dumps(data)