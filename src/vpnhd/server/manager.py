"""Multi-server management system for VPNHD."""

import asyncio
import asyncssh
from typing import Optional, Dict, Any, List

from ..utils.logging import get_logger
from ..config.manager import ConfigManager
from .models import (
    ServerProfile,
    ServerGroup,
    ServerOperation,
)

logger = get_logger(__name__)


class ServerManager:
    """Manage multiple VPN servers from a central location."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize server manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.logger = logger

        # Server profiles storage
        self.servers: Dict[str, ServerProfile] = {}
        self.groups: Dict[str, ServerGroup] = {}

        # Operation history
        self.operations: List[ServerOperation] = []
        self.max_operations_history = 1000

        # SSH connection pool
        self._ssh_connections: Dict[str, asyncssh.SSHClientConnection] = {}

        # Load servers from config
        self._load_servers()

    def _load_servers(self) -> None:
        """Load server profiles from configuration."""
        try:
            servers_data = self.config.get('servers', {})

            for server_name, server_data in servers_data.items():
                try:
                    profile = ServerProfile(**server_data)
                    self.servers[server_name] = profile
                    self.logger.info(f"Loaded server profile: {server_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load server {server_name}: {e}")

            self.logger.info(f"Loaded {len(self.servers)} server profiles")

        except Exception as e:
            self.logger.error(f"Failed to load servers: {e}")

    def _save_servers(self) -> None:
        """Save server profiles to configuration."""
        try:
            servers_data = {
                name: profile.to_dict()
                for name, profile in self.servers.items()
            }

            self.config.set('servers', servers_data)
            self.config.save()
            self.logger.debug("Saved server profiles to configuration")

        except Exception as e:
            self.logger.error(f"Failed to save servers: {e}")

    def add_server(self, profile: ServerProfile) -> bool:
        """Add a new server profile.

        Args:
            profile: Server profile to add

        Returns:
            bool: True if added successfully
        """
        if profile.name in self.servers:
            self.logger.error(f"Server {profile.name} already exists")
            return False

        try:
            self.servers[profile.name] = profile
            self._save_servers()
            self.logger.info(f"Added server: {profile.name}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to add server {profile.name}: {e}")
            return False

    def remove_server(self, server_name: str) -> bool:
        """Remove a server profile.

        Args:
            server_name: Server name to remove

        Returns:
            bool: True if removed successfully
        """
        if server_name not in self.servers:
            self.logger.error(f"Server {server_name} not found")
            return False

        try:
            # Close SSH connection if exists
            asyncio.create_task(self._close_ssh_connection(server_name))

            del self.servers[server_name]
            self._save_servers()
            self.logger.info(f"Removed server: {server_name}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to remove server {server_name}: {e}")
            return False

    def get_server(self, server_name: str) -> Optional[ServerProfile]:
        """Get a server profile.

        Args:
            server_name: Server name

        Returns:
            Optional[ServerProfile]: Server profile or None
        """
        return self.servers.get(server_name)

    def list_servers(
        self,
        enabled_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[ServerProfile]:
        """List server profiles with optional filtering.

        Args:
            enabled_only: Only return enabled servers
            tags: Filter by tags (any match)

        Returns:
            List of server profiles
        """
        servers = list(self.servers.values())

        if enabled_only:
            servers = [s for s in servers if s.enabled]

        if tags:
            servers = [s for s in servers if any(tag in s.tags for tag in tags)]

        return servers

    async def _get_ssh_connection(
        self, server_name: str
    ) -> Optional[asyncssh.SSHClientConnection]:
        """Get or create SSH connection to server.

        Args:
            server_name: Server name

        Returns:
            Optional[asyncssh.SSHClientConnection]: SSH connection or None
        """
        profile = self.get_server(server_name)
        if not profile:
            return None

        # Return existing connection if alive
        if server_name in self._ssh_connections:
            conn = self._ssh_connections[server_name]
            if not conn.is_closed():
                return conn
            else:
                # Clean up dead connection
                del self._ssh_connections[server_name]

        # Create new connection
        try:
            conn_info = profile.connection

            connect_params: Dict[str, Any] = {
                'host': conn_info.host,
                'port': conn_info.port,
                'username': conn_info.username,
                'known_hosts': None,  # Disable host key checking for simplicity
            }

            if conn_info.key_path:
                connect_params['client_keys'] = [conn_info.key_path]
            elif conn_info.password:
                connect_params['password'] = conn_info.password
            else:
                self.logger.error(
                    f"No authentication method for {server_name}"
                )
                return None

            self.logger.debug(f"Connecting to {server_name} via SSH...")
            conn = await asyncio.wait_for(
                asyncssh.connect(**connect_params),
                timeout=30
            )

            self._ssh_connections[server_name] = conn
            self.logger.info(f"SSH connection established to {server_name}")
            return conn

        except asyncio.TimeoutError:
            self.logger.error(f"SSH connection timeout for {server_name}")
            return None
        except Exception as e:
            self.logger.error(f"SSH connection failed for {server_name}: {e}")
            return None

    async def _close_ssh_connection(self, server_name: str) -> None:
        """Close SSH connection to server.

        Args:
            server_name: Server name
        """
        if server_name in self._ssh_connections:
            try:
                conn = self._ssh_connections[server_name]
                conn.close()
                await conn.wait_closed()
                del self._ssh_connections[server_name]
                self.logger.debug(f"Closed SSH connection to {server_name}")
            except Exception as e:
                self.logger.error(
                    f"Error closing SSH connection to {server_name}: {e}"
                )

    async def execute_command(
        self, server_name: str, command: str, timeout: int = 30
    ) -> Optional[str]:
        """Execute command on remote server.

        Args:
            server_name: Server name
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Optional[str]: Command output or None on failure
        """
        conn = await self._get_ssh_connection(server_name)
        if not conn:
            return None

        try:
            result = await asyncio.wait_for(
                conn.run(command, check=True),
                timeout=timeout
            )
            return result.stdout

        except asyncio.TimeoutError:
            self.logger.error(
                f"Command timeout on {server_name}: {command}"
            )
            return None
        except Exception as e:
            self.logger.error(
                f"Command failed on {server_name}: {command} - {e}"
            )
            return None

    async def check_server_status(self, server_name: str) -> bool:
        """Check server status and update profile.

        Args:
            server_name: Server name

        Returns:
            bool: True if server is online
        """
        profile = self.get_server(server_name)
        if not profile:
            return False

        try:
            # Try to establish SSH connection
            conn = await self._get_ssh_connection(server_name)

            if not conn:
                profile.update_status(
                    online=False,
                    vpn_running=False,
                    error_message="SSH connection failed"
                )
                return False

            # Server is reachable
            profile.update_status(online=True, error_message=None)

            # Check if VPN is running
            output = await self.execute_command(
                server_name,
                f"ip link show {profile.vpn_interface}"
            )
            vpn_running = output is not None and 'UP' in output

            # Get system uptime
            uptime_output = await self.execute_command(
                server_name,
                "cat /proc/uptime"
            )
            uptime = None
            if uptime_output:
                try:
                    uptime = int(float(uptime_output.split()[0]))
                except (ValueError, IndexError):
                    # Invalid uptime format, keep as None
                    pass

            # Update status
            profile.update_status(
                vpn_running=vpn_running,
                uptime=uptime,
            )

            self.logger.info(
                f"Server {server_name} status: online={True}, vpn={vpn_running}"
            )
            return True

        except Exception as e:
            self.logger.exception(f"Error checking status for {server_name}: {e}")
            profile.update_status(
                online=False,
                vpn_running=False,
                error_message=str(e)
            )
            return False

    async def collect_server_metrics(self, server_name: str) -> bool:
        """Collect metrics from server.

        Args:
            server_name: Server name

        Returns:
            bool: True if metrics collected successfully
        """
        profile = self.get_server(server_name)
        if not profile or not profile.status.online:
            return False

        try:
            # Get WireGuard peer count
            output = await self.execute_command(
                server_name,
                f"wg show {profile.vpn_interface} peers | wc -l"
            )
            active_clients = 0
            if output:
                try:
                    active_clients = int(output.strip())
                except ValueError:
                    # Invalid number format, keep default 0
                    pass

            # Get traffic statistics (simplified - would need parsing)
            # This is a placeholder for actual metric collection

            profile.update_metrics(
                active_clients=active_clients,
            )

            self.logger.debug(f"Collected metrics for {server_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error collecting metrics for {server_name}: {e}")
            return False

    async def check_all_servers(self) -> Dict[str, bool]:
        """Check status of all enabled servers.

        Returns:
            Dict mapping server names to online status
        """
        servers = self.list_servers(enabled_only=True)

        results = await asyncio.gather(
            *[self.check_server_status(s.name) for s in servers],
            return_exceptions=True
        )

        return {
            server.name: result if isinstance(result, bool) else False
            for server, result in zip(servers, results)
        }

    async def collect_all_metrics(self) -> Dict[str, bool]:
        """Collect metrics from all online servers.

        Returns:
            Dict mapping server names to collection success
        """
        servers = [
            s for s in self.list_servers(enabled_only=True)
            if s.status.online
        ]

        results = await asyncio.gather(
            *[self.collect_server_metrics(s.name) for s in servers],
            return_exceptions=True
        )

        return {
            server.name: result if isinstance(result, bool) else False
            for server, result in zip(servers, results)
        }

    def create_group(self, group: ServerGroup) -> bool:
        """Create a server group.

        Args:
            group: Server group

        Returns:
            bool: True if created successfully
        """
        if group.name in self.groups:
            self.logger.error(f"Group {group.name} already exists")
            return False

        self.groups[group.name] = group
        self.logger.info(f"Created server group: {group.name}")
        return True

    def get_group(self, group_name: str) -> Optional[ServerGroup]:
        """Get a server group.

        Args:
            group_name: Group name

        Returns:
            Optional[ServerGroup]: Group or None
        """
        return self.groups.get(group_name)

    def list_groups(self) -> List[ServerGroup]:
        """List all server groups.

        Returns:
            List of server groups
        """
        return list(self.groups.values())

    async def cleanup(self) -> None:
        """Clean up resources (close SSH connections)."""
        self.logger.info("Cleaning up server manager...")

        # Close all SSH connections
        for server_name in list(self._ssh_connections.keys()):
            await self._close_ssh_connection(server_name)

        self.logger.info("Server manager cleanup complete")

    def get_summary(self) -> Dict[str, Any]:
        """Get server manager summary.

        Returns:
            Dict with summary information
        """
        servers = list(self.servers.values())
        online_count = sum(1 for s in servers if s.status.online)
        vpn_running_count = sum(1 for s in servers if s.status.vpn_running)
        enabled_count = sum(1 for s in servers if s.enabled)

        return {
            'total_servers': len(servers),
            'enabled_servers': enabled_count,
            'online_servers': online_count,
            'vpn_running': vpn_running_count,
            'total_groups': len(self.groups),
            'ssh_connections': len(self._ssh_connections),
        }
