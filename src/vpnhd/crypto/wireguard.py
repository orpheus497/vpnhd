"""WireGuard key management utilities for VPNHD."""

from pathlib import Path
from typing import Optional, Tuple

from ..system.commands import execute_command, get_command_output, run_command_with_input
from ..utils.constants import PERM_PRIVATE_KEY, WG_KEY_LENGTH
from ..utils.logging import get_logger

logger = get_logger("crypto.wireguard")


def generate_keypair() -> Tuple[str, str]:
    """
    Generate WireGuard private/public key pair.

    Returns:
        Tuple[str, str]: (private_key, public_key)
    """
    logger.info("Generating WireGuard keypair")

    try:
        # Generate private key
        private_result = execute_command("wg genkey", check=False, capture_output=True)

        if not private_result.success:
            raise Exception("Failed to generate private key")

        private_key = private_result.stdout.strip()

        # Derive public key from private key
        public_key = derive_public_key(private_key)

        if not public_key:
            raise Exception("Failed to derive public key")

        logger.debug(f"Generated keypair (public key: {public_key})")

        return private_key, public_key

    except Exception as e:
        logger.error(f"Error generating keypair: {e}")
        raise


def generate_preshared_key() -> str:
    """
    Generate WireGuard preshared key.

    Returns:
        str: Preshared key
    """
    logger.info("Generating WireGuard preshared key")

    try:
        result = execute_command("wg genpsk", check=False, capture_output=True)

        if not result.success:
            raise Exception("Failed to generate preshared key")

        psk = result.stdout.strip()
        logger.debug("Generated preshared key")

        return psk

    except Exception as e:
        logger.error(f"Error generating preshared key: {e}")
        raise


def save_private_key(key: str, path: Path, mode: int = PERM_PRIVATE_KEY) -> bool:
    """
    Save private key to file with secure permissions.

    Args:
        key: Private key content
        path: File path
        mode: File permissions (default: 0600)

    Returns:
        bool: True if saved successfully
    """
    logger.info(f"Saving private key to {path}")

    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Write key to file
        if path.exists():
            logger.warning(f"Overwriting existing key file: {path}")

        # Write with secure permissions
        path.write_text(key + "\n")
        path.chmod(mode)

        logger.info(f"Private key saved with permissions {oct(mode)}")
        return True

    except Exception as e:
        logger.error(f"Error saving private key: {e}")
        return False


def load_private_key(path: Path) -> Optional[str]:
    """
    Load private key from file.

    Args:
        path: File path

    Returns:
        Optional[str]: Private key or None if failed
    """
    logger.debug(f"Loading private key from {path}")

    try:
        if not path.exists():
            logger.error(f"Private key file not found: {path}")
            return None

        key = path.read_text().strip()

        # Validate key format
        if not validate_key(key, "private"):
            logger.error("Invalid private key format")
            return None

        return key

    except Exception as e:
        logger.error(f"Error loading private key: {e}")
        return None


def derive_public_key(private_key: str) -> Optional[str]:
    """
    Derive public key from private key.

    Args:
        private_key: Private key

    Returns:
        Optional[str]: Public key or None if failed
    """
    try:
        # Use wg pubkey command to derive public key via stdin
        # (prevents key exposure in process list)
        result = run_command_with_input(
            ["wg", "pubkey"], input_data=private_key + "\n", check=False, capture_output=True
        )

        if not result.success:
            logger.error("Failed to derive public key")
            return None

        public_key = result.stdout.strip()

        # Validate
        if not validate_key(public_key, "public"):
            logger.error("Derived public key is invalid")
            return None

        return public_key

    except Exception as e:
        logger.error(f"Error deriving public key: {e}")
        return None


def validate_key(key: str, key_type: str = "private") -> bool:
    """
    Validate WireGuard key format.

    Args:
        key: Key to validate
        key_type: "private" or "public"

    Returns:
        bool: True if valid
    """
    if not key:
        return False

    # WireGuard keys are base64 encoded 32-byte values (44 characters with padding)
    if len(key) != WG_KEY_LENGTH:
        logger.debug(f"Invalid key length: {len(key)} (expected {WG_KEY_LENGTH})")
        return False

    # Check if it's valid base64
    import base64

    try:
        decoded = base64.b64decode(key)
        if len(decoded) != 32:
            logger.debug(f"Invalid decoded key length: {len(decoded)}")
            return False

        return True

    except Exception as e:
        logger.debug(f"Key validation failed: {e}")
        return False


def get_public_key_from_private_file(private_key_path: Path) -> Optional[str]:
    """
    Get public key from private key file.

    Args:
        private_key_path: Path to private key file

    Returns:
        Optional[str]: Public key or None if failed
    """
    private_key = load_private_key(private_key_path)

    if private_key:
        return derive_public_key(private_key)

    return None


def save_keypair(
    private_key: str, public_key: str, private_path: Path, public_path: Optional[Path] = None
) -> bool:
    """
    Save both private and public keys.

    Args:
        private_key: Private key
        public_key: Public key
        private_path: Path for private key
        public_path: Optional path for public key

    Returns:
        bool: True if both saved successfully
    """
    # Save private key
    if not save_private_key(private_key, private_path):
        return False

    # Save public key if path provided
    if public_path:
        try:
            public_path.write_text(public_key + "\n")
            public_path.chmod(0o644)
            logger.info(f"Public key saved to {public_path}")
        except Exception as e:
            logger.error(f"Error saving public key: {e}")
            return False

    return True


def generate_and_save_keypair(
    private_path: Path, public_path: Optional[Path] = None
) -> Optional[Tuple[str, str]]:
    """
    Generate and save a new keypair.

    Args:
        private_path: Path for private key
        public_path: Optional path for public key

    Returns:
        Optional[Tuple[str, str]]: (private_key, public_key) or None if failed
    """
    try:
        # Generate keypair
        private_key, public_key = generate_keypair()

        # Save keys
        if save_keypair(private_key, public_key, private_path, public_path):
            return private_key, public_key

        return None

    except Exception as e:
        logger.error(f"Error generating and saving keypair: {e}")
        return None
