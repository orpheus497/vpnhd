"""Network utilities module for VPNHD."""

from .discovery import discover_network, get_primary_interface, get_default_gateway, detect_lan_subnet, NetworkInfo, NetworkInterface
from .validation import validate_ip_address, validate_network, validate_ip_in_network, is_private_ip
from .testing import test_connectivity, test_port_open, get_public_ip
from .interfaces import InterfaceManager

__all__ = [
    'discover_network',
    'get_primary_interface',
    'get_default_gateway',
    'detect_lan_subnet',
    'NetworkInfo',
    'NetworkInterface',
    'validate_ip_address',
    'validate_network',
    'validate_ip_in_network',
    'is_private_ip',
    'test_connectivity',
    'test_port_open',
    'get_public_ip',
    'InterfaceManager'
]
