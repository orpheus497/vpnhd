"""Cryptography utilities module for VPNHD."""

from .wireguard import (
    generate_keypair,
    generate_preshared_key,
    save_private_key,
    load_private_key,
    derive_public_key,
    validate_key
)
from .ssh import (
    generate_ssh_keypair,
    get_ssh_public_key,
    add_ssh_key_to_authorized_keys,
    test_ssh_key_auth
)

__all__ = [
    'generate_keypair',
    'generate_preshared_key',
    'save_private_key',
    'load_private_key',
    'derive_public_key',
    'validate_key',
    'generate_ssh_keypair',
    'get_ssh_public_key',
    'add_ssh_key_to_authorized_keys',
    'test_ssh_key_auth'
]
