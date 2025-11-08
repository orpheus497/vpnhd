"""Menu systems for VPNHD."""

from typing import Optional, TYPE_CHECKING

from .display import Display
from .prompts import Prompts
from ..utils.constants import PHASE_NAMES

if TYPE_CHECKING:
    from ..config.manager import ConfigManager


class MainMenu:
    """Main menu handler."""

    def __init__(self, config_manager: "ConfigManager"):
        """
        Initialize main menu.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.display = Display()
        self.prompts = Prompts()

    def show(self) -> str:
        """
        Display main menu and get user choice.

        Returns:
            str: User's menu choice
        """
        self.display.clear()
        self.display.banner("VPNHD - VPN Helper Daemon", "Privacy-First Home VPN Setup")

        self.display.newline()
        self.display.print("Welcome! This program will guide you through setting up", style="white")
        self.display.print("a complete privacy-focused home VPN using WireGuard.", style="white")

        # Display current status
        self.display.newline()
        self.display.heading("Current Status:", style="cyan bold")

        # Show phase status
        for phase_num in range(1, 9):
            phase_info = self.config.get_phase_info(phase_num)
            if phase_info:
                self.display.phase_status(
                    phase_num, phase_info["name"], phase_info["completed"], in_progress=False
                )

        # Show progress
        completion = self.config.get_completion_percentage()
        self.display.newline()
        self.display.print(
            f"Progress: {completion:.0f}% complete ({sum(1 for i in range(1, 9) if self.config.is_phase_complete(i))}/8 phases)",
            style="yellow",
        )

        # Display menu options
        self.display.newline()
        options = [
            ("1", "Continue to next phase"),
            ("2", "Jump to specific phase"),
            ("3", "Review configuration"),
            ("4", "Show phase details"),
            ("5", "Troubleshooting"),
            ("6", "View guide documentation"),
            ("0", "Exit"),
        ]

        choice = self.prompts.menu("Main Menu", options)

        return choice

    def show_phase_selection(self) -> Optional[int]:
        """
        Show phase selection menu.

        Returns:
            Optional[int]: Selected phase number or None
        """
        self.display.clear()
        self.display.heading("Select Phase", style="cyan bold")

        options = []
        for phase_num in range(1, 9):
            phase_name = PHASE_NAMES.get(phase_num, f"Phase {phase_num}")
            completed = "[DONE]" if self.config.is_phase_complete(phase_num) else ""
            options.append((str(phase_num), f"{phase_name} {completed}"))

        choice = self.prompts.menu("Available Phases", options, allow_back=True)

        if choice == "b":
            return None

        return int(choice)

    def show_configuration_review(self) -> None:
        """Display configuration review."""
        self.display.clear()
        self.display.heading("Configuration Review", style="cyan bold")
        self.display.separator()

        # Network Configuration
        self.display.heading("Network Configuration")
        self.display.key_value("LAN Network", self.config.get("network.lan.subnet", "Not set"))
        self.display.key_value("Router IP", self.config.get("network.lan.router_ip", "Not set"))
        self.display.key_value("Server IP", self.config.get("network.lan.server_ip", "Not set"))
        self.display.newline()
        self.display.key_value("VPN Network", self.config.get("network.vpn.network", "Not set"))
        self.display.key_value("Server VPN IP", self.config.get("network.vpn.server_ip", "Not set"))
        self.display.key_value(
            "WireGuard Port", str(self.config.get("network.wireguard_port", "Not set"))
        )

        # Server Information
        self.display.newline()
        self.display.heading("Server Information")
        self.display.key_value("Hostname", self.config.get("server.hostname", "Not set"))
        self.display.key_value("Username", self.config.get("server.username", "Not set"))
        self.display.key_value("LAN IP", self.config.get("server.lan_ip", "Not set"))
        self.display.key_value("Public IP", self.config.get("server.public_ip", "Not set"))
        self.display.key_value("OS", self.config.get("server.os", "Not set"))
        self.display.key_value("Interface", self.config.get("server.interface", "Not set"))

        # Clients
        self.display.newline()
        self.display.heading("Clients")

        clients = self.config.get("clients", {})
        for client_id, client_data in clients.items():
            name = client_data.get("name", client_id)
            status = "Configured" if client_data.get("configured", False) else "Not configured"
            self.display.key_value(
                name,
                f"IP: {client_data.get('vpn_ip', 'N/A')} - Mode: {client_data.get('vpn_mode', 'N/A')} - {status}",
            )

        # Security
        self.display.newline()
        self.display.heading("Security")

        security = self.config.get("security", {})
        self.display.key_value(
            "SSH Keys", "Enabled" if security.get("ssh_key_auth_enabled") else "Disabled"
        )
        self.display.key_value(
            "Password Auth", "Disabled" if security.get("ssh_password_auth_disabled") else "Enabled"
        )
        self.display.key_value(
            "Firewall (UFW)", "Active" if security.get("firewall_enabled") else "Inactive"
        )
        self.display.key_value(
            "fail2ban", "Running" if security.get("fail2ban_enabled") else "Not running"
        )

        self.display.separator()
        self.prompts.pause()

    def show_phase_details(self, phase_number: int) -> None:
        """
        Show details for a specific phase.

        Args:
            phase_number: Phase number (1-8)
        """
        phase_info = self.config.get_phase_info(phase_number)

        if not phase_info:
            self.display.error(f"Invalid phase number: {phase_number}")
            return

        self.display.clear()
        self.display.heading(f"Phase {phase_number}: {phase_info['name']}", style="cyan bold")
        self.display.separator()

        # Status
        status = "COMPLETED" if phase_info["completed"] else "NOT STARTED"
        status_style = "green" if phase_info["completed"] else "yellow"
        self.display.print(f"Status: {status}", style=status_style)

        # Completion date
        if phase_info["date_completed"]:
            self.display.key_value("Completed", phase_info["date_completed"])

        # Notes
        if phase_info.get("notes"):
            self.display.newline()
            self.display.heading("Notes:")
            self.display.print(phase_info["notes"])

        # Phase-specific details
        if phase_number == 2:  # WireGuard Server
            server_pubkey = phase_info.get("server_public_key")
            if server_pubkey:
                self.display.newline()
                self.display.key_value("Server Public Key", server_pubkey)

        self.display.separator()
        self.prompts.pause()

    def show_troubleshooting(self) -> None:
        """Display troubleshooting menu."""
        self.display.clear()
        self.display.heading("Troubleshooting", style="cyan bold")

        self.display.print("\nCommon Issues:\n", style="yellow bold")

        issues = [
            "WireGuard won't start",
            "Cannot connect to VPN",
            "No internet through VPN",
            "SSH connection refused",
            "Port forwarding not working",
            "Firewall blocking connections",
        ]

        self.display.list_items(issues, numbered=True)

        self.display.newline()
        self.display.print("For detailed troubleshooting, please refer to:", style="white")
        self.display.print("  ~/.config/vpnhd/logs/vpnhd.log", style="cyan")
        self.display.print("  .devdocs/PART-4-PHASES-7-8-SECURITY-AND-COMPLETION.md", style="cyan")

        self.prompts.pause()

    def confirm_phase_execution(self, phase_number: int, phase_name: str) -> bool:
        """
        Confirm before executing a phase.

        Args:
            phase_number: Phase number
            phase_name: Phase name

        Returns:
            bool: True if user confirms
        """
        self.display.newline()
        return self.prompts.confirm(
            f"Ready to execute Phase {phase_number}: {phase_name}?", default=True
        )
