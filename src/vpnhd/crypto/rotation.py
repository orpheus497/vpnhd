"""Automated cryptographic key rotation for VPN and SSH."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.manager import ConfigManager
from ..notifications.manager import NotificationManager
from ..system.commands import execute_command_async
from ..utils.logging import get_logger

logger = get_logger(__name__)


class KeyRotationManager:
    """Manage automated rotation of cryptographic keys."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        notification_manager: Optional[NotificationManager] = None,
    ):
        """Initialize key rotation manager.

        Args:
            config_manager: Configuration manager instance
            notification_manager: Notification manager for alerts
        """
        self.config = config_manager or ConfigManager()
        self.notifications = notification_manager
        self.logger = logger

        # Rotation settings
        self.wireguard_interval_days = self.config.get("security.key_rotation.wireguard_days", 90)
        self.ssh_interval_days = self.config.get("security.key_rotation.ssh_days", 180)
        self.auto_rotation_enabled = self.config.get("security.key_rotation.enabled", False)

        # Track last rotations
        self.last_wireguard_rotation: Optional[datetime] = None
        self.last_ssh_rotation: Optional[datetime] = None

        # Rotation task
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Load rotation history
        self._load_rotation_history()

    def _load_rotation_history(self) -> None:
        """Load rotation history from config."""
        try:
            history = self.config.get("security.key_rotation.history", {})

            if "last_wireguard_rotation" in history:
                self.last_wireguard_rotation = datetime.fromisoformat(
                    history["last_wireguard_rotation"]
                )

            if "last_ssh_rotation" in history:
                self.last_ssh_rotation = datetime.fromisoformat(history["last_ssh_rotation"])

        except Exception as e:
            self.logger.error(f"Failed to load rotation history: {e}")

    def _save_rotation_history(self) -> None:
        """Save rotation history to config."""
        try:
            history = {}

            if self.last_wireguard_rotation:
                history["last_wireguard_rotation"] = self.last_wireguard_rotation.isoformat()

            if self.last_ssh_rotation:
                history["last_ssh_rotation"] = self.last_ssh_rotation.isoformat()

            self.config.set("security.key_rotation.history", history)
            self.config.save()

        except Exception as e:
            self.logger.error(f"Failed to save rotation history: {e}")

    async def generate_wireguard_keypair(self) -> Optional[Dict[str, str]]:
        """Generate new WireGuard key pair.

        Returns:
            Optional[Dict]: Dict with 'private_key' and 'public_key' or None
        """
        try:
            # Generate private key
            result = await execute_command_async(["wg", "genkey"], check=True)
            if not result.success:
                self.logger.error("Failed to generate WireGuard private key")
                return None

            private_key = result.stdout.strip()

            # Derive public key
            result = await execute_command_async(["wg", "pubkey"], stdin=private_key, check=True)
            if not result.success:
                self.logger.error("Failed to derive WireGuard public key")
                return None

            public_key = result.stdout.strip()

            return {
                "private_key": private_key,
                "public_key": public_key,
            }

        except Exception as e:
            self.logger.exception(f"Error generating WireGuard keypair: {e}")
            return None

    async def rotate_wireguard_server_keys(self) -> bool:
        """Rotate WireGuard server keys.

        Returns:
            bool: True if rotation successful
        """
        try:
            self.logger.info("Starting WireGuard server key rotation")

            # Generate new server keypair
            keypair = await self.generate_wireguard_keypair()
            if not keypair:
                return False

            # Backup current keys
            current_private = self.config.get("server.private_key")
            current_public = self.config.get("server.public_key")

            backup_data = {
                "private_key": current_private,
                "public_key": current_public,
                "rotated_at": datetime.now().isoformat(),
            }

            # Store backup
            backups = self.config.get("security.key_rotation.backups", [])
            backups.append(backup_data)
            # Keep only last 5 backups
            backups = backups[-5:]
            self.config.set("security.key_rotation.backups", backups)

            # Update server keys
            self.config.set("server.private_key", keypair["private_key"])
            self.config.set("server.public_key", keypair["public_key"])
            self.config.save()

            # Reload WireGuard interface
            interface = self.config.get("network.vpn.interface", "wg0")

            # Bring down interface
            await execute_command_async(["wg-quick", "down", interface], sudo=True, check=False)

            # Bring up with new keys
            await execute_command_async(["wg-quick", "up", interface], sudo=True, check=True)

            # Update rotation timestamp
            self.last_wireguard_rotation = datetime.now()
            self._save_rotation_history()

            self.logger.info("WireGuard server keys rotated successfully")

            # Publish KEY_ROTATION_COMPLETED event
            try:
                from ..events import KeyRotationEvent, EventType, event_bus
                event = KeyRotationEvent(
                    EventType.KEY_ROTATION_COMPLETED,
                    "wireguard",
                    {"new_public_key": keypair["public_key"]}
                )
                event_bus.publish(event)
            except Exception as e:
                self.logger.warning(f"Failed to publish KEY_ROTATION_COMPLETED event: {e}")

            # Send notification (old way)
            if self.notifications:
                await self.notifications.send_notification(
                    event_type="key_rotation",
                    message="WireGuard server keys have been rotated",
                    details={
                        "key_type": "wireguard_server",
                        "new_public_key": keypair["public_key"],
                    },
                    severity="info",
                )

            return True

        except Exception as e:
            self.logger.exception(f"WireGuard key rotation failed: {e}")

            # Publish KEY_ROTATION_FAILED event
            try:
                from ..events import KeyRotationEvent, EventType, event_bus
                event = KeyRotationEvent(
                    EventType.KEY_ROTATION_FAILED,
                    "wireguard",
                    {"error": str(e)}
                )
                event_bus.publish(event)
            except Exception as err:
                self.logger.warning(f"Failed to publish KEY_ROTATION_FAILED event: {err}")

            # Send error notification (old way)
            if self.notifications:
                await self.notifications.send_notification(
                    event_type="error",
                    message="WireGuard key rotation failed",
                    details={"error": str(e)},
                    severity="error",
                )

            return False

    async def rotate_wireguard_client_keys(self, client_name: str) -> bool:
        """Rotate WireGuard keys for a specific client.

        Args:
            client_name: Client name

        Returns:
            bool: True if rotation successful
        """
        try:
            self.logger.info(f"Rotating WireGuard keys for client: {client_name}")

            # Get current client config
            client_config = self.config.get(f"clients.{client_name}")
            if not client_config:
                self.logger.error(f"Client {client_name} not found")
                return False

            # Generate new keypair
            keypair = await self.generate_wireguard_keypair()
            if not keypair:
                return False

            # Backup current keys
            backup = {
                "private_key": client_config.get("private_key"),
                "public_key": client_config.get("public_key"),
                "rotated_at": datetime.now().isoformat(),
            }

            # Update client keys
            client_config["private_key"] = keypair["private_key"]
            client_config["public_key"] = keypair["public_key"]
            client_config["key_rotated_at"] = datetime.now().isoformat()

            self.config.set(f"clients.{client_name}", client_config)
            self.config.save()

            # Update WireGuard peer configuration
            interface = self.config.get("network.vpn.interface", "wg0")

            # Remove old peer
            await execute_command_async(
                ["wg", "set", interface, "peer", backup["public_key"], "remove"],
                sudo=True,
                check=False,
            )

            # Add peer with new key
            allowed_ips = client_config.get("allowed_ips", [])
            await execute_command_async(
                [
                    "wg",
                    "set",
                    interface,
                    "peer",
                    keypair["public_key"],
                    "allowed-ips",
                    ",".join(allowed_ips),
                ],
                sudo=True,
                check=True,
            )

            self.logger.info(f"Client {client_name} keys rotated successfully")

            # Send notification
            if self.notifications:
                await self.notifications.send_notification(
                    event_type="key_rotation",
                    message=f"Client {client_name} keys have been rotated",
                    details={
                        "key_type": "wireguard_client",
                        "client_name": client_name,
                        "new_public_key": keypair["public_key"],
                    },
                    severity="info",
                )

            return True

        except Exception as e:
            self.logger.exception(f"Client key rotation failed for {client_name}: {e}")
            return False

    async def rotate_all_client_keys(self) -> Dict[str, bool]:
        """Rotate keys for all clients.

        Returns:
            Dict mapping client names to rotation success
        """
        clients = self.config.get("clients", {})
        results = {}

        for client_name in clients.keys():
            success = await self.rotate_wireguard_client_keys(client_name)
            results[client_name] = success

        return results

    async def generate_ssh_keypair(
        self, key_type: str = "ed25519", key_size: Optional[int] = None
    ) -> Optional[Dict[str, str]]:
        """Generate new SSH key pair.

        Args:
            key_type: Key type (rsa, ed25519, ecdsa)
            key_size: Key size (for RSA, default 4096)

        Returns:
            Optional[Dict]: Dict with 'private_key' and 'public_key' or None
        """
        try:
            # Create temp directory for keys
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                key_path = Path(tmpdir) / "id_temp"

                # Build ssh-keygen command
                cmd = [
                    "ssh-keygen",
                    "-t",
                    key_type,
                    "-f",
                    str(key_path),
                    "-N",
                    "",  # No passphrase
                    "-C",
                    f"vpnhd-rotated-{datetime.now().isoformat()}",
                ]

                if key_type == "rsa" and key_size:
                    cmd.extend(["-b", str(key_size)])

                # Generate keys
                result = await execute_command_async(cmd, check=True)
                if not result.success:
                    return None

                # Read keys
                private_key = key_path.read_text()
                public_key = (key_path.with_suffix(".pub")).read_text()

                return {
                    "private_key": private_key,
                    "public_key": public_key,
                    "key_type": key_type,
                }

        except Exception as e:
            self.logger.exception(f"Error generating SSH keypair: {e}")
            return None

    async def rotate_ssh_keys(self) -> bool:
        """Rotate SSH keys for server access.

        Returns:
            bool: True if rotation successful
        """
        try:
            self.logger.info("Starting SSH key rotation")

            # Generate new SSH keypair
            keypair = await self.generate_ssh_keypair(key_type="ed25519")
            if not keypair:
                return False

            # SSH key paths
            ssh_dir = Path.home() / ".ssh"
            ssh_dir.mkdir(mode=0o700, exist_ok=True)

            private_key_path = ssh_dir / "vpnhd_id_ed25519"
            public_key_path = ssh_dir / "vpnhd_id_ed25519.pub"

            # Backup current keys if they exist
            if private_key_path.exists():
                backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
                private_key_path.rename(ssh_dir / f"vpnhd_id_ed25519.backup_{backup_suffix}")
                if public_key_path.exists():
                    public_key_path.rename(ssh_dir / f"vpnhd_id_ed25519.pub.backup_{backup_suffix}")

            # Write new keys
            private_key_path.write_text(keypair["private_key"])
            private_key_path.chmod(0o600)

            public_key_path.write_text(keypair["public_key"])
            public_key_path.chmod(0o644)

            # Update rotation timestamp
            self.last_ssh_rotation = datetime.now()
            self._save_rotation_history()

            self.logger.info("SSH keys rotated successfully")

            # Send notification
            if self.notifications:
                await self.notifications.send_notification(
                    event_type="key_rotation",
                    message="SSH keys have been rotated",
                    details={
                        "key_type": "ssh",
                        "private_key_path": str(private_key_path),
                        "public_key_path": str(public_key_path),
                    },
                    severity="info",
                )

            return True

        except Exception as e:
            self.logger.exception(f"SSH key rotation failed: {e}")
            return False

    def is_rotation_needed(self, key_type: str) -> bool:
        """Check if key rotation is needed.

        Args:
            key_type: 'wireguard' or 'ssh'

        Returns:
            bool: True if rotation is needed
        """
        now = datetime.now()

        if key_type == "wireguard":
            if not self.last_wireguard_rotation:
                return True

            delta = now - self.last_wireguard_rotation
            return delta.days >= self.wireguard_interval_days

        elif key_type == "ssh":
            if not self.last_ssh_rotation:
                return True

            delta = now - self.last_ssh_rotation
            return delta.days >= self.ssh_interval_days

        return False

    async def check_and_rotate(self) -> Dict[str, Any]:
        """Check if rotation is needed and perform if necessary.

        Returns:
            Dict with rotation results
        """
        results = {
            "wireguard": {"needed": False, "rotated": False},
            "ssh": {"needed": False, "rotated": False},
        }

        # Check WireGuard rotation
        if self.is_rotation_needed("wireguard"):
            results["wireguard"]["needed"] = True
            self.logger.info("WireGuard key rotation is needed")

            success = await self.rotate_wireguard_server_keys()
            results["wireguard"]["rotated"] = success

        # Check SSH rotation
        if self.is_rotation_needed("ssh"):
            results["ssh"]["needed"] = True
            self.logger.info("SSH key rotation is needed")

            success = await self.rotate_ssh_keys()
            results["ssh"]["rotated"] = success

        return results

    async def start_auto_rotation(self) -> None:
        """Start automatic key rotation scheduler."""
        if not self.auto_rotation_enabled:
            self.logger.info("Automatic key rotation is disabled")
            return

        if self._running:
            self.logger.warning("Auto rotation already running")
            return

        self._running = True
        self.logger.info("Starting automatic key rotation scheduler")

        # Check interval: daily
        self._task = asyncio.create_task(self._auto_rotation_loop())

    async def stop_auto_rotation(self) -> None:
        """Stop automatic key rotation."""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping automatic key rotation")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                # Expected when task is cancelled
                pass
            self._task = None

    async def _auto_rotation_loop(self) -> None:
        """Automatic rotation check loop."""
        # Check once per day
        check_interval = 86400  # 24 hours

        while self._running:
            try:
                await asyncio.sleep(check_interval)

                # Perform rotation check
                results = await self.check_and_rotate()

                # Log results
                if results["wireguard"]["rotated"]:
                    self.logger.info("Automatic WireGuard key rotation completed")

                if results["ssh"]["rotated"]:
                    self.logger.info("Automatic SSH key rotation completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in auto-rotation loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry

    def get_status(self) -> Dict[str, Any]:
        """Get key rotation status.

        Returns:
            Dict with status information
        """
        now = datetime.now()

        wireguard_days_since = None
        if self.last_wireguard_rotation:
            wireguard_days_since = (now - self.last_wireguard_rotation).days

        ssh_days_since = None
        if self.last_ssh_rotation:
            ssh_days_since = (now - self.last_ssh_rotation).days

        return {
            "auto_rotation_enabled": self.auto_rotation_enabled,
            "auto_rotation_running": self._running,
            "wireguard": {
                "interval_days": self.wireguard_interval_days,
                "last_rotation": (
                    self.last_wireguard_rotation.isoformat()
                    if self.last_wireguard_rotation
                    else None
                ),
                "days_since_rotation": wireguard_days_since,
                "rotation_needed": self.is_rotation_needed("wireguard"),
            },
            "ssh": {
                "interval_days": self.ssh_interval_days,
                "last_rotation": (
                    self.last_ssh_rotation.isoformat() if self.last_ssh_rotation else None
                ),
                "days_since_rotation": ssh_days_since,
                "rotation_needed": self.is_rotation_needed("ssh"),
            },
        }
