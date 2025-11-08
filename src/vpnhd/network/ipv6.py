"""IPv6 utilities and support for VPNHD.

This module provides comprehensive IPv6 network management including address
validation, routing, forwarding configuration, and ULA prefix generation.
"""

import ipaddress
import secrets
from typing import Optional, List
from pathlib import Path

from ..utils.logging import get_logger
from ..system.commands import execute_command_async

logger = get_logger(__name__)


class IPv6Manager:
    """Manage IPv6 configuration and operations."""

    def __init__(self):
        """Initialize IPv6 manager."""
        self.logger = logger

    async def is_ipv6_supported(self) -> bool:
        """Check if IPv6 is supported on system.

        Returns:
            bool: True if IPv6 is available
        """
        try:
            result = await execute_command_async(["ip", "-6", "addr"], check=False)
            return result.success
        except Exception as e:
            self.logger.warning(f"IPv6 support check failed: {e}")
            return False

    async def is_ipv6_enabled(self) -> bool:
        """Check if IPv6 is enabled globally.

        Returns:
            bool: True if IPv6 is enabled
        """
        try:
            result = await execute_command_async(
                ["sysctl", "-n", "net.ipv6.conf.all.disable_ipv6"], check=False
            )
            if result.success:
                # 0 = enabled, 1 = disabled
                return result.stdout.strip() == "0"
            return False
        except Exception as e:
            self.logger.error(f"Failed to check IPv6 status: {e}")
            return False

    async def enable_ipv6(self) -> bool:
        """Enable IPv6 globally on the system.

        Returns:
            bool: True if successfully enabled
        """
        try:
            result = await execute_command_async(
                ["sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"], sudo=True, check=False
            )

            if result.success:
                # Make persistent
                await self._persist_sysctl("net.ipv6.conf.all.disable_ipv6", "0")
                self.logger.info("IPv6 enabled globally")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to enable IPv6: {e}")
            return False

    async def get_ipv6_address(self, interface: str, scope: str = "global") -> Optional[str]:
        """Get IPv6 address for interface.

        Args:
            interface: Network interface name
            scope: Address scope (global, link, host)

        Returns:
            Optional[str]: IPv6 address or None if not found
        """
        try:
            result = await execute_command_async(
                ["ip", "-6", "addr", "show", "dev", interface, "scope", scope], check=False
            )

            if result.success:
                # Parse output to extract IPv6 address
                for line in result.stdout.split("\n"):
                    if "inet6" in line and f"scope {scope}" in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            # Remove prefix length
                            return parts[1].split("/")[0]
            return None
        except Exception as e:
            self.logger.error(f"Failed to get IPv6 address: {e}")
            return None

    async def get_all_ipv6_addresses(self, interface: str) -> List[str]:
        """Get all IPv6 addresses for interface.

        Args:
            interface: Network interface name

        Returns:
            List[str]: List of IPv6 addresses
        """
        addresses = []

        for scope in ["global", "link", "host"]:
            addr = await self.get_ipv6_address(interface, scope)
            if addr:
                addresses.append(addr)

        return addresses

    async def configure_ipv6_forwarding(self, enable: bool = True) -> bool:
        """Enable or disable IPv6 forwarding.

        Args:
            enable: True to enable, False to disable

        Returns:
            bool: True if successfully configured
        """
        value = "1" if enable else "0"

        try:
            # Set for all interfaces
            result = await execute_command_async(
                ["sysctl", "-w", f"net.ipv6.conf.all.forwarding={value}"], sudo=True, check=False
            )

            if not result.success:
                return False

            # Set for default interface
            await execute_command_async(
                ["sysctl", "-w", f"net.ipv6.conf.default.forwarding={value}"],
                sudo=True,
                check=False,
            )

            # Make persistent
            await self._persist_sysctl("net.ipv6.conf.all.forwarding", value)
            await self._persist_sysctl("net.ipv6.conf.default.forwarding", value)

            action = "enabled" if enable else "disabled"
            self.logger.info(f"IPv6 forwarding {action}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to configure IPv6 forwarding: {e}")
            return False

    def generate_ula_prefix(self, prefix_len: int = 48) -> str:
        """Generate Unique Local Address (ULA) prefix for VPN.

        ULA addresses are in the fd00::/8 range and are meant for local
        communication that should not be routed on the global Internet.

        Args:
            prefix_len: Prefix length (default: 48 for /48 prefix)

        Returns:
            str: ULA prefix in CIDR notation (e.g., "fd12:3456:7890::/48")
        """
        # ULA prefix: fd00::/8
        # We generate a random 40-bit global ID
        random_bits = secrets.randbits(40)

        # Construct the prefix: fd + 40-bit random + zeros
        # fd00:0000:0000::/48 format
        prefix_int = 0xFD00000000000000 | (random_bits << 16)

        # Convert to IPv6 address
        addr = ipaddress.IPv6Address(prefix_int)
        network = ipaddress.IPv6Network(f"{addr}/{prefix_len}", strict=False)

        self.logger.info(f"Generated ULA prefix: {network}")
        return str(network)

    def validate_ipv6_network(self, network: str) -> bool:
        """Validate IPv6 network CIDR notation.

        Args:
            network: IPv6 network in CIDR notation

        Returns:
            bool: True if valid
        """
        try:
            ipaddress.IPv6Network(network, strict=False)
            return True
        except ValueError:
            return False

    def validate_ipv6_address(self, address: str) -> bool:
        """Validate IPv6 address.

        Args:
            address: IPv6 address

        Returns:
            bool: True if valid
        """
        try:
            ipaddress.IPv6Address(address)
            return True
        except ValueError:
            return False

    async def add_ipv6_address(self, interface: str, address: str, prefix_len: int = 64) -> bool:
        """Add IPv6 address to interface.

        Args:
            interface: Network interface name
            address: IPv6 address
            prefix_len: Prefix length (default: 64)

        Returns:
            bool: True if successfully added
        """
        if not self.validate_ipv6_address(address):
            self.logger.error(f"Invalid IPv6 address: {address}")
            return False

        try:
            result = await execute_command_async(
                ["ip", "-6", "addr", "add", f"{address}/{prefix_len}", "dev", interface],
                sudo=True,
                check=False,
            )

            if result.success:
                self.logger.info(f"Added IPv6 address {address}/{prefix_len} to {interface}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to add IPv6 address: {e}")
            return False

    async def remove_ipv6_address(self, interface: str, address: str, prefix_len: int = 64) -> bool:
        """Remove IPv6 address from interface.

        Args:
            interface: Network interface name
            address: IPv6 address
            prefix_len: Prefix length

        Returns:
            bool: True if successfully removed
        """
        try:
            result = await execute_command_async(
                ["ip", "-6", "addr", "del", f"{address}/{prefix_len}", "dev", interface],
                sudo=True,
                check=False,
            )

            if result.success:
                self.logger.info(f"Removed IPv6 address {address}/{prefix_len} from {interface}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to remove IPv6 address: {e}")
            return False

    async def add_ipv6_route(
        self,
        destination: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None,
        metric: Optional[int] = None,
    ) -> bool:
        """Add IPv6 route.

        Args:
            destination: Destination network in CIDR notation
            gateway: Gateway IPv6 address (optional)
            interface: Network interface (optional)
            metric: Route metric (optional)

        Returns:
            bool: True if successfully added
        """
        if not self.validate_ipv6_network(destination):
            self.logger.error(f"Invalid IPv6 destination: {destination}")
            return False

        try:
            cmd = ["ip", "-6", "route", "add", destination]

            if gateway:
                if not self.validate_ipv6_address(gateway):
                    self.logger.error(f"Invalid IPv6 gateway: {gateway}")
                    return False
                cmd.extend(["via", gateway])

            if interface:
                cmd.extend(["dev", interface])

            if metric is not None:
                cmd.extend(["metric", str(metric)])

            result = await execute_command_async(cmd, sudo=True, check=False)

            if result.success:
                self.logger.info(f"Added IPv6 route: {destination}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to add IPv6 route: {e}")
            return False

    async def delete_ipv6_route(
        self, destination: str, gateway: Optional[str] = None, interface: Optional[str] = None
    ) -> bool:
        """Delete IPv6 route.

        Args:
            destination: Destination network in CIDR notation
            gateway: Gateway IPv6 address (optional)
            interface: Network interface (optional)

        Returns:
            bool: True if successfully deleted
        """
        try:
            cmd = ["ip", "-6", "route", "del", destination]

            if gateway:
                cmd.extend(["via", gateway])

            if interface:
                cmd.extend(["dev", interface])

            result = await execute_command_async(cmd, sudo=True, check=False)

            if result.success:
                self.logger.info(f"Deleted IPv6 route: {destination}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to delete IPv6 route: {e}")
            return False

    async def get_ipv6_routes(self) -> List[dict]:
        """Get all IPv6 routes.

        Returns:
            List[dict]: List of route information dictionaries
        """
        routes = []

        try:
            result = await execute_command_async(["ip", "-6", "route", "show"], check=False)

            if result.success:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        routes.append(self._parse_route_line(line))

            return routes
        except Exception as e:
            self.logger.error(f"Failed to get IPv6 routes: {e}")
            return []

    def _parse_route_line(self, line: str) -> dict:
        """Parse ip route output line.

        Args:
            line: Route output line

        Returns:
            dict: Parsed route information
        """
        parts = line.split()
        route = {"destination": parts[0] if parts else "unknown"}

        for i, part in enumerate(parts):
            if part == "via" and i + 1 < len(parts):
                route["gateway"] = parts[i + 1]
            elif part == "dev" and i + 1 < len(parts):
                route["interface"] = parts[i + 1]
            elif part == "metric" and i + 1 < len(parts):
                route["metric"] = parts[i + 1]
            elif part == "proto" and i + 1 < len(parts):
                route["proto"] = parts[i + 1]

        return route

    async def configure_ipv6_privacy_extensions(self, interface: str, enable: bool = True) -> bool:
        """Configure IPv6 privacy extensions (RFC 4941).

        Privacy extensions generate temporary IPv6 addresses to enhance privacy.

        Args:
            interface: Network interface name
            enable: True to enable privacy extensions

        Returns:
            bool: True if successfully configured
        """
        value = "2" if enable else "0"  # 2 = prefer temporary addresses

        try:
            result = await execute_command_async(
                ["sysctl", "-w", f"net.ipv6.conf.{interface}.use_tempaddr={value}"],
                sudo=True,
                check=False,
            )

            if result.success:
                # Make persistent
                await self._persist_sysctl(f"net.ipv6.conf.{interface}.use_tempaddr", value)

                action = "enabled" if enable else "disabled"
                self.logger.info(f"IPv6 privacy extensions {action} for {interface}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to configure privacy extensions: {e}")
            return False

    async def _persist_sysctl(self, key: str, value: str) -> bool:
        """Persist sysctl configuration.

        Args:
            key: Sysctl key
            value: Sysctl value

        Returns:
            bool: True if successfully persisted
        """
        sysctl_conf = Path("/etc/sysctl.d/99-vpnhd-ipv6.conf")

        try:
            # Read existing config
            existing_config = {}
            if sysctl_conf.exists():
                content = sysctl_conf.read_text()
                for line in content.split("\n"):
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        existing_config[k.strip()] = v.strip()

            # Update config
            existing_config[key] = value

            # Write back
            lines = [f"{k} = {v}" for k, v in existing_config.items()]
            new_content = "\n".join(lines) + "\n"

            # Write with sudo
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                tmp.write(new_content)
                tmp_path = tmp.name

            result = await execute_command_async(
                ["cp", tmp_path, str(sysctl_conf)], sudo=True, check=False
            )

            Path(tmp_path).unlink()  # Clean up temp file

            return result.success
        except Exception as e:
            self.logger.error(f"Failed to persist sysctl: {e}")
            return False

    async def test_ipv6_connectivity(self, target: str = "2001:4860:4860::8888") -> bool:
        """Test IPv6 connectivity by pinging a target.

        Args:
            target: IPv6 address to ping (default: Google Public DNS)

        Returns:
            bool: True if connectivity is working
        """
        try:
            result = await execute_command_async(
                ["ping6", "-c", "3", "-W", "5", target], check=False, timeout=10
            )

            if result.success and "0% packet loss" in result.stdout:
                self.logger.info(f"IPv6 connectivity test to {target}: SUCCESS")
                return True

            self.logger.warning(f"IPv6 connectivity test to {target}: FAILED")
            return False
        except Exception as e:
            self.logger.error(f"IPv6 connectivity test failed: {e}")
            return False
