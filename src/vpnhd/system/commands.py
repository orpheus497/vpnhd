"""Safe command execution utilities for VPNHD."""

import subprocess
import shlex
import asyncio
from dataclasses import dataclass
from typing import Optional, List, Union
from pathlib import Path

from ..utils.logging import get_logger
from ..utils.constants import COMMAND_TIMEOUT_DEFAULT


# Sensitive parameter patterns that should be redacted in logs
SENSITIVE_PARAMS = {
    "-p",
    "--password",
    "--pass",
    "--key",
    "--secret",
    "--token",
    "--api-key",
    "--apikey",
    "--auth",
    "--credential",
    "--private-key",
}


def _has_sensitive_params(command_list: List[str]) -> bool:
    """
    Check if command contains sensitive parameters.

    Args:
        command_list: Command as list of strings

    Returns:
        True if command contains sensitive parameters
    """
    for arg in command_list:
        if any(arg.lower().startswith(param) for param in SENSITIVE_PARAMS):
            return True
    return False


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
    command: Union[str, List[str]],
    sudo: bool = False,
    check: bool = True,
    capture_output: bool = True,
    timeout: Optional[int] = None,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
) -> CommandResult:
    """
    Execute command safely without shell injection vulnerabilities.

    Args:
        command: Command to execute (string or list of arguments)
        sudo: Whether to use sudo
        check: Raise exception on non-zero exit
        capture_output: Capture stdout/stderr
        timeout: Command timeout in seconds
        cwd: Working directory
        env: Environment variables

    Returns:
        CommandResult: Execution result

    Security:
        This function uses array-based command execution (shell=False)
        to prevent command injection attacks. Commands are never executed
        through a shell unless absolutely necessary.
    """
    logger = get_logger("commands")

    # Parse command if string
    if isinstance(command, str):
        command_list = shlex.split(command)
    else:
        command_list = list(command)

    # Prepend sudo if requested
    if sudo:
        command_list = ["sudo"] + command_list

    # Use default timeout if not specified
    if timeout is None:
        timeout = COMMAND_TIMEOUT_DEFAULT

    # Log command for debugging (only if it doesn't contain sensitive parameters)
    command_str = " ".join(command_list)
    if not _has_sensitive_params(command_list):
        logger.debug(f"Executing command: {command_str}")
    else:
        logger.debug("Executing command with sensitive parameters (not logged for security)")

    try:
        # Execute command safely WITHOUT shell=True
        result = subprocess.run(
            command_list,
            shell=False,  # SECURITY: Prevents command injection
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            check=False,  # We handle errors manually
        )

        success = result.returncode == 0

        if not success:
            if not _has_sensitive_params(command_list):
                logger.warning(f"Command failed with exit code {result.returncode}: {command_str}")
            else:
                logger.warning(
                    f"Command with sensitive parameters failed with "
                    f"exit code {result.returncode}"
                )
            if result.stderr:
                logger.warning(f"  stderr: {result.stderr.strip()}")

        if check and not success:
            raise subprocess.CalledProcessError(
                result.returncode, command_str, output=result.stdout, stderr=result.stderr
            )

        return CommandResult(
            exit_code=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            success=success,
            command=command_str,
        )

    except subprocess.TimeoutExpired as e:
        if not _has_sensitive_params(command_list):
            logger.error(f"Command timed out after {timeout}s: {command_str}")
        else:
            logger.error(f"Command with sensitive parameters timed out after {timeout}s")
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False,
            command=command_str,
        )

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return CommandResult(
            exit_code=-1, stdout="", stderr=str(e), success=False, command=command_str
        )


