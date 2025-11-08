"""WireGuard server configuration management.

This module handles adding/removing peers to the WireGuard server configuration
and reloading the service without disconnecting existing peers.
"""

from pathlib import Path
from typing import Optional, List, Dict
import re

from ..system.commands import execute_command, run_command_with_input
from ..system.files import FileManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ServerConfigManager:
    """Manages WireGuard server configuration and peer management."""

    def __init__(self, config_path: str = "/etc/wireguard/wg0.conf"):
        """Initialize server config manager.

        Args:
            config_path: Path to WireGuard server configuration file
        """
        self.config_path = Path(config_path)
        self.file_manager = FileManager()

    def add_peer_to_server(
        self,
        client_name: str,
        public_key: str,
        vpn_ip: str,
        preshared_key: Optional[str] = None,
        allowed_ips: Optional[str] = None,
    ) -> bool:
        """Add a new peer to the WireGuard server configuration.

        Args:
            client_name: Descriptive name for the client
            public_key: Client's WireGuard public key
            vpn_ip: Client's VPN IP address (e.g., "10.66.66.2")
            preshared_key: Optional preshared key for additional security
            allowed_ips: Optional custom allowed IPs (defaults to vpn_ip/32)

        Returns:
            True if peer was added successfully, False otherwise
        """
        try:
            # Verify config file exists
            if not self.config_path.exists():
                logger.error(f"WireGuard config not found: {self.config_path}")
                return False

            # Check if peer already exists
            if self.verify_peer_exists(public_key):
                logger.warning(f"Peer with public key {public_key[:20]}... already exists")
                return False

            # Read current configuration
            current_config = self.config_path.read_text()

            # Set default allowed IPs if not provided
            if allowed_ips is None:
                allowed_ips = f"{vpn_ip}/32"

            # Build peer section
            peer_section = f"\n# {client_name}\n"
            peer_section += "[Peer]\n"
            peer_section += f"PublicKey = {public_key}\n"
            if preshared_key:
                peer_section += f"PresharedKey = {preshared_key}\n"
            peer_section += f"AllowedIPs = {allowed_ips}\n"

            # Backup current config
            backup_path = self.file_manager.backup_file(str(self.config_path))
            if not backup_path:
                logger.error("Failed to backup server configuration")
                return False

            # Append peer section
            new_config = current_config.rstrip() + "\n" + peer_section

            # Write new configuration
            self.config_path.write_text(new_config)
            logger.info(f"Added peer {client_name} to server configuration")

            # Reload WireGuard to apply changes
            if not self.reload_wireguard_server():
                logger.error("Failed to reload WireGuard server")
                # Restore backup on failure
                self.file_manager.restore_backup(str(self.config_path), str(backup_path))
                return False

            return True

        except Exception as e:
            logger.exception(f"Error adding peer to server: {e}")
            return False

    def remove_peer_from_server(self, public_key: str) -> bool:
        """Remove a peer from the WireGuard server configuration.

        Args:
            public_key: Client's WireGuard public key to remove

        Returns:
            True if peer was removed successfully, False otherwise
        """
        try:
            if not self.config_path.exists():
                logger.error(f"WireGuard config not found: {self.config_path}")
                return False

            # Read current configuration
            current_config = self.config_path.read_text()

            # Pattern to match peer section with this public key
            # Match comment, [Peer], and all following keys until next section or EOF
            peer_pattern = re.compile(
                rf"(#[^\n]*\n)?\[Peer\]\nPublicKey\s*=\s*{re.escape(public_key)}\n"
                rf"(?:(?:PresharedKey|AllowedIPs)\s*=\s*[^\n]+\n)*",
                re.MULTILINE,
            )

            # Remove the peer section
            new_config = peer_pattern.sub("", current_config)

            # Clean up multiple consecutive blank lines
            new_config = re.sub(r"\n{3,}", "\n\n", new_config)

            # Backup and write
            backup_path = self.file_manager.backup_file(str(self.config_path))
            if not backup_path:
                logger.error("Failed to backup server configuration")
                return False

            self.config_path.write_text(new_config)
            logger.info(f"Removed peer with public key {public_key[:20]}...")

            # Reload WireGuard
            if not self.reload_wireguard_server():
                logger.error("Failed to reload WireGuard server")
                self.file_manager.restore_backup(str(self.config_path), str(backup_path))
                return False

            return True

        except Exception as e:
            logger.exception(f"Error removing peer from server: {e}")
            return False

    def reload_wireguard_server(self) -> bool:
        """Reload WireGuard server configuration without disconnecting peers.

        Uses `wg syncconf` to apply configuration changes without interrupting
        existing connections. Avoids process substitution by using stdin.

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            # First, get the stripped configuration
            strip_result = execute_command(
                ["wg-quick", "strip", "wg0"],
                sudo=True,
                capture_output=True
            )

            if strip_result.success:
                # Apply the stripped config via stdin
                sync_result = run_command_with_input(
                    ["wg", "syncconf", "wg0", "/dev/stdin"],
                    input_data=strip_result.stdout,
                    sudo=True
                )

                if sync_result.success:
                    logger.info("WireGuard server configuration reloaded (syncconf)")
                    return True

            # If syncconf fails, try restarting the service
            logger.warning("syncconf failed, attempting service restart")
            result = execute_command(["systemctl", "restart", "wg-quick@wg0"], sudo=True)

            if result.success:
                logger.info("WireGuard server restarted successfully")
                return True

            logger.error(f"Failed to reload WireGuard: {result.stderr}")
            return False

        except Exception as e:
            logger.exception(f"Error reloading WireGuard server: {e}")
            return False

    def get_server_peers(self) -> List[Dict[str, str]]:
        """Get list of all configured peers from the server configuration.

        Returns:
            List of dictionaries containing peer information:
            [{"public_key": "...", "allowed_ips": "..."}, ...]
        """
        peers = []

        try:
            if not self.config_path.exists():
                return peers

            current_config = self.config_path.read_text()

            # Find all [Peer] sections
            peer_sections = re.split(r"\[Peer\]", current_config)[1:]  # Skip [Interface]

            for section in peer_sections:
                peer_info = {}

                # Extract PublicKey
                pub_key_match = re.search(r"PublicKey\s*=\s*([^\s]+)", section)
                if pub_key_match:
                    peer_info["public_key"] = pub_key_match.group(1)

                # Extract AllowedIPs
                allowed_ips_match = re.search(r"AllowedIPs\s*=\s*([^\n]+)", section)
                if allowed_ips_match:
                    peer_info["allowed_ips"] = allowed_ips_match.group(1).strip()

                # Extract PresharedKey if present
                psk_match = re.search(r"PresharedKey\s*=\s*([^\s]+)", section)
                if psk_match:
                    peer_info["preshared_key"] = psk_match.group(1)

                if peer_info:
                    peers.append(peer_info)

        except Exception as e:
            logger.exception(f"Error getting server peers: {e}")

        return peers

    def verify_peer_exists(self, public_key: str) -> bool:
        """Check if a peer with the given public key already exists.

        Args:
            public_key: WireGuard public key to check

        Returns:
            True if peer exists, False otherwise
        """
        peers = self.get_server_peers()
        return any(peer.get("public_key") == public_key for peer in peers)

    def get_next_available_ip(self, vpn_network: str = "10.66.66") -> Optional[str]:
        """Get the next available IP address in the VPN network.

        Args:
            vpn_network: VPN network prefix (e.g., "10.66.66")

        Returns:
            Next available IP address as string, or None if network is full
        """
        try:
            peers = self.get_server_peers()

            # Extract all used IPs
            used_ips = set()
            for peer in peers:
                allowed_ips = peer.get("allowed_ips", "")
                # Extract IP from CIDR notation (e.g., "10.66.66.2/32" -> "10.66.66.2")
                ip_match = re.match(r"(\d+\.\d+\.\d+\.\d+)", allowed_ips)
                if ip_match:
                    used_ips.add(ip_match.group(1))

            # Server typically uses .1, so start checking from .2
            for i in range(2, 255):
                candidate_ip = f"{vpn_network}.{i}"
                if candidate_ip not in used_ips:
                    return candidate_ip

            logger.error("No available IPs in VPN network")
            return None

        except Exception as e:
            logger.exception(f"Error finding next available IP: {e}")
            return None

    def is_server_running(self) -> bool:
        """Check if WireGuard server is currently running.

        Returns:
            True if server is running, False otherwise
        """
        result = execute_command("systemctl is-active wg-quick@wg0")
        return result.success and result.stdout.strip() == "active"
