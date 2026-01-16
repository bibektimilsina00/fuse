"""Command-line interface for Fuse - Workflow automation."""

import os
import sys

import click
import uvicorn
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    Fuse - Workflow automation.

    Build, deploy, and manage workflows with visual builder, AI integration,
    and extensive node library.
    """
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5678, help="Port to bind to (default: 5678)")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--workers", default=1, help="Number of worker processes")
@click.option("--no-browser", is_flag=True, help="Do not open browser automatically")
def start(host: str, port: int, reload: bool, workers: int, no_browser: bool):
    """Start the Fuse automation server."""

    url = f"http://{'localhost' if host == '0.0.0.0' else host}:{port}"

    console.print(
        Panel.fit(
            f"""[bold cyan]🚀 Fuse - Workflow Automation[/bold cyan]
        
[green]Starting server...[/green]
[dim]Host:[/dim] {host}
[dim]Port:[/dim] {port}
[dim]Workers:[/dim] {workers}
[dim]Reload:[/dim] {reload}

[yellow]Access the UI at:[/yellow] [link]{url}[/link]
        """,
            title="🎯 Server Configuration",
            border_style="cyan",
        )
    )

    # Open browser automatically
    if not no_browser:
        import threading
        import time
        import webbrowser

        def open_browser():
            time.sleep(1.5)  # Wait for server to start
            console.print(f"[cyan]🌐 Opening browser at {url}[/cyan]")
            webbrowser.open(url)

        thread = threading.Thread(target=open_browser, daemon=True)
        thread.start()

    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info",
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Server stopped gracefully[/yellow]")
        sys.exit(0)


@main.command()
def init():
    """Initialize a new Fuse automation project."""
    console.print(
        Panel(
            """[bold green]✓ Initializing Fuse - Workflow Automation[/bold green]
        
This will create the necessary configuration files and directories.
        """,
            border_style="green",
        )
    )

    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        console.print("[cyan]Creating .env file...[/cyan]")
        with open(".env", "w") as f:
            f.write(
                """# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/automation

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production

# AI API Keys (Optional - for AI nodes)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Environment
ENVIRONMENT=local
"""
            )
        console.print("[green]✓ Created .env file[/green]")
    else:
        console.print("[yellow]⚠ .env file already exists[/yellow]")

    console.print("\n[bold green]✓ Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Edit [cyan].env[/cyan] with your configuration")
    console.print("2. Run [cyan]fluxo start[/cyan] to start the server")


@main.command()
def version():
    """Show version information."""
    from rich.table import Table

    table = Table(title="Version Information", show_header=False)
    table.add_row("Package", "fluxo")
    table.add_row("Version", "0.1.0")
    table.add_row(
        "Python",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )

    console.print(table)


if __name__ == "__main__":
    main()
