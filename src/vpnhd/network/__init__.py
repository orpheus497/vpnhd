"""Network utilities module for VPNHD."""

from .discovery import (
    NetworkInfo,
    NetworkInterface,
    detect_lan_subnet,
    discover_network,
    get_default_gateway,
    get_primary_interface,
)
from .interfaces import InterfaceManager
from .testing import get_public_ip, test_connectivity, test_port_open
from .validation import is_private_ip, validate_ip_address, validate_ip_in_network, validate_network

__all__ = [
    "discover_network",
    "get_primary_interface",
    "get_default_gateway",
    "detect_lan_subnet",
    "NetworkInfo",
    "NetworkInterface",
    "validate_ip_address",
    "validate_network",
    "validate_ip_in_network",
    "is_private_ip",
    "test_connectivity",
    "test_port_open",
    "get_public_ip",
    "InterfaceManager",
]
