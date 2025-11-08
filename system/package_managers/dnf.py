"""DNF package manager implementation (Fedora/RHEL/CentOS)."""

from typing import List, Optional
from .base import PackageManager
from ...utils.command import execute_command_async


class DNFPackageManager(PackageManager):
    """DNF package manager for Fedora/RHEL/CentOS systems."""

    @property
    def name(self) -> str:
        return "dnf"

    async def is_available(self) -> bool:
        """Check if DNF is available."""
        result = await execute_command_async(
            ['which', 'dnf'],
            check=False
        )
        return result.success

    async def update_cache(self) -> bool:
        """Update DNF package cache."""
        self.logger.info("Updating DNF package cache...")

        result = await execute_command_async(
            ['dnf', 'check-update'],
            sudo=True,
            check=False
        )

        # check-update returns 100 if updates are available, 0 if none
        if result.returncode in [0, 100]:
            self.logger.info("DNF cache updated successfully")
            return True
        else:
            self.logger.error(f"Failed to update DNF cache: {result.stderr}")
            return False

    async def install_package(
        self,
        package: str,
        version: Optional[str] = None
    ) -> bool:
        """Install a package using DNF."""
        package_spec = f"{package}-{version}" if version else package

        self.logger.info(f"Installing package: {package_spec}")

        result = await execute_command_async(
            ['dnf', 'install', '-y', package_spec],
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info(f"Package {package} installed successfully")
            return True
        else:
            self.logger.error(f"Failed to install {package}: {result.stderr}")
            return False

    async def install_packages(self, packages: List[str]) -> bool:
        """Install multiple packages using DNF."""
        if not packages:
            return True

        self.logger.info(f"Installing packages: {', '.join(packages)}")

        result = await execute_command_async(
            ['dnf', 'install', '-y'] + packages,
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info("All packages installed successfully")
            return True
        else:
            self.logger.error(f"Failed to install packages: {result.stderr}")
            return False

    async def remove_package(self, package: str) -> bool:
        """Remove a package using DNF."""
        self.logger.info(f"Removing package: {package}")

        result = await execute_command_async(
            ['dnf', 'remove', '-y', package],
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info(f"Package {package} removed successfully")
            return True
        else:
            self.logger.error(f"Failed to remove {package}: {result.stderr}")
            return False

    async def is_package_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        result = await execute_command_async(
            ['rpm', '-q', package],
            check=False
        )

        return result.success

    async def get_package_version(self, package: str) -> Optional[str]:
        """Get installed package version."""
        result = await execute_command_async(
            ['rpm', '-q', '--queryformat', '%{VERSION}-%{RELEASE}', package],
            check=False
        )

        if result.success:
            return result.stdout.strip()

        return None

    async def upgrade_package(self, package: str) -> bool:
        """Upgrade a package to latest version."""
        self.logger.info(f"Upgrading package: {package}")

        result = await execute_command_async(
            ['dnf', 'upgrade', '-y', package],
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info(f"Package {package} upgraded successfully")
            return True
        else:
            self.logger.error(f"Failed to upgrade {package}: {result.stderr}")
            return False

    async def upgrade_all(self) -> bool:
        """Upgrade all installed packages."""
        self.logger.info("Upgrading all packages...")

        result = await execute_command_async(
            ['dnf', 'upgrade', '-y'],
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info("All packages upgraded successfully")
            return True
        else:
            self.logger.error(f"Failed to upgrade packages: {result.stderr}")
            return False

    async def autoremove(self) -> bool:
        """Remove unused packages."""
        self.logger.info("Removing unused packages...")

        result = await execute_command_async(
            ['dnf', 'autoremove', '-y'],
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info("Unused packages removed successfully")
            return True
        else:
            self.logger.error(f"Failed to autoremove: {result.stderr}")
            return False

    async def clean_cache(self) -> bool:
        """Clean DNF cache."""
        self.logger.info("Cleaning DNF cache...")

        result = await execute_command_async(
            ['dnf', 'clean', 'all'],
            sudo=True,
            check=False
        )

        if result.success:
            self.logger.info("DNF cache cleaned successfully")
            return True
        else:
            self.logger.error(f"Failed to clean cache: {result.stderr}")
            return False
