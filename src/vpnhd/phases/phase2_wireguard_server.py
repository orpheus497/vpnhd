"""Phase 2: WireGuard Server Setup."""

from pathlib import Path

from jinja2 import Template

from ..crypto.server_config import ServerConfigManager
from ..crypto.wireguard import derive_public_key, generate_keypair, save_private_key
from ..network.interfaces import InterfaceManager
from ..system.services import ServiceManager
from ..utils.constants import WIREGUARD_SERVER_TEMPLATE
from ..utils.logging import get_logger
from .base import Phase, PhaseStatus

logger = get_logger(__name__)


class Phase2WireGuardServer(Phase):
    """Phase 2: WireGuard Server Setup."""

    @property
    def name(self) -> str:
        return "WireGuard Server Setup"

    @property
    def number(self) -> int:
        return 2

    @property
    def description(self) -> str:
        return """Install and configure WireGuard VPN server with proper networking."""

    @property
    def long_description(self) -> str:
        return """WireGuard is the tunnel builder for your VPN. It creates an encrypted tunnel
        from anywhere to your home, making it impossible for others to see your traffic."""

    def check_prerequisites(self) -> bool:
        """Check if Phase 1 is complete."""
        if not self.config.is_phase_complete(1):
            self.display.error("Phase 1 must be completed first")
            return False
        return True

    def execute(self) -> bool:
        """Execute Phase 2."""
        try:
            self.status = PhaseStatus.IN_PROGRESS
            self.show_introduction()

            # Install WireGuard
            from ..system.packages import PackageManager

            pkg_mgr = PackageManager()
            if not pkg_mgr.is_package_installed("wireguard"):
                self.display.info("Installing WireGuard...")
                pkg_mgr.install_package("wireguard-tools")

            # Enable IP forwarding
            self.display.info("Enabling IP forwarding...")
            iface_mgr = InterfaceManager()
            iface_mgr.enable_ip_forwarding()

            # Generate server keys
            self.display.info("Generating server keypair...")
            private_key, public_key = generate_keypair()

            private_key_path = Path("/etc/wireguard/server_private.key")
            save_private_key(private_key, private_key_path)

            self.config.set("phases.phase2_wireguard_server.server_public_key", public_key)

            # Create WireGuard config
            self.display.info("Creating WireGuard configuration...")
            self._create_wireguard_config(private_key)

            # Start WireGuard
            self.display.info("Starting WireGuard service...")
            svc_mgr = ServiceManager()
            svc_mgr.enable_service("wg-quick@wg0")
            svc_mgr.start_service("wg-quick@wg0")

            if svc_mgr.is_service_active("wg-quick@wg0"):
                self.display.success("WireGuard is running!")
                self.config.set("security.wireguard_running", True)
            else:
                raise Exception("WireGuard failed to start")

            self.mark_complete("WireGuard server configured")
            self.config.save()

            return True

        except Exception as e:
            self.mark_failed(str(e))
            self.display.error(f"Phase 2 failed: {e}")
            return False

    def _create_wireguard_config(self, private_key: str) -> None:
        """Create WireGuard server configuration."""
        if not WIREGUARD_SERVER_TEMPLATE.exists():
            raise FileNotFoundError(f"Template not found: {WIREGUARD_SERVER_TEMPLATE}")

        with open(WIREGUARD_SERVER_TEMPLATE) as f:
            template = Template(f.read())

        config = template.render(
            vpn_server_ip=self.config.get("network.vpn.server_ip"),
            vpn_subnet_mask="24",
            server_private_key=private_key,
            wireguard_port=self.config.get("network.wireguard_port"),
            server_interface=self.config.get("server.interface"),
            clients=[],  # Will add clients in later phases
        )

        config_path = Path("/etc/wireguard/wg0.conf")
        config_path.write_text(config)
        config_path.chmod(0o600)
