"""Base interface for package managers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ...utils.logging import get_logger

logger = get_logger(__name__)


class PackageManager(ABC):
    """Abstract base class for package managers."""

    def __init__(self):
        """Initialize package manager."""
        self.logger = logger

    @property
    @abstractmethod
    def name(self) -> str:
        """Get package manager name."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this package manager is available on the system.

        Returns:
            bool: True if package manager is available
        """
        pass

    @abstractmethod
    async def update_cache(self) -> bool:
        """Update package cache/repository information.

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    async def install_package(self, package: str, version: Optional[str] = None) -> bool:
        """Install a package.

        Args:
            package: Package name
            version: Optional specific version

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    async def install_packages(self, packages: List[str]) -> bool:
        """Install multiple packages.

        Args:
            packages: List of package names

        Returns:
            bool: True if all successful
        """
        pass

    @abstractmethod
    async def remove_package(self, package: str) -> bool:
        """Remove a package.

        Args:
            package: Package name

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    async def is_package_installed(self, package: str) -> bool:
        """Check if a package is installed.

        Args:
            package: Package name

        Returns:
            bool: True if installed
        """
        pass

    @abstractmethod
    async def get_package_version(self, package: str) -> Optional[str]:
        """Get installed package version.

        Args:
            package: Package name

        Returns:
            Optional[str]: Version string or None if not installed
        """
        pass

    @abstractmethod
    async def upgrade_package(self, package: str) -> bool:
        """Upgrade a package to latest version.

        Args:
            package: Package name

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    async def upgrade_all(self) -> bool:
        """Upgrade all installed packages.

        Returns:
            bool: True if successful
        """
        pass

    async def ensure_packages_installed(
        self, packages: List[str], update_cache: bool = True
    ) -> Dict[str, bool]:
        """Ensure packages are installed, installing if necessary.

        Args:
            packages: List of package names
            update_cache: Update cache before checking

        Returns:
            Dict mapping package names to installation success
        """
        results = {}

        # Update cache first if requested
        if update_cache:
            await self.update_cache()

        # Check and install each package
        for package in packages:
            installed = await self.is_package_installed(package)

            if installed:
                self.logger.info(f"Package {package} is already installed")
                results[package] = True
            else:
                self.logger.info(f"Installing package {package}...")
                success = await self.install_package(package)
                results[package] = success

                if success:
                    self.logger.info(f"Package {package} installed successfully")
                else:
                    self.logger.error(f"Failed to install package {package}")

        return results

    async def get_info(self) -> Dict[str, Any]:
        """Get package manager information.

        Returns:
            Dict with package manager info
        """
        available = await self.is_available()

        return {
            "name": self.name,
            "available": available,
        }
