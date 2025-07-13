"""Web-related CLI commands."""

import click
import webbrowser
import subprocess
import time
from pathlib import Path

from rich.console import Console

console = Console()


@click.command()
@click.option(
    "--port", "-p",
    default=8000,
    help="Port to run the web server on"
)
@click.option(
    "--open-browser", "-o",
    is_flag=True,
    help="Open browser automatically"
)
def serve(port: int, open_browser: bool):
    """Start the web interface server."""
    console.print(f"\n[bold green]Starting Minesweeper AI Benchmark Web Interface[/bold green]")
    console.print(f"Server will be available at: http://localhost:{port}\n")
    
    if open_browser:
        # Wait a moment for server to start
        def open_browser_delayed():
            time.sleep(2)
            webbrowser.open(f"http://localhost:{port}")
        
        import threading
        threading.Thread(target=open_browser_delayed).start()
    
    try:
        # Run uvicorn
        subprocess.run([
            "uvicorn",
            "src.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", str(port)
        ])
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error starting server: {e}[/red]")
        console.print("Make sure uvicorn is installed: pip install uvicorn[standard]")


@click.command()
def open_web():
    """Open the web interface in browser (if server is running)."""
    import requests
    
    url = "http://localhost:8000"
    
    # Check if server is running
    try:
        response = requests.get(f"{url}/health", timeout=1)
        if response.status_code == 200:
            webbrowser.open(url)
            console.print(f"[green]Opened {url} in browser[/green]")
        else:
            console.print("[red]Server is not responding properly[/red]")
    except requests.exceptions.RequestException:
        console.print("[red]Web server is not running![/red]")
        console.print("Start it with: minesweeper-benchmark serve")


@click.command()
def export_leaderboard():
    """Export current leaderboard data as JSON."""
    import requests
    import json
    
    url = "http://localhost:8000/api/leaderboard"
    output_file = Path("leaderboard_export.json")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]Leaderboard exported to {output_file}[/green]")
        console.print(f"Total entries: {len(data)}")
        
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error exporting leaderboard: {e}[/red]")
        console.print("Make sure the web server is running")


# Add commands to main CLI
def add_web_commands(cli_group):
    """Add web commands to the main CLI group."""
    cli_group.add_command(serve)
    cli_group.add_command(open_web)
    cli_group.add_command(export_leaderboard)