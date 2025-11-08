"""Phase 8: Security Hardening."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..system.packages import PackageManager
from ..system.services import ServiceManager


class Phase8Security(Phase):
    """Phase 8: Security Hardening with UFW and fail2ban."""

    @property
    def name(self) -> str:
        return "Security Hardening"

    @property
    def number(self) -> int:
        return 8

    @property
    def description(self) -> str:
        return "Final security hardening with UFW firewall and fail2ban intrusion prevention."

    @property
    def long_description(self) -> str:
        return """This adds layers of security: UFW firewall blocks unwanted connections,
        and fail2ban automatically blocks attackers who try to break in."""

    def check_prerequisites(self) -> bool:
        return self.config.is_phase_complete(7)

    def execute(self) -> bool:
        try:
            self.show_introduction()

            pkg_mgr = PackageManager()
            svc_mgr = ServiceManager()

            # Install UFW
            if not pkg_mgr.is_package_installed("ufw"):
                self.display.info("Installing UFW...")
                pkg_mgr.install_package("ufw")

            # Configure UFW
            self._configure_ufw()

            # Install fail2ban
            if not pkg_mgr.is_package_installed("fail2ban"):
                self.display.info("Installing fail2ban...")
                pkg_mgr.install_package("fail2ban")

            # Configure fail2ban
            self._configure_fail2ban()

            self.display.success("Security hardening complete!")

            self.mark_complete("Security hardening applied")
            self.config.save()
            return True

        except Exception as e:
            self.mark_failed(str(e))
            return False

    def _configure_ufw(self) -> None:
        """Configure UFW firewall."""
        from ..system.commands import execute_command

        self.display.info("Configuring UFW firewall...")

        # Default policies
        execute_command("ufw default deny incoming", sudo=True, check=False)
        execute_command("ufw default allow outgoing", sudo=True, check=False)

        # Allow WireGuard
        wg_port = self.config.get("network.wireguard_port", 51820)
        execute_command(f"ufw allow {wg_port}/udp comment 'WireGuard VPN'", sudo=True, check=False)

        # Allow SSH from VPN
        vpn_network = self.config.get("network.vpn.network", "10.66.66.0/24")
        ssh_port = self.config.get("network.ssh_port", 22)
        execute_command(f"ufw allow from {vpn_network} to any port {ssh_port} proto tcp comment 'SSH from VPN'", sudo=True, check=False)

        # Enable UFW
        execute_command("ufw --force enable", sudo=True, check=False)

        self.config.set("security.firewall_enabled", True)
        self.config.set("phases.phase8_security.ufw_configured", True)
        self.display.success("UFW configured and enabled")

    def _configure_fail2ban(self) -> None:
        """Configure fail2ban."""
        from ..system.services import ServiceManager

        self.display.info("Configuring fail2ban...")

        svc_mgr = ServiceManager()
        svc_mgr.enable_service("fail2ban")
        svc_mgr.start_service("fail2ban")

        if svc_mgr.is_service_active("fail2ban"):
            self.config.set("security.fail2ban_enabled", True)
            self.config.set("phases.phase8_security.fail2ban_configured", True)
            self.display.success("fail2ban is running")
