"""Network validation utilities for VPNHD."""

import ipaddress
from typing import Optional

from ..utils.logging import get_logger

logger = get_logger("network.validation")


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


def is_private_ip(ip: str) -> bool:
    """
    Check if IP address is in a private range.

    Args:
        ip: IP address

    Returns:
        bool: True if IP is private
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_private
    except (ValueError, ipaddress.AddressValueError):
        return False


def is_loopback_ip(ip: str) -> bool:
    """
    Check if IP address is loopback.

    Args:
        ip: IP address

    Returns:
        bool: True if IP is loopback
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_loopback
    except (ValueError, ipaddress.AddressValueError):
        return False


def get_network_info(network: str) -> Optional[dict]:
    """
    Get information about a network.

    Args:
        network: Network in CIDR notation

    Returns:
        Optional[dict]: Network information or None if invalid
    """
    try:
        net_obj = ipaddress.IPv4Network(network, strict=False)

        return {
            "network": str(net_obj.network_address),
            "netmask": str(net_obj.netmask),
            "broadcast": str(net_obj.broadcast_address),
            "num_addresses": net_obj.num_addresses,
            "prefix_length": net_obj.prefixlen,
            "first_host": str(net_obj.network_address + 1) if net_obj.num_addresses > 2 else None,
            "last_host": str(net_obj.broadcast_address - 1) if net_obj.num_addresses > 2 else None,
        }

    except Exception as e:
        logger.error(f"Failed to get network info: {e}")
        return None


def cidr_to_netmask(cidr: int) -> str:
    """
    Convert CIDR prefix length to dotted decimal netmask.

    Args:
        cidr: CIDR prefix length (e.g., 24)

    Returns:
        str: Netmask in dotted decimal (e.g., "255.255.255.0")
    """
    try:
        network = ipaddress.IPv4Network(f"0.0.0.0/{cidr}", strict=False)
        return str(network.netmask)
    except Exception:
        return ""


def netmask_to_cidr(netmask: str) -> Optional[int]:
    """
    Convert dotted decimal netmask to CIDR prefix length.

    Args:
        netmask: Netmask in dotted decimal (e.g., "255.255.255.0")

    Returns:
        Optional[int]: CIDR prefix length (e.g., 24) or None if invalid
    """
    try:
        network = ipaddress.IPv4Network(f"0.0.0.0/{netmask}", strict=False)
        return network.prefixlen
    except Exception:
        return None


def ip_in_same_network(ip1: str, ip2: str, netmask: str) -> bool:
    """
    Check if two IP addresses are in the same network.

    Args:
        ip1: First IP address
        ip2: Second IP address
        netmask: Network mask

    Returns:
        bool: True if in same network
    """
    try:
        # Create network from first IP
        network1 = ipaddress.IPv4Network(f"{ip1}/{netmask}", strict=False)

        # Check if second IP is in that network
        ip2_obj = ipaddress.IPv4Address(ip2)

        return ip2_obj in network1
    except Exception:
        return False


def calculate_subnet(ip: str, netmask: str) -> Optional[str]:
    """
    Calculate subnet from IP and netmask.

    Args:
        ip: IP address
        netmask: Netmask (dotted decimal or CIDR)

    Returns:
        Optional[str]: Subnet in CIDR notation or None if invalid
    """
    try:
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network)
    except Exception:
        return None
