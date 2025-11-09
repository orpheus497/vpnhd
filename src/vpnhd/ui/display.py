"""Display utilities for VPNHD using Rich library."""

from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from ..utils.constants import (
    COLOR_ERROR,
    COLOR_HEADING,
    COLOR_INFO,
    COLOR_SUCCESS,
    COLOR_WARNING,
    SYMBOL_COMPLETE,
    SYMBOL_ERROR,
    SYMBOL_IN_PROGRESS,
    SYMBOL_INCOMPLETE,
    SYMBOL_WARNING,
)


class Display:
    """Handles terminal display formatting using Rich."""

    def __init__(self):
        """Initialize display handler."""
        self.console = Console()

    def print(self, message: str, style: Optional[str] = None) -> None:
        """
        Print a message.

        Args:
            message: Message to print
            style: Optional Rich style
        """
        self.console.print(message, style=style)

    def success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"{SYMBOL_COMPLETE} {message}", style=COLOR_SUCCESS)

    def error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"{SYMBOL_ERROR} {message}", style=COLOR_ERROR)

    def warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"{SYMBOL_WARNING} {message}", style=COLOR_WARNING)

    def info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"ℹ {message}", style=COLOR_INFO)

    def heading(self, text: str, style: str = COLOR_HEADING) -> None:
        """Print heading."""
        self.console.print(f"\n{text}", style=style)

    def panel(self, content: str, title: Optional[str] = None, border_style: str = "blue") -> None:
        """
        Display content in a panel.

        Args:
            content: Panel content
            title: Optional panel title
            border_style: Border color/style
        """
        panel = Panel(content, title=title, border_style=border_style, box=box.ROUNDED)
        self.console.print(panel)

    def banner(self, title: str, subtitle: Optional[str] = None) -> None:
        """
        Display application banner.

        Args:
            title: Main title
            subtitle: Optional subtitle
        """
        content = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            content += f"\n{subtitle}"

        self.panel(content, border_style="cyan")

    def separator(self, char: str = "─") -> None:
        """Print separator line."""
        width = self.console.width
        self.console.print(char * width, style="dim")

    def table(
        self,
        title: Optional[str] = None,
        columns: Optional[List[str]] = None,
        rows: Optional[List[List[str]]] = None,
        show_header: bool = True,
    ) -> Table:
        """
        Create and display a table.

        Args:
            title: Table title
            columns: Column headers
            rows: Table rows
            show_header: Whether to show header row

        Returns:
            Table: Rich Table object
        """
        table = Table(title=title, show_header=show_header, box=box.ROUNDED)

        if columns:
            for col in columns:
                table.add_column(col, style="cyan")

        if rows:
            for row in rows:
                table.add_row(*row)

        self.console.print(table)
        return table

    def phase_status(
        self, phase_number: int, name: str, completed: bool, in_progress: bool = False
    ) -> None:
        """
        Display phase status.

        Args:
            phase_number: Phase number
            name: Phase name
            completed: Whether phase is completed
            in_progress: Whether phase is in progress
        """
        if completed:
            symbol = SYMBOL_COMPLETE
            style = COLOR_SUCCESS
            status = "COMPLETE"
        elif in_progress:
            symbol = SYMBOL_IN_PROGRESS
            style = COLOR_WARNING
            status = "IN PROGRESS"
        else:
            symbol = SYMBOL_INCOMPLETE
            style = "dim"
            status = "NOT STARTED"

        self.console.print(f"  {symbol} Phase {phase_number}: {name} [{status}]", style=style)

    def progress_bar(self, total: int, description: str = "Processing") -> Progress:
        """
        Create a progress bar.

        Args:
            total: Total number of steps
            description: Description text

        Returns:
            Progress: Rich Progress object
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

        return progress

    def spinner(self, text: str = "Working..."):
        """
        Show a spinner.

        Args:
            text: Spinner text
        """
        with self.console.status(text, spinner="dots"):
            pass

    def markdown(self, md_text: str) -> None:
        """
        Display markdown formatted text.

        Args:
            md_text: Markdown text
        """
        md = Markdown(md_text)
        self.console.print(md)

    def code_block(self, code: str, language: str = "bash", line_numbers: bool = False) -> None:
        """
        Display syntax-highlighted code block.

        Args:
            code: Code to display
            language: Programming language
            line_numbers: Whether to show line numbers
        """
        syntax = Syntax(code, language, line_numbers=line_numbers, theme="monokai")
        self.console.print(syntax)

    def clear(self) -> None:
        """Clear the terminal screen."""
        self.console.clear()

    def rule(self, title: Optional[str] = None, style: str = "blue") -> None:
        """
        Display a horizontal rule.

        Args:
            title: Optional title in the middle
            style: Rule style
        """
        from rich.rule import Rule

        self.console.print(Rule(title, style=style))

    def list_items(
        self, items: List[str], numbered: bool = False, style: Optional[str] = None
    ) -> None:
        """
        Display a list of items.

        Args:
            items: List items
            numbered: Whether to number items
            style: Optional style
        """
        for i, item in enumerate(items, 1):
            if numbered:
                self.console.print(f"  {i}. {item}", style=style)
            else:
                self.console.print(f"  • {item}", style=style)

    def key_value(
        self, key: str, value: str, key_style: str = "cyan", value_style: Optional[str] = None
    ) -> None:
        """
        Display key-value pair.

        Args:
            key: Key
            value: Value
            key_style: Style for key
            value_style: Style for value
        """
        self.console.print(f"  {key}: ", style=key_style, end="")
        self.console.print(value, style=value_style)

    def confirmation_summary(self, data: Dict[str, Any], title: str = "Please Confirm") -> None:
        """
        Display confirmation summary.

        Args:
            data: Data to display
            title: Summary title
        """
        self.heading(title)
        self.separator()

        for key, value in data.items():
            self.key_value(key, str(value))

        self.separator()

    def eli5_explanation(self, concept: str, explanation: str) -> None:
        """
        Display ELI5 (Explain Like I'm 5) explanation.

        Args:
            concept: Concept being explained
            explanation: Simple explanation
        """
        content = f"[bold]{concept}[/bold] (Explained Simply)\n\n{explanation}"
        self.panel(content, border_style="green")

    def step_header(self, step_number: int, total_steps: int, description: str) -> None:
        """
        Display step header.

        Args:
            step_number: Current step number
            total_steps: Total number of steps
            description: Step description
        """
        self.rule(f"Step {step_number}/{total_steps}: {description}", style="cyan")

    def newline(self, count: int = 1) -> None:
        """Print blank lines."""
        for _ in range(count):
            self.console.print()
