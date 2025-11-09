"""Phase 1: Debian Server Installation."""

from pathlib import Path

from ..system.commands import execute_command
from ..utils.logging import get_logger
from .base import Phase

logger = get_logger(__name__)


class Phase1Debian(Phase):
    """Phase 1: Debian Installation Guide."""

    @property
    def name(self) -> str:
        return "Debian Server Installation"

    @property
    def number(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return """This phase helps you install Debian Linux on your server hardware.
        We'll verify the installation and gather basic system information."""

    @property
    def long_description(self) -> str:
        return (
            "Debian is like the foundation of your house - it's the operating system "
            "that runs on your server computer. Think of it as the base layer that "
            "everything else sits on top of. We need this installed before we can "
            "build your VPN system."
        )

    def check_prerequisites(self) -> bool:
        """No prerequisites for Phase 1."""
        return True

    def execute(self) -> bool:
        """Execute Phase 1: Debian installation guide."""
        try:
            self.status = self.status.IN_PROGRESS
            self.show_introduction()

            # Check if Debian is already installed
            is_debian = self._check_debian_installed()

            if is_debian:
                self.display.success("Debian is already installed!")
                version = self._get_debian_version()
                if version:
                    self.display.info(f"Detected Debian version: {version}")

                # Collect server information
                self._collect_server_info()

            else:
                self.display.warning("Debian does not appear to be installed.")
                self._show_installation_guide()

                if not self.prompts.confirm("Have you completed the Debian installation?"):
                    return False

                self._collect_server_info()

            # Mark complete
            self.mark_complete("Debian installation verified")
            self.display.success("Phase 1 completed successfully!")

            return True

        except Exception as e:
            self.mark_failed(str(e))
            self.display.error(f"Phase 1 failed: {e}")
            return False

    def _check_debian_installed(self) -> bool:
        """Check if Debian is installed by parsing /etc/os-release."""
        try:
            os_release_path = Path("/etc/os-release")
            if not os_release_path.exists():
                return False

            content = os_release_path.read_text().lower()
            return "debian" in content

        except Exception as e:
            logger.error(f"Error checking Debian installation: {e}")
            return False

    def _get_debian_version(self) -> str:
        """Get Debian version."""
        result = execute_command("lsb_release -r -s", check=False, capture_output=True)
        if result.success:
            return result.stdout.strip()
        return "Unknown"

    def _show_installation_guide(self) -> None:
        """Show Debian installation guide."""
        self.display.heading("Debian Installation Guide")
        guide_text = """
1. Download Debian ISO from debian.org
2. Create bootable USB using Rufus (Windows) or dd (Linux/Mac)
3. Boot from USB and follow installation wizard
4. Choose "Standard system utilities" and "SSH server"
5. Complete installation and reboot
        """
        self.display.print(guide_text)
        self.prompts.pause()

    def _collect_server_info(self) -> None:
        """Collect server information."""
        self.display.heading("Server Information")

        # Get hostname
        result = execute_command("hostname", check=False, capture_output=True)
        hostname = result.stdout.strip() if result.success else ""

        # Allow user to set/change
        hostname = self.prompts.hostname("Enter server hostname", default=hostname or "vpn-server")
        self.config.set("server.hostname", hostname)

        # Username
        import os

        username = os.environ.get("USER", "admin")
        username = self.prompts.text("Enter admin username", default=username)
        self.config.set("server.username", username)

        # Network interface
        from ..network.discovery import get_primary_interface

        primary_iface = get_primary_interface()

        if primary_iface:
            self.config.set("server.interface", primary_iface.name)
            self.config.set("network.lan.interface", primary_iface.name)
            if primary_iface.ip_address:
                self.config.set("server.lan_ip", primary_iface.ip_address)
                self.config.set("network.lan.server_ip", primary_iface.ip_address)
            if primary_iface.mac_address:
                self.config.set("server.mac_address", primary_iface.mac_address)

        # Detect subnet
        from ..network.discovery import detect_lan_subnet, get_default_gateway

        lan_subnet = detect_lan_subnet()
        if lan_subnet:
            self.config.set("network.lan.subnet", lan_subnet)

        gateway = get_default_gateway()
        if gateway:
            self.config.set("network.lan.router_ip", gateway)

        self.config.save()
        self.display.success("Server information collected")
