"""Package management utilities for VPNHD."""

from typing import List, Optional, Tuple
import platform

from ..utils.logging import get_logger
from ..utils.constants import (
    REQUIRED_PACKAGES_DEBIAN,
    REQUIRED_PACKAGES_FEDORA,
    COMMAND_TIMEOUT_INSTALL
)
from .commands import execute_command, check_command_exists


class PackageManager:
    """Manages system package installation and verification."""

    def __init__(self):
        """Initialize package manager."""
        self.logger = get_logger("PackageManager")
        self.distro = self._detect_distro()
        self.package_manager = self._get_package_manager()

    def _detect_distro(self) -> str:
        """
        Detect Linux distribution.

        Returns:
            str: Distribution name (debian, ubuntu, fedora, etc.)
        """
        try:
            # Try to read /etc/os-release
            with open('/etc/os-release', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('ID='):
                        distro = line.split('=')[1].strip().strip('"')
                        self.logger.debug(f"Detected distribution: {distro}")
                        return distro
        except Exception as e:
            self.logger.warning(f"Could not detect distribution: {e}")

        return "unknown"

    def _get_package_manager(self) -> str:
        """
        Get appropriate package manager for this system.

        Returns:
            str: Package manager command (apt, dnf, yum, etc.)
        """
        if check_command_exists("apt"):
            return "apt"
        elif check_command_exists("apt-get"):
            return "apt-get"
        elif check_command_exists("dnf"):
            return "dnf"
        elif check_command_exists("yum"):
            return "yum"
        elif check_command_exists("pacman"):
            return "pacman"
        else:
            self.logger.warning("Could not detect package manager")
            return "unknown"

    def is_package_installed(self, package: str) -> bool:
        """
        Check if a package is installed.

        Args:
            package: Package name

        Returns:
            bool: True if installed
        """
        if self.package_manager in ("apt", "apt-get"):
            result = execute_command(
                f"dpkg -l {package}",
                check=False,
                capture_output=True
            )
            return result.success

        elif self.package_manager in ("dnf", "yum"):
            result = execute_command(
                f"rpm -q {package}",
                check=False,
                capture_output=True
            )
            return result.success

        elif self.package_manager == "pacman":
            result = execute_command(
                f"pacman -Q {package}",
                check=False,
                capture_output=True
            )
            return result.success

        return False

    def install_package(self, package: str, assume_yes: bool = True) -> bool:
        """
        Install a package.

        Args:
            package: Package name
            assume_yes: Auto-confirm installation

        Returns:
            bool: True if installation succeeded
        """
        self.logger.info(f"Installing package: {package}")

        # Check if already installed
        if self.is_package_installed(package):
            self.logger.info(f"Package {package} is already installed")
            return True

        # Build install command
        if self.package_manager in ("apt", "apt-get"):
            cmd = f"{self.package_manager} install"
            if assume_yes:
                cmd += " -y"
            cmd += f" {package}"

        elif self.package_manager in ("dnf", "yum"):
            cmd = f"{self.package_manager} install"
            if assume_yes:
                cmd += " -y"
            cmd += f" {package}"

        elif self.package_manager == "pacman":
            cmd = f"pacman -S"
            if assume_yes:
                cmd += " --noconfirm"
            cmd += f" {package}"

        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        # Execute installation
        result = execute_command(
            cmd,
            sudo=True,
            check=False,
            timeout=COMMAND_TIMEOUT_INSTALL
        )

        if result.success:
            self.logger.info(f"Successfully installed {package}")
        else:
            self.logger.error(f"Failed to install {package}")

        return result.success

    def install_packages(self, packages: List[str], assume_yes: bool = True) -> Tuple[List[str], List[str]]:
        """
        Install multiple packages.

        Args:
            packages: List of package names
            assume_yes: Auto-confirm installation

        Returns:
            Tuple[List[str], List[str]]: (successful, failed) package lists
        """
        successful = []
        failed = []

        for package in packages:
            if self.install_package(package, assume_yes):
                successful.append(package)
            else:
                failed.append(package)

        return successful, failed

    def update_package_cache(self) -> bool:
        """
        Update package manager cache.

        Returns:
            bool: True if update succeeded
        """
        self.logger.info("Updating package cache")

        if self.package_manager in ("apt", "apt-get"):
            cmd = f"{self.package_manager} update"

        elif self.package_manager in ("dnf", "yum"):
            cmd = f"{self.package_manager} check-update"

        elif self.package_manager == "pacman":
            cmd = "pacman -Sy"

        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        result = execute_command(cmd, sudo=True, check=False)
        return result.success

    def upgrade_packages(self, assume_yes: bool = True) -> bool:
        """
        Upgrade all installed packages.

        Args:
            assume_yes: Auto-confirm upgrade

        Returns:
            bool: True if upgrade succeeded
        """
        self.logger.info("Upgrading packages")

        if self.package_manager in ("apt", "apt-get"):
            cmd = f"{self.package_manager} upgrade"
            if assume_yes:
                cmd += " -y"

        elif self.package_manager in ("dnf", "yum"):
            cmd = f"{self.package_manager} upgrade"
            if assume_yes:
                cmd += " -y"

        elif self.package_manager == "pacman":
            cmd = "pacman -Syu"
            if assume_yes:
                cmd += " --noconfirm"

        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        result = execute_command(
            cmd,
            sudo=True,
            check=False,
            timeout=COMMAND_TIMEOUT_INSTALL
        )

        return result.success

    def get_required_packages(self) -> List[str]:
        """
        Get list of required packages for this distribution.

        Returns:
            List[str]: List of required package names
        """
        if self.distro in ("debian", "ubuntu", "pop"):
            return REQUIRED_PACKAGES_DEBIAN
        elif self.distro in ("fedora", "rhel", "centos"):
            return REQUIRED_PACKAGES_FEDORA
        else:
            self.logger.warning(f"Unknown distribution {self.distro}, using Debian packages")
            return REQUIRED_PACKAGES_DEBIAN

    def check_required_packages(self) -> Tuple[List[str], List[str]]:
        """
        Check which required packages are installed/missing.

        Returns:
            Tuple[List[str], List[str]]: (installed, missing) package lists
        """
        required = self.get_required_packages()
        installed = []
        missing = []

        for package in required:
            if self.is_package_installed(package):
                installed.append(package)
            else:
                missing.append(package)

        return installed, missing

    def install_required_packages(self, assume_yes: bool = True) -> bool:
        """
        Install all required packages.

        Args:
            assume_yes: Auto-confirm installation

        Returns:
            bool: True if all packages installed successfully
        """
        installed, missing = self.check_required_packages()

        if not missing:
            self.logger.info("All required packages are already installed")
            return True

        self.logger.info(f"Installing {len(missing)} required packages")

        # Update package cache first
        self.update_package_cache()

        # Install missing packages
        successful, failed = self.install_packages(missing, assume_yes)

        if failed:
            self.logger.error(f"Failed to install packages: {', '.join(failed)}")
            return False

        self.logger.info("All required packages installed successfully")
        return True

    def remove_package(self, package: str, assume_yes: bool = True) -> bool:
        """
        Remove a package.

        Args:
            package: Package name
            assume_yes: Auto-confirm removal

        Returns:
            bool: True if removal succeeded
        """
        self.logger.info(f"Removing package: {package}")

        if self.package_manager in ("apt", "apt-get"):
            cmd = f"{self.package_manager} remove"
            if assume_yes:
                cmd += " -y"
            cmd += f" {package}"

        elif self.package_manager in ("dnf", "yum"):
            cmd = f"{self.package_manager} remove"
            if assume_yes:
                cmd += " -y"
            cmd += f" {package}"

        elif self.package_manager == "pacman":
            cmd = f"pacman -R"
            if assume_yes:
                cmd += " --noconfirm"
            cmd += f" {package}"

        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        result = execute_command(cmd, sudo=True, check=False)
        return result.success
