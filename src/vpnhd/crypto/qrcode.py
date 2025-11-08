"""QR code generation for WireGuard configuration.

This module handles generating QR codes from WireGuard client configurations,
making it easy to configure mobile devices by scanning.
"""

from pathlib import Path
from typing import Optional
import io

try:
    import qrcode
    import qrcode.image.svg
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

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
    if not QRCODE_AVAILABLE:
        logger.error(
            "qrcode library is not installed. Install with: "
            "pip install qrcode[pil]"
        )
        return False

    try:
        if output_path:
            # Generate QR code and save to file
            return save_qr_code(config_text, output_path)
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
    if not QRCODE_AVAILABLE:
        logger.error("qrcode library is not installed")
        return False

    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add data
        qr.add_data(config_text)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image
        img.save(output_path)
        logger.info(f"QR code saved to {output_path}")
        return True

    except Exception as e:
        logger.exception(f"Error saving QR code: {e}")
        return False


def display_qr_terminal(config_text: str) -> bool:
    """Display a QR code in the terminal using ASCII art.

    Args:
        config_text: WireGuard configuration file content

    Returns:
        True if QR code was displayed successfully, False otherwise
    """
    if not QRCODE_AVAILABLE:
        logger.error("qrcode library is not installed")
        return False

    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )

        # Add data
        qr.add_data(config_text)
        qr.make(fit=True)

        # Print to terminal using ASCII characters
        # Use white/black blocks for better visibility
        qr.print_ascii(invert=True)

        return True

    except Exception as e:
        logger.exception(f"Error displaying QR code in terminal: {e}")
        return False


def display_qr_terminal_tty(config_text: str) -> bool:
    """Display a QR code in the terminal using Unicode blocks.

    This version uses Unicode block characters for better visual quality.

    Args:
        config_text: WireGuard configuration file content

    Returns:
        True if QR code was displayed successfully, False otherwise
    """
    if not QRCODE_AVAILABLE:
        logger.error("qrcode library is not installed")
        return False

    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )

        # Add data
        qr.add_data(config_text)
        qr.make(fit=True)

        # Print using Unicode block characters
        qr.print_tty()

        return True

    except Exception as e:
        logger.exception(f"Error displaying QR code with TTY: {e}")
        # Fallback to ASCII
        return display_qr_terminal(config_text)


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
    """Verify that qrcode library is available.

    Returns:
        True if qrcode is installed, False otherwise
    """
    return QRCODE_AVAILABLE


def install_qrencode() -> bool:
    """Attempt to install qrcode library using pip.

    Note: This function is deprecated and kept for backwards compatibility.
    The qrcode library should be installed via requirements.txt.

    Returns:
        False (manual installation required)
    """
    logger.warning(
        "install_qrencode() is deprecated. "
        "Please install qrcode library via: pip install qrcode[pil]"
    )
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


def generate_qr_svg(config_text: str, output_path: str) -> bool:
    """Generate a QR code as an SVG image.

    Args:
        config_text: WireGuard configuration file content
        output_path: Path to save QR code SVG file

    Returns:
        True if QR code was saved successfully, False otherwise
    """
    if not QRCODE_AVAILABLE:
        logger.error("qrcode library is not installed")
        return False

    try:
        # Create QR code instance with SVG factory
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            image_factory=qrcode.image.svg.SvgPathImage
        )

        # Add data
        qr.add_data(config_text)
        qr.make(fit=True)

        # Create SVG image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save SVG
        with open(output_path, 'wb') as f:
            img.save(f)

        logger.info(f"QR code SVG saved to {output_path}")
        return True

    except Exception as e:
        logger.exception(f"Error generating SVG QR code: {e}")
        return False
