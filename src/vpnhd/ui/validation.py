"""Input validation utilities for VPNHD UI."""

import re
from typing import Optional, Callable

from ..network.validation import validate_ip_address, validate_network
from ..utils.helpers import validate_hostname as validate_hostname_helper
from ..utils.helpers import validate_port as validate_port_helper


class InputValidator:
    """Validates user input."""

    @staticmethod
    def validate_ip(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate IP address input.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        if not value:
            return False, "IP address cannot be empty"

        if validate_ip_address(value):
            return True, None
        else:
            return False, f"Invalid IP address: {value}"

    @staticmethod
    def validate_network_cidr(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate network in CIDR notation.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        if not value:
            return False, "Network cannot be empty"

        if validate_network(value):
            return True, None
        else:
            return False, f"Invalid network (use CIDR notation, e.g., 192.168.1.0/24): {value}"

    @staticmethod
    def validate_hostname(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate hostname.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        if not value:
            return False, "Hostname cannot be empty"

        if validate_hostname_helper(value):
            return True, None
        else:
            return False, f"Invalid hostname (use lowercase letters, numbers, and hyphens): {value}"

    @staticmethod
    def validate_port(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate port number.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            port = int(value)
            if validate_port_helper(port):
                return True, None
            else:
                return False, "Port must be between 1 and 65535"

        except ValueError:
            return False, "Port must be a number"

    @staticmethod
    def validate_email(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate email address.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        if not value:
            return False, "Email cannot be empty"

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, value):
            return True, None
        else:
            return False, f"Invalid email address: {value}"

    @staticmethod
    def validate_not_empty(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate that value is not empty.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        if value and value.strip():
            return True, None
        else:
            return False, "Value cannot be empty"

    @staticmethod
    def validate_yes_no(value: str) -> tuple[bool, Optional[str]]:
        """
        Validate yes/no input.

        Args:
            value: Input value

        Returns:
            tuple: (is_valid, error_message)
        """
        value_lower = value.lower().strip()
        if value_lower in ('y', 'yes', 'n', 'no'):
            return True, None
        else:
            return False, "Please enter 'y' or 'n'"

    @staticmethod
    def validate_choice(value: str, choices: list) -> tuple[bool, Optional[str]]:
        """
        Validate choice from list.

        Args:
            value: Input value
            choices: List of valid choices

        Returns:
            tuple: (is_valid, error_message)
        """
        if value in choices:
            return True, None
        else:
            return False, f"Invalid choice. Must be one of: {', '.join(str(c) for c in choices)}"

    @staticmethod
    def validate_integer(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> tuple[bool, Optional[str]]:
        """
        Validate integer input.

        Args:
            value: Input value
            min_val: Optional minimum value
            max_val: Optional maximum value

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            int_val = int(value)

            if min_val is not None and int_val < min_val:
                return False, f"Value must be at least {min_val}"

            if max_val is not None and int_val > max_val:
                return False, f"Value must be at most {max_val}"

            return True, None

        except ValueError:
            return False, "Value must be an integer"

    @staticmethod
    def validate_path(value: str, must_exist: bool = False) -> tuple[bool, Optional[str]]:
        """
        Validate file path.

        Args:
            value: Input value
            must_exist: Whether path must exist

        Returns:
            tuple: (is_valid, error_message)
        """
        from pathlib import Path

        if not value:
            return False, "Path cannot be empty"

        try:
            path = Path(value).expanduser()

            if must_exist and not path.exists():
                return False, f"Path does not exist: {value}"

            return True, None

        except Exception as e:
            return False, f"Invalid path: {e}"

    @staticmethod
    def create_custom_validator(
        validation_func: Callable[[str], bool],
        error_message: str
    ) -> Callable[[str], tuple[bool, Optional[str]]]:
        """
        Create a custom validator.

        Args:
            validation_func: Function that returns True if valid
            error_message: Error message if invalid

        Returns:
            Callable: Validator function
        """
        def validator(value: str) -> tuple[bool, Optional[str]]:
            if validation_func(value):
                return True, None
            else:
                return False, error_message

        return validator
