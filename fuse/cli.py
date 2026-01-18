"""Command-line interface for Fuse - Workflow automation."""

import os
import sys

import click
import uvicorn
from rich.console import Console
from rich.panel import Panel

import logging

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.36")
def main():
    """
    Fuse - Workflow automation.

    Build, deploy, and manage workflows with visual builder, AI integration,
    and extensive node library.
    """
    pass


def setup_db():
    """Run migrations and seed initial data if needed."""
    # Suppress verbose migration logging and specific config warnings
    import logging
    import warnings
    logging.getLogger("alembic").setLevel(logging.WARNING)
    warnings.filterwarnings("ignore", message=".*FIRST_SUPERUSER_PASSWORD.*")
    
    try:
        from alembic.config import Config
        from alembic import command
        from pathlib import Path
        import fuse

        # 1. Discover paths
        import fuse
        package_dir = Path(fuse.__file__).parent
        project_dir = package_dir.parent
        
        # Prioritize location inside package (for bundled installs)
        alembic_ini = package_dir / "alembic.ini"
        
        if not alembic_ini.exists():
            # Fallback to project root (for development)
            alembic_ini = project_dir / "alembic.ini"
        
        if not alembic_ini.exists():
            console.print(f"[yellow]⚠ alembic.ini not found (checked {package_dir} and {project_dir}), skipping auto-migrations[/yellow]")
            return

        # 2. Discover migration scripts location
        # Usually 'alembic/' directory next to alembic.ini
        script_location = alembic_ini.parent / "alembic"
        if not script_location.exists():
            console.print(f"[yellow]⚠ Migration directory not found at {script_location}, skipping[/yellow]")
            return

        console.print("[cyan]⚙ Checking database and running migrations...[/cyan]")
        
        # 3. Create Alembic config and run upgrade
        # We must set script_location to an absolute path for it to work regardless of CWD
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(script_location))
        
        # Ensure SQLALCHEMY_DATABASE_URI is used (env.py handles this via fuse.config)
        command.upgrade(alembic_cfg, "head")
        
        # 4. Seed initial data
        # Search for initial_data.py (priority to package-internal)
        initial_data_script = package_dir / "initial_data.py"
        
        if not initial_data_script.exists():
            # Fallback to project root
            initial_data_script = project_dir / "initial_data.py"

        if initial_data_script.exists():
            console.print("[cyan]🌱 Seeding initial data...[/cyan]")
            import subprocess
            subprocess.run(
                [sys.executable, str(initial_data_script)],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )
        
        console.print("[green]✓ Database is up to date.[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error setting up database: {e}[/red]")
        import traceback
        logger.debug(traceback.format_exc())
        # Continue anyway


def wait_for_server(url: str, timeout: int = 15):
    """Wait for the server to be healthy."""
    import time
    import httpx

    start_time = time.time()
    health_url = f"{url.rstrip('/')}/health"
    
    while time.time() - start_time < timeout:
        try:
            with httpx.Client() as client:
                response = client.get(health_url, timeout=1.0)
                if response.status_code == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5678, help="Port to bind to (default: 5678)")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--workers", default=1, help="Number of worker processes")
@click.option("--no-browser", is_flag=True, help="Do not open browser automatically")
@click.option("--skip-migration", is_flag=True, help="Skip database migrations")
def start(host: str, port: int, reload: bool, workers: int, no_browser: bool, skip_migration: bool):
    """Start the Fuse automation server."""

    if not skip_migration:
        setup_db()

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

[dim]Press [bold]o[/bold] to open browser | [bold]q[/bold] to quit[/dim]
        """,
            title="🎯 Server Configuration",
            border_style="cyan",
        )
    )

    # Browser & Keyboard controller
    import threading
    import webbrowser

    def browser_controller():
        # First-time automatic open
        if not no_browser:
            if wait_for_server(url):
                console.print(f"[cyan]🌐 Opening browser at {url}[/cyan]")
                webbrowser.open(url)
            else:
                console.print("[yellow]⚠ Server health check timed out, browser not opened automatically[/yellow]")
        
        # Listen for keyboard input
        try:
            while True:
                cmd = input().lower().strip()
                if cmd == 'o':
                    console.print(f"[cyan]🌐 Re-opening browser at {url}[/cyan]")
                    webbrowser.open(url)
                elif cmd == 'q':
                    console.print("[yellow]👋 Stopping server...[/yellow]")
                    import os
                    import signal
                    os.kill(os.getpid(), signal.SIGINT)
                    break
        except EOFError:
            pass

    thread = threading.Thread(target=browser_controller, daemon=True)
    thread.start()

    try:
        uvicorn.run(
            "fuse.main:app",
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
# For local SQLite (default)
DATABASE_URL=sqlite:///./fuse.db

# Redis Configuration (Optional, defaults to memory if not available)
# REDIS_URL=redis://localhost:6379/0

# Security (Change this in production!)
SECRET_KEY=dev-secret-key-12345

# Initial User Data
FIRST_SUPERUSER_EMAIL=admin@fuse.io
FIRST_SUPERUSER_PASSWORD=changethis

# AI API Keys (Optional - for AI nodes)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# GOOGLE_API_KEY=

# Environment
ENVIRONMENT=local
"""
            )
        console.print("[green]✓ Created .env file[/green]")
    else:
        console.print("[yellow]⚠ .env file already exists[/yellow]")

    console.print("\n[bold green]✓ Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Edit [cyan].env[/cyan] with your configuration (e.g. AI keys)")
    console.print("2. Run [cyan]fuse start[/cyan] to initialize database and start the server")
    console.print("3. Login with [cyan]admin@fuse.io[/cyan] / [cyan]changethis[/cyan]")


@main.command()
def version():
    """Show version information."""
    from rich.table import Table

    table = Table(title="Version Information", show_header=False)
    table.add_row("Package", "fuse-io")
    table.add_row("Version", "0.1.36")
    table.add_row(
        "Python",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )

    console.print(table)


if __name__ == "__main__":
    main()
