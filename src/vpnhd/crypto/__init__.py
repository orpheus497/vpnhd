"""Cryptography utilities module for VPNHD."""

from .qrcode import (
    display_qr_terminal,
    generate_qr_code,
    generate_qr_for_config_file,
    save_qr_code,
    verify_qrcode_available,
)
from .rotation import KeyRotationManager
from .server_config import ServerConfigManager
from .ssh import (
    add_ssh_key_to_authorized_keys,
    generate_ssh_keypair,
    get_ssh_public_key,
    test_ssh_key_auth,
)
from .wireguard import (
    derive_public_key,
    generate_keypair,
    generate_preshared_key,
    load_private_key,
    save_private_key,
    validate_key,
)

__all__ = [
    "generate_keypair",
    "generate_preshared_key",
    "save_private_key",
    "load_private_key",
    "derive_public_key",
    "validate_key",
    "generate_ssh_keypair",
    "get_ssh_public_key",
    "add_ssh_key_to_authorized_keys",
    "test_ssh_key_auth",
    "ServerConfigManager",
    "generate_qr_code",
    "save_qr_code",
    "display_qr_terminal",
    "generate_qr_for_config_file",
    "verify_qrcode_available",
    "KeyRotationManager",
]
