"""
VPNHD - VPN Helper Daemon

A privacy-first automation tool for setting up WireGuard-based home VPN systems.

Author: orpheus497
License: GPL-3.0
"""

from .cli import main
from .__version__ import __version__, __author__

__all__ = ['main', '__version__', '__author__']
