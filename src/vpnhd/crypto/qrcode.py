"""QR code generation for WireGuard configuration.

This module handles generating QR codes from WireGuard client configurations,
making it easy to configure mobile devices by scanning.
"""

from pathlib import Path
from typing import Optional
import subprocess
import tempfile

from ..system.commands import execute_command, check_command_exists, run_command_with_input
from ..utils.logging import get_logger

logger = get_logger(__name__)


def generate_qr_code(config_text: str, output_path: Optional[str] = None) -> bool:
    """Generate a QR code from WireGuard configuration text.

    Args:
        config_text: WireGuard configuration file content
        output_path: Optional path to save QR code image (PNG format)

    Returns:
        True if QR code was generated successfully, False otherwise
    """
    try:
        # Check if qrencode is installed
        if not check_command_exists("qrencode"):
            logger.error(
                "qrencode is not installed. Install with: "
                "apt install qrencode (Debian/Ubuntu) or "
                "dnf install qrencode (Fedora)"
            )
            return False

        if output_path:
            # Generate QR code and save to file
            cmd = f"qrencode -t PNG -o {output_path} -l L"
            result = run_command_with_input(cmd, input_data=config_text)

            if result.success:
                logger.info(f"QR code saved to {output_path}")
                return True
            else:
                logger.error(f"Failed to generate QR code: {result.stderr}")
                return False
        else:
            # Generate QR code to stdout (terminal display)
            return display_qr_terminal(config_text)

    except Exception as e:
        logger.exception(f"Error generating QR code: {e}")
        return False


def save_qr_code(config_text: str, output_path: str) -> bool:
    """Save a QR code image to a file.

    Args:
        config_text: WireGuard configuration file content
        output_path: Path to save QR code image (PNG format)

    Returns:
        True if QR code was saved successfully, False otherwise
    """
    return generate_qr_code(config_text, output_path)


def display_qr_terminal(config_text: str) -> bool:
    """Display a QR code in the terminal using ASCII art.

    Args:
        config_text: WireGuard configuration file content

    Returns:
        True if QR code was displayed successfully, False otherwise
    """
    try:
        # Check if qrencode is installed
        if not check_command_exists("qrencode"):
            logger.error("qrencode is not installed")
            return False

        # Generate QR code as ASCII art (terminal output)
        # -t ANSIUTF8 creates colored terminal output
        # -t UTF8 creates black and white terminal output
        # We'll use ANSIUTF8 for better visibility
        result = run_command_with_input("qrencode -t ANSIUTF8", input_data=config_text)

        if result.success:
            print(result.stdout)
            return True
        else:
            # Fallback to UTF8 if ANSIUTF8 not supported
            result = run_command_with_input("qrencode -t UTF8", input_data=config_text)
            if result.success:
                print(result.stdout)
                return True
            else:
                logger.error(f"Failed to display QR code: {result.stderr}")
                return False

    except Exception as e:
        logger.exception(f"Error displaying QR code in terminal: {e}")
        return False


def generate_qr_for_config_file(config_file_path: str, output_path: Optional[str] = None) -> bool:
    """Generate a QR code from a WireGuard configuration file.

    Args:
        config_file_path: Path to WireGuard configuration file
        output_path: Optional path to save QR code image

    Returns:
        True if QR code was generated successfully, False otherwise
    """
    try:
        config_path = Path(config_file_path)

        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_file_path}")
            return False

        # Read configuration file
        config_text = config_path.read_text()

        # Generate QR code
        return generate_qr_code(config_text, output_path)

    except Exception as e:
        logger.exception(f"Error generating QR code from file: {e}")
        return False


def verify_qrcode_available() -> bool:
    """Verify that qrencode is available on the system.

    Returns:
        True if qrencode is installed, False otherwise
    """
    return check_command_exists("qrencode")


def install_qrencode() -> bool:
    """Attempt to install qrencode using the system package manager.

    Returns:
        True if installation was successful, False otherwise
    """
    try:
        # Try to detect package manager and install
        if check_command_exists("apt"):
            result = execute_command(["apt", "install", "-y", "qrencode"], sudo=True)
            return result.success
        elif check_command_exists("dnf"):
            result = execute_command(["dnf", "install", "-y", "qrencode"], sudo=True)
            return result.success
        elif check_command_exists("yum"):
            result = execute_command(["yum", "install", "-y", "qrencode"], sudo=True)
            return result.success
        elif check_command_exists("pacman"):
            result = execute_command(["pacman", "-S", "--noconfirm", "qrencode"], sudo=True)
            return result.success
        else:
            logger.error("Could not detect package manager to install qrencode")
            return False

    except Exception as e:
        logger.exception(f"Error installing qrencode: {e}")
        return False


def create_qr_with_metadata(
    config_text: str, client_name: str, output_dir: str
) -> Optional[str]:
    """Create a QR code with metadata and save to a structured directory.

    Args:
        config_text: WireGuard configuration file content
        client_name: Name of the client (used for filename)
        output_dir: Directory to save the QR code

    Returns:
        Path to the generated QR code file, or None on failure
    """
    try:
        output_path_obj = Path(output_dir)
        output_path_obj.mkdir(parents=True, exist_ok=True)

        # Create filename with sanitized client name
        safe_name = "".join(c for c in client_name if c.isalnum() or c in ("-", "_"))
        qr_filename = f"{safe_name}_qrcode.png"
        qr_path = output_path_obj / qr_filename

        # Generate QR code
        if generate_qr_code(config_text, str(qr_path)):
            logger.info(f"QR code created for {client_name}: {qr_path}")
            return str(qr_path)
        else:
            return None

    except Exception as e:
        logger.exception(f"Error creating QR code with metadata: {e}")
        return None