def execute_commands(
    commands: List[str],
    sudo: bool = False,
    stop_on_error: bool = True,
    timeout: Optional[int] = None,
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
        result = execute_command(command, sudo=sudo, check=False, timeout=timeout)

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
    result = execute_command(f"command -v {shlex.quote(command)}", check=False, capture_output=True)
    return result.success


def run_command_with_input(
    command: Union[str, List[str]],
    input_data: str,
    sudo: bool = False,
    timeout: Optional[int] = None,
    capture_output: bool = True,
) -> CommandResult:
    """
    Run command with stdin input safely.

    Args:
        command: Command to execute (string or list of arguments)
        input_data: Data to send to stdin
        sudo: Whether to use sudo
        timeout: Command timeout in seconds
        capture_output: Capture stdout/stderr

    Returns:
        CommandResult: Execution result

    Security:
        Uses array-based command execution to prevent injection attacks.
    """
    logger = get_logger("commands")

    # Parse command if string
    if isinstance(command, str):
        command_list = shlex.split(command)
    else:
        command_list = list(command)

    # Prepend sudo if requested
    if sudo:
        command_list = ["sudo"] + command_list

    if timeout is None:
        timeout = COMMAND_TIMEOUT_DEFAULT

    command_str = " ".join(command_list)
    logger.debug(f"Executing command with input: {command_str}")

    try:
        result = subprocess.run(
            command_list,
            shell=False,  # SECURITY: Prevents command injection
            input=input_data,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False,
        )

        success = result.returncode == 0

        return CommandResult(
            exit_code=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
            success=success,
            command=command_str,
        )

    except subprocess.TimeoutExpired as e:
        logger.error(f"Command with input timed out after {timeout}s: {command_str}")
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False,
            command=command_str,
        )

    except Exception as e:
        logger.error(f"Error executing command with input: {e}")
        return CommandResult(
            exit_code=-1, stdout="", stderr=str(e), success=False, command=command_str
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

    result = execute_command([command, version_flag], check=False)
    if result.success:
        return result.stdout.strip().split("\n")[0]

    return None


async def execute_command_async(
    command: Union[str, List[str]],
    sudo: bool = False,
    check: bool = True,
    timeout: Optional[int] = None,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
) -> CommandResult:
    """
    Execute command asynchronously without shell injection vulnerabilities.

    Args:
        command: Command to execute (string or list of arguments)
        sudo: Whether to use sudo
        check: Raise exception on non-zero exit
        timeout: Command timeout in seconds
        cwd: Working directory
        env: Environment variables

    Returns:
        CommandResult: Execution result

    Security:
        This function uses array-based command execution to prevent
        command injection attacks. Commands are never executed through
        a shell.
    """
    logger = get_logger("commands")

    # Parse command if string
    if isinstance(command, str):
        command_list = shlex.split(command)
    else:
        command_list = list(command)

    # Prepend sudo if requested
    if sudo:
        command_list = ["sudo"] + command_list

    # Use default timeout if not specified
    if timeout is None:
        timeout = COMMAND_TIMEOUT_DEFAULT

    # Log command for debugging (only if it doesn't contain sensitive parameters)
    command_str = " ".join(command_list)
    if not _has_sensitive_params(command_list):
        logger.debug(f"Executing async command: {command_str}")
    else:
        logger.debug("Executing async command with sensitive parameters (not logged)")

    try:
        # Execute command safely using asyncio subprocess
        process = await asyncio.create_subprocess_exec(
            *command_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        # Wait for process with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            if not _has_sensitive_params(command_list):
                logger.error(f"Async command timed out after {timeout}s: {command_str}")
            else:
                logger.error(f"Async command with sensitive parameters timed out")
            return CommandResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                success=False,
                command=command_str,
            )

        exit_code = process.returncode
        success = exit_code == 0

        stdout_str = stdout.decode() if stdout else ""
        stderr_str = stderr.decode() if stderr else ""

        if not success:
            if not _has_sensitive_params(command_list):
                logger.warning(f"Async command failed with exit code {exit_code}: {command_str}")
            else:
                logger.warning(f"Async command with sensitive parameters failed")
            if stderr_str:
                logger.warning(f"  stderr: {stderr_str.strip()}")

        if check and not success:
            raise subprocess.CalledProcessError(
                exit_code, command_str, output=stdout_str, stderr=stderr_str
            )

        return CommandResult(
            exit_code=exit_code,
            stdout=stdout_str,
            stderr=stderr_str,
            success=success,
            command=command_str,
        )

    except Exception as e:
        logger.error(f"Error executing async command: {e}")
        return CommandResult(
            exit_code=-1, stdout="", stderr=str(e), success=False, command=command_str
        )
