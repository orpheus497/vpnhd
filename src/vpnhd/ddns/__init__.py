"""Dynamic DNS integration for VPNHD."""

from .manager import DDNSManager
from .detector import IPChangeDetector

__all__ = ['DDNSManager', 'IPChangeDetector']
