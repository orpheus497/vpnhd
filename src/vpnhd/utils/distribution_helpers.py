"""Distribution-related helper utilities for Linux client setup."""

from typing import Tuple

from .constants import SUPPORTED_CLIENT_DISTROS, WIREGUARD_PACKAGES


def prompt_for_distribution(display, prompts) -> str:
    """Prompt user to select their Linux distribution.

    Args:
        display: Display manager for UI output
        prompts: Prompts manager for user input

    Returns:
        str: Distribution key (e.g., 'fedora', 'ubuntu', 'linux')
    """
    display.heading("Select Your Linux Distribution")
    display.newline()

    # Build choices from supported distributions
    choices = []
    for key, info in SUPPORTED_CLIENT_DISTROS.items():
        choices.append(f"{info['name']} ({key})")

    choices.append("Other (generic Linux)")

    choice = prompts.choice("Which Linux distribution are you using?", choices)

    # Extract distribution key from choice
    if choice == "Other (generic Linux)":
        return "linux"

    # Extract key from choice (e.g., "Fedora (fedora)" -> "fedora")
    for key, info in SUPPORTED_CLIENT_DISTROS.items():
        if f"({key})" in choice:
            return key

    return "linux"


def get_package_install_command(pkg_manager: str, packages: list) -> str:
    """Get the installation command for a package manager.

    Args:
        pkg_manager: Package manager name (apt, dnf, yum, pacman)
        packages: List of package names to install

    Returns:
        str: Installation command(s) for the package manager
    """
    pkg_list = " ".join(packages)

    if pkg_manager == "apt":
        return f"sudo apt update\n   sudo apt install -y {pkg_list}"
    elif pkg_manager == "dnf":
        return f"sudo dnf install -y {pkg_list}"
    elif pkg_manager == "yum":
        return f"sudo yum install -y {pkg_list}"
    elif pkg_manager == "pacman":
        return f"sudo pacman -S --noconfirm {pkg_list}"
    else:
        # Fallback for unknown package managers
        return f"# Install WireGuard packages: {pkg_list}"


def generate_wireguard_install_instructions(distro: str, always_on: bool = True) -> str:
    """Generate WireGuard installation instructions for a distribution.

    Args:
        distro: Distribution key (e.g., 'fedora', 'ubuntu')
        always_on: Whether this is an always-on or on-demand configuration

    Returns:
        str: Formatted installation instructions in Markdown
    """
    # Get package manager for this distribution
    pkg_manager = SUPPORTED_CLIENT_DISTROS.get(distro, {}).get("package_manager", "apt")

    # Get WireGuard packages for this package manager
    wg_packages = WIREGUARD_PACKAGES.get(pkg_manager, ["wireguard-tools"])

    # Get installation command
    install_cmd = get_package_install_command(pkg_manager, wg_packages)

    # Build instructions based on mode
    if always_on:
        step4_content = """4. **Enable and start WireGuard:**

   ```bash
   sudo systemctl enable wg-quick@wg0
   sudo systemctl start wg-quick@wg0
   ```

5. **Verify connection:**

   ```bash
   sudo wg show
   curl ifconfig.me  # Should show your server's public IP
   ```

**Note:** This configuration routes ALL your traffic through the VPN for maximum privacy."""
    else:
        step4_content = """4. **Connect manually when needed:**

   ```bash
   # Start VPN
   sudo wg-quick up wg0

   # Stop VPN
   sudo wg-quick down wg0

   # Check status
   sudo wg show
   ```

5. **Optional: Create aliases for convenience:**

   ```bash
   echo "alias vpn-up='sudo wg-quick up wg0'" >> ~/.bashrc
   echo "alias vpn-down='sudo wg-quick down wg0'" >> ~/.bashrc
   source ~/.bashrc
   ```

**Note:** This configuration is on-demand (manual control) and isolated from other VPN clients
for enhanced security. Use `vpn-up` to connect and `vpn-down` to disconnect."""

    instructions = f"""
**On your Linux desktop/laptop ({distro}):**

1. **Install WireGuard:**

   ```bash
   {install_cmd}
   ```

2. **Create configuration file:**

   ```bash
   sudo nano /etc/wireguard/wg0.conf
   ```

   Paste the configuration shown above.

3. **Set permissions:**

   ```bash
   sudo chmod 600 /etc/wireguard/wg0.conf
   ```

{step4_content}
"""

    return instructions
