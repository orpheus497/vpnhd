"""SSH key management utilities for VPNHD."""

from pathlib import Path
from typing import Optional, Tuple

from ..utils.logging import get_logger
from ..utils.constants import SSH_DIR, SSH_KEY_DEFAULT_TYPE, SSH_KEY_RSA_BITS
from ..system.commands import execute_command


logger = get_logger("crypto.ssh")


def generate_ssh_keypair(
    key_path: Path,
    key_type: str = SSH_KEY_DEFAULT_TYPE,
    comment: Optional[str] = None,
    passphrase: str = ""
) -> bool:
    """
    Generate SSH keypair.

    Args:
        key_path: Path for private key (public key will be .pub)
        key_type: Key type (ed25519, rsa, ecdsa)
        comment: Optional comment for key
        passphrase: Optional passphrase (empty string for no passphrase)

    Returns:
        bool: True if keypair generated successfully
    """
    logger.info(f"Generating SSH keypair: {key_path} (type: {key_type})")

    try:
        # Ensure SSH directory exists
        key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Build ssh-keygen command
        cmd = f"ssh-keygen -t {key_type}"

        # Add key size for RSA
        if key_type == "rsa":
            cmd += f" -b {SSH_KEY_RSA_BITS}"

        # Add comment if provided
        if comment:
            cmd += f" -C '{comment}'"
        else:
            # Use default comment (user@hostname)
            import socket
            from ..utils.helpers import get_username
            comment = f"{get_username()}@{socket.gethostname()}"
            cmd += f" -C '{comment}'"

        # Add output file
        cmd += f" -f {key_path}"

        # Add passphrase
        if passphrase:
            cmd += f" -N '{passphrase}'"
        else:
            cmd += " -N ''"

        # Execute command
        result = execute_command(cmd, check=False, capture_output=True)

        if not result.success:
            logger.error(f"Failed to generate SSH keypair: {result.stderr}")
            return False

        # Set proper permissions
        key_path.chmod(0o600)
        public_key_path = Path(str(key_path) + ".pub")
        if public_key_path.exists():
            public_key_path.chmod(0o644)

        logger.info(f"SSH keypair generated successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating SSH keypair: {e}")
        return False


def get_ssh_public_key(private_key_path: Path) -> Optional[str]:
    """
    Get public key from private key file.

    Args:
        private_key_path: Path to private key

    Returns:
        Optional[str]: Public key content or None if failed
    """
    try:
        public_key_path = Path(str(private_key_path) + ".pub")

        if public_key_path.exists():
            return public_key_path.read_text().strip()

        # Try to derive public key from private key
        result = execute_command(
            f"ssh-keygen -y -f {private_key_path}",
            check=False,
            capture_output=True
        )

        if result.success:
            return result.stdout.strip()

        return None

    except Exception as e:
        logger.error(f"Error getting SSH public key: {e}")
        return None


def add_ssh_key_to_authorized_keys(
    public_key: str,
    username: Optional[str] = None,
    remote_host: Optional[str] = None
) -> bool:
    """
    Add SSH public key to authorized_keys.

    Args:
        public_key: Public key content
        username: Username (for remote host)
        remote_host: Remote host (if None, add to local authorized_keys)

    Returns:
        bool: True if key added successfully
    """
    try:
        if remote_host and username:
            # Use ssh-copy-id for remote host
            logger.info(f"Adding SSH key to {username}@{remote_host}")

            # Create temporary key file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pub') as tmp:
                tmp.write(public_key + '\n')
                tmp_path = tmp.name

            try:
                result = execute_command(
                    f"ssh-copy-id -i {tmp_path} {username}@{remote_host}",
                    check=False,
                    capture_output=True
                )

                Path(tmp_path).unlink(missing_ok=True)

                if not result.success:
                    logger.error(f"Failed to copy SSH key: {result.stderr}")
                    return False

                logger.info("SSH key added to remote authorized_keys")
                return True

            finally:
                Path(tmp_path).unlink(missing_ok=True)

        else:
            # Add to local authorized_keys
            authorized_keys_path = SSH_DIR / "authorized_keys"

            logger.info(f"Adding SSH key to local authorized_keys")

            # Ensure .ssh directory exists
            SSH_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

            # Check if key already exists
            if authorized_keys_path.exists():
                existing_keys = authorized_keys_path.read_text()
                if public_key in existing_keys:
                    logger.info("SSH key already in authorized_keys")
                    return True

            # Append key to authorized_keys
            with open(authorized_keys_path, 'a') as f:
                f.write(public_key + '\n')

            # Set proper permissions
            authorized_keys_path.chmod(0o600)

            logger.info("SSH key added to authorized_keys")
            return True

    except Exception as e:
        logger.error(f"Error adding SSH key to authorized_keys: {e}")
        return False


