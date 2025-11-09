"""Configuration synchronization between VPN servers."""

import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from .manager import ServerManager
from .models import SyncConfiguration

logger = get_logger(__name__)


class ConfigSync:
    """Synchronize configurations across multiple VPN servers."""

    def __init__(
        self, server_manager: ServerManager, sync_config: Optional[SyncConfiguration] = None
    ):
        """Initialize configuration sync.

        Args:
            server_manager: Server manager instance
            sync_config: Sync configuration
        """
        self.server_manager = server_manager
        self.sync_config = sync_config or SyncConfiguration()
        self.logger = logger

        # Sync state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_sync: Optional[datetime] = None

    async def get_server_config_hash(self, server_name: str) -> Optional[str]:
        """Get hash of server's configuration.

        Args:
            server_name: Server name

        Returns:
            Optional[str]: Configuration hash or None
        """
        try:
            # Get configuration file from server
            config_content = await self.server_manager.execute_command(
                server_name, "cat ~/.config/vpnhd/config.yaml 2>/dev/null || echo '{}'"
            )

            if not config_content:
                return None

            # Calculate hash
            config_hash = hashlib.sha256(config_content.encode()).hexdigest()
            return config_hash

        except Exception as e:
            self.logger.error(f"Failed to get config hash for {server_name}: {e}")
            return None

    async def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get full configuration from server.

        Args:
            server_name: Server name

        Returns:
            Optional[Dict]: Configuration data or None
        """
        try:
            # Execute command to read config
            config_content = await self.server_manager.execute_command(
                server_name, "cat ~/.config/vpnhd/config.yaml"
            )

            if not config_content:
                return None

            # Parse YAML (simplified - would need actual YAML parser)
            # For now, assume JSON format or convert
            import yaml

            config_data = yaml.safe_load(config_content)
            return config_data

        except Exception as e:
            self.logger.error(f"Failed to get config from {server_name}: {e}")
            return None

    async def push_config_to_server(self, server_name: str, config_data: Dict[str, Any]) -> bool:
        """Push configuration to server.

        Args:
            server_name: Server name
            config_data: Configuration data

        Returns:
            bool: True if successful
        """
        try:
            # Convert config to YAML
            import yaml

            config_yaml = yaml.safe_dump(config_data, default_flow_style=False)

            # Create temp file and upload
            temp_path = f"/tmp/vpnhd_config_{datetime.now().timestamp()}.yaml"

            # Write config via SSH (multi-step process)
            commands = [
                "mkdir -p ~/.config/vpnhd",
                f"cat > {temp_path} << 'VPNHD_CONFIG_EOF'\n{config_yaml}\nVPNHD_CONFIG_EOF",
                f"mv {temp_path} ~/.config/vpnhd/config.yaml",
            ]

            for cmd in commands:
                result = await self.server_manager.execute_command(server_name, cmd)
                if result is None:
                    self.logger.error(f"Failed to push config to {server_name}")
                    return False

            self.logger.info(f"Successfully pushed config to {server_name}")
            return True

        except Exception as e:
            self.logger.exception(f"Error pushing config to {server_name}: {e}")
            return False

    async def sync_client_configs(
        self, source_server: str, target_servers: List[str]
    ) -> Dict[str, bool]:
        """Synchronize client configurations from source to targets.

        Args:
            source_server: Source server name
            target_servers: List of target server names

        Returns:
            Dict mapping server names to sync success
        """
        if not self.sync_config.sync_clients:
            self.logger.info("Client sync is disabled")
            return {server: False for server in target_servers}

        try:
            # Get source config
            source_config = await self.get_server_config(source_server)
            if not source_config:
                self.logger.error(f"Failed to get config from {source_server}")
                return {server: False for server in target_servers}

            # Extract client configurations
            clients = source_config.get("clients", {})
            if not clients:
                self.logger.warning(f"No clients found in {source_server}")
                return {server: False for server in target_servers}

            # Sync to each target
            results = {}
            for target in target_servers:
                if target in self.sync_config.excluded_servers:
                    self.logger.info(f"Skipping excluded server: {target}")
                    results[target] = False
                    continue

                # Get target config
                target_config = await self.get_server_config(target)
                if not target_config:
                    results[target] = False
                    continue

                # Merge client configs
                target_config["clients"] = clients

                # Push updated config
                success = await self.push_config_to_server(target, target_config)
                results[target] = success

            return results

        except Exception as e:
            self.logger.exception(f"Error syncing client configs: {e}")
            return {server: False for server in target_servers}

    async def sync_server_settings(
        self,
        source_server: str,
        target_servers: List[str],
        settings_keys: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """Synchronize specific server settings.

        Args:
            source_server: Source server name
            target_servers: List of target server names
            settings_keys: Specific settings to sync (None = all)

        Returns:
            Dict mapping server names to sync success
        """
        if not self.sync_config.sync_settings:
            self.logger.info("Settings sync is disabled")
            return {server: False for server in target_servers}

        try:
            # Get source config
            source_config = await self.get_server_config(source_server)
            if not source_config:
                return {server: False for server in target_servers}

            # Extract settings
            if settings_keys:
                settings = {
                    key: source_config.get(key) for key in settings_keys if key in source_config
                }
            else:
                # Sync all non-client settings
                settings = {
                    k: v
                    for k, v in source_config.items()
                    if k not in ["clients", "servers"]  # Exclude client/server lists
                }

            # Sync to each target
            results = {}
            for target in target_servers:
                if target in self.sync_config.excluded_servers:
                    results[target] = False
                    continue

                # Get target config
                target_config = await self.get_server_config(target)
                if not target_config:
                    results[target] = False
                    continue

                # Merge settings
                target_config.update(settings)

                # Push updated config
                success = await self.push_config_to_server(target, target_config)
                results[target] = success

            return results

        except Exception as e:
            self.logger.exception(f"Error syncing server settings: {e}")
            return {server: False for server in target_servers}

    async def detect_config_conflicts(self, server_names: List[str]) -> Dict[str, Any]:
        """Detect configuration conflicts between servers.

        Args:
            server_names: List of server names to check

        Returns:
            Dict with conflict information
        """
        try:
            # Get configs from all servers
            configs = {}
            hashes = {}

            for server in server_names:
                config = await self.get_server_config(server)
                if config:
                    configs[server] = config
                    config_hash = await self.get_server_config_hash(server)
                    if config_hash:
                        hashes[server] = config_hash

            # Find differences
            conflicts = []
            reference_server = server_names[0] if server_names else None

            if reference_server and reference_server in configs:
                ref_config = configs[reference_server]

                for server in server_names[1:]:
                    if server not in configs:
                        continue

                    # Compare configs
                    diffs = self._find_config_differences(ref_config, configs[server])

                    if diffs:
                        conflicts.append(
                            {
                                "servers": [reference_server, server],
                                "differences": diffs,
                            }
                        )

            return {
                "has_conflicts": len(conflicts) > 0,
                "conflicts": conflicts,
                "config_hashes": hashes,
            }

        except Exception as e:
            self.logger.exception(f"Error detecting conflicts: {e}")
            return {"has_conflicts": False, "conflicts": [], "config_hashes": {}}

    def _find_config_differences(
        self, config1: Dict[str, Any], config2: Dict[str, Any], path: str = ""
    ) -> List[Dict[str, Any]]:
        """Find differences between two configurations.

        Args:
            config1: First configuration
            config2: Second configuration
            path: Current path in config tree

        Returns:
            List of differences
        """
        diffs = []

        # Check keys in config1
        for key in config1:
            current_path = f"{path}.{key}" if path else key

            if key not in config2:
                diffs.append(
                    {
                        "path": current_path,
                        "type": "missing_in_second",
                        "value1": config1[key],
                    }
                )
            elif isinstance(config1[key], dict) and isinstance(config2[key], dict):
                # Recursive comparison
                nested_diffs = self._find_config_differences(
                    config1[key], config2[key], current_path
                )
                diffs.extend(nested_diffs)
            elif config1[key] != config2[key]:
                diffs.append(
                    {
                        "path": current_path,
                        "type": "value_mismatch",
                        "value1": config1[key],
                        "value2": config2[key],
                    }
                )

        # Check for keys only in config2
        for key in config2:
            if key not in config1:
                current_path = f"{path}.{key}" if path else key
                diffs.append(
                    {
                        "path": current_path,
                        "type": "missing_in_first",
                        "value2": config2[key],
                    }
                )

        return diffs

    async def auto_sync(self, primary_server: str) -> Dict[str, Any]:
        """Automatically sync from primary server to all others.

        Args:
            primary_server: Primary server name (source)

        Returns:
            Dict with sync results
        """
        try:
            # Get all enabled servers except primary
            all_servers = self.server_manager.list_servers(enabled_only=True)
            target_servers = [
                s.name
                for s in all_servers
                if s.name != primary_server and s.name not in self.sync_config.excluded_servers
            ]

            if not target_servers:
                self.logger.info("No target servers for sync")
                return {"success": True, "synced_servers": []}

            # Sync clients if enabled
            client_results = {}
            if self.sync_config.sync_clients:
                client_results = await self.sync_client_configs(primary_server, target_servers)

            # Sync settings if enabled
            settings_results = {}
            if self.sync_config.sync_settings:
                settings_results = await self.sync_server_settings(primary_server, target_servers)

            # Update last sync time
            self._last_sync = datetime.now()

            return {
                "success": True,
                "primary_server": primary_server,
                "target_servers": target_servers,
                "client_sync": client_results,
                "settings_sync": settings_results,
                "timestamp": self._last_sync.isoformat(),
            }

        except Exception as e:
            self.logger.exception(f"Auto-sync failed: {e}")
            return {"success": False, "error": str(e)}

    async def start_auto_sync(self, primary_server: str) -> None:
        """Start automatic synchronization loop.

        Args:
            primary_server: Primary server name
        """
        if not self.sync_config.enabled or self.sync_config.sync_interval <= 0:
            self.logger.info("Auto-sync is disabled")
            return

        if self._running:
            self.logger.warning("Auto-sync already running")
            return

        self._running = True
        self.logger.info(
            f"Starting auto-sync from {primary_server} "
            f"(interval: {self.sync_config.sync_interval}s)"
        )

        self._task = asyncio.create_task(self._auto_sync_loop(primary_server))

    async def stop_auto_sync(self) -> None:
        """Stop automatic synchronization."""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping auto-sync")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                # Expected when task is cancelled
                pass
            self._task = None

    async def _auto_sync_loop(self, primary_server: str) -> None:
        """Automatic sync loop."""
        while self._running:
            try:
                await asyncio.sleep(self.sync_config.sync_interval)

                # Perform sync
                result = await self.auto_sync(primary_server)

                if result["success"]:
                    self.logger.info("Auto-sync completed successfully")
                else:
                    self.logger.error(f"Auto-sync failed: {result.get('error')}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in auto-sync loop: {e}")
                await asyncio.sleep(60)  # Wait before retry

    def get_status(self) -> Dict[str, Any]:
        """Get sync status.

        Returns:
            Dict with status information
        """
        return {
            "enabled": self.sync_config.enabled,
            "auto_sync_running": self._running,
            "sync_interval": self.sync_config.sync_interval,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "sync_clients": self.sync_config.sync_clients,
            "sync_settings": self.sync_config.sync_settings,
            "excluded_servers": self.sync_config.excluded_servers,
        }
