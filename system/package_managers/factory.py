"""Package manager factory for automatic detection."""

from typing import Optional, Type, List
from .base import PackageManager
from .apt import APTPackageManager
from .dnf import DNFPackageManager
from ...utils.logging import get_logger

logger = get_logger(__name__)


class PackageManagerFactory:
    """Factory for detecting and creating appropriate package manager."""

    # Registry of package managers in order of preference
    MANAGERS: List[Type[PackageManager]] = [
        APTPackageManager,
        DNFPackageManager,
    ]

    @classmethod
    async def detect_package_manager(cls) -> Optional[PackageManager]:
        """Detect and return the appropriate package manager for the system.

        Returns:
            Optional[PackageManager]: Package manager instance or None
        """
        for manager_class in cls.MANAGERS:
            manager = manager_class()

            try:
                if await manager.is_available():
                    logger.info(f"Detected package manager: {manager.name}")
                    return manager
            except Exception as e:
                logger.debug(f"Error checking {manager.name} availability: {e}")
                continue

        logger.error("No supported package manager found")
        return None

    @classmethod
    async def get_package_manager(cls, name: Optional[str] = None) -> Optional[PackageManager]:
        """Get a specific package manager or auto-detect.

        Args:
            name: Package manager name (apt, dnf) or None for auto-detect

        Returns:
            Optional[PackageManager]: Package manager instance or None
        """
        if name is None:
            return await cls.detect_package_manager()

        # Find specific package manager
        for manager_class in cls.MANAGERS:
            manager = manager_class()
            if manager.name == name.lower():
                if await manager.is_available():
                    return manager
                else:
                    logger.error(f"Package manager {name} not available")
                    return None

        logger.error(f"Unknown package manager: {name}")
        return None

    @classmethod
    def list_supported_managers(cls) -> List[str]:
        """List all supported package managers.

        Returns:
            List of package manager names
        """
        return [m().name for m in cls.MANAGERS]


async def get_package_manager(name: Optional[str] = None) -> Optional[PackageManager]:
    """Convenience function to get package manager.

    Args:
        name: Package manager name or None for auto-detect

    Returns:
        Optional[PackageManager]: Package manager instance or None
    """
    return await PackageManagerFactory.get_package_manager(name)