def test_ssh_key_auth(host: str, username: str, private_key_path: Optional[Path] = None) -> bool:
    """
    Test SSH key authentication to a host.

    Args:
        host: Remote host
        username: Username
        private_key_path: Optional path to private key

    Returns:
        bool: True if authentication successful
    """
    logger.info(f"Testing SSH key authentication to {username}@{host}")

    try:
        cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=10"

        if private_key_path:
            cmd += f" -i {private_key_path}"

        cmd += f" {username}@{host} 'exit 0'"

        result = execute_command(cmd, check=False, capture_output=True)

        if result.success:
            logger.info("SSH key authentication successful")
            return True
        else:
            logger.warning(f"SSH key authentication failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error testing SSH key authentication: {e}")
        return False


def remove_ssh_key_from_authorized_keys(public_key: str) -> bool:
    """
    Remove SSH public key from authorized_keys.

    Args:
        public_key: Public key content to remove

    Returns:
        bool: True if key removed successfully
    """
    try:
        authorized_keys_path = SSH_DIR / "authorized_keys"

        if not authorized_keys_path.exists():
            logger.warning("authorized_keys file does not exist")
            return True

        # Read current keys
        lines = authorized_keys_path.read_text().splitlines()

        # Filter out the key to remove
        new_lines = [line for line in lines if public_key not in line]

        if len(new_lines) == len(lines):
            logger.warning("SSH key not found in authorized_keys")
            return True

        # Write back
        authorized_keys_path.write_text('\n'.join(new_lines) + '\n')

        logger.info("SSH key removed from authorized_keys")
        return True

    except Exception as e:
        logger.error(f"Error removing SSH key: {e}")
        return False


def get_ssh_key_fingerprint(key_path: Path) -> Optional[str]:
    """
    Get fingerprint of an SSH key.

    Args:
        key_path: Path to SSH key file

    Returns:
        Optional[str]: Key fingerprint or None if failed
    """
    try:
        result = execute_command(
            f"ssh-keygen -lf {key_path}",
            check=False,
            capture_output=True
        )

        if result.success:
            return result.stdout.strip()

        return None

    except Exception as e:
        logger.error(f"Error getting SSH key fingerprint: {e}")
        return None


def check_ssh_key_exists(key_path: Path) -> bool:
    """
    Check if SSH key exists.

    Args:
        key_path: Path to private key

    Returns:
        bool: True if both private and public key exist
    """
    public_key_path = Path(str(key_path) + ".pub")

    return key_path.exists() and public_key_path.exists()


def list_ssh_keys(ssh_dir: Path = SSH_DIR) -> list:
    """
    List all SSH keys in a directory.

    Args:
        ssh_dir: SSH directory path (default: ~/.ssh)

    Returns:
        list: List of SSH key file paths
    """
    try:
        if not ssh_dir.exists():
            return []

        keys = []

        # Look for common SSH key files
        for pattern in ["id_*", "*_rsa", "*_ed25519", "*_ecdsa"]:
            for key_file in ssh_dir.glob(pattern):
                # Exclude .pub files
                if not key_file.name.endswith('.pub'):
                    keys.append(key_file)

        return keys

    except Exception as e:
        logger.error(f"Error listing SSH keys: {e}")
        return []
