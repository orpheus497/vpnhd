"""Helper utility functions for VPNHD."""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import re
import socket
import hashlib


def ensure_directory_exists(path: Path, mode: int = 0o700) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path
        mode: Directory permissions (default: 0700)

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True, mode=mode)
        return True
    except Exception as e:
        return False


def ensure_file_exists(path: Path, content: str = "", mode: int = 0o600) -> bool:
    """
    Ensure a file exists, creating it if necessary.

    Args:
        path: File path
        content: Default content if file doesn't exist
        mode: File permissions (default: 0600)

    Returns:
        bool: True if file exists or was created successfully
    """
    try:
        # Create parent directory if needed (exist_ok=True handles race conditions)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Use 'x' mode to atomically create file only if it doesn't exist
        # This prevents TOCTOU race conditions
        try:
            with path.open("x") as f:
                f.write(content)
            path.chmod(mode)
        except FileExistsError:
            # File already exists, which is fine
            pass
        return True
    except Exception:
        return False


def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """
    Read and parse a JSON file.

    Args:
        path: File path

    Returns:
        Optional[Dict]: Parsed JSON data or None if error
    """
    try:
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def write_json_file(path: Path, data: Dict[str, Any], mode: int = 0o600) -> bool:
    """
    Write data to a JSON file.

    Args:
        path: File path
        data: Data to write
        mode: File permissions (default: 0600)

    Returns:
        bool: True if successful
    """
    try:
        ensure_directory_exists(path.parent)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        path.chmod(mode)
        return True
    except Exception:
        return False


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        str: ISO formatted timestamp
    """
    return datetime.utcnow().isoformat() + "Z"


def get_timestamp_filename() -> str:
    """
    Get timestamp suitable for filenames.

    Returns:
        str: Timestamp string (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def validate_hostname(hostname: str) -> bool:
    """
    Validate hostname format.

    Args:
        hostname: Hostname to validate

    Returns:
        bool: True if valid
    """
    if not hostname or len(hostname) > 63:
        return False

    pattern = r"^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
    return bool(re.match(pattern, hostname.lower()))


def validate_port(port: int) -> bool:
    """
    Validate port number.

    Args:
        port: Port number

    Returns:
        bool: True if valid (1-65535)
    """
    return 1 <= port <= 65535


def is_root() -> bool:
    """
    Check if running as root.

    Returns:
        bool: True if running as root
    """
    import os

    return os.geteuid() == 0


def get_username() -> str:
    """
    Get current username.

    Returns:
        str: Username
    """
    import os

    return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def get_hostname() -> str:
    """
    Get system hostname.

    Returns:
        str: Hostname
    """
    return socket.gethostname()


def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get value from nested dictionary using dot notation.

    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., "network.lan.router_ip")
        default: Default value if key not found

    Returns:
        Any: Value at key path or default
    """
    keys = key_path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
    """
    Set value in nested dictionary using dot notation.

    Args:
        data: Dictionary to modify
        key_path: Dot-separated key path (e.g., "network.lan.router_ip")
        value: Value to set
    """
    keys = key_path.split(".")
    current = data

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def delete_nested_value(data: Dict[str, Any], key_path: str) -> bool:
    """
    Delete value from nested dictionary using dot notation.

    Args:
        data: Dictionary to modify
        key_path: Dot-separated key path (e.g., "clients.fedora")

    Returns:
        bool: True if key was found and deleted, False otherwise
    """
    keys = key_path.split(".")
    current = data

    # Navigate to parent of final key
    for key in keys[:-1]:
        if key not in current:
            return False
        current = current[key]

    # Delete final key if it exists
    final_key = keys[-1]
    if final_key in current:
        del current[final_key]
        return True

    return False


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes into human-readable string.

    Args:
        bytes_count: Number of bytes

    Returns:
        str: Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def calculate_file_hash(path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Calculate hash of a file.

    Args:
        path: File path
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Optional[str]: Hex digest of file hash or None if error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing potentially dangerous characters.

    Args:
        filename: Filename to sanitize

    Returns:
        str: Sanitized filename
    """
    # Remove path separators and null bytes
    filename = filename.replace("/", "_").replace("\\", "_").replace("\0", "")

    # Remove control characters
    filename = "".join(char for char in filename if ord(char) >= 32)

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def yes_no_to_bool(value: str) -> bool:
    """
    Convert yes/no string to boolean.

    Args:
        value: String value (y/yes/n/no, case-insensitive)

    Returns:
        bool: True for yes, False for no
    """
    return value.lower() in ("y", "yes", "true", "1")


def bool_to_yes_no(value: bool) -> str:
    """
    Convert boolean to yes/no string.

    Args:
        value: Boolean value

    Returns:
        str: "Yes" or "No"
    """
    return "Yes" if value else "No"


def list_to_string(items: List[str], separator: str = ", ", last_separator: str = " and ") -> str:
    """
    Convert list to human-readable string.

    Args:
        items: List of items
        separator: Separator between items
        last_separator: Separator before last item

    Returns:
        str: Formatted string
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]}{last_separator}{items[1]}"

    return separator.join(items[:-1]) + last_separator + items[-1]


def expand_path(path: str) -> Path:
    """
    Expand user home directory and resolve path.

    Args:
        path: Path string (may contain ~)

    Returns:
        Path: Expanded and resolved path
    """
    return Path(path).expanduser().resolve()


def is_valid_file_path(path: Path) -> bool:
    """
    Check if a path is valid and safe.

    Args:
        path: Path to validate

    Returns:
        bool: True if valid and safe
    """
    try:
        # Check if path is absolute
        if not path.is_absolute():
            return False

        # Check if path contains any suspicious patterns
        path_str = str(path)
        if ".." in path_str or path_str.startswith("/dev") or path_str.startswith("/proc"):
            return False

        return True
    except Exception:
        return False


def retry_on_failure(func, max_attempts: int = 3, delay: float = 1.0):
    """
    Retry a function on failure.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds

    Returns:
        Result of function or raises last exception
    """
    import time

    last_exception = None
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                time.sleep(delay)

    if last_exception:
        raise last_exception
