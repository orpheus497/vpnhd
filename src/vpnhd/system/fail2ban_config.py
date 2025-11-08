"""fail2ban intrusion prevention configuration.

This module handles creation and management of fail2ban jail configurations
for SSH and WireGuard protection.
"""

from pathlib import Path
from typing import Optional, List, Dict
from jinja2 import Template

from .commands import execute_command
from .files import FileManager
from .services import ServiceManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class Fail2banConfigManager:
    """Manages fail2ban configuration and jails."""

    def __init__(self, jail_dir: str = "/etc/fail2ban/jail.d"):
        """Initialize fail2ban config manager.

        Args:
            jail_dir: Directory for jail configuration files
        """
        self.jail_dir = Path(jail_dir)
        self.file_manager = FileManager()
        self.service_manager = ServiceManager()

    def create_ssh_jail(
        self,
        ban_time: int = 3600,
        find_time: int = 600,
        max_retry: int = 5,
        port: int = 22,
    ) -> bool:
        """Create a custom SSH jail configuration.

        Args:
            ban_time: Time in seconds an IP is banned (default: 3600 = 1 hour)
            find_time: Time window in seconds to count retries (default: 600 = 10 min)
            max_retry: Maximum number of failures before ban (default: 5)
            port: SSH port to protect (default: 22)

        Returns:
            True if jail was created successfully, False otherwise
        """
        try:
            logger.info("Creating fail2ban SSH jail")

            # Ensure jail directory exists
            self.jail_dir.mkdir(parents=True, exist_ok=True)

            # Create jail configuration
            jail_config = f"""# SSH jail configuration - Created by VPNHD
[sshd]
enabled = true
port = {port}
filter = sshd
logpath = /var/log/auth.log
maxretry = {max_retry}
findtime = {find_time}
bantime = {ban_time}
backend = systemd
"""

            # Write jail file
            jail_path = self.jail_dir / "sshd.local"
            jail_path.write_text(jail_config)

            logger.info(f"Created SSH jail configuration: {jail_path}")

            # Reload fail2ban
            if not self.reload_fail2ban():
                logger.error("Failed to reload fail2ban")
                return False

            return True

        except Exception as e:
            logger.exception(f"Error creating SSH jail: {e}")
            return False

    def create_wireguard_jail(
        self, ban_time: int = 7200, find_time: int = 600, max_retry: int = 3, port: int = 51820
    ) -> bool:
        """Create a custom WireGuard jail configuration.

        This protects against UDP flooding on the WireGuard port.

        Args:
            ban_time: Time in seconds an IP is banned (default: 7200 = 2 hours)
            find_time: Time window in seconds to count retries (default: 600 = 10 min)
            max_retry: Maximum number of failures before ban (default: 3)
            port: WireGuard port to protect (default: 51820)

        Returns:
            True if jail was created successfully, False otherwise
        """
        try:
            logger.info("Creating fail2ban WireGuard jail")

            # Ensure jail directory exists
            self.jail_dir.mkdir(parents=True, exist_ok=True)

            # First, create the filter file
            filter_dir = Path("/etc/fail2ban/filter.d")
            filter_dir.mkdir(parents=True, exist_ok=True)

            # WireGuard filter configuration
            filter_config = """# WireGuard filter - Created by VPNHD
[Definition]
failregex = .*kernel:.*wireguard.*: Invalid handshake initiation from <HOST>.*
            .*kernel:.*wireguard.*: Handshake for peer .* did not complete after .* seconds, retrying from <HOST>
ignoreregex =
"""

            filter_path = filter_dir / "wireguard.conf"
            filter_path.write_text(filter_config)

            logger.info(f"Created WireGuard filter: {filter_path}")

            # Create jail configuration
            jail_config = f"""# WireGuard jail configuration - Created by VPNHD
[wireguard]
enabled = true
port = {port}
protocol = udp
filter = wireguard
logpath = /var/log/kern.log
maxretry = {max_retry}
findtime = {find_time}
bantime = {ban_time}
backend = systemd
"""

            jail_path = self.jail_dir / "wireguard.local"
            jail_path.write_text(jail_config)

            logger.info(f"Created WireGuard jail configuration: {jail_path}")

            # Reload fail2ban
            if not self.reload_fail2ban():
                logger.error("Failed to reload fail2ban")
                return False

            return True

        except Exception as e:
            logger.exception(f"Error creating WireGuard jail: {e}")
            return False

    def configure_ban_settings(self, ban_time: int, find_time: int, max_retry: int) -> Dict[str, int]:
        """Configure default ban settings.

        Args:
            ban_time: Default ban time in seconds
            find_time: Default find time in seconds
            max_retry: Default maximum retries

        Returns:
            Dictionary with the configured settings
        """
        return {"ban_time": ban_time, "find_time": find_time, "max_retry": max_retry}

    def enable_jails(self, jail_names: List[str]) -> bool:
        """Enable specific jails.

        Args:
            jail_names: List of jail names to enable (e.g., ["sshd", "wireguard"])

        Returns:
            True if all jails were enabled successfully, False otherwise
        """
        try:
            for jail_name in jail_names:
                jail_path = self.jail_dir / f"{jail_name}.local"

                if not jail_path.exists():
                    logger.warning(f"Jail file not found: {jail_path}")
                    continue

                # Read current configuration
                config = jail_path.read_text()

                # Update enabled status
                if "enabled = false" in config:
                    config = config.replace("enabled = false", "enabled = true")
                    jail_path.write_text(config)
                    logger.info(f"Enabled jail: {jail_name}")

            # Reload fail2ban to apply changes
            return self.reload_fail2ban()

        except Exception as e:
            logger.exception(f"Error enabling jails: {e}")
            return False

    def disable_jails(self, jail_names: List[str]) -> bool:
        """Disable specific jails.

        Args:
            jail_names: List of jail names to disable

        Returns:
            True if all jails were disabled successfully, False otherwise
        """
        try:
            for jail_name in jail_names:
                jail_path = self.jail_dir / f"{jail_name}.local"

                if not jail_path.exists():
                    logger.warning(f"Jail file not found: {jail_path}")
                    continue

                # Read current configuration
                config = jail_path.read_text()

                # Update enabled status
                if "enabled = true" in config:
                    config = config.replace("enabled = true", "enabled = false")
                    jail_path.write_text(config)
                    logger.info(f"Disabled jail: {jail_name}")

            # Reload fail2ban to apply changes
            return self.reload_fail2ban()

        except Exception as e:
            logger.exception(f"Error disabling jails: {e}")
            return False

    def get_banned_ips(self, jail_name: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of currently banned IPs.

        Args:
            jail_name: Optional specific jail to check (checks all jails if None)

        Returns:
            List of dictionaries with jail name and banned IP information
        """
        banned_ips = []

        try:
            if jail_name:
                # Get banned IPs for specific jail
                result = execute_command(f"fail2ban-client status {jail_name}")
                if result.success:
                    banned_ips.extend(self._parse_banned_ips(result.stdout, jail_name))
            else:
                # Get all active jails
                result = execute_command("fail2ban-client status")
                if result.success:
                    # Extract jail names from status output
                    import re

                    jail_match = re.search(r"Jail list:\s+(.+)", result.stdout)
                    if jail_match:
                        jails = [j.strip() for j in jail_match.group(1).split(",")]

                        # Get banned IPs for each jail
                        for jail in jails:
                            jail_result = execute_command(f"fail2ban-client status {jail}")
                            if jail_result.success:
                                banned_ips.extend(
                                    self._parse_banned_ips(jail_result.stdout, jail)
                                )

        except Exception as e:
            logger.exception(f"Error getting banned IPs: {e}")

        return banned_ips

    def _parse_banned_ips(self, status_output: str, jail_name: str) -> List[Dict[str, str]]:
        """Parse fail2ban status output to extract banned IPs.

        Args:
            status_output: Output from fail2ban-client status command
            jail_name: Name of the jail

        Returns:
            List of dictionaries with IP information
        """
        banned_ips = []

        try:
            import re

            # Look for "Currently banned:" line
            banned_match = re.search(r"Currently banned:\s+(\d+)", status_output)
            if banned_match and int(banned_match.group(1)) > 0:
                # Extract IP list
                ip_match = re.search(r"Banned IP list:\s+(.+)", status_output)
                if ip_match:
                    ips = [ip.strip() for ip in ip_match.group(1).split()]
                    for ip in ips:
                        banned_ips.append({"jail": jail_name, "ip": ip})

        except Exception as e:
            logger.exception(f"Error parsing banned IPs: {e}")

        return banned_ips

    def unban_ip(self, ip: str, jail_name: Optional[str] = None) -> bool:
        """Unban a specific IP address.

        Args:
            ip: IP address to unban
            jail_name: Optional specific jail (unbans from all jails if None)

        Returns:
            True if IP was unbanned successfully, False otherwise
        """
        try:
            if jail_name:
                result = execute_command(f"fail2ban-client set {jail_name} unbanip {ip}")
                if result.success:
                    logger.info(f"Unbanned {ip} from {jail_name}")
                    return True
                else:
                    logger.error(f"Failed to unban {ip} from {jail_name}")
                    return False
            else:
                # Unban from all jails
                # Get list of active jails
                result = execute_command("fail2ban-client status")
                if result.success:
                    import re

                    jail_match = re.search(r"Jail list:\s+(.+)", result.stdout)
                    if jail_match:
                        jails = [j.strip() for j in jail_match.group(1).split(",")]

                        success = True
                        for jail in jails:
                            result = execute_command(f"fail2ban-client set {jail} unbanip {ip}")
                            if result.success:
                                logger.info(f"Unbanned {ip} from {jail}")
                            else:
                                success = False

                        return success

                return False

        except Exception as e:
            logger.exception(f"Error unbanning IP: {e}")
            return False

    def reload_fail2ban(self) -> bool:
        """Reload fail2ban configuration.

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            result = execute_command("fail2ban-client reload")
            if result.success:
                logger.info("fail2ban reloaded successfully")
                return True
            else:
                logger.error(f"Failed to reload fail2ban: {result.stderr}")
                return False

        except Exception as e:
            logger.exception(f"Error reloading fail2ban: {e}")
            return False

    def is_fail2ban_running(self) -> bool:
        """Check if fail2ban service is running.

        Returns:
            True if running, False otherwise
        """
        return self.service_manager.get_service_status("fail2ban") == "active"

    def get_jail_status(self, jail_name: str) -> Optional[Dict[str, any]]:
        """Get detailed status of a specific jail.

        Args:
            jail_name: Name of the jail

        Returns:
            Dictionary with jail status information, or None on error
        """
        try:
            result = execute_command(f"fail2ban-client status {jail_name}")
            if not result.success:
                return None

            import re

            status = {"jail_name": jail_name}

            # Parse status output
            filter_match = re.search(r"Filter\s*:\s*(.+)", result.stdout)
            if filter_match:
                status["filter"] = filter_match.group(1).strip()

            currently_failed = re.search(r"Currently failed:\s+(\d+)", result.stdout)
            if currently_failed:
                status["currently_failed"] = int(currently_failed.group(1))

            total_failed = re.search(r"Total failed:\s+(\d+)", result.stdout)
            if total_failed:
                status["total_failed"] = int(total_failed.group(1))

            currently_banned = re.search(r"Currently banned:\s+(\d+)", result.stdout)
            if currently_banned:
                status["currently_banned"] = int(currently_banned.group(1))

            total_banned = re.search(r"Total banned:\s+(\d+)", result.stdout)
            if total_banned:
                status["total_banned"] = int(total_banned.group(1))

            return status

        except Exception as e:
            logger.exception(f"Error getting jail status: {e}")
            return None
