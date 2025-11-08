"""Phase 3: Router Port Forwarding."""

from .base import Phase
from ..network.testing import get_public_ip


class Phase3Router(Phase):
    """Phase 3: Router Port Forwarding Guide."""

    @property
    def name(self) -> str:
        return "Router Port Forwarding"

    @property
    def number(self) -> int:
        return 3

    @property
    def description(self) -> str:
        return "Configure router to forward WireGuard port to server."

    @property
    def long_description(self) -> str:
        return """Port forwarding tells your router to send VPN connections to your server.
        It's like telling your doorman to send specific visitors to your apartment."""

    def check_prerequisites(self) -> bool:
        return self.config.is_phase_complete(2)

    def execute(self) -> bool:
        try:
            self.show_introduction()

            # Get public IP
            self.display.info("Detecting public IP...")
            public_ip = get_public_ip()
            if public_ip:
                self.display.success(f"Public IP: {public_ip}")
                self.config.set("server.public_ip", public_ip)

            # Show router configuration guide
            router_ip = self.config.get("network.lan.router_ip", "192.168.1.1")
            wg_port = self.config.get("network.wireguard_port", 51820)
            server_ip = self.config.get("server.lan_ip")

            guide = f"""
## Router Configuration Steps:

1. Open browser and go to: http://{router_ip}
2. Login with router admin credentials
3. Find "Port Forwarding" or "Virtual Server" section
4. Add new rule:
   - External Port: {wg_port}
   - Internal IP: {server_ip}
   - Internal Port: {wg_port}
   - Protocol: UDP
5. Save and apply settings

Your public IP for client configurations: {public_ip}
            """

            self.display.markdown(guide)
            self.prompts.pause()

            if self.prompts.confirm("Have you configured port forwarding?"):
                self.mark_complete("Port forwarding configured")
                self.config.save()
                return True

            return False

        except Exception as e:
            self.mark_failed(str(e))
            return False
