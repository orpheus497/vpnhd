"""Constants used throughout the VPNHD application."""

import os
from pathlib import Path

# Application Information
APP_NAME = "VPNHD"
APP_FULL_NAME = "VPN Helper Daemon"
APP_VERSION = "1.0.0"
APP_LICENSE = "GPL-3.0"
APP_AUTHOR = "orpheus497"

# Configuration Paths
CONFIG_DIR = Path.home() / ".config" / "vpnhd"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_DIR = CONFIG_DIR / "backups"
LOG_DIR = CONFIG_DIR / "logs"
LOG_FILE = LOG_DIR / "vpnhd.log"
QR_CODE_DIR = CONFIG_DIR / "qrcodes"

# Template Paths (absolute)
TEMPLATE_DIR = Path(__file__).parent.parent / "config" / "templates"
WIREGUARD_SERVER_TEMPLATE = TEMPLATE_DIR / "wireguard_server.conf.j2"
WIREGUARD_CLIENT_TEMPLATE = TEMPLATE_DIR / "wireguard_client.conf.j2"
UFW_RULES_TEMPLATE = TEMPLATE_DIR / "ufw_rules.j2"

# System Paths
WIREGUARD_DIR = Path("/etc/wireguard")
WIREGUARD_CONFIG = WIREGUARD_DIR / "wg0.conf"
SSH_DIR = Path.home() / ".ssh"
SSH_CONFIG = Path("/etc/ssh/sshd_config")
FAIL2BAN_JAIL_DIR = Path("/etc/fail2ban/jail.d")
FAIL2BAN_FILTER_DIR = Path("/etc/fail2ban/filter.d")

# Network Defaults
DEFAULT_VPN_NETWORK = "10.66.66.0/24"
DEFAULT_VPN_SERVER_IP = "10.66.66.1"
DEFAULT_WIREGUARD_PORT = 51820
DEFAULT_SSH_PORT = 22

# VPN Client IP Assignments (default suggestions)
VPN_CLIENT_IPS = {
    "linux_desktop_always_on": "10.66.66.2",
    "linux_desktop_on_demand": "10.66.66.3",
    "mobile": "10.66.66.10",
}

# Phase Names
PHASE_NAMES = {
    1: "Debian Server Installation",
    2: "WireGuard Server Setup",
    3: "Router Port Forwarding",
    4: "Linux Desktop Client (Always-On)",
    5: "Linux Desktop Client (On-Demand)",
    6: "Mobile Client (Android/iOS)",
    7: "SSH Key Authentication",
    8: "Security Hardening",
}

# Phase Keys (for config)
PHASE_KEYS = {
    1: "phase1_debian",
    2: "phase2_wireguard_server",
    3: "phase3_router",
    4: "phase4_linux_client",
    5: "phase5_linux_client_ondemand",
    6: "phase6_mobile",
    7: "phase7_ssh_keys",
    8: "phase8_security",
}

# Required System Packages
REQUIRED_PACKAGES_DEBIAN = [
    "python3",
    "python3-pip",
    "wireguard",
    "wireguard-tools",
    "openssh-client",
    "openssh-server",
    "ufw",
    "fail2ban",
    "systemd",
    "iproute2",
    "iptables",
    "net-tools",
]

REQUIRED_PACKAGES_FEDORA = [
    "python3",
    "python3-pip",
    "wireguard-tools",
    "openssh-clients",
    "openssh-server",
    "firewalld",
    "fail2ban",
    "systemd",
    "iproute",
    "iptables",
    "net-tools",
]

# Optional Packages (deprecated - Python libraries used instead)
OPTIONAL_PACKAGES = [
    # "qrencode" is deprecated - using Python qrcode library instead
]

# Supported Linux Distributions for Clients
SUPPORTED_CLIENT_DISTROS = {
    "debian": {"name": "Debian", "package_manager": "apt"},
    "ubuntu": {"name": "Ubuntu", "package_manager": "apt"},
    "pop": {"name": "Pop!_OS", "package_manager": "apt"},
    "elementary": {"name": "elementary OS", "package_manager": "apt"},
    "mint": {"name": "Linux Mint", "package_manager": "apt"},
    "fedora": {"name": "Fedora", "package_manager": "dnf"},
    "centos": {"name": "CentOS", "package_manager": "yum"},
    "rhel": {"name": "Red Hat Enterprise Linux", "package_manager": "yum"},
    "arch": {"name": "Arch Linux", "package_manager": "pacman"},
    "manjaro": {"name": "Manjaro", "package_manager": "pacman"},
}

