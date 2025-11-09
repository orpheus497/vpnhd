"""Dynamic DNS integration for VPNHD."""

from .detector import IPChangeDetector
from .manager import DDNSManager

__all__ = ["DDNSManager", "IPChangeDetector"]
