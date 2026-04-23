"""
Shared utilities for HuGGeMs commands
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import click


def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def validate_input_dir(ctx, param, value):
    """Validate that input directory exists and is readable."""
    if value is None:
        return None

    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Input directory does not exist: {value}")
    if not path.is_dir():
        raise click.BadParameter(f"Input path is not a directory: {value}")
    if not os.access(path, os.R_OK):
        raise click.BadParameter(f"Input directory is not readable: {value}")

    return str(path.resolve())


def validate_output_dir(ctx, param, value):
    """Validate and create output directory if needed."""
    if value is None:
        return None

    path = Path(value)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise click.BadParameter(f"Cannot create output directory: {e}")

    if not os.access(path, os.W_OK):
        raise click.BadParameter(f"Output directory is not writable: {value}")

    return str(path.resolve())


def check_tool_available(tool_name: str) -> bool:
    """Check if a required tool is available in PATH."""
    import shutil
    import platform
    
    # Direct check
    if shutil.which(tool_name) is not None:
        return True
    
    # Case-insensitive check for Linux (some tools have mixed case like dRep)
    if platform.system() == "Linux":
        import subprocess
        try:
            result = subprocess.run(
                ["which", tool_name.lower()],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
        
        # Try the actual command with --version as fallback
        try:
            result = subprocess.run(
                [tool_name, "--version"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            pass
    
    return False


def check_tools_available(tools: list) -> dict:
    """Check multiple tools and return their availability status."""
    results = {}
    for tool in tools:
        results[tool] = check_tool_available(tool)
    return results


def log_step(step: str, message: str):
    """Log a pipeline step with consistent formatting."""
    click.echo(click.style(f"\n{'=' * 60}", fg="blue"))
    click.echo(click.style(f"  {step}", fg="cyan", bold=True))
    click.echo(click.style(f"{'=' * 60}", fg="blue"))
    if message:
        click.echo(message)


def log_warning(message: str):
    """Log a warning message."""
    click.echo(click.style(f"WARNING: {message}", fg="yellow"))


def log_error(message: str):
    """Log an error message."""
    click.echo(click.style(f"ERROR: {message}", fg="red", bold=True))


def log_success(message: str):
    """Log a success message."""
    click.echo(click.style(f"SUCCESS: {message}", fg="green"))


def get_default_db_path(db_name: str) -> Optional[str]:
    """Get default database path from common locations."""
    common_paths = [
        os.path.join(os.path.expanduser("~"), ".huggems", "db", db_name),
        os.path.join(os.path.expanduser("~"), "data", "huggems", db_name),
        os.path.join(os.getcwd(), "db", db_name),
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None
