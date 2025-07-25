"""Compete page endpoint"""
from http.server import BaseHTTPRequestHandler
import os
from pathlib import Path

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Serve the main index.html but with compete section active
        base_path = Path(__file__).parent.parent
        index_path = base_path / 'vercel' / 'static' / 'index-rams.html'
        
        if index_path.exists():
            content = index_path.read_text()
            
            # Modify the content to show compete section by default
            # and update the active nav item
            content = content.replace('href="#compete" class="nav-link"', 'href="#compete" class="nav-link active"')
            content = content.replace('href="#overview" class="nav-link active"', 'href="#overview" class="nav-link"')
            content = content.replace('<section id="compete" class="section" style="display: none;">', '<section id="compete" class="section" style="display: block;">')
            content = content.replace('<section id="overview" class="section">', '<section id="overview" class="section" style="display: none;">')
            
            # Update navigation links to use real URLs instead of hash navigation
            content = content.replace('href="#overview"', 'href="/"')
            content = content.replace('href="#compete"', 'href="/compete"')
            content = content.replace('href="#benchmark"', 'href="/benchmark"')
            content = content.replace('href="#sessions"', 'href="/sessions"')
            content = content.replace('href="#leaderboard"', 'href="/leaderboard"')
            content = content.replace('href="#prompts"', 'href="/prompts"')
            
            self.wfile.write(content.encode())
        else:
            self.wfile.write(b"<h1>Compete page not found</h1>")