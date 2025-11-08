"""APT package manager implementation (Debian/Ubuntu)."""

from typing import List, Optional
from .base import PackageManager
from ...utils.command import execute_command_async


class APTPackageManager(PackageManager):
    """APT package manager for Debian/Ubuntu systems."""

    @property
    def name(self) -> str:
        return "apt"

    async def is_available(self) -> bool:
        """Check if APT is available."""
        result = await execute_command_async(["which", "apt-get"], check=False)
        return result.success

    async def update_cache(self) -> bool:
        """Update APT package cache."""
        self.logger.info("Updating APT package cache...")

        result = await execute_command_async(["apt-get", "update"], sudo=True, check=False)

        if result.success:
            self.logger.info("APT cache updated successfully")
            return True
        else:
            self.logger.error(f"Failed to update APT cache: {result.stderr}")
            return False

    async def install_package(self, package: str, version: Optional[str] = None) -> bool:
        """Install a package using APT."""
        package_spec = f"{package}={version}" if version else package

        self.logger.info(f"Installing package: {package_spec}")

        result = await execute_command_async(
            ["apt-get", "install", "-y", "--no-install-recommends", package_spec],
            sudo=True,
            check=False,
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )

        if result.success:
            self.logger.info(f"Package {package} installed successfully")
            return True
        else:
            self.logger.error(f"Failed to install {package}: {result.stderr}")
            return False

    async def install_packages(self, packages: List[str]) -> bool:
        """Install multiple packages using APT."""
        if not packages:
            return True

        self.logger.info(f"Installing packages: {', '.join(packages)}")

        result = await execute_command_async(
            ["apt-get", "install", "-y", "--no-install-recommends"] + packages,
            sudo=True,
            check=False,
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )

        if result.success:
            self.logger.info("All packages installed successfully")
            return True
        else:
            self.logger.error(f"Failed to install packages: {result.stderr}")
            return False

    async def remove_package(self, package: str) -> bool:
        """Remove a package using APT."""
        self.logger.info(f"Removing package: {package}")

        result = await execute_command_async(
            ["apt-get", "remove", "-y", package],
            sudo=True,
            check=False,
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )

        if result.success:
            self.logger.info(f"Package {package} removed successfully")
            return True
        else:
            self.logger.error(f"Failed to remove {package}: {result.stderr}")
            return False

    async def is_package_installed(self, package: str) -> bool:
        """Check if a package is installed."""
        result = await execute_command_async(["dpkg", "-s", package], check=False)

        # Check for "Status: install ok installed" in output
        if result.success and "Status: install ok installed" in result.stdout:
            return True

        return False

    async def get_package_version(self, package: str) -> Optional[str]:
        """Get installed package version."""
        result = await execute_command_async(
            ["dpkg-query", "-W", "-f=${Version}", package], check=False
        )

        if result.success:
            return result.stdout.strip()

        return None

    async def upgrade_package(self, package: str) -> bool:
        """Upgrade a package to latest version."""
        self.logger.info(f"Upgrading package: {package}")

        result = await execute_command_async(
            ["apt-get", "install", "--only-upgrade", "-y", package],
            sudo=True,
            check=False,
            env={"DEBIAN_FRONTEND": "noninteractive"},
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

        # Update cache first
        await self.update_cache()

        # Upgrade packages
        result = await execute_command_async(
            ["apt-get", "upgrade", "-y"],
            sudo=True,
            check=False,
            env={"DEBIAN_FRONTEND": "noninteractive"},
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
            ["apt-get", "autoremove", "-y"],
            sudo=True,
            check=False,
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )

        if result.success:
            self.logger.info("Unused packages removed successfully")
            return True
        else:
            self.logger.error(f"Failed to autoremove: {result.stderr}")
            return False

    async def clean_cache(self) -> bool:
        """Clean APT cache."""
        self.logger.info("Cleaning APT cache...")

        result = await execute_command_async(["apt-get", "clean"], sudo=True, check=False)

        if result.success:
            self.logger.info("APT cache cleaned successfully")
            return True
        else:
            self.logger.error(f"Failed to clean cache: {result.stderr}")
            return False
