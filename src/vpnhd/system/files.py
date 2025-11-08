"""File system operation utilities for VPNHD."""

from pathlib import Path
from typing import Optional, List
import shutil
import filecmp

from ..utils.logging import get_logger
from ..utils.helpers import ensure_directory_exists, calculate_file_hash
from ..utils.constants import PERM_PRIVATE_KEY, PERM_CONFIG_FILE
from .commands import execute_command


class FileManager:
    """Manages file system operations."""

    def __init__(self):
        """Initialize file manager."""
        self.logger = get_logger("FileManager")

    def backup_file(self, file_path: Path, backup_suffix: str = ".backup") -> Optional[Path]:
        """
        Create a backup of a file.

        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix for backup file

        Returns:
            Optional[Path]: Path to backup file or None if failed
        """
        if not file_path.exists():
            self.logger.warning(f"Cannot backup non-existent file: {file_path}")
            return None

        backup_path = Path(str(file_path) + backup_suffix)

        try:
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Backed up {file_path} to {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Failed to backup file: {e}")
            return None

    def restore_backup(self, backup_path: Path, original_path: Path) -> bool:
        """
        Restore a file from backup.

        Args:
            backup_path: Path to backup file
            original_path: Path to restore to

        Returns:
            bool: True if restored successfully
        """
        if not backup_path.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            return False

        try:
            shutil.copy2(backup_path, original_path)
            self.logger.info(f"Restored {original_path} from {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False

    def safe_write_file(
        self,
        file_path: Path,
        content: str,
        mode: int = PERM_CONFIG_FILE,
        backup: bool = True,
        sudo: bool = False
    ) -> bool:
        """
        Safely write content to a file with backup.

        Args:
            file_path: Path to file
            content: Content to write
            mode: File permissions
            backup: Whether to create backup if file exists
            sudo: Whether to use sudo for writing

        Returns:
            bool: True if write succeeded
        """
        try:
            # Backup existing file if requested
            if backup and file_path.exists():
                self.backup_file(file_path)

            # Ensure parent directory exists
            ensure_directory_exists(file_path.parent)

            if sudo:
                # Write to temp file first, then move with sudo
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                # Move to final location with sudo
                result = execute_command(
                    f"mv {tmp_path} {file_path}",
                    sudo=True,
                    check=False
                )

                if not result.success:
                    Path(tmp_path).unlink(missing_ok=True)
                    return False

                # Set permissions
                execute_command(
                    ["chmod", oct(mode)[2:], str(file_path)],
                    sudo=True,
                    check=False
                )

            else:
                # Write directly
                file_path.write_text(content)
                file_path.chmod(mode)

            self.logger.info(f"Wrote file: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write file: {e}")
            return False

    def safe_read_file(self, file_path: Path, sudo: bool = False) -> Optional[str]:
        """
        Safely read content from a file.

        Args:
            file_path: Path to file
            sudo: Whether to use sudo for reading

        Returns:
            Optional[str]: File content or None if failed
        """
        try:
            if not file_path.exists():
                self.logger.warning(f"File not found: {file_path}")
                return None

            if sudo:
                result = execute_command(
                    f"cat {file_path}",
                    sudo=True,
                    check=False,
                    capture_output=True
                )

                if result.success:
                    return result.stdout
                else:
                    return None

            else:
                return file_path.read_text()

        except Exception as e:
            self.logger.error(f"Failed to read file: {e}")
            return None

    def append_to_file(
        self,
        file_path: Path,
        content: str,
        sudo: bool = False
    ) -> bool:
        """
        Append content to a file.

        Args:
            file_path: Path to file
            content: Content to append
            sudo: Whether to use sudo

        Returns:
            bool: True if append succeeded
        """
        try:
            if sudo:
                # Use tee -a to append with sudo
                result = execute_command(
                    f"echo '{content}' | sudo tee -a {file_path} > /dev/null",
                    check=False
                )
                return result.success

            else:
                with open(file_path, 'a') as f:
                    f.write(content)
                return True

        except Exception as e:
            self.logger.error(f"Failed to append to file: {e}")
            return False

    def delete_file(self, file_path: Path, sudo: bool = False) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to file
            sudo: Whether to use sudo

        Returns:
            bool: True if deletion succeeded
        """
        try:
            if not file_path.exists():
                self.logger.debug(f"File already deleted: {file_path}")
                return True

            if sudo:
                result = execute_command(
                    ["rm", "-f", str(file_path)],
                    sudo=True,
                    check=False
                )
                return result.success

            else:
                file_path.unlink()
                self.logger.info(f"Deleted file: {file_path}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return False

    def copy_file(
        self,
        source: Path,
        destination: Path,
        sudo: bool = False,
        preserve_permissions: bool = True
    ) -> bool:
        """
        Copy a file.

        Args:
            source: Source file path
            destination: Destination file path
            sudo: Whether to use sudo
            preserve_permissions: Preserve source file permissions

        Returns:
            bool: True if copy succeeded
        """
        try:
            if not source.exists():
                self.logger.error(f"Source file not found: {source}")
                return False

            ensure_directory_exists(destination.parent)

            if sudo:
                cmd = f"cp {source} {destination}"
                if preserve_permissions:
                    cmd = f"cp -p {source} {destination}"

                result = execute_command(cmd, sudo=True, check=False)
                return result.success

            else:
                if preserve_permissions:
                    shutil.copy2(source, destination)
                else:
                    shutil.copy(source, destination)

                self.logger.info(f"Copied {source} to {destination}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to copy file: {e}")
            return False

    def move_file(self, source: Path, destination: Path, sudo: bool = False) -> bool:
        """
        Move a file.

        Args:
            source: Source file path
            destination: Destination file path
            sudo: Whether to use sudo

        Returns:
            bool: True if move succeeded
        """
        try:
            if not source.exists():
                self.logger.error(f"Source file not found: {source}")
                return False

            ensure_directory_exists(destination.parent)

            if sudo:
                result = execute_command(
                    f"mv {source} {destination}",
                    sudo=True,
                    check=False
                )
                return result.success

            else:
                shutil.move(str(source), str(destination))
                self.logger.info(f"Moved {source} to {destination}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to move file: {e}")
            return False

    def set_permissions(self, file_path: Path, mode: int, sudo: bool = False) -> bool:
        """
        Set file permissions.

        Args:
            file_path: Path to file
            mode: Permissions mode (e.g., 0o600)
            sudo: Whether to use sudo

        Returns:
            bool: True if permissions set successfully
        """
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False

            if sudo:
                result = execute_command(
                    f"chmod {oct(mode)[2:]} {file_path}",
                    sudo=True,
                    check=False
                )
                return result.success

            else:
                file_path.chmod(mode)
                self.logger.info(f"Set permissions {oct(mode)} on {file_path}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to set permissions: {e}")
            return False

    def set_owner(self, file_path: Path, owner: str, group: Optional[str] = None, sudo: bool = True) -> bool:
        """
        Set file owner and group.

        Args:
            file_path: Path to file
            owner: Owner username
            group: Group name (optional)
            sudo: Whether to use sudo

        Returns:
            bool: True if ownership set successfully
        """
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False

            owner_spec = owner
            if group:
                owner_spec = f"{owner}:{group}"

            result = execute_command(
                f"chown {owner_spec} {file_path}",
                sudo=sudo,
                check=False
            )

            if result.success:
                self.logger.info(f"Set owner {owner_spec} on {file_path}")

            return result.success

        except Exception as e:
            self.logger.error(f"Failed to set owner: {e}")
            return False

    def files_are_identical(self, file1: Path, file2: Path) -> bool:
        """
        Check if two files are identical.

        Args:
            file1: First file path
            file2: Second file path

        Returns:
            bool: True if files are identical
        """
        if not file1.exists() or not file2.exists():
            return False

        try:
            return filecmp.cmp(file1, file2, shallow=False)
        except Exception:
            return False

    def get_file_size(self, file_path: Path) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            Optional[int]: File size or None if error
        """
        try:
            if file_path.exists():
                return file_path.stat().st_size
        except Exception:
            pass

        return None

    def verify_file_hash(
        self,
        file_path: Path,
        expected_hash: str,
        algorithm: str = 'sha256'
    ) -> bool:
        """
        Verify file hash matches expected value.

        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm (default: sha256)

        Returns:
            bool: True if hash matches
        """
        actual_hash = calculate_file_hash(file_path, algorithm)
        if actual_hash is None:
            return False

        return actual_hash.lower() == expected_hash.lower()
