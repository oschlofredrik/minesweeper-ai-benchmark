"""Simple test endpoint to debug issues."""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Test basic response
            response = {
                "status": "ok",
                "message": "Test endpoint working"
            }
            
            # Try importing modules one by one
            import_results = {}
            
            try:
                from .lib import supabase_db
                import_results["supabase_db"] = "success"
            except Exception as e:
                import_results["supabase_db"] = str(e)
            
            try:
                from .lib.logging_config import get_logger
                import_results["logging_config"] = "success"
            except Exception as e:
                import_results["logging_config"] = str(e)
            
            try:
                from .lib.errors import ValidationError
                import_results["errors"] = "success"
            except Exception as e:
                import_results["errors"] = str(e)
                
            response["imports"] = import_results
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "error": "Test endpoint error",
                "details": str(e),
                "type": type(e).__name__
            }
            self.wfile.write(json.dumps(error_response).encode())