"""Phase 4: Fedora Client Setup."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..crypto.wireguard import generate_keypair


class Phase4Fedora(Phase):
    """Phase 4: Fedora Client Setup (Always-On)."""

    @property
    def name(self) -> str:
        return "Fedora Client Setup"

    @property
    def number(self) -> int:
        return 4

    @property
    def description(self) -> str:
        return "Configure Fedora laptop as always-on VPN client."

    @property
    def long_description(self) -> str:
        return """This sets up your Fedora laptop to automatically connect to the VPN
        whenever it has internet, protecting all your traffic."""

    def check_prerequisites(self) -> bool:
        return self.config.is_phase_complete(2)

    def execute(self) -> bool:
        try:
            self.show_introduction()

            # Generate client keys
            private_key, public_key = generate_keypair()

            # Create client config
            template_path = Path(__file__).parent.parent / "config" / "templates" / "wireguard_client.conf.j2"
            with open(template_path) as f:
                template = Template(f.read())

            config = template.render(
                client_vpn_ip=self.config.get("network.vpn.clients.fedora.ip"),
                vpn_subnet_mask="24",
                client_private_key=private_key,
                server_public_key=self.config.get("phases.phase2_wireguard_server.server_public_key"),
                server_public_ip=self.config.get("server.public_ip"),
                wireguard_port=self.config.get("network.wireguard_port"),
                route_all_traffic=True,
                dns_servers=["1.1.1.1", "8.8.8.8"],
                vpn_network=self.config.get("network.vpn.network")
            )

            self.display.heading("Fedora Client Configuration")
            self.display.code_block(config, "ini")
            self.display.info("Save this configuration to /etc/wireguard/wg0.conf on your Fedora laptop")

            self.config.set("clients.fedora.public_key", public_key)
            self.config.set("clients.fedora.configured", True)

            self.mark_complete("Fedora client configured")
            self.config.save()
            return True

        except Exception as e:
            self.mark_failed(str(e))
            return False
