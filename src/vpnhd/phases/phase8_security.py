"""Phase 8: Security Hardening."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..system.packages import PackageManager
from ..system.services import ServiceManager
from ..system.fail2ban_config import Fail2banConfigManager
from ..utils.logging import get_logger
from ..utils.constants import (
    FAIL2BAN_SSH_BAN_TIME,
    FAIL2BAN_SSH_MAX_RETRY,
    FAIL2BAN_WIREGUARD_BAN_TIME,
    FAIL2BAN_WIREGUARD_MAX_RETRY,
    DEFAULT_WIREGUARD_PORT,
    DEFAULT_SSH_PORT
)
from ..security.validators import is_valid_port

logger = get_logger(__name__)


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
        """Configure UFW firewall with validated inputs."""
        from ..system.commands import execute_command

        self.display.info("Configuring UFW firewall...")

        # Get and validate ports
        wg_port = self.config.get("network.wireguard_port", DEFAULT_WIREGUARD_PORT)
        ssh_port = self.config.get("network.ssh_port", DEFAULT_SSH_PORT)

        # Validate port numbers
        if not is_valid_port(wg_port):
            logger.error(f"Invalid WireGuard port: {wg_port}")
            self.display.error(f"Invalid WireGuard port: {wg_port}")
            return

        if not is_valid_port(ssh_port):
            logger.error(f"Invalid SSH port: {ssh_port}")
            self.display.error(f"Invalid SSH port: {ssh_port}")
            return

        # Default policies
        execute_command(["ufw", "default", "deny", "incoming"], sudo=True, check=False)
        execute_command(["ufw", "default", "allow", "outgoing"], sudo=True, check=False)

        # Allow WireGuard
        execute_command(
            ["ufw", "allow", f"{int(wg_port)}/udp", "comment", "WireGuard VPN"],
            sudo=True,
            check=False
        )

        # Allow SSH from VPN
        vpn_network = self.config.get("network.vpn.network", "10.66.66.0/24")
        execute_command(
            ["ufw", "allow", "from", vpn_network, "to", "any", "port", str(ssh_port), "proto", "tcp", "comment", "SSH from VPN"],
            sudo=True,
            check=False
        )

        # Enable UFW
        execute_command(["ufw", "--force", "enable"], sudo=True, check=False)

        self.config.set("security.firewall_enabled", True)
        self.config.set("phases.phase8_security.ufw_configured", True)
        self.display.success("UFW configured and enabled")

    def _configure_fail2ban(self) -> None:
        """Configure fail2ban with custom jails for SSH and WireGuard."""
        self.display.info("Configuring fail2ban...")

        fail2ban_mgr = Fail2banConfigManager()
        svc_mgr = ServiceManager()

        # Ensure fail2ban service is running
        svc_mgr.enable_service("fail2ban")
        svc_mgr.start_service("fail2ban")

        if not svc_mgr.is_service_active("fail2ban"):
            self.display.error("Failed to start fail2ban service")
            return

        # Create SSH jail
        ssh_port = self.config.get("network.ssh_port", 22)
        if fail2ban_mgr.create_ssh_jail(
            ban_time=FAIL2BAN_SSH_BAN_TIME,
            find_time=600,
            max_retry=FAIL2BAN_SSH_MAX_RETRY,
            port=ssh_port
        ):
            self.display.success("✓ SSH jail configured")
            self.config.set("security.fail2ban_ssh_jail_configured", True)
            self.config.set("phases.phase8_security.ssh_jail_configured", True)
        else:
            self.display.warning("Failed to configure SSH jail")

        # Create WireGuard jail
        wg_port = self.config.get("network.wireguard_port", 51820)
        if fail2ban_mgr.create_wireguard_jail(
            ban_time=FAIL2BAN_WIREGUARD_BAN_TIME,
            find_time=600,
            max_retry=FAIL2BAN_WIREGUARD_MAX_RETRY,
            port=wg_port
        ):
            self.display.success("✓ WireGuard jail configured")
            self.config.set("security.fail2ban_wireguard_jail_configured", True)
            self.config.set("phases.phase8_security.wireguard_jail_configured", True)
        else:
            self.display.warning("Failed to configure WireGuard jail")

        # Final status
        if fail2ban_mgr.is_fail2ban_running():
            self.config.set("security.fail2ban_enabled", True)
            self.config.set("phases.phase8_security.fail2ban_configured", True)
            self.display.success("fail2ban is running with custom jails")
            self.display.newline()
            self.display.info(f"SSH protection: Ban after {FAIL2BAN_SSH_MAX_RETRY} failures for {FAIL2BAN_SSH_BAN_TIME}s")
            self.display.info(f"WireGuard protection: Ban after {FAIL2BAN_WIREGUARD_MAX_RETRY} failures for {FAIL2BAN_WIREGUARD_BAN_TIME}s")

    def verify(self) -> bool:
        """Verify that security hardening was successful."""
        from ..system.commands import execute_command

        # Check UFW is enabled
        result = execute_command(
            ["ufw", "status"],
            sudo=True,
            check=False,
            capture_output=True
        )
        if not result.success or "Status: active" not in result.stdout:
            return False

        # Check fail2ban is running
        fail2ban_mgr = Fail2banConfigManager()
        if not fail2ban_mgr.is_fail2ban_running():
            return False

        return True

    def rollback(self) -> bool:
        """Rollback security hardening changes."""
        try:
            from ..system.commands import execute_command

            # Disable UFW
            execute_command(["ufw", "--force", "disable"], sudo=True, check=False)
            logger.info("UFW disabled")

            # Stop fail2ban
            svc_mgr = ServiceManager()
            svc_mgr.stop_service("fail2ban")
            svc_mgr.disable_service("fail2ban")
            logger.info("fail2ban stopped")

            self.config.set("security.firewall_enabled", False)
            self.config.set("security.fail2ban_enabled", False)
            self.config.save()

            return True
        except Exception as e:
            logger.exception(f"Error during rollback: {e}")
            return False
