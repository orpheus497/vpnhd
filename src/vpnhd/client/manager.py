"""Client management module for VPNHD.

This module provides comprehensive client management functionality including
listing, adding, removing, and monitoring VPN clients.
"""

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Template

from ..config.manager import ConfigManager
from ..crypto.qrcode import create_qr_with_metadata, generate_qr_code
from ..crypto.server_config import ServerConfigManager
from ..crypto.wireguard import generate_keypair
from ..utils.constants import QR_CODE_DIR, TEMPLATE_DIR
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ClientInfo:
    """Information about a VPN client."""

    name: str
    public_key: str
    vpn_ip: str
    allowed_ips: str = ""
    description: str = ""
    device_type: str = ""  # desktop, mobile, server, etc.
    os: str = ""  # linux, android, ios, windows, macos
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    enabled: bool = True
    preshared_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientInfo":
        """Create from dictionary."""
        return cls(**data)


class ClientManager:
    """Manages VPN clients with metadata and advanced features."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize client manager.

        Args:
            config_manager: Optional config manager instance
        """
        self.config_manager = config_manager or ConfigManager()
        self.server_config = ServerConfigManager()
        self.clients_db_path = Path.home() / ".config" / "vpnhd" / "clients.json"
        self.clients_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_clients_db()

    def _load_clients_db(self):
        """Load clients database from disk."""
        try:
            if self.clients_db_path.exists():
                with open(self.clients_db_path, "r") as f:
                    data = json.load(f)
                    self.clients = {name: ClientInfo.from_dict(info) for name, info in data.items()}
            else:
                self.clients = {}
                self._save_clients_db()
        except Exception as e:
            logger.exception(f"Error loading clients database: {e}")
            self.clients = {}

    def _save_clients_db(self):
        """Save clients database to disk."""
        try:
            data = {name: client.to_dict() for name, client in self.clients.items()}
            with open(self.clients_db_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.exception(f"Error saving clients database: {e}")

    def list_clients(
        self,
        enabled_only: bool = False,
        device_type: Optional[str] = None,
        os_filter: Optional[str] = None,
    ) -> List[ClientInfo]:
        """List all clients with optional filtering.

        Args:
            enabled_only: Only return enabled clients
            device_type: Filter by device type (desktop, mobile, server)
            os_filter: Filter by operating system

        Returns:
            List of ClientInfo objects
        """
        clients = list(self.clients.values())

        if enabled_only:
            clients = [c for c in clients if c.enabled]

        if device_type:
            clients = [c for c in clients if c.device_type == device_type]

        if os_filter:
            clients = [c for c in clients if c.os.lower() == os_filter.lower()]

        # Sort by creation date (newest first)
        clients.sort(key=lambda c: c.created_at, reverse=True)

        return clients

    def get_client(self, name: str) -> Optional[ClientInfo]:
        """Get client by name.

        Args:
            name: Client name

        Returns:
            ClientInfo object or None if not found
        """
        return self.clients.get(name)

    def get_client_by_public_key(self, public_key: str) -> Optional[ClientInfo]:
        """Get client by public key.

        Args:
            public_key: WireGuard public key

        Returns:
            ClientInfo object or None if not found
        """
        for client in self.clients.values():
            if client.public_key == public_key:
                return client
        return None

    def add_client(
        self,
        name: str,
        description: str = "",
        device_type: str = "desktop",
        os: str = "linux",
        vpn_ip: Optional[str] = None,
        generate_qr: bool = False,
        qr_output_dir: Optional[str] = None,
    ) -> Optional[ClientInfo]:
        """Add a new VPN client.

        Args:
            name: Client name (must be unique)
            description: Optional description
            device_type: Device type (desktop, mobile, server)
            os: Operating system (linux, android, ios, windows, macos)
            vpn_ip: Specific VPN IP (auto-assigned if None)
            generate_qr: Generate QR code for mobile clients
            qr_output_dir: QR code output directory

        Returns:
            ClientInfo object if successful, None otherwise
        """
        try:
            # Check if client already exists
            if name in self.clients:
                logger.error(f"Client '{name}' already exists")
                return None

            # Generate keypair
            private_key, public_key = generate_keypair()

            # Determine VPN IP
            if vpn_ip is None:
                vpn_ip = self.server_config.get_next_available_ip()
                if vpn_ip is None:
                    logger.error("No available IP addresses")
                    return None

            # Set allowed IPs
            allowed_ips = f"{vpn_ip}/32"

            # Create client info
            client_info = ClientInfo(
                name=name,
                public_key=public_key,
                vpn_ip=vpn_ip,
                allowed_ips=allowed_ips,
                description=description,
                device_type=device_type,
                os=os,
            )

            # Add to server configuration
            if not self.server_config.add_peer_to_server(
                client_name=name, public_key=public_key, vpn_ip=vpn_ip
            ):
                logger.error(f"Failed to add client '{name}' to server")
                return None

            # Save client private key to config
            self.config_manager.set(f"clients.{name}.private_key", private_key)
            self.config_manager.set(f"clients.{name}.public_key", public_key)
            self.config_manager.set(f"clients.{name}.vpn_ip", vpn_ip)
            self.config_manager.save()

            # Generate QR code if requested
            if generate_qr and device_type == "mobile":
                config_text = self._generate_client_config(name, private_key, vpn_ip)
                qr_dir = qr_output_dir or QR_CODE_DIR
                qr_path = create_qr_with_metadata(
                    config_text=config_text, client_name=name, output_dir=qr_dir
                )
                if qr_path:
                    logger.info(f"QR code generated: {qr_path}")

            # Add to clients database
            self.clients[name] = client_info
            self._save_clients_db()

            logger.info(f"Client '{name}' added successfully")
            return client_info

        except Exception as e:
            logger.exception(f"Error adding client: {e}")
            return None

    def remove_client(self, name: str) -> bool:
        """Remove a client.

        Args:
            name: Client name

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self.clients.get(name)
            if not client:
                logger.error(f"Client '{name}' not found")
                return False

            # Remove from server configuration
            if not self.server_config.remove_peer_from_server(client.public_key):
                logger.warning(f"Failed to remove client '{name}' from server config")
                # Continue anyway to clean up database

            # Remove from clients database
            del self.clients[name]
            self._save_clients_db()

            # Remove from config
            self.config_manager.delete(f"clients.{name}")
            self.config_manager.save()

            logger.info(f"Client '{name}' removed successfully")
            return True

        except Exception as e:
            logger.exception(f"Error removing client: {e}")
            return False

    def enable_client(self, name: str) -> bool:
        """Enable a client.

        Args:
            name: Client name

        Returns:
            True if successful, False otherwise
        """
        client = self.clients.get(name)
        if not client:
            logger.error(f"Client '{name}' not found")
            return False

        client.enabled = True
        client.last_modified = datetime.now().isoformat()
        self._save_clients_db()
        return True

    def disable_client(self, name: str) -> bool:
        """Disable a client.

        Args:
            name: Client name

        Returns:
            True if successful, False otherwise
        """
        client = self.clients.get(name)
        if not client:
            logger.error(f"Client '{name}' not found")
            return False

        client.enabled = False
        client.last_modified = datetime.now().isoformat()
        self._save_clients_db()
        return True

    def update_client(
        self,
        name: str,
        description: Optional[str] = None,
        device_type: Optional[str] = None,
        os: Optional[str] = None,
    ) -> bool:
        """Update client metadata.

        Args:
            name: Client name
            description: New description
            device_type: New device type
            os: New operating system

        Returns:
            True if successful, False otherwise
        """
        client = self.clients.get(name)
        if not client:
            logger.error(f"Client '{name}' not found")
            return False

        if description is not None:
            client.description = description
        if device_type is not None:
            client.device_type = device_type
        if os is not None:
            client.os = os

        client.last_modified = datetime.now().isoformat()
        self._save_clients_db()
        return True

    def get_client_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get connection status for a client.

        Args:
            name: Client name

        Returns:
            Dictionary with status information or None
        """
        client = self.clients.get(name)
        if not client:
            return None

        try:
            # Use wg show to get peer status
            result = subprocess.run(
                ["wg", "show", "wg0", "dump"], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return {"connected": False, "error": "Failed to query WireGuard status"}

            # Parse output
            for line in result.stdout.strip().split("\n"):
                if not line or line.startswith("wg0"):
                    continue

                parts = line.split("\t")
                if len(parts) >= 5 and parts[0] == client.public_key:
                    return {
                        "connected": True,
                        "public_key": parts[0],
                        "preshared_key": parts[1] if parts[1] != "(none)" else None,
                        "endpoint": parts[2] if parts[2] != "(none)" else None,
                        "allowed_ips": parts[3],
                        "latest_handshake": parts[4],
                        "transfer_rx": parts[5] if len(parts) > 5 else "0",
                        "transfer_tx": parts[6] if len(parts) > 6 else "0",
                        "persistent_keepalive": parts[7] if len(parts) > 7 else "off",
                    }

            return {"connected": False}

        except Exception as e:
            logger.exception(f"Error getting client status: {e}")
            return {"connected": False, "error": str(e)}

    def get_all_connected_clients(self) -> List[str]:
        """Get list of currently connected client names.

        Returns:
            List of client names that are currently connected
        """
        connected = []
        for name in self.clients:
            status = self.get_client_status(name)
            if status and status.get("connected"):
                connected.append(name)
        return connected

    def _generate_client_config(self, client_name: str, private_key: str, vpn_ip: str) -> str:
        """Generate WireGuard configuration for client.

        Args:
            client_name: Client name
            private_key: Client private key
            vpn_ip: Client VPN IP

        Returns:
            Configuration file content
        """
        template_path = TEMPLATE_DIR / "wireguard_client.conf.j2"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path) as f:
            template = Template(f.read())

        config = template.render(
            client_name=client_name,
            client_vpn_ip=vpn_ip,
            vpn_subnet_mask="24",
            client_private_key=private_key,
            server_public_key=self.config_manager.get(
                "phases.phase2_wireguard_server.server_public_key"
            ),
            server_public_ip=self.config_manager.get("server.public_ip"),
            wireguard_port=self.config_manager.get("network.wireguard_port", 51820),
            route_all_traffic=True,
            dns_servers=["1.1.1.1", "8.8.8.8"],
            vpn_network=self.config_manager.get("network.vpn.network", "10.66.66.0/24"),
        )

        return config

    def export_client_config(self, name: str, output_path: Optional[str] = None) -> Optional[str]:
        """Export client configuration to file.

        Args:
            name: Client name
            output_path: Output file path (auto-generated if None)

        Returns:
            Path to exported config file or None
        """
        try:
            client = self.clients.get(name)
            if not client:
                logger.error(f"Client '{name}' not found")
                return None

            # Get private key
            private_key = self.config_manager.get(f"clients.{name}.private_key")
            if not private_key:
                logger.error(f"Private key not found for client '{name}'")
                return None

            # Generate config
            config_text = self._generate_client_config(name, private_key, client.vpn_ip)

            # Determine output path
            if output_path is None:
                output_dir = Path.home() / ".config" / "vpnhd" / "client_configs"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{name}.conf"
            else:
                output_path = Path(output_path)

            # Write config
            output_path.write_text(config_text)
            logger.info(f"Client config exported to {output_path}")

            return str(output_path)

        except Exception as e:
            logger.exception(f"Error exporting client config: {e}")
            return None

    def get_client_count(self) -> int:
        """Get total number of clients.

        Returns:
            Number of clients
        """
        return len(self.clients)

    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics.

        Returns:
            Dictionary with statistics
        """
        total = len(self.clients)
        enabled = sum(1 for c in self.clients.values() if c.enabled)
        disabled = total - enabled
        connected = len(self.get_all_connected_clients())

        # Count by device type
        by_device = {}
        for client in self.clients.values():
            dtype = client.device_type or "unknown"
            by_device[dtype] = by_device.get(dtype, 0) + 1

        # Count by OS
        by_os = {}
        for client in self.clients.values():
            os_name = client.os or "unknown"
            by_os[os_name] = by_os.get(os_name, 0) + 1

        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "connected": connected,
            "by_device_type": by_device,
            "by_os": by_os,
        }
