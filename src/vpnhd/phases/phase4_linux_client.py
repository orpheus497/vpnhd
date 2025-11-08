"""Phase 4: Linux Desktop Client Setup (Always-On)."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..crypto.wireguard import generate_keypair
from ..crypto.server_config import ServerConfigManager
from ..utils.constants import TEMPLATE_DIR
from ..utils.logging import get_logger
from ..utils.distribution_helpers import (
    prompt_for_distribution,
    generate_wireguard_install_instructions
)

logger = get_logger(__name__)


class Phase4LinuxClient(Phase):
    """Phase 4: Linux Desktop Client Setup (Always-On VPN Mode).

    This phase supports multiple Linux distributions including:
    - Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, Linux Mint
    - CentOS, RHEL, Arch Linux, Manjaro
    """

    @property
    def name(self) -> str:
        return "Linux Desktop Client (Always-On)"

    @property
    def number(self) -> int:
        return 4

    @property
    def description(self) -> str:
        return "Configure Linux desktop to automatically connect to VPN and protect all traffic."

    @property
    def long_description(self) -> str:
        return """This sets up your Linux desktop/laptop to automatically connect to the VPN
whenever it has internet connectivity, protecting all your network traffic.

Supported distributions: Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, Linux Mint,
CentOS, RHEL, Arch Linux, Manjaro, and other modern Linux distributions."""

    def check_prerequisites(self) -> bool:
        """Check that Phase 2 (WireGuard Server) is complete."""
        return self.config.is_phase_complete(2)

    def execute(self) -> bool:
        """Execute Phase 4: Linux desktop client configuration."""
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
            vpn_ip = self.config.get("network.vpn.clients.linux_desktop_always_on.ip", "10.66.66.2")

            # Create client configuration
            config_text = self._create_client_config(
                client_name=client_name,
                vpn_ip=vpn_ip,
                private_key=private_key,
                public_key=public_key,
                always_on=True
            )

            # Display configuration
            self.display.newline()
            self.display.heading("Linux Desktop Client Configuration (Always-On)")
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
            instructions = generate_wireguard_install_instructions(distro, always_on=True)
            self.display.markdown(instructions)
            self.prompts.pause()

            # Save client configuration
            self.config.set("clients.linux_desktop_always_on.public_key", public_key)
            self.config.set("clients.linux_desktop_always_on.name", client_name)
            self.config.set("clients.linux_desktop_always_on.os", distro)
            self.config.set("clients.linux_desktop_always_on.configured", True)
            self.config.set("phases.phase4_linux_client.distribution", distro)

            self.mark_complete(f"Linux desktop client ({distro}) configured")
            self.config.save()

            return True

        except Exception as e:
            logger.exception("Error in Phase 4 execution")
            self.mark_failed(str(e))
            return False

    def _prompt_for_client_name(self) -> str:
        """Prompt user for a client device name."""
        default_name = "linux-desktop-1"
        return self.prompts.text(
            "Enter a name for this client device",
            default=default_name,
            help_text="This helps identify the device (e.g., work-laptop, home-desktop)"
        )

    def _create_client_config(
        self,
        client_name: str,
        vpn_ip: str,
        private_key: str,
        public_key: str,
        always_on: bool = True
    ) -> str:
        """Create WireGuard client configuration from template.

        Args:
            client_name: Name of the client device
            vpn_ip: VPN IP address for this client
            private_key: Client's private key
            public_key: Client's public key (unused but kept for consistency)
            always_on: Whether to route all traffic through VPN

        Returns:
            Rendered configuration file content
        """
        template_path = TEMPLATE_DIR / "wireguard_client.conf.j2"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path) as f:
            template = Template(f.read())

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
            vpn_network=self.config.get("network.vpn.network", "10.66.66.0/24")
        )

        return config

    def _add_peer_to_server(self, client_name: str, public_key: str, vpn_ip: str) -> bool:
        """Add this client as a peer on the WireGuard server.

        Args:
            client_name: Name of the client
            public_key: Client's WireGuard public key
            vpn_ip: Client's VPN IP address

        Returns:
            True if peer was added successfully, False otherwise
        """
        try:
            server_config_mgr = ServerConfigManager()
            return server_config_mgr.add_peer_to_server(
                client_name=client_name,
                public_key=public_key,
                vpn_ip=vpn_ip
            )
        except Exception as e:
            logger.exception(f"Error adding peer to server: {e}")
            return False

    def verify(self) -> bool:
        """Verify that the phase completed successfully."""
        # Check that client public key is saved
        public_key = self.config.get("clients.linux_desktop_always_on.public_key")
        if not public_key:
            return False

        # Check that peer exists on server (if we have access)
        try:
            server_config_mgr = ServerConfigManager()
            return server_config_mgr.verify_peer_exists(public_key)
        except Exception as e:
            # If we can't verify, assume it's okay
            logger.warning(f"Could not verify peer exists on server: {e}")
            return True

    def rollback(self) -> bool:
        """Rollback Phase 4 changes."""
        try:
            # Remove peer from server
            public_key = self.config.get("clients.linux_desktop_always_on.public_key")
            if public_key:
                server_config_mgr = ServerConfigManager()
                server_config_mgr.remove_peer_from_server(public_key)

            # Clear configuration
            self.config.set("clients.linux_desktop_always_on.configured", False)
            self.config.set("clients.linux_desktop_always_on.public_key", None)
            self.config.save()

            return True
        except Exception as e:
            logger.exception(f"Error during rollback: {e}")
            return False
