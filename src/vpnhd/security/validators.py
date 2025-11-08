"""Security validators for user input and system data.

This module provides comprehensive validation functions for all
user inputs to prevent injection attacks and ensure data integrity.
"""

import re
import ipaddress
from typing import Optional
from pathlib import Path

from ..utils.logging import get_logger
from ..utils.constants import HOSTNAME_PATTERN, IP_ADDRESS_PATTERN, CIDR_PATTERN

logger = get_logger(__name__)


def is_valid_hostname(hostname: str) -> bool:
    """Validate hostname format.

    Args:
        hostname: Hostname to validate

    Returns:
        True if hostname is valid, False otherwise

    Examples:
        >>> is_valid_hostname("server1")
        True
        >>> is_valid_hostname("my-server.local")
        True
        >>> is_valid_hostname("invalid_host!")
        False
    """
    if not hostname or len(hostname) > 253:
        return False

    # Check each label
    labels = hostname.split('.')
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', label, re.IGNORECASE):
            return False

    return True


def is_valid_ip(ip_address: str) -> bool:
    """Validate IP address format (IPv4 or IPv6).

    Args:
        ip_address: IP address to validate

    Returns:
        True if IP address is valid, False otherwise

    Examples:
        >>> is_valid_ip("192.168.1.1")
        True
        >>> is_valid_ip("2001:db8::1")
        True
        >>> is_valid_ip("999.999.999.999")
        False
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def is_valid_ipv4(ip_address: str) -> bool:
    """Validate IPv4 address format specifically.

    Args:
        ip_address: IPv4 address to validate

    Returns:
        True if valid IPv4, False otherwise
    """
    try:
        addr = ipaddress.ip_address(ip_address)
        return isinstance(addr, ipaddress.IPv4Address)
    except ValueError:
        return False


def is_valid_cidr(cidr: str) -> bool:
    """Validate CIDR notation.

    Args:
        cidr: CIDR notation to validate (e.g., "10.0.0.0/24")

    Returns:
        True if valid CIDR, False otherwise

    Examples:
        >>> is_valid_cidr("10.66.66.0/24")
        True
        >>> is_valid_cidr("192.168.1.0/32")
        True
        >>> is_valid_cidr("10.0.0.0/99")
        False
    """
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def is_valid_port(port: int) -> bool:
    """Validate port number.

    Args:
        port: Port number to validate

    Returns:
        True if valid port (1-65535), False otherwise

    Examples:
        >>> is_valid_port(22)
        True
        >>> is_valid_port(51820)
        True
        >>> is_valid_port(0)
        False
        >>> is_valid_port(70000)
        False
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def is_valid_mac_address(mac: str) -> bool:
    """Validate MAC address format.

    Args:
        mac: MAC address to validate

    Returns:
        True if valid MAC address, False otherwise

    Examples:
        >>> is_valid_mac_address("00:11:22:33:44:55")
        True
        >>> is_valid_mac_address("00-11-22-33-44-55")
        True
        >>> is_valid_mac_address("invalid")
        False
    """
    # Support both : and - separators
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))


def is_safe_path(path: str) -> bool:
    """Check if path is safe (no directory traversal).

    Args:
        path: File path to validate

    Returns:
        True if path is safe, False otherwise

    Examples:
        >>> is_safe_path("/etc/wireguard/wg0.conf")
        True
        >>> is_safe_path("../../etc/passwd")
        False
    """
    try:
        # Resolve path and check for traversal
        p = Path(path).resolve()

        # Check for common dangerous patterns
        dangerous_patterns = ['..', '~']
        path_str = str(p)

        for pattern in dangerous_patterns:
            if pattern in path_str:
                return False

        return True

    except Exception as e:
        logger.warning(f"Path validation error: {e}")
        return False


def is_valid_wireguard_key(key: str) -> bool:
    """Validate WireGuard key format.

    Args:
        key: WireGuard key to validate (base64 encoded)

    Returns:
        True if valid key format, False otherwise

    Examples:
        >>> is_valid_wireguard_key("cGFzc3dvcmQxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OQ==")
        True
    """
    # WireGuard keys are 44 characters base64
    if len(key) != 44:
        return False

    # Check base64 format
    pattern = r'^[A-Za-z0-9+/]{43}=$'
    return bool(re.match(pattern, key))


def sanitize_hostname(hostname: str) -> str:
    """Sanitize hostname by removing invalid characters.

    Args:
        hostname: Hostname to sanitize

    Returns:
        Sanitized hostname

    Examples:
        >>> sanitize_hostname("My Server!")
        "myserver"
    """
    # Convert to lowercase
    hostname = hostname.lower()

    # Remove invalid characters
    hostname = re.sub(r'[^a-z0-9-]', '', hostname)

    # Remove leading/trailing hyphens
    hostname = hostname.strip('-')

    # Limit length
    hostname = hostname[:63]

    return hostname


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing dangerous characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename

    Examples:
        >>> sanitize_filename("my file!.conf")
        "my_file.conf"
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

    # Prevent hidden files
    if filename.startswith('.'):
        filename = '_' + filename[1:]

    return filename


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
