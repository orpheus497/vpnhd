"""Base class for all setup phases."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from ..config.manager import ConfigManager
    from ..ui.display import Display
    from ..ui.prompts import Prompts


class PhaseStatus(Enum):
    """Phase execution status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Phase(ABC):
    """Base class for all setup phases."""

    def __init__(self, config_manager: "ConfigManager", display: "Display", prompts: "Prompts"):
        """
        Initialize phase.

        Args:
            config_manager: Configuration manager instance
            display: Display instance for output
            prompts: Prompts instance for user input
        """
        self.config = config_manager
        self.display = display
        self.prompts = prompts
        self.status = PhaseStatus.NOT_STARTED
        self.error_message: Optional[str] = None
        self.logger = get_logger(f"Phase{self.number}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return phase name."""
        pass

    @property
    @abstractmethod
    def number(self) -> int:
        """Return phase number (1-8)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return brief description of phase."""
        pass

    @property
    @abstractmethod
    def long_description(self) -> str:
        """Return detailed ELI5 description."""
        pass

    @abstractmethod
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for this phase are met.

        Returns:
            bool: True if ready to execute, False otherwise
        """
        pass

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the phase.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    def rollback(self) -> bool:
        """
        Rollback phase changes (optional, override if needed).

        Returns:
            bool: True if rollback successful, False otherwise
        """
        self.logger.info(f"Rollback not implemented for {self.name}")
        return True

    def verify(self) -> bool:
        """
        Verify phase completion (optional, override if needed).

        Returns:
            bool: True if verification passed, False otherwise
        """
        self.logger.info(f"Verification not implemented for {self.name}")
        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get phase status.

        Returns:
            dict: Status information
        """
        return {
            "name": self.name,
            "number": self.number,
            "status": self.status.value,
            "error_message": self.error_message,
        }

    def show_introduction(self) -> None:
        """Show phase introduction with ELI5 explanation."""
        self.display.clear()
        self.display.rule(f"Phase {self.number}: {self.name}", style="cyan")
        self.display.newline()

        # Show ELI5 explanation
        self.display.eli5_explanation(f"What is {self.name.split(':')[0]}?", self.long_description)

        self.display.newline()
        self.display.heading("What this phase does:")
        self.display.print(self.description, style="white")
        self.display.newline()

    def mark_complete(self, notes: str = "") -> None:
        """
        Mark phase as complete.

        Args:
            notes: Optional completion notes
        """
        self.status = PhaseStatus.COMPLETED
        self.config.mark_phase_complete(self.number, notes)
        self.config.save()
        self.logger.info(f"Phase {self.number} marked as complete")

    def mark_failed(self, error: str) -> None:
        """
        Mark phase as failed.

        Args:
            error: Error message
        """
        self.status = PhaseStatus.FAILED
        self.error_message = error
        self.logger.error(f"Phase {self.number} failed: {error}")

    def is_complete(self) -> bool:
        """
        Check if phase is already complete.

        Returns:
            bool: True if complete
        """
        return self.config.is_phase_complete(self.number)
