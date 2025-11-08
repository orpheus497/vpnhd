"""Configuration validation for VPNHD."""

import ipaddress
from typing import Dict, Any, List, Optional, Tuple
import re

from ..utils.helpers import validate_hostname, validate_port


class ConfigValidator:
    """Validates VPNHD configuration data."""

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        Validate IP address format.

        Args:
            ip: IP address string

        Returns:
            bool: True if valid IPv4 address
        """
        try:
            ipaddress.IPv4Address(ip)
            return True
        except (ValueError, ipaddress.AddressValueError):
            return False

    @staticmethod
    def validate_network(network: str) -> bool:
        """
        Validate network in CIDR notation.

        Args:
            network: Network string (e.g., "192.168.1.0/24")

        Returns:
            bool: True if valid network
        """
        try:
            ipaddress.IPv4Network(network, strict=False)
            return True
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            return False

    @staticmethod
    def validate_ip_in_network(ip: str, network: str) -> bool:
        """
        Check if IP address is within a network.

        Args:
            ip: IP address
            network: Network in CIDR notation

        Returns:
            bool: True if IP is in network
        """
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            network_obj = ipaddress.IPv4Network(network, strict=False)
            return ip_obj in network_obj
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            return False

    @staticmethod
    def validate_hostname_format(hostname: str) -> bool:
        """
        Validate hostname format.

        Args:
            hostname: Hostname string

        Returns:
            bool: True if valid
        """
        return validate_hostname(hostname)

    @staticmethod
    def validate_port_number(port: int) -> bool:
        """
        Validate port number.

        Args:
            port: Port number

        Returns:
            bool: True if valid (1-65535)
        """
        return validate_port(port)

    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """
        Validate MAC address format.

        Args:
            mac: MAC address string

        Returns:
            bool: True if valid
        """
        pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        return bool(re.match(pattern, mac))

    @staticmethod
    def validate_phase_number(phase: int) -> bool:
        """
        Validate phase number.

        Args:
            phase: Phase number

        Returns:
            bool: True if valid (1-8)
        """
        return 1 <= phase <= 8

    @staticmethod
    def validate_network_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate network configuration section.

        Args:
            config: Network configuration dictionary

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Validate LAN configuration
        if "lan" in config:
            lan = config["lan"]

            if lan.get("router_ip") and not ConfigValidator.validate_ip_address(lan["router_ip"]):
                errors.append(f"Invalid LAN router IP: {lan['router_ip']}")

            if lan.get("server_ip") and not ConfigValidator.validate_ip_address(lan["server_ip"]):
                errors.append(f"Invalid LAN server IP: {lan['server_ip']}")

            if lan.get("subnet") and not ConfigValidator.validate_network(lan["subnet"]):
                errors.append(f"Invalid LAN subnet: {lan['subnet']}")

            # Check if server IP is in subnet
            if lan.get("server_ip") and lan.get("subnet"):
                if not ConfigValidator.validate_ip_in_network(lan["server_ip"], lan["subnet"]):
                    errors.append(f"Server IP {lan['server_ip']} is not in subnet {lan['subnet']}")

        # Validate VPN configuration
        if "vpn" in config:
            vpn = config["vpn"]

            if vpn.get("network") and not ConfigValidator.validate_network(vpn["network"]):
                errors.append(f"Invalid VPN network: {vpn['network']}")

            if vpn.get("server_ip") and not ConfigValidator.validate_ip_address(vpn["server_ip"]):
                errors.append(f"Invalid VPN server IP: {vpn['server_ip']}")

            # Check if VPN server IP is in VPN network
            if vpn.get("server_ip") and vpn.get("network"):
                if not ConfigValidator.validate_ip_in_network(vpn["server_ip"], vpn["network"]):
                    errors.append(
                        f"VPN server IP {vpn['server_ip']} is not in VPN network {vpn['network']}"
                    )

            # Validate client IPs
            if "clients" in vpn:
                for client_name, client_config in vpn["clients"].items():
                    if "ip" in client_config:
                        if not ConfigValidator.validate_ip_address(client_config["ip"]):
                            errors.append(
                                f"Invalid client IP for {client_name}: {client_config['ip']}"
                            )
                        elif vpn.get("network"):
                            if not ConfigValidator.validate_ip_in_network(
                                client_config["ip"], vpn["network"]
                            ):
                                errors.append(
                                    f"Client IP {client_config['ip']} for {client_name} "
                                    f"is not in VPN network"
                                )

        # Validate ports
        if "wireguard_port" in config:
            if not ConfigValidator.validate_port_number(config["wireguard_port"]):
                errors.append(f"Invalid WireGuard port: {config['wireguard_port']}")

        if "ssh_port" in config:
            if not ConfigValidator.validate_port_number(config["ssh_port"]):
                errors.append(f"Invalid SSH port: {config['ssh_port']}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_server_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate server configuration section.

        Args:
            config: Server configuration dictionary

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        if config.get("hostname") and not ConfigValidator.validate_hostname_format(
            config["hostname"]
        ):
            errors.append(f"Invalid hostname format: {config['hostname']}")

        if config.get("lan_ip") and not ConfigValidator.validate_ip_address(config["lan_ip"]):
            errors.append(f"Invalid server LAN IP: {config['lan_ip']}")

        if config.get("mac_address") and not ConfigValidator.validate_mac_address(
            config["mac_address"]
        ):
            errors.append(f"Invalid MAC address: {config['mac_address']}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_full_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate entire configuration.

        Args:
            config: Full configuration dictionary

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        all_errors = []

        # Validate required top-level keys
        required_keys = ["version", "network", "server", "clients", "security", "phases", "paths"]
        for key in required_keys:
            if key not in config:
                all_errors.append(f"Missing required configuration key: {key}")

        # Validate network configuration
        if "network" in config:
            valid, errors = ConfigValidator.validate_network_config(config["network"])
            all_errors.extend(errors)

        # Validate server configuration
        if "server" in config:
            valid, errors = ConfigValidator.validate_server_config(config["server"])
            all_errors.extend(errors)

        return len(all_errors) == 0, all_errors

    @staticmethod
    def validate_wireguard_key(key: str, key_type: str = "private") -> bool:
        """
        Validate WireGuard key format.

        Args:
            key: Key string
            key_type: "private" or "public"

        Returns:
            bool: True if valid WireGuard key
        """
        if not key:
            return False

        # WireGuard keys are base64 encoded 32-byte values (44 characters with padding)
        if len(key) != 44:
            return False

        # Check if it's valid base64
        import base64

        try:
            decoded = base64.b64decode(key)
            return len(decoded) == 32
        except Exception:
            return False
