"""SSH daemon configuration management.

This module handles programmatic modification of SSH daemon configuration,
including disabling password authentication and enabling key-based authentication.
"""

from pathlib import Path
from typing import Optional, Dict, List
import re

from .commands import execute_command
from .files import FileManager
from .services import ServiceManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SSHConfigManager:
    """Manages SSH daemon configuration."""

    def __init__(self, config_path: str = "/etc/ssh/sshd_config"):
        """Initialize SSH config manager.

        Args:
            config_path: Path to sshd_config file
        """
        self.config_path = Path(config_path)
        self.file_manager = FileManager()
        self.service_manager = ServiceManager()

    def disable_password_auth(self) -> bool:
        """Disable SSH password authentication.

        This sets PasswordAuthentication to 'no' in sshd_config and restarts
        the SSH daemon. A backup of the original configuration is created.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Disabling SSH password authentication")

            # Backup current configuration
            backup_path = self.file_manager.backup_file(str(self.config_path))
            if not backup_path:
                logger.error("Failed to backup sshd_config")
                return False

            logger.info(f"Backed up sshd_config to {backup_path}")

            # Set PasswordAuthentication to no
            if not self.set_ssh_config_option("PasswordAuthentication", "no"):
                logger.error("Failed to set PasswordAuthentication")
                return False

            # Ensure PubkeyAuthentication is enabled
            if not self.set_ssh_config_option("PubkeyAuthentication", "yes"):
                logger.error("Failed to set PubkeyAuthentication")
                return False

            # Test configuration before restarting
            if not self.test_ssh_config():
                logger.error("SSH configuration test failed, restoring backup")
                self.file_manager.restore_backup(str(self.config_path), str(backup_path))
                return False

            # Restart SSH daemon
            if not self.restart_ssh_service():
                logger.error("Failed to restart SSH service, restoring backup")
                self.file_manager.restore_backup(str(self.config_path), str(backup_path))
                return False

            logger.info("SSH password authentication disabled successfully")
            return True

        except Exception as e:
            logger.exception(f"Error disabling password authentication: {e}")
            return False

    def enable_pubkey_auth(self) -> bool:
        """Enable SSH public key authentication.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Enabling SSH public key authentication")

            # Backup current configuration
            backup_path = self.file_manager.backup_file(str(self.config_path))
            if not backup_path:
                logger.error("Failed to backup sshd_config")
                return False

            # Set PubkeyAuthentication to yes
            if not self.set_ssh_config_option("PubkeyAuthentication", "yes"):
                logger.error("Failed to set PubkeyAuthentication")
                return False

            # Test and restart
            if not self.test_ssh_config():
                logger.error("SSH configuration test failed, restoring backup")
                self.file_manager.restore_backup(str(self.config_path), str(backup_path))
                return False

            if not self.restart_ssh_service():
                logger.error("Failed to restart SSH service, restoring backup")
                self.file_manager.restore_backup(str(self.config_path), str(backup_path))
                return False

            logger.info("SSH public key authentication enabled successfully")
            return True

        except Exception as e:
            logger.exception(f"Error enabling public key authentication: {e}")
            return False

    def set_ssh_config_option(self, option: str, value: str) -> bool:
        """Set an SSH configuration option.

        This method handles both adding new options and modifying existing ones,
        including commented-out options.

        Args:
            option: Configuration option name (e.g., "PasswordAuthentication")
            value: Value to set (e.g., "no", "yes", "22")

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config_path.exists():
                logger.error(f"SSH config not found: {self.config_path}")
                return False

            # Read current configuration
            lines = self.config_path.read_text().split("\n")
            modified = False
            new_lines = []

            # Pattern to match the option (including commented versions)
            option_pattern = re.compile(rf"^\s*#?\s*{re.escape(option)}\s+", re.IGNORECASE)

            for line in lines:
                if option_pattern.match(line):
                    # Replace this line with the new value
                    new_lines.append(f"{option} {value}")
                    modified = True
                else:
                    new_lines.append(line)

            # If option was not found, add it at the end
            if not modified:
                new_lines.append(f"\n# Added by VPNHD")
                new_lines.append(f"{option} {value}")

            # Write the modified configuration
            new_config = "\n".join(new_lines)
            self.config_path.write_text(new_config)

            logger.info(f"Set {option} = {value} in sshd_config")
            return True

        except Exception as e:
            logger.exception(f"Error setting SSH config option: {e}")
            return False

    def get_ssh_config_option(self, option: str) -> Optional[str]:
        """Get the current value of an SSH configuration option.

        Args:
            option: Configuration option name

        Returns:
            Current value of the option, or None if not found
        """
        try:
            if not self.config_path.exists():
                return None

            lines = self.config_path.read_text().split("\n")

            # Pattern to match the option (excluding commented lines)
            option_pattern = re.compile(rf"^\s*{re.escape(option)}\s+(.+)", re.IGNORECASE)

            for line in lines:
                match = option_pattern.match(line)
                if match:
                    return match.group(1).strip()

            return None

        except Exception as e:
            logger.exception(f"Error getting SSH config option: {e}")
            return None

    def test_ssh_config(self) -> bool:
        """Test SSH configuration for syntax errors.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            result = execute_command("sshd -t")
            if result.success:
                logger.info("SSH configuration test passed")
                return True
            else:
                logger.error(f"SSH configuration test failed: {result.stderr}")
                return False

        except Exception as e:
            logger.exception(f"Error testing SSH configuration: {e}")
            return False

    def restart_ssh_service(self) -> bool:
        """Restart SSH daemon safely.

        Returns:
            True if restart was successful, False otherwise
        """
        try:
            # Try different service names (depends on distribution)
            service_names = ["sshd", "ssh"]

            for service_name in service_names:
                # Check if service exists using systemctl status
                result = execute_command(
                    ["systemctl", "status", service_name],
                    check=False,
                    capture_output=True
                )
                # systemctl status returns 0-4 for loaded services, >4 for not found
                if result.exit_code <= 4:
                    # Restart the service
                    if self.service_manager.restart(service_name):
                        logger.info(f"SSH service ({service_name}) restarted successfully")
                        return True

            logger.error("Could not find SSH service to restart")
            return False

        except Exception as e:
            logger.exception(f"Error restarting SSH service: {e}")
            return False

    def backup_ssh_config(self) -> Optional[str]:
        """Create a backup of the current SSH configuration.

        Returns:
            Path to backup file, or None on failure
        """
        return self.file_manager.backup_file(str(self.config_path))

    def restore_ssh_config(self, backup_path: str) -> bool:
        """Restore SSH configuration from a backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if restore was successful, False otherwise
        """
        try:
            if not Path(backup_path).exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            if self.file_manager.restore_backup(str(self.config_path), backup_path):
                # Test the restored configuration
                if not self.test_ssh_config():
                    logger.error("Restored SSH configuration is invalid")
                    return False

                # Restart SSH service
                if not self.restart_ssh_service():
                    logger.error("Failed to restart SSH service after restore")
                    return False

                logger.info("SSH configuration restored successfully")
                return True
            else:
                logger.error("Failed to restore SSH configuration")
                return False

        except Exception as e:
            logger.exception(f"Error restoring SSH configuration: {e}")
            return False

    def get_all_options(self) -> Dict[str, str]:
        """Get all currently set SSH configuration options.

        Returns:
            Dictionary of option names and values
        """
        options = {}

        try:
            if not self.config_path.exists():
                return options

            lines = self.config_path.read_text().split("\n")

            # Pattern to match any option (excluding comments)
            option_pattern = re.compile(r"^\s*(\w+)\s+(.+)")

            for line in lines:
                match = option_pattern.match(line)
                if match:
                    option_name = match.group(1)
                    option_value = match.group(2).strip()
                    options[option_name] = option_value

        except Exception as e:
            logger.exception(f"Error getting all SSH options: {e}")

        return options

    def disable_root_login(self) -> bool:
        """Disable SSH root login.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Disabling SSH root login")
        return self.set_ssh_config_option("PermitRootLogin", "no")

    def set_port(self, port: int) -> bool:
        """Set SSH port.

        Args:
            port: Port number (1-65535)

        Returns:
            True if successful, False otherwise
        """
        if not (1 <= port <= 65535):
            logger.error(f"Invalid port number: {port}")
            return False

        logger.info(f"Setting SSH port to {port}")
        return self.set_ssh_config_option("Port", str(port))
