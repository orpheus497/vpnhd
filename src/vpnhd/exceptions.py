"""Custom exceptions for VPNHD application.

This module defines a hierarchy of custom exceptions for better
error handling and debugging throughout the application.
"""


class VPNHDError(Exception):
    """Base exception for all VPNHD errors."""

    pass


class ConfigurationError(VPNHDError):
    """Raised when configuration is invalid or cannot be loaded."""

    pass


class PhaseError(VPNHDError):
    """Base exception for phase-related errors."""

    pass


class PrerequisiteError(PhaseError):
    """Raised when phase prerequisites are not met."""

    def __init__(self, phase_number: int, missing_items: list):
        self.phase_number = phase_number
        self.missing_items = missing_items
        message = (
            f"Phase {phase_number} prerequisites not met. " f"Missing: {', '.join(missing_items)}"
        )
        super().__init__(message)


class PhaseExecutionError(PhaseError):
    """Raised when phase execution fails."""

    def __init__(self, phase_number: int, reason: str):
        self.phase_number = phase_number
        self.reason = reason
        message = f"Phase {phase_number} execution failed: {reason}"
        super().__init__(message)


class ValidationError(VPNHDError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        message = f"Validation failed for {field}='{value}': {reason}"
        super().__init__(message)


class NetworkError(VPNHDError):
    """Raised when network operations fail."""

    pass


class SystemCommandError(VPNHDError):
    """Raised when system command execution fails."""

    def __init__(self, command: str, exit_code: int, stderr: str):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        message = (
            f"Command failed with exit code {exit_code}: {command}\n" f"Error output: {stderr}"
        )
        super().__init__(message)


class SecurityError(VPNHDError):
    """Raised when security checks fail."""

    pass


class DependencyError(VPNHDError):
    """Raised when required dependencies are missing."""

    def __init__(self, missing_dependencies: list):
        self.missing_dependencies = missing_dependencies
        message = f"Missing dependencies: {', '.join(missing_dependencies)}"
        super().__init__(message)
