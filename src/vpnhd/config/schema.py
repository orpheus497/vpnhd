"""Configuration schema and default configuration for VPNHD."""

from typing import Dict, Any
from ..utils.helpers import get_timestamp


def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration structure.

    Returns:
        Dict[str, Any]: Default configuration dictionary
    """
    return {
        "version": "1.0.0",
        "created_date": get_timestamp(),
        "last_modified": get_timestamp(),

        "network": {
            "lan": {
                "router_ip": "",
                "subnet": "",
                "server_ip": "",
                "interface": ""
            },
            "vpn": {
                "network": "10.66.66.0/24",
                "subnet_mask": "255.255.255.0",
                "server_ip": "10.66.66.1",
                "clients": {
                    "fedora": {
                        "ip": "10.66.66.2",
                        "name": "fedora-laptop"
                    },
                    "popos": {
                        "ip": "10.66.66.3",
                        "name": "popos-laptop"
                    },
                    "termux": {
                        "ip": "10.66.66.10",
                        "name": "android-phone"
                    }
                }
            },
            "wireguard_port": 51820,
            "ssh_port": 22
        },

        "server": {
            "hostname": "",
            "username": "",
            "lan_ip": "",
            "mac_address": "",
            "interface": "",
            "os": "debian",
            "os_version": "",
            "architecture": "amd64",
            "public_ip": ""
        },

        "clients": {
            "fedora": {
                "name": "fedora-laptop",
                "os": "fedora",
                "vpn_mode": "always-on",
                "vpn_ip": "10.66.66.2",
                "public_key": None,
                "private_key_path": "",
                "configured": False
            },
            "popos": {
                "name": "popos-laptop",
                "os": "popos",
                "vpn_mode": "on-demand",
                "vpn_ip": "10.66.66.3",
                "public_key": None,
                "private_key_path": "",
                "isolated": True,
                "configured": False
            },
            "termux": {
                "name": "android-phone",
                "os": "android",
                "vpn_mode": "on-demand",
                "vpn_ip": "10.66.66.10",
                "public_key": None,
                "private_key_path": "",
                "configured": False
            }
        },

        "security": {
            "ssh_key_auth_enabled": False,
            "ssh_password_auth_disabled": False,
            "firewall_enabled": False,
            "fail2ban_enabled": False,
            "wireguard_running": False
        },

        "phases": {
            "phase1_debian": {
                "completed": False,
                "date_completed": None,
                "notes": ""
            },
            "phase2_wireguard_server": {
                "completed": False,
                "date_completed": None,
                "server_private_key_path": "/etc/wireguard/server_private.key",
                "server_public_key": None,
                "notes": ""
            },
            "phase3_router": {
                "completed": False,
                "date_completed": None,
                "port_forwarding_verified": False,
                "notes": ""
            },
            "phase4_fedora": {
                "completed": False,
                "date_completed": None,
                "notes": ""
            },
            "phase5_popos": {
                "completed": False,
                "date_completed": None,
                "notes": ""
            },
            "phase6_termux": {
                "completed": False,
                "date_completed": None,
                "notes": ""
            },
            "phase7_ssh_keys": {
                "completed": False,
                "date_completed": None,
                "ssh_key_path": "~/.ssh/id_ed25519",
                "notes": ""
            },
            "phase8_security": {
                "completed": False,
                "date_completed": None,
                "ufw_configured": False,
                "fail2ban_configured": False,
                "notes": ""
            }
        },

        "paths": {
            "wireguard_config_dir": "/etc/wireguard",
            "wireguard_server_config": "/etc/wireguard/wg0.conf",
            "ssh_config": "/etc/ssh/sshd_config",
            "backup_dir": "~/.config/vpnhd/backups"
        }
    }


# JSON Schema for configuration validation
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "created_date": {"type": "string"},
        "last_modified": {"type": "string"},
        "network": {
            "type": "object",
            "properties": {
                "lan": {
                    "type": "object",
                    "properties": {
                        "router_ip": {"type": "string"},
                        "subnet": {"type": "string"},
                        "server_ip": {"type": "string"},
                        "interface": {"type": "string"}
                    }
                },
                "vpn": {
                    "type": "object",
                    "properties": {
                        "network": {"type": "string"},
                        "subnet_mask": {"type": "string"},
                        "server_ip": {"type": "string"},
                        "clients": {"type": "object"}
                    }
                },
                "wireguard_port": {"type": "integer"},
                "ssh_port": {"type": "integer"}
            }
        },
        "server": {"type": "object"},
        "clients": {"type": "object"},
        "security": {"type": "object"},
        "phases": {"type": "object"},
        "paths": {"type": "object"}
    },
    "required": ["version", "network", "server", "clients", "security", "phases", "paths"]
}
