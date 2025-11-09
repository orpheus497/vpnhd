"""
VPNHD - VPN Helper Daemon

A privacy-first automation tool for setting up WireGuard-based home VPN systems.

Author: orpheus497
License: GPL-3.0
"""

from .__version__ import __author__, __version__
from .cli import main

__all__ = ["main", "__version__", "__author__"]
