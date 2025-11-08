"""Phase 5: Linux Desktop Client Setup (On-Demand)."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..crypto.wireguard import generate_keypair
from ..crypto.server_config import ServerConfigManager
from ..utils.constants import TEMPLATE_DIR
from ..utils.logging import get_logger
from ..utils.distribution_helpers import (
    prompt_for_distribution,
    generate_wireguard_install_instructions,
)

logger = get_logger(__name__)


class Phase5LinuxClientOnDemand(Phase):
    """Phase 5: Linux Desktop Client Setup (On-Demand VPN Mode).

    This phase configures a Linux desktop/laptop for on-demand VPN access,
    isolated from other VPN clients for additional security.

    Supports: Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, Linux Mint,
    CentOS, RHEL, Arch Linux, Manjaro, and other modern Linux distributions.
    """

    @property
    def name(self) -> str:
        return "Linux Desktop Client (On-Demand)"

    @property
    def number(self) -> int:
        return 5

    @property
    def description(self) -> str:
        return "Configure Linux desktop for on-demand VPN (manually controlled, isolated)."

    @property
    def long_description(self) -> str:
        return """This sets up your Linux desktop/laptop for on-demand VPN connectivity.
You control when the VPN is active, and this client is isolated from other VPN clients
for additional security.

Ideal for devices that need selective VPN access or work in trusted environments.

Supported distributions: Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, Linux Mint,
CentOS, RHEL, Arch Linux, Manjaro, and other modern Linux distributions."""

    def check_prerequisites(self) -> bool:
        """Check that Phase 2 (WireGuard Server) is complete."""
        return self.config.is_phase_complete(2)

    def execute(self) -> bool:
        """Execute Phase 5: Linux desktop client (on-demand) configuration."""
        try:
            self.show_introduction()

            # Prompt for distribution
            distro = prompt_for_distribution(self.display, self.prompts)
            if not distro:
                self.mark_failed("No distribution selected")
                return False

            # Prompt for client details
            client_name = self._prompt_for_client_name()

            # Generate client keys
            self.display.info("Generating WireGuard keypair for client...")
            private_key, public_key = generate_keypair()

            # Get VPN IP
            vpn_ip = self.config.get("network.vpn.clients.linux_desktop_on_demand.ip", "10.66.66.3")

            # Create client configuration (on-demand mode)
            config_text = self._create_client_config(
                client_name=client_name,
                vpn_ip=vpn_ip,
                private_key=private_key,
                public_key=public_key,
                always_on=False,  # On-demand mode
                isolated=True,  # Isolated from other clients
            )

            # Display configuration
            self.display.newline()
            self.display.heading("Linux Desktop Client Configuration (On-Demand)")
            self.display.code_block(config_text, "ini")
            self.display.newline()

            # Add peer to server
            if self._add_peer_to_server(client_name, public_key, vpn_ip):
                self.display.success(f"✓ Client peer added to server successfully")
            else:
                self.display.error("Failed to add peer to server - you'll need to add manually")

            # Show installation instructions
            self.display.newline()
            self.display.heading("Installation Instructions")
            instructions = generate_wireguard_install_instructions(distro, always_on=False)
            self.display.markdown(instructions)
            self.prompts.pause()

            # Save client configuration
            self.config.set("clients.linux_desktop_on_demand.public_key", public_key)
            self.config.set("clients.linux_desktop_on_demand.name", client_name)
            self.config.set("clients.linux_desktop_on_demand.os", distro)
            self.config.set("clients.linux_desktop_on_demand.configured", True)
            self.config.set("phases.phase5_linux_client_ondemand.distribution", distro)

            self.mark_complete(f"Linux desktop client ({distro}, on-demand) configured")
            self.config.save()

            return True

        except Exception as e:
            logger.exception("Error in Phase 5 execution")
            self.mark_failed(str(e))
            return False

    def _prompt_for_client_name(self) -> str:
        """Prompt user for a client device name."""
        default_name = "linux-desktop-2"
        return self.prompts.text(
            "Enter a name for this client device",
            default=default_name,
            help_text="This helps identify the device (e.g., personal-laptop, secondary-computer)",
        )

    def _create_client_config(
        self,
        client_name: str,
        vpn_ip: str,
        private_key: str,
        public_key: str,
        always_on: bool = False,
        isolated: bool = True,
    ) -> str:
        """Create WireGuard client configuration from template.

        Args:
            client_name: Name of the client device
            vpn_ip: VPN IP address for this client
            private_key: Client's private key
            public_key: Client's public key
            always_on: Whether to route all traffic through VPN
            isolated: Whether to isolate this client from other VPN clients

        Returns:
            Rendered configuration file content
        """
        template_path = TEMPLATE_DIR / "wireguard_client.conf.j2"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path) as f:
            template = Template(f.read())

        # For isolated clients, only allow access to specific IPs
        # Only route traffic destined for the VPN server, not all traffic
        allowed_ips = f"{self.config.get('network.vpn.server_ip')}/32"
        if not isolated:
            allowed_ips = self.config.get("network.vpn.network", "10.66.66.0/24")

        config = template.render(
            client_name=client_name,
            client_vpn_ip=vpn_ip,
            vpn_subnet_mask="24",
            client_private_key=private_key,
            server_public_key=self.config.get("phases.phase2_wireguard_server.server_public_key"),
            server_public_ip=self.config.get("server.public_ip"),
            wireguard_port=self.config.get("network.wireguard_port", 51820),
            route_all_traffic=always_on,
            dns_servers=["1.1.1.1", "8.8.8.8"],
            vpn_network=self.config.get("network.vpn.network", "10.66.66.0/24"),
            allowed_ips=allowed_ips,
            isolated=isolated,
        )

        return config

    def _add_peer_to_server(self, client_name: str, public_key: str, vpn_ip: str) -> bool:
        """Add this client as a peer on the WireGuard server."""
        try:
            server_config_mgr = ServerConfigManager()
            return server_config_mgr.add_peer_to_server(
                client_name=client_name, public_key=public_key, vpn_ip=vpn_ip
            )
        except Exception as e:
            logger.exception(f"Error adding peer to server: {e}")
            return False

    def verify(self) -> bool:
        """Verify that the phase completed successfully."""
        public_key = self.config.get("clients.linux_desktop_on_demand.public_key")
        if not public_key:
            return False

        try:
            server_config_mgr = ServerConfigManager()
            return server_config_mgr.verify_peer_exists(public_key)
        except Exception as e:
            logger.warning(f"Could not verify peer exists on server: {e}")
            return True

    def rollback(self) -> bool:
        """Rollback Phase 5 changes."""
        try:
            public_key = self.config.get("clients.linux_desktop_on_demand.public_key")
            if public_key:
                server_config_mgr = ServerConfigManager()
                server_config_mgr.remove_peer_from_server(public_key)

            self.config.set("clients.linux_desktop_on_demand.configured", False)
            self.config.set("clients.linux_desktop_on_demand.public_key", None)
            self.config.save()

            return True
        except Exception as e:
            logger.exception(f"Error during rollback: {e}")
            return False