# WireGuard package names per distribution
WIREGUARD_PACKAGES = {
    "apt": ["wireguard", "wireguard-tools"],
    "dnf": ["wireguard-tools"],
    "yum": ["wireguard-tools"],
    "pacman": ["wireguard-tools"],
}

# Error Messages
ERROR_NOT_ROOT = "This operation requires root privileges. Please run with sudo."
ERROR_CONFIG_NOT_FOUND = "Configuration file not found. Please run initial setup."
ERROR_INVALID_PHASE = "Invalid phase number. Must be between 1 and 8."
ERROR_PREREQUISITES_NOT_MET = "Prerequisites for this phase are not met."

# Success Messages
SUCCESS_PHASE_COMPLETE = "Phase completed successfully!"
SUCCESS_CONFIG_SAVED = "Configuration saved successfully."
SUCCESS_BACKUP_CREATED = "Backup created successfully."

# UI Constants
BORDER_CHAR = "━"
CORNER_CHAR = "╔╗╚╝"
SEPARATOR = "─" * 60

# Progress Symbols
SYMBOL_COMPLETE = "✓"
SYMBOL_INCOMPLETE = "○"
SYMBOL_IN_PROGRESS = "⧗"
SYMBOL_ERROR = "✗"
SYMBOL_WARNING = "⚠"

# Colors (for Rich library)
COLOR_SUCCESS = "green"
COLOR_ERROR = "red"
COLOR_WARNING = "yellow"
COLOR_INFO = "blue"
COLOR_HEADING = "cyan bold"
COLOR_PROMPT = "magenta"

# Timeout values (seconds)
COMMAND_TIMEOUT_DEFAULT = 60
COMMAND_TIMEOUT_LONG = 300
COMMAND_TIMEOUT_INSTALL = 600

# File Permissions
PERM_PRIVATE_KEY = 0o600
PERM_PUBLIC_KEY = 0o644
PERM_CONFIG_FILE = 0o600
PERM_DIRECTORY = 0o700

# Validation Patterns
HOSTNAME_PATTERN = r"^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
IP_ADDRESS_PATTERN = r"^(\d{1,3}\.){3}\d{1,3}$"
CIDR_PATTERN = r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"

# WireGuard Constants
WG_KEY_LENGTH = 44  # Base64 encoded 32-byte key
WG_INTERFACE_NAME = "wg0"
WG_KEEPALIVE = 25

# SSH Constants
SSH_KEY_TYPES = ["ed25519", "rsa", "ecdsa"]
SSH_KEY_DEFAULT_TYPE = "ed25519"
SSH_KEY_RSA_BITS = 4096

# UFW Rules
UFW_DEFAULT_INCOMING = "deny"
UFW_DEFAULT_OUTGOING = "allow"

# fail2ban Settings
FAIL2BAN_DEFAULT_BAN_TIME = 3600  # 1 hour
FAIL2BAN_DEFAULT_FIND_TIME = 600  # 10 minutes
FAIL2BAN_DEFAULT_MAX_RETRY = 5
FAIL2BAN_SSH_BAN_TIME = 3600
FAIL2BAN_SSH_MAX_RETRY = 5
FAIL2BAN_WIREGUARD_BAN_TIME = 7200  # 2 hours
FAIL2BAN_WIREGUARD_MAX_RETRY = 3

# Debian Versions
DEBIAN_SUPPORTED_VERSIONS = ["12", "13"]
DEBIAN_VERSION_NAMES = {
    "12": "Bookworm",
    "13": "Trixie",
}

# Python Version Requirements
PYTHON_MIN_VERSION = "3.11"
PYTHON_MIN_VERSION_TUPLE = (3, 11)

# Fedora Versions
FEDORA_SUPPORTED_VERSIONS = ["38", "39", "40"]

# Pop!_OS Versions
POPOS_SUPPORTED_VERSIONS = ["22.04"]

# External Services (for port forwarding test)
PORT_CHECK_SERVICES = [
    "https://ifconfig.me",
    "https://api.ipify.org",
    "https://icanhazip.com",
]

# Maximum retries
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Buffer sizes
BUFFER_SIZE_KB = 64
BUFFER_SIZE_BYTES = BUFFER_SIZE_KB * 1024
