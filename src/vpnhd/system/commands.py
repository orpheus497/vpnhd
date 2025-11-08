"""Safe command execution utilities for VPNHD."""

import subprocess
import shlex
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

from ..utils.logging import get_logger
from ..utils.constants import COMMAND_TIMEOUT_DEFAULT


@dataclass
class CommandResult:
    """Result of command execution."""
    exit_code: int
    stdout: str
    stderr: str
    success: bool
    command: str

    def __bool__(self) -> bool:
        """Allow boolean evaluation of result."""
        return self.success


def execute_command(
    command: str,
    sudo: bool = False,
    check: bool = True,
    capture_output: bool = True,
    timeout: Optional[int] = None,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None
) -> CommandResult:
    """
    Execute shell command safely.

    Args:
        command: Command to execute
        sudo: Whether to use sudo
        check: Raise exception on non-zero exit
        capture_output: Capture stdout/stderr
        timeout: Command timeout in seconds
        cwd: Working directory
        env: Environment variables

    Returns:
        CommandResult: Execution result
    """
    logger = get_logger("commands")

    # Prepend sudo if requested
    if sudo:
        command = f"sudo {command}"

    # Use default timeout if not specified
    if timeout is None:
        timeout = COMMAND_TIMEOUT_DEFAULT

    logger.debug(f"Executing command: {command}")

    try:
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            check=False  # We handle errors manually
        )

        success = result.returncode == 0

        if not success:
            logger.warning(f"Command failed with exit code {result.returncode}: {command}")
            if result.stderr:
                logger.warning(f"  stderr: {result.stderr.strip()}")

        if check and not success:
            raise subprocess.CalledProcessError(
                result.returncode,
                command,
                output=result.stdout,
                stderr=result.stderr
            )

        return CommandResult(
            exit_code=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            success=success,
            command=command
        )

    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {command}")
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False,
            command=command
        )

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr=str(e),
            success=False,
            command=command
        )


def execute_commands(
    commands: List[str],
    sudo: bool = False,
    stop_on_error: bool = True,
    timeout: Optional[int] = None
) -> List[CommandResult]:
    """
    Execute multiple commands in sequence.

    Args:
        commands: List of commands
        sudo: Whether to use sudo
        stop_on_error: Stop on first error
        timeout: Command timeout in seconds

    Returns:
        List[CommandResult]: Results for each command
    """
    logger = get_logger("commands")
    results = []

    for command in commands:
        result = execute_command(
            command,
            sudo=sudo,
            check=False,
            timeout=timeout
        )

        results.append(result)

        if stop_on_error and not result.success:
            logger.warning(f"Stopping command execution due to error in: {command}")
            break

    return results


def check_command_exists(command: str) -> bool:
    """
    Check if command exists in PATH.

    Args:
        command: Command name

    Returns:
        bool: True if command exists
    """
    result = execute_command(
        f"command -v {shlex.quote(command)}",
        check=False,
        capture_output=True
    )
    return result.success


def run_command_with_input(
    command: str,
    input_data: str,
    sudo: bool = False,
    timeout: Optional[int] = None
) -> CommandResult:
    """
    Run command with stdin input.

    Args:
        command: Command to execute
        input_data: Data to send to stdin
        sudo: Whether to use sudo
        timeout: Command timeout in seconds

    Returns:
        CommandResult: Execution result
    """
    logger = get_logger("commands")

    if sudo:
        command = f"sudo {command}"

    if timeout is None:
        timeout = COMMAND_TIMEOUT_DEFAULT

    logger.debug(f"Executing command with input: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        success = result.returncode == 0

        return CommandResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            success=success,
            command=command
        )

    except Exception as e:
        logger.error(f"Error executing command with input: {e}")
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr=str(e),
            success=False,
            command=command
        )


def get_command_output(command: str, sudo: bool = False) -> Optional[str]:
    """
    Get command output as string.

    Args:
        command: Command to execute
        sudo: Whether to use sudo

    Returns:
        Optional[str]: Command output or None if failed
    """
    result = execute_command(command, sudo=sudo, check=False)
    if result.success:
        return result.stdout.strip()
    return None


def command_exists_any(commands: List[str]) -> bool:
    """
    Check if any of the commands exist.

    Args:
        commands: List of command names

    Returns:
        bool: True if at least one command exists
    """
    return any(check_command_exists(cmd) for cmd in commands)


def get_command_version(command: str, version_flag: str = "--version") -> Optional[str]:
    """
    Get version of a command.

    Args:
        command: Command name
        version_flag: Flag to get version (default: --version)

    Returns:
        Optional[str]: Version string or None if failed
    """
    if not check_command_exists(command):
        return None

    result = execute_command(f"{command} {version_flag}", check=False)
    if result.success:
        return result.stdout.strip().split('\n')[0]

    return None
