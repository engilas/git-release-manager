"""Utility functions for GRM."""

import sys
from typing import Any
import click


def error_exit(message: str, exit_code: int = 1) -> None:
    """Print error message and exit.

    Args:
        message: Error message to display
        exit_code: Exit code (default: 1)
    """
    click.echo(click.style(f"Error: {message}", fg="red"), err=True)
    sys.exit(exit_code)


def success_message(message: str) -> None:
    """Print success message in green.

    Args:
        message: Success message to display
    """
    click.echo(click.style(message, fg="green"))


def warning_message(message: str) -> None:
    """Print warning message in yellow.

    Args:
        message: Warning message to display
    """
    click.echo(click.style(f"Warning: {message}", fg="yellow"))


def info_message(message: str) -> None:
    """Print info message in blue.

    Args:
        message: Info message to display
    """
    click.echo(click.style(message, fg="blue"))


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses enter

    Returns:
        True if user confirms, False otherwise
    """
    return click.confirm(message, default=default)


def prompt_choice(message: str, choices: list, default: Any = None) -> Any:
    """Prompt user to choose from a list of options.

    Args:
        message: Prompt message
        choices: List of valid choices
        default: Default choice if user just presses enter

    Returns:
        Selected choice
    """
    return click.prompt(message, type=click.Choice(choices), default=default)
