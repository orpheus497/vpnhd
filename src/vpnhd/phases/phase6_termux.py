"""Phase 6: Termux/Android Setup."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..crypto.wireguard import generate_keypair


class Phase6Termux(Phase):
    """Phase 6: Termux/Android Setup."""

    @property
    def name(self) -> str:
        return "Termux/Android Setup"

    @property
    def number(self) -> int:
        return 6

    @property
    def description(self) -> str:
        return "Configure Android phone with WireGuard app and Termux."

    @property
    def long_description(self) -> str:
        return """This sets up your Android phone to connect to your VPN when needed,
        protecting your mobile traffic when on public WiFi."""

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
                client_vpn_ip=self.config.get("network.vpn.clients.termux.ip"),
                vpn_subnet_mask="24",
                client_private_key=private_key,
                server_public_key=self.config.get("phases.phase2_wireguard_server.server_public_key"),
                server_public_ip=self.config.get("server.public_ip"),
                wireguard_port=self.config.get("network.wireguard_port"),
                route_all_traffic=True,
                dns_servers=["1.1.1.1"],
                vpn_network=self.config.get("network.vpn.network")
            )

            self.display.heading("Android/Termux Client Configuration")
            self.display.code_block(config, "ini")
            self.display.info("\nTo add to WireGuard app: Scan QR code or copy configuration manually")

            self.config.set("clients.termux.public_key", public_key)
            self.config.set("clients.termux.configured", True)

            self.mark_complete("Termux client configured")
            self.config.save()
            return True

        except Exception as e:
            self.mark_failed(str(e))
            return False
