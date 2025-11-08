"""User input prompts for VPNHD."""

from typing import Optional, List, Callable
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.console import Console

from .validation import InputValidator


class Prompts:
    """Handles user input prompts."""

    def __init__(self):
        """Initialize prompts handler."""
        self.console = Console()
        self.validator = InputValidator()

    def text(
        self,
        message: str,
        default: Optional[str] = None,
        validator: Optional[Callable[[str], tuple[bool, Optional[str]]]] = None,
        password: bool = False
    ) -> str:
        """
        Prompt for text input.

        Args:
            message: Prompt message
            default: Default value
            validator: Validation function
            password: Whether to hide input

        Returns:
            str: User input
        """
        while True:
            value = Prompt.ask(
                message,
                default=default,
                password=password,
                console=self.console
            )

            if validator:
                is_valid, error = validator(value)
                if not is_valid:
                    self.console.print(f"[red]{error}[/red]")
                    continue

            return value

    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Prompt for yes/no confirmation.

        Args:
            message: Prompt message
            default: Default value

        Returns:
            bool: User confirmation
        """
        return Confirm.ask(message, default=default, console=self.console)

    def choice(
        self,
        message: str,
        choices: List[str],
        default: Optional[str] = None
    ) -> str:
        """
        Prompt for single choice from list.

        Args:
            message: Prompt message
            choices: List of choices
            default: Default choice

        Returns:
            str: Selected choice
        """
        choices_str = "/".join(choices)
        prompt_msg = f"{message} [{choices_str}]"

        validator = lambda v: self.validator.validate_choice(v, choices)

        return self.text(prompt_msg, default=default, validator=validator)

    def integer(
        self,
        message: str,
        default: Optional[int] = None,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None
    ) -> int:
        """
        Prompt for integer input.

        Args:
            message: Prompt message
            default: Default value
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            int: User input
        """
        while True:
            try:
                if default is not None:
                    value_str = Prompt.ask(message, default=str(default), console=self.console)
                else:
                    value_str = Prompt.ask(message, console=self.console)

                value = int(value_str)

                if min_val is not None and value < min_val:
                    self.console.print(f"[red]Value must be at least {min_val}[/red]")
                    continue

                if max_val is not None and value > max_val:
                    self.console.print(f"[red]Value must be at most {max_val}[/red]")
                    continue

                return value

            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")

    def ip_address(
        self,
        message: str,
        default: Optional[str] = None
    ) -> str:
        """
        Prompt for IP address with validation.

        Args:
            message: Prompt message
            default: Default IP

        Returns:
            str: Valid IP address
        """
        return self.text(
            message,
            default=default,
            validator=self.validator.validate_ip
        )

    def network(
        self,
        message: str,
        default: Optional[str] = None
    ) -> str:
        """
        Prompt for network in CIDR notation.

        Args:
            message: Prompt message
            default: Default network

        Returns:
            str: Valid network
        """
        return self.text(
            message,
            default=default,
            validator=self.validator.validate_network_cidr
        )

    def hostname(
        self,
        message: str,
        default: Optional[str] = None
    ) -> str:
        """
        Prompt for hostname with validation.

        Args:
            message: Prompt message
            default: Default hostname

        Returns:
            str: Valid hostname
        """
        return self.text(
            message,
            default=default,
            validator=self.validator.validate_hostname
        )

    def port(
        self,
        message: str,
        default: Optional[int] = None
    ) -> int:
        """
        Prompt for port number with validation.

        Args:
            message: Prompt message
            default: Default port

        Returns:
            int: Valid port number
        """
        while True:
            value_str = self.text(
                message,
                default=str(default) if default else None,
                validator=self.validator.validate_port
            )

            return int(value_str)

    def password(
        self,
        message: str = "Password",
        confirm: bool = True,
        min_length: int = 8
    ) -> str:
        """
        Prompt for password input.

        Args:
            message: Prompt message
            confirm: Whether to ask for confirmation
            min_length: Minimum password length

        Returns:
            str: Password
        """
        while True:
            password = self.text(f"{message}", password=True)

            if len(password) < min_length:
                self.console.print(f"[red]Password must be at least {min_length} characters[/red]")
                continue

            if confirm:
                password2 = self.text(f"{message} (confirm)", password=True)

                if password != password2:
                    self.console.print("[red]Passwords do not match. Please try again.[/red]")
                    continue

            return password

    def menu(
        self,
        title: str,
        options: List[tuple[str, str]],
        allow_back: bool = False
    ) -> str:
        """
        Display a menu and get user choice.

        Args:
            title: Menu title
            options: List of (key, description) tuples
            allow_back: Whether to allow going back

        Returns:
            str: Selected option key
        """
        from rich.table import Table
        from rich import box

        # Display menu title
        self.console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

        # Create menu table
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Description")

        valid_choices = []

        for key, description in options:
            table.add_row(f"[{key}]", description)
            valid_choices.append(key)

        if allow_back:
            table.add_row("[b]", "Go back")
            valid_choices.append("b")

        self.console.print(table)

        # Get user choice
        while True:
            choice = Prompt.ask(
                "\nYour choice",
                console=self.console
            ).lower()

            if choice in valid_choices:
                return choice

            self.console.print(f"[red]Invalid choice. Please enter one of: {', '.join(valid_choices)}[/red]")

    def pause(self, message: str = "Press Enter to continue...") -> None:
        """
        Pause and wait for user to press Enter.

        Args:
            message: Message to display
        """
        Prompt.ask(message, console=self.console)

    def multiline(self, message: str, default: Optional[str] = None) -> str:
        """
        Prompt for multiline text input.

        Args:
            message: Prompt message
            default: Default value

        Returns:
            str: User input
        """
        self.console.print(f"[cyan]{message}[/cyan] (Enter a blank line to finish)")

        lines = []

        while True:
            line = input()
            if not line:
                break
            lines.append(line)

        result = '\n'.join(lines)

        if not result and default:
            return default

        return result
