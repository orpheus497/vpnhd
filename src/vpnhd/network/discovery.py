"""Network discovery utilities for VPNHD."""

import socket
from dataclasses import dataclass
from typing import Dict, List, Optional

import psutil

from ..system.commands import execute_command, get_command_output
from ..utils.logging import get_logger
from .validation import calculate_subnet, validate_ip_address

logger = get_logger("network.discovery")


@dataclass
class NetworkInterface:
    """Network interface information."""

    name: str
    mac_address: str
    ip_address: Optional[str]
    netmask: Optional[str]
    broadcast: Optional[str]
    is_up: bool
    is_loopback: bool


@dataclass
class NetworkInfo:
    """Complete network information."""

    interfaces: List[NetworkInterface]
    default_gateway: Optional[str]
    dns_servers: List[str]
    hostname: str


def get_all_interfaces() -> List[NetworkInterface]:
    """
    Get information about all network interfaces.

    Returns:
        List[NetworkInterface]: List of network interfaces
    """
    interfaces = []

    try:
        # Get all network interfaces with psutil
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        for iface_name, addrs in net_if_addrs.items():
            try:
                # Get MAC address
                mac = None
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        mac = addr.address
                        break

                # Get IPv4 information
                ip_address = None
                netmask = None
                broadcast = None

                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        ip_address = addr.address
                        netmask = addr.netmask
                        broadcast = addr.broadcast
                        break

                # Check if interface is up
                is_up = False
                if iface_name in net_if_stats:
                    is_up = net_if_stats[iface_name].isup

                # Check if loopback
                is_loopback = iface_name == "lo" or (ip_address and ip_address.startswith("127."))

                interfaces.append(
                    NetworkInterface(
                        name=iface_name,
                        mac_address=mac or "",
                        ip_address=ip_address,
                        netmask=netmask,
                        broadcast=broadcast,
                        is_up=is_up,
                        is_loopback=is_loopback,
                    )
                )

            except Exception as e:
                logger.warning(f"Error getting info for interface {iface_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error listing interfaces: {e}")

    return interfaces


def get_primary_interface() -> Optional[NetworkInterface]:
    """
    Get primary network interface (used for default route).

    Returns:
        Optional[NetworkInterface]: Primary interface or None
    """
    try:
        # Get default gateway info using ip route
        output = get_command_output("ip route show default")
        if output:
            parts = output.split()
            if "dev" in parts:
                dev_index = parts.index("dev")
                if dev_index + 1 < len(parts):
                    default_iface = parts[dev_index + 1]

                    # Get information for this interface
                    interfaces = get_all_interfaces()
                    for iface in interfaces:
                        if iface.name == default_iface:
                            return iface

    except Exception as e:
        logger.error(f"Error getting primary interface: {e}")

    # Fallback: return first non-loopback interface with IP
    interfaces = get_all_interfaces()
    for iface in interfaces:
        if not iface.is_loopback and iface.ip_address:
            return iface

    return None


def get_default_gateway() -> Optional[str]:
    """
    Get default gateway IP address.

    Returns:
        Optional[str]: Gateway IP or None
    """
    try:
        # Use ip route command to get default gateway
        output = get_command_output("ip route show default")
        if output:
            parts = output.split()
            if "via" in parts:
                via_index = parts.index("via")
                if via_index + 1 < len(parts):
                    gateway = parts[via_index + 1]
                    if validate_ip_address(gateway):
                        return gateway

    except Exception as e:
        logger.error(f"Error getting default gateway: {e}")

    return None


def detect_lan_subnet() -> Optional[str]:
    """
    Detect LAN subnet (e.g., "192.168.1.0/24").

    Returns:
        Optional[str]: Subnet in CIDR notation or None
    """
    primary = get_primary_interface()

    if primary and primary.ip_address and primary.netmask:
        subnet = calculate_subnet(primary.ip_address, primary.netmask)
        logger.debug(f"Detected LAN subnet: {subnet}")
        return subnet

    return None


def get_dns_servers() -> List[str]:
    """
    Get configured DNS servers.

    Returns:
        List[str]: List of DNS server IPs
    """
    dns_servers = []

    try:
        # Try reading /etc/resolv.conf
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("nameserver"):
                    parts = line.split()
                    if len(parts) >= 2:
                        dns_ip = parts[1]
                        if validate_ip_address(dns_ip):
                            dns_servers.append(dns_ip)

    except Exception as e:
        logger.warning(f"Error reading DNS servers: {e}")

    return dns_servers


def get_hostname() -> str:
    """
    Get system hostname.

    Returns:
        str: Hostname
    """
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def discover_network() -> NetworkInfo:
    """
    Discover current network configuration.

    Returns:
        NetworkInfo: Complete network information
    """
    logger.info("Discovering network configuration")

    interfaces = get_all_interfaces()
    gateway = get_default_gateway()
    dns = get_dns_servers()
    hostname = get_hostname()

    network_info = NetworkInfo(
        interfaces=interfaces, default_gateway=gateway, dns_servers=dns, hostname=hostname
    )

    logger.debug(f"Found {len(interfaces)} interfaces")
    logger.debug(f"Default gateway: {gateway}")
    logger.debug(f"DNS servers: {dns}")

    return network_info


def get_interface_by_name(name: str) -> Optional[NetworkInterface]:
    """
    Get interface information by name.

    Args:
        name: Interface name (e.g., "eth0")

    Returns:
        Optional[NetworkInterface]: Interface info or None
    """
    interfaces = get_all_interfaces()

    for iface in interfaces:
        if iface.name == name:
            return iface

    return None


def get_mac_address(interface: str) -> Optional[str]:
    """
    Get MAC address for an interface.

    Args:
        interface: Interface name

    Returns:
        Optional[str]: MAC address or None
    """
    iface = get_interface_by_name(interface)
    if iface:
        return iface.mac_address

    return None


def is_interface_up(interface: str) -> bool:
    """
    Check if an interface is up.

    Args:
        interface: Interface name

    Returns:
        bool: True if interface is up
    """
    iface = get_interface_by_name(interface)
    if iface:
        return iface.is_up

    return False
