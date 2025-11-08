"""Network interface management utilities for VPNHD."""

from typing import Optional, List
from pathlib import Path

from ..utils.logging import get_logger
from ..system.commands import execute_command
from ..security.validators import (
    is_valid_interface_name,
    is_valid_ip,
    is_valid_cidr,
    is_valid_netmask,
)
from ..exceptions import ValidationError
from .discovery import get_interface_by_name


logger = get_logger("network.interfaces")


class InterfaceManager:
    """Manages network interfaces."""

    def __init__(self):
        """Initialize interface manager."""
        self.logger = logger

    def bring_interface_up(self, interface: str) -> bool:
        """
        Bring a network interface up.

        Args:
            interface: Interface name

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If interface name is invalid
        """
        # SECURITY: Validate interface name to prevent command injection
        if not is_valid_interface_name(interface):
            raise ValidationError("interface", interface, "Invalid interface name format")

        self.logger.info(f"Bringing interface {interface} up")

        result = execute_command(["ip", "link", "set", interface, "up"], sudo=True, check=False)

        return result.success

    def bring_interface_down(self, interface: str) -> bool:
        """
        Bring a network interface down.

        Args:
            interface: Interface name

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If interface name is invalid
        """
        # SECURITY: Validate interface name to prevent command injection
        if not is_valid_interface_name(interface):
            raise ValidationError("interface", interface, "Invalid interface name format")

        self.logger.info(f"Bringing interface {interface} down")

        result = execute_command(["ip", "link", "set", interface, "down"], sudo=True, check=False)

        return result.success

    def set_ip_address(self, interface: str, ip: str, netmask: str = "24") -> bool:
        """
        Set IP address on an interface.

        Args:
            interface: Interface name
            ip: IP address
            netmask: Network mask (CIDR or dotted decimal)

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If any parameter is invalid
        """
        # SECURITY: Validate all inputs to prevent command injection
        if not is_valid_interface_name(interface):
            raise ValidationError("interface", interface, "Invalid interface name format")

        if not is_valid_ip(ip):
            raise ValidationError("ip", ip, "Invalid IP address format")

        if not is_valid_netmask(netmask):
            raise ValidationError("netmask", netmask, "Invalid netmask format")

        self.logger.info(f"Setting IP {ip}/{netmask} on {interface}")

        result = execute_command(
            ["ip", "addr", "add", f"{ip}/{netmask}", "dev", interface], sudo=True, check=False
        )

        return result.success

    def enable_ip_forwarding(self) -> bool:
        """
        Enable IP forwarding in the kernel.

        Returns:
            bool: True if successful
        """
        self.logger.info("Enabling IP forwarding")

        # Enable temporarily
        result1 = execute_command(["sysctl", "-w", "net.ipv4.ip_forward=1"], sudo=True, check=False)

        # Make permanent using Python file I/O instead of shell pipes
        sysctl_conf = Path("/etc/sysctl.conf")

        if sysctl_conf.exists():
            try:
                # Read current content
                content = sysctl_conf.read_text()

                # Check if already configured
                if "net.ipv4.ip_forward=1" not in content:
                    # Add to sysctl.conf using file manager
                    from ..system.files import FileManager

                    fm = FileManager()

                    # Append to existing content
                    new_content = (
                        content.rstrip()
                        + "\n# Enable IP forwarding for VPN\nnet.ipv4.ip_forward=1\n"
                    )
                    fm.safe_write_file(sysctl_conf, new_content, sudo=True)

                    self.logger.info("Added IP forwarding to sysctl.conf")

            except Exception as e:
                self.logger.warning(f"Could not make IP forwarding permanent: {e}")

        return result1.success

    def disable_ip_forwarding(self) -> bool:
        """
        Disable IP forwarding in the kernel.

        Returns:
            bool: True if successful
        """
        self.logger.info("Disabling IP forwarding")

        result = execute_command(["sysctl", "-w", "net.ipv4.ip_forward=0"], sudo=True, check=False)

        return result.success

    def is_ip_forwarding_enabled(self) -> bool:
        """
        Check if IP forwarding is enabled.

        Returns:
            bool: True if enabled
        """
        result = execute_command(
            ["sysctl", "net.ipv4.ip_forward"], check=False, capture_output=True
        )

        if result.success and "= 1" in result.stdout:
            return True

        return False

    def add_route(self, network: str, gateway: str, interface: Optional[str] = None) -> bool:
        """
        Add a static route.

        Args:
            network: Destination network in CIDR notation
            gateway: Gateway IP address
            interface: Optional interface name

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If any parameter is invalid
        """
        # SECURITY: Validate all inputs
        if not is_valid_cidr(network):
            raise ValidationError("network", network, "Invalid network CIDR format")

        if not is_valid_ip(gateway):
            raise ValidationError("gateway", gateway, "Invalid gateway IP format")

        if interface and not is_valid_interface_name(interface):
            raise ValidationError("interface", interface, "Invalid interface name format")

        # Build command as array
        cmd = ["ip", "route", "add", network, "via", gateway]
        if interface:
            cmd.extend(["dev", interface])

        self.logger.info(
            f"Adding route: {network} via {gateway}" + (f" dev {interface}" if interface else "")
        )

        result = execute_command(cmd, sudo=True, check=False)
        return result.success

    def delete_route(self, network: str) -> bool:
        """
        Delete a static route.

        Args:
            network: Destination network in CIDR notation

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If network is invalid
        """
        # SECURITY: Validate network
        if not is_valid_cidr(network):
            raise ValidationError("network", network, "Invalid network CIDR format")

        self.logger.info(f"Deleting route to {network}")

        result = execute_command(["ip", "route", "del", network], sudo=True, check=False)

        return result.success

    def flush_interface(self, interface: str) -> bool:
        """
        Flush all IP addresses from an interface.

        Args:
            interface: Interface name

        Returns:
            bool: True if successful

        Raises:
            ValidationError: If interface name is invalid
        """
        # SECURITY: Validate interface name
        if not is_valid_interface_name(interface):
            raise ValidationError("interface", interface, "Invalid interface name format")

        self.logger.info(f"Flushing interface {interface}")

        result = execute_command(["ip", "addr", "flush", "dev", interface], sudo=True, check=False)

        return result.success

    def get_interface_stats(self, interface: str) -> Optional[dict]:
        """
        Get statistics for an interface.

        Args:
            interface: Interface name

        Returns:
            Optional[dict]: Interface statistics or None

        Raises:
            ValidationError: If interface name is invalid
        """
        # SECURITY: Validate interface name
        if not is_valid_interface_name(interface):
            raise ValidationError("interface", interface, "Invalid interface name format")

        result = execute_command(
            ["ip", "-s", "link", "show", interface], check=False, capture_output=True
        )

        if result.success:
            # Parse output for stats
            # This is a simplified version
            return {"raw_output": result.stdout}

        return None
