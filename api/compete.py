"""Compete page endpoint - redirects to main app"""
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Redirect to main app with compete hash
        self.send_response(301)
        self.send_header('Location', '/#compete')
        self.end_headers()