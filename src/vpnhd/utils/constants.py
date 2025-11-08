"""Constants used throughout the VPNHD application."""

from pathlib import Path
import os

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

# System Paths
WIREGUARD_DIR = Path("/etc/wireguard")
WIREGUARD_CONFIG = WIREGUARD_DIR / "wg0.conf"
SSH_DIR = Path.home() / ".ssh"
SSH_CONFIG = Path("/etc/ssh/sshd_config")

# Network Defaults
DEFAULT_VPN_NETWORK = "10.66.66.0/24"
DEFAULT_VPN_SERVER_IP = "10.66.66.1"
DEFAULT_WIREGUARD_PORT = 51820
DEFAULT_SSH_PORT = 22

# VPN Client IP Assignments
VPN_CLIENT_IPS = {
    "fedora": "10.66.66.2",
    "popos": "10.66.66.3",
    "termux": "10.66.66.10",
}

# Phase Names
PHASE_NAMES = {
    1: "Debian Server Installation",
    2: "WireGuard Server Setup",
    3: "Router Port Forwarding",
    4: "Fedora Client Setup",
    5: "Pop!_OS Client Setup",
    6: "Termux/Android Setup",
    7: "SSH Key Authentication",
    8: "Security Hardening",
}

# Phase Keys (for config)
PHASE_KEYS = {
    1: "phase1_debian",
    2: "phase2_wireguard_server",
    3: "phase3_router",
    4: "phase4_fedora",
    5: "phase5_popos",
    6: "phase6_termux",
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

# Optional Packages
OPTIONAL_PACKAGES = [
    "qrencode",  # For QR code generation
]

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
HOSTNAME_PATTERN = r'^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$'
IP_ADDRESS_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'
CIDR_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'

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

# Debian Versions
DEBIAN_SUPPORTED_VERSIONS = ["11", "12"]
DEBIAN_VERSION_NAMES = {
    "11": "Bullseye",
    "12": "Bookworm",
}

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
