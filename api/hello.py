from http.server import BaseHTTPRequestHandler
import json
import sys
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            result = {"status": "testing imports"}
            
            # Test 1: Can we access lib directory?
            try:
                import os
                result["cwd"] = os.getcwd()
                result["lib_exists"] = os.path.exists("lib")
                result["api_lib_exists"] = os.path.exists("api/lib")
                result["files"] = os.listdir(".")[:10]  # First 10 files
            except Exception as e:
                result["dir_error"] = str(e)
            
            # Test 2: Try importing from lib
            try:
                from lib import db
                result["lib_db_import"] = "success"
            except Exception as e:
                result["lib_db_error"] = str(e)
                result["lib_db_traceback"] = traceback.format_exc()
            
            # Test 3: Try dot import
            try:
                from .lib import db
                result["dot_lib_db_import"] = "success"
            except Exception as e:
                result["dot_lib_db_error"] = str(e)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_data = {
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            self.wfile.write(json.dumps(error_data).encode())