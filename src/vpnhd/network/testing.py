"""Network connectivity testing utilities for VPNHD."""

import socket
import urllib.request
import urllib.error
from typing import Optional, List

from ..utils.logging import get_logger
from ..utils.constants import PORT_CHECK_SERVICES
from ..system.commands import execute_command


logger = get_logger("network.testing")


def test_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: int = 5) -> bool:
    """
    Test network connectivity to a host.

    Args:
        host: Host to test (default: Google DNS)
        port: Port to test (default: 53/DNS)
        timeout: Timeout in seconds

    Returns:
        bool: True if connected successfully
    """
    try:
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()

        return result == 0

    except Exception as e:
        logger.warning(f"Connectivity test failed: {e}")
        return False


def test_port_open(host: str, port: int, timeout: int = 5) -> bool:
    """
    Test if a port is open on a host.

    Args:
        host: Host to test
        port: Port number
        timeout: Timeout in seconds

    Returns:
        bool: True if port is open
    """
    try:
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            logger.debug(f"Port {port} is open on {host}")
            return True
        else:
            logger.debug(f"Port {port} is closed on {host}")
            return False

    except Exception as e:
        logger.warning(f"Port test failed: {e}")
        return False


def ping_host(host: str, count: int = 4, timeout: int = 5) -> bool:
    """
    Ping a host.

    Args:
        host: Host to ping
        count: Number of ping packets
        timeout: Timeout in seconds

    Returns:
        bool: True if ping successful
    """
    result = execute_command(
        f"ping -c {count} -W {timeout} {host}",
        check=False,
        capture_output=True
    )

    return result.success


def get_public_ip() -> Optional[str]:
    """
    Get public IP address using external service.

    Returns:
        Optional[str]: Public IP address or None if failed
    """
    for service_url in PORT_CHECK_SERVICES:
        try:
            logger.debug(f"Trying to get public IP from {service_url}")

            with urllib.request.urlopen(service_url, timeout=10) as response:
                ip = response.read().decode('utf-8').strip()

                # Validate it's an IP address
                from .validation import validate_ip_address
                if validate_ip_address(ip):
                    logger.info(f"Public IP: {ip}")
                    return ip

        except Exception as e:
            logger.debug(f"Failed to get public IP from {service_url}: {e}")
            continue

    logger.error("Failed to get public IP from all services")
    return None


def test_dns_resolution(hostname: str = "google.com", timeout: int = 5) -> bool:
    """
    Test DNS resolution.

    Args:
        hostname: Hostname to resolve
        timeout: Timeout in seconds

    Returns:
        bool: True if resolution successful
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(hostname)
        return True

    except Exception as e:
        logger.warning(f"DNS resolution failed: {e}")
        return False


def test_internet_connectivity() -> bool:
    """
    Test general internet connectivity.

    Returns:
        bool: True if internet is accessible
    """
    # Test DNS resolution
    if not test_dns_resolution():
        logger.warning("DNS resolution failed")
        return False

    # Test connectivity to well-known servers
    test_hosts = [
        ("8.8.8.8", 53),  # Google DNS
        ("1.1.1.1", 53),  # Cloudflare DNS
    ]

    for host, port in test_hosts:
        if test_connectivity(host, port):
            logger.debug(f"Successfully connected to {host}:{port}")
            return True

    logger.error("Failed to connect to any test hosts")
    return False


def traceroute(host: str, max_hops: int = 30) -> Optional[str]:
    """
    Perform traceroute to a host.

    Args:
        host: Destination host
        max_hops: Maximum number of hops

    Returns:
        Optional[str]: Traceroute output or None if failed
    """
    result = execute_command(
        f"traceroute -m {max_hops} {host}",
        check=False,
        capture_output=True,
        timeout=60
    )

    if result.success:
        return result.stdout

    return None


def check_port_forwarding(external_ip: str, port: int, timeout: int = 10) -> bool:
    """
    Check if port forwarding is working.

    Args:
        external_ip: External/public IP address
        port: Port to check
        timeout: Timeout in seconds

    Returns:
        bool: True if port is accessible from outside
    """
    logger.info(f"Testing port forwarding for {external_ip}:{port}")

    # Note: This is a basic check that requires the service to be running
    # For WireGuard (UDP), this won't work perfectly
    # A real check would require an external service

    # For now, just verify the port is listening locally
    result = execute_command(
        f"ss -tuln | grep ':{port}'",
        check=False,
        capture_output=True
    )

    if result.success and str(port) in result.stdout:
        logger.info(f"Port {port} is listening locally")
        return True

    logger.warning(f"Port {port} does not appear to be listening")
    return False


def measure_latency(host: str, count: int = 10) -> Optional[float]:
    """
    Measure latency to a host in milliseconds.

    Args:
        host: Host to ping
        count: Number of ping packets

    Returns:
        Optional[float]: Average latency in ms or None if failed
    """
    result = execute_command(
        f"ping -c {count} {host}",
        check=False,
        capture_output=True
    )

    if result.success:
        # Parse average latency from output
        import re
        match = re.search(r'avg[^0-9]+([\d.]+)', result.stdout)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

    return None


def test_vpn_connectivity(vpn_server_ip: str, vpn_interface: str = "wg0") -> bool:
    """
    Test VPN connectivity.

    Args:
        vpn_server_ip: VPN server IP address
        vpn_interface: VPN interface name

    Returns:
        bool: True if VPN is connected and working
    """
    # Check if VPN interface exists
    result = execute_command(
        f"ip link show {vpn_interface}",
        check=False,
        capture_output=True
    )

    if not result.success:
        logger.error(f"VPN interface {vpn_interface} not found")
        return False

    # Ping VPN server
    if not ping_host(vpn_server_ip, count=3):
        logger.error(f"Cannot ping VPN server at {vpn_server_ip}")
        return False

    logger.info("VPN connectivity test passed")
    return True
