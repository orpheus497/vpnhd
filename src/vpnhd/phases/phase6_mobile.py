"""Phase 6: Mobile Client Setup (Android/iOS)."""

from pathlib import Path
from jinja2 import Template
from .base import Phase
from ..crypto.wireguard import generate_keypair
from ..crypto.server_config import ServerConfigManager
from ..crypto.qrcode import (
    generate_qr_code,
    display_qr_terminal,
    create_qr_with_metadata,
    verify_qrcode_available,
    install_qrencode
)
from ..utils.constants import TEMPLATE_DIR, QR_CODE_DIR
from ..utils.logging import get_logger

logger = get_logger(__name__)


class Phase6Mobile(Phase):
    """Phase 6: Mobile Client Setup for Android and iOS devices.

    Supports easy setup via QR code scanning with WireGuard mobile apps.
    """

    @property
    def name(self) -> str:
        return "Mobile Client (Android/iOS)"

    @property
    def number(self) -> int:
        return 6

    @property
    def description(self) -> str:
        return "Configure mobile devices (Android/iOS) with QR code for easy setup."

    @property
    def long_description(self) -> str:
        return """This sets up your mobile device (Android phone/tablet or iOS device) to connect
to your VPN. Configuration is done via QR code for quick and easy setup.

**Requirements:**
- Install WireGuard app from Google Play Store (Android) or App Store (iOS)
- Have your mobile device ready to scan the QR code

**Features:**
- QR code for instant configuration
- On-demand VPN (control when VPN is active)
- Battery-efficient configuration"""

    def check_prerequisites(self) -> bool:
        """Check that Phase 2 (WireGuard Server) is complete."""
        return self.config.is_phase_complete(2)

    def execute(self) -> bool:
        """Execute Phase 6: Mobile client configuration."""
        try:
            self.show_introduction()

            # Check for qrencode availability
            if not verify_qrcode_available():
                self.display.warning("qrencode is not installed. Attempting to install...")
                if not install_qrencode():
                    self.display.error("Failed to install qrencode. QR code generation will be skipped.")
                    if not self.prompts.confirm("Continue without QR code?", default=True):
                        return False

            # Prompt for mobile platform
            platform = self._prompt_for_platform()

            # Prompt for device details
            device_name = self._prompt_for_device_name()

            # Generate client keys
            self.display.info("Generating WireGuard keypair for mobile device...")
            private_key, public_key = generate_keypair()

            # Get VPN IP
            vpn_ip = self.config.get("network.vpn.clients.mobile.ip", "10.66.66.10")

            # Create client configuration
            config_text = self._create_mobile_config(
                device_name=device_name,
                vpn_ip=vpn_ip,
                private_key=private_key,
                public_key=public_key
            )

            # Display configuration
            self.display.newline()
            self.display.heading(f"Mobile Client Configuration ({platform})")
            self.display.code_block(config_text, "ini")
            self.display.newline()

            # Generate and display QR code
            qr_code_path = None
            if verify_qrcode_available():
                qr_code_path = self._generate_qr_code(device_name, config_text)
                if qr_code_path:
                    self.display.success(f"✓ QR code saved to: {qr_code_path}")
                    self.display.newline()

                # Display QR code in terminal
                self.display.heading("Scan this QR Code with WireGuard App")
                self.display.newline()
                display_qr_terminal(config_text)
                self.display.newline()
            else:
                self.display.warning("QR code generation skipped (qrencode not available)")

            # Add peer to server
            if self._add_peer_to_server(device_name, public_key, vpn_ip):
                self.display.success(f"✓ Mobile device peer added to server successfully")
            else:
                self.display.error("Failed to add peer to server - you'll need to add manually")

            # Show setup instructions
            self._show_mobile_instructions(platform)

            # Save client configuration
            self.config.set("clients.mobile.public_key", public_key)
            self.config.set("clients.mobile.name", device_name)
            self.config.set("clients.mobile.os", platform)
            self.config.set("clients.mobile.configured", True)
            if qr_code_path:
                self.config.set("clients.mobile.qr_code_path", qr_code_path)
            self.config.set("phases.phase6_mobile.platform", platform)
            self.config.set("phases.phase6_mobile.qr_code_generated", qr_code_path is not None)

            self.mark_complete(f"Mobile client ({platform}) configured")
            self.config.save()

            return True

        except Exception as e:
            logger.exception("Error in Phase 6 execution")
            self.mark_failed(str(e))
            return False

    def _prompt_for_platform(self) -> str:
        """Prompt user to select their mobile platform."""
        self.display.heading("Select Your Mobile Platform")
        self.display.newline()

        choice = self.prompts.choice(
            "Which mobile platform are you using?",
            ["Android", "iOS (iPhone/iPad)"]
        )

        return "android" if "Android" in choice else "ios"

    def _prompt_for_device_name(self) -> str:
        """Prompt user for a device name."""
        default_name = "mobile-device"
        return self.prompts.text(
            "Enter a name for this mobile device",
            default=default_name,
            help_text="This helps identify the device (e.g., android-phone, iphone, tablet)"
        )

    def _create_mobile_config(
        self,
        device_name: str,
        vpn_ip: str,
        private_key: str,
        public_key: str
    ) -> str:
        """Create WireGuard mobile configuration from template.

        Args:
            device_name: Name of the mobile device
            vpn_ip: VPN IP address for this device
            private_key: Client's private key
            public_key: Client's public key

        Returns:
            Rendered configuration file content
        """
        template_path = TEMPLATE_DIR / "wireguard_client.conf.j2"

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path) as f:
            template = Template(f.read())

        # Mobile config: on-demand, no routing all traffic (battery-efficient)
        config = template.render(
            client_name=device_name,
            client_vpn_ip=vpn_ip,
            vpn_subnet_mask="24",
            client_private_key=private_key,
            server_public_key=self.config.get("phases.phase2_wireguard_server.server_public_key"),
            server_public_ip=self.config.get("server.public_ip"),
            wireguard_port=self.config.get("network.wireguard_port", 51820),
            route_all_traffic=False,  # On-demand for mobile
            dns_servers=["1.1.1.1", "8.8.8.8"],
            vpn_network=self.config.get("network.vpn.network", "10.66.66.0/24")
        )

        return config

    def _generate_qr_code(self, device_name: str, config_text: str) -> str:
        """Generate QR code from configuration.

        Args:
            device_name: Name of the device
            config_text: WireGuard configuration content

        Returns:
            Path to the generated QR code file, or None on failure
        """
        try:
            # Ensure QR code directory exists
            qr_dir = Path(QR_CODE_DIR).expanduser()
            qr_dir.mkdir(parents=True, exist_ok=True)

            # Generate QR code
            qr_path = create_qr_with_metadata(
                config_text=config_text,
                client_name=device_name,
                output_dir=str(qr_dir)
            )

            return qr_path
        except Exception as e:
            logger.exception(f"Error generating QR code: {e}")
            return None

    def _add_peer_to_server(self, device_name: str, public_key: str, vpn_ip: str) -> bool:
        """Add this mobile device as a peer on the WireGuard server."""
        try:
            server_config_mgr = ServerConfigManager()
            return server_config_mgr.add_peer_to_server(
                client_name=device_name,
                public_key=public_key,
                vpn_ip=vpn_ip
            )
        except Exception as e:
            logger.exception(f"Error adding peer to server: {e}")
            return False

    def _show_mobile_instructions(self, platform: str):
        """Show mobile-specific setup instructions.

        Args:
            platform: Mobile platform ('android' or 'ios')
        """
        self.display.newline()
        self.display.heading("Mobile Setup Instructions")

        if platform == "android":
            instructions = """
**On your Android device:**

1. **Install WireGuard app:**
   - Open Google Play Store
   - Search for "WireGuard"
   - Install the official WireGuard app

2. **Add VPN configuration:**
   - Open WireGuard app
   - Tap the **+** button
   - Select **Scan from QR code**
   - Scan the QR code displayed above

3. **Connect to VPN:**
   - Tap the toggle switch next to your VPN configuration
   - VPN is now active!

4. **Verify connection:**
   - Open a web browser
   - Visit: https://ifconfig.me
   - You should see your server's public IP address

**Tips:**
- Toggle VPN on/off as needed from the WireGuard app
- Add a Quick Settings tile for faster access
- The app shows connection statistics and data usage
"""
        else:  # ios
            instructions = """
**On your iOS device (iPhone/iPad):**

1. **Install WireGuard app:**
   - Open App Store
   - Search for "WireGuard"
   - Install the official WireGuard app

2. **Add VPN configuration:**
   - Open WireGuard app
   - Tap **Add a tunnel**
   - Select **Create from QR code**
   - Scan the QR code displayed above
   - Give it a name (e.g., "Home VPN")

3. **Connect to VPN:**
   - Tap the toggle switch next to your VPN configuration
   - Approve the VPN configuration when prompted
   - VPN is now active!

4. **Verify connection:**
   - Open Safari
   - Visit: https://ifconfig.me
   - You should see your server's public IP address

**Tips:**
- Toggle VPN on/off from the WireGuard app or Control Center
- Add VPN widget to home screen for quick access
- View connection details and statistics in the app
"""

        self.display.markdown(instructions)
        self.prompts.pause()

    def verify(self) -> bool:
        """Verify that the phase completed successfully."""
        public_key = self.config.get("clients.mobile.public_key")
        if not public_key:
            return False

        try:
            server_config_mgr = ServerConfigManager()
            return server_config_mgr.verify_peer_exists(public_key)
        except:
            return True

    def rollback(self) -> bool:
        """Rollback Phase 6 changes."""
        try:
            public_key = self.config.get("clients.mobile.public_key")
            if public_key:
                server_config_mgr = ServerConfigManager()
                server_config_mgr.remove_peer_from_server(public_key)

            # Remove QR code file if it exists
            qr_code_path = self.config.get("clients.mobile.qr_code_path")
            if qr_code_path:
                qr_path = Path(qr_code_path)
                if qr_path.exists():
                    qr_path.unlink()

            self.config.set("clients.mobile.configured", False)
            self.config.set("clients.mobile.public_key", None)
            self.config.set("clients.mobile.qr_code_path", "")
            self.config.save()

            return True
        except Exception as e:
            logger.exception(f"Error during rollback: {e}")
            return False
