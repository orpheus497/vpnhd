"""Package manager abstraction layer."""

from .base import PackageManager
from .apt import APTPackageManager
from .dnf import DNFPackageManager
from .factory import PackageManagerFactory, get_package_manager

__all__ = [
    'PackageManager',
    'APTPackageManager',
    'DNFPackageManager',
    'PackageManagerFactory',
    'get_package_manager',
]
