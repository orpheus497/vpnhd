"""Backup and restore manager for VPNHD.

This module provides comprehensive backup and restore functionality for VPN
configurations, client data, and system state.
"""

import tarfile
import shutil
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

from ..config.manager import ConfigManager
from ..client import ClientManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    created_at: str
    description: str
    version: str
    size_bytes: int
    checksum: str
    includes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        """Create from dictionary."""
        return cls(**data)


class BackupManager:
    """Manages backups and restores for VPNHD."""

    def __init__(self):
        """Initialize backup manager."""
        self.backup_dir = Path.home() / ".config" / "vpnhd" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.config_dir = Path.home() / ".config" / "vpnhd"
        self.wireguard_dir = Path("/etc/wireguard")
        self.ssh_dir = Path.home() / ".ssh"

    def create_backup(
        self,
        description: str = "",
        include_wireguard: bool = True,
        include_ssh: bool = True,
        include_config: bool = True,
        include_clients: bool = True
    ) -> Optional[str]:
        """Create a new backup.

        Args:
            description: Description of the backup
            include_wireguard: Include WireGuard configuration
            include_ssh: Include SSH keys
            include_config: Include VPNHD configuration
            include_clients: Include client database

        Returns:
            Backup ID if successful, None otherwise
        """
        try:
            # Generate backup ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}"

            logger.info(f"Creating backup: {backup_id}")

            # Create temporary backup directory
            temp_dir = self.backup_dir / f"{backup_id}_temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            includes = []

            # Backup VPNHD configuration
            if include_config:
                config_backup_dir = temp_dir / "config"
                config_backup_dir.mkdir()

                config_file = self.config_dir / "config.json"
                if config_file.exists():
                    shutil.copy2(config_file, config_backup_dir / "config.json")
                    includes.append("vpnhd_config")

            # Backup client database
            if include_clients:
                clients_file = self.config_dir / "clients.json"
                if clients_file.exists():
                    if not (temp_dir / "config").exists():
                        (temp_dir / "config").mkdir()
                    shutil.copy2(clients_file, temp_dir / "config" / "clients.json")
                    includes.append("client_database")

            # Backup WireGuard configuration
            if include_wireguard:
                wg_backup_dir = temp_dir / "wireguard"
                wg_backup_dir.mkdir()

                wg_config = self.wireguard_dir / "wg0.conf"
                if wg_config.exists():
                    # Note: This requires sudo to read
                    try:
                        content = wg_config.read_text()
                        (wg_backup_dir / "wg0.conf").write_text(content)
                        includes.append("wireguard_config")
                    except PermissionError:
                        logger.warning("Cannot backup WireGuard config (requires sudo)")

            # Backup SSH keys
            if include_ssh:
                ssh_backup_dir = temp_dir / "ssh"
                ssh_backup_dir.mkdir()

                # Backup known VPN-related SSH keys
                ssh_keys = list(self.ssh_dir.glob("vpnhd_*"))
                if ssh_keys:
                    for key_file in ssh_keys:
                        shutil.copy2(key_file, ssh_backup_dir / key_file.name)
                    includes.append("ssh_keys")

            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                created_at=datetime.now().isoformat(),
                description=description,
                version="1.0.0",
                size_bytes=0,  # Will be updated
                checksum="",  # Will be updated
                includes=includes
            )

            # Write metadata
            metadata_file = temp_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)

            # Create tar.gz archive
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(temp_dir, arcname=backup_id)

            # Calculate checksum and size
            checksum = self._calculate_checksum(archive_path)
            size_bytes = archive_path.stat().st_size

            # Update metadata
            metadata.checksum = checksum
            metadata.size_bytes = size_bytes

            # Save updated metadata separately
            metadata_path = self.backup_dir / f"{backup_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)

            # Clean up temp directory
            shutil.rmtree(temp_dir)

            logger.info(f"Backup created successfully: {archive_path}")
            logger.info(f"Size: {size_bytes / 1024:.2f} KB, Checksum: {checksum[:16]}...")

            return backup_id

        except Exception as e:
            logger.exception(f"Error creating backup: {e}")

            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            return None

    def restore_backup(
        self,
        backup_id: str,
        restore_wireguard: bool = True,
        restore_ssh: bool = True,
        restore_config: bool = True,
        restore_clients: bool = True,
        verify_checksum: bool = True
    ) -> bool:
        """Restore from a backup.

        Args:
            backup_id: Backup ID to restore
            restore_wireguard: Restore WireGuard configuration
            restore_ssh: Restore SSH keys
            restore_config: Restore VPNHD configuration
            restore_clients: Restore client database
            verify_checksum: Verify backup integrity before restoring

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Restoring backup: {backup_id}")

            # Verify backup exists
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            if not archive_path.exists():
                logger.error(f"Backup not found: {backup_id}")
                return False

            # Load metadata
            metadata = self.get_backup_metadata(backup_id)
            if not metadata:
                logger.error(f"Metadata not found for backup: {backup_id}")
                return False

            # Verify checksum
            if verify_checksum:
                current_checksum = self._calculate_checksum(archive_path)
                if current_checksum != metadata.checksum:
                    logger.error("Backup checksum verification failed!")
                    return False
                logger.info("Backup checksum verified")

            # Extract to temporary directory
            temp_dir = self.backup_dir / f"{backup_id}_restore_temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(temp_dir)

            extracted_dir = temp_dir / backup_id

            # Restore VPNHD configuration
            if restore_config and "vpnhd_config" in metadata.includes:
                config_file = extracted_dir / "config" / "config.json"
                if config_file.exists():
                    target = self.config_dir / "config.json"
                    # Backup current config first
                    if target.exists():
                        shutil.copy2(target, target.with_suffix(".json.bak"))
                    shutil.copy2(config_file, target)
                    logger.info("VPNHD configuration restored")

            # Restore client database
            if restore_clients and "client_database" in metadata.includes:
                clients_file = extracted_dir / "config" / "clients.json"
                if clients_file.exists():
                    target = self.config_dir / "clients.json"
                    # Backup current clients first
                    if target.exists():
                        shutil.copy2(target, target.with_suffix(".json.bak"))
                    shutil.copy2(clients_file, target)
                    logger.info("Client database restored")

            # Restore WireGuard configuration
            if restore_wireguard and "wireguard_config" in metadata.includes:
                wg_config = extracted_dir / "wireguard" / "wg0.conf"
                if wg_config.exists():
                    try:
                        target = self.wireguard_dir / "wg0.conf"
                        # This requires sudo
                        logger.warning("WireGuard config restore requires manual sudo operation")
                        logger.info(f"Extracted WireGuard config to: {wg_config}")
                        logger.info(f"Manually copy to: {target}")
                    except Exception as e:
                        logger.warning(f"Cannot restore WireGuard config: {e}")

            # Restore SSH keys
            if restore_ssh and "ssh_keys" in metadata.includes:
                ssh_dir = extracted_dir / "ssh"
                if ssh_dir.exists():
                    for key_file in ssh_dir.glob("*"):
                        target = self.ssh_dir / key_file.name
                        shutil.copy2(key_file, target)
                        target.chmod(0o600)
                    logger.info("SSH keys restored")

            # Clean up
            shutil.rmtree(temp_dir)

            logger.info(f"Backup {backup_id} restored successfully")
            return True

        except Exception as e:
            logger.exception(f"Error restoring backup: {e}")

            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            return False

    def list_backups(self) -> List[BackupMetadata]:
        """List all available backups.

        Returns:
            List of backup metadata, sorted by date (newest first)
        """
        backups = []

        for metadata_file in self.backup_dir.glob("backup_*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    metadata = BackupMetadata.from_dict(data)
                    backups.append(metadata)
            except Exception as e:
                logger.warning(f"Error loading metadata from {metadata_file}: {e}")

        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    def get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get metadata for a specific backup.

        Args:
            backup_id: Backup ID

        Returns:
            BackupMetadata or None if not found
        """
        metadata_file = self.backup_dir / f"{backup_id}_metadata.json"

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                return BackupMetadata.from_dict(data)
        except Exception as e:
            logger.exception(f"Error loading metadata: {e}")
            return None

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup.

        Args:
            backup_id: Backup ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            metadata_path = self.backup_dir / f"{backup_id}_metadata.json"

            if archive_path.exists():
                archive_path.unlink()

            if metadata_path.exists():
                metadata_path.unlink()

            logger.info(f"Backup {backup_id} deleted")
            return True

        except Exception as e:
            logger.exception(f"Error deleting backup: {e}")
            return False

    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity.

        Args:
            backup_id: Backup ID to verify

        Returns:
            True if valid, False otherwise
        """
        try:
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            if not archive_path.exists():
                logger.error(f"Backup archive not found: {backup_id}")
                return False

            metadata = self.get_backup_metadata(backup_id)
            if not metadata:
                logger.error(f"Metadata not found for backup: {backup_id}")
                return False

            # Verify checksum
            current_checksum = self._calculate_checksum(archive_path)
            if current_checksum != metadata.checksum:
                logger.error("Checksum mismatch!")
                logger.error(f"Expected: {metadata.checksum}")
                logger.error(f"Got: {current_checksum}")
                return False

            # Try to open tar file
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.getmembers()

            logger.info(f"Backup {backup_id} verified successfully")
            return True

        except Exception as e:
            logger.exception(f"Error verifying backup: {e}")
            return False

    def get_backup_size(self, backup_id: str) -> int:
        """Get size of a backup in bytes.

        Args:
            backup_id: Backup ID

        Returns:
            Size in bytes, or 0 if not found
        """
        archive_path = self.backup_dir / f"{backup_id}.tar.gz"
        if archive_path.exists():
            return archive_path.stat().st_size
        return 0

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Delete old backups, keeping only the most recent.

        Args:
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return 0

        # Delete old backups
        to_delete = backups[keep_count:]
        deleted_count = 0

        for backup in to_delete:
            if self.delete_backup(backup.backup_id):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count

    def export_backup(
        self,
        backup_id: str,
        destination: str
    ) -> bool:
        """Export a backup to external location.

        Args:
            backup_id: Backup ID to export
            destination: Destination path

        Returns:
            True if successful, False otherwise
        """
        try:
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            metadata_path = self.backup_dir / f"{backup_id}_metadata.json"

            if not archive_path.exists():
                logger.error(f"Backup not found: {backup_id}")
                return False

            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)

            # Copy archive
            shutil.copy2(archive_path, dest_path / f"{backup_id}.tar.gz")

            # Copy metadata
            if metadata_path.exists():
                shutil.copy2(metadata_path, dest_path / f"{backup_id}_metadata.json")

            logger.info(f"Backup exported to {destination}")
            return True

        except Exception as e:
            logger.exception(f"Error exporting backup: {e}")
            return False

    def import_backup(self, source_path: str) -> Optional[str]:
        """Import a backup from external location.

        Args:
            source_path: Path to backup archive

        Returns:
            Backup ID if successful, None otherwise
        """
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Source file not found: {source_path}")
                return None

            # Extract backup ID from filename
            if source.name.endswith(".tar.gz"):
                backup_id = source.stem.replace(".tar", "")
            else:
                logger.error("Invalid backup file format")
                return None

            # Copy to backup directory
            dest_archive = self.backup_dir / f"{backup_id}.tar.gz"
            shutil.copy2(source, dest_archive)

            # Look for metadata file
            source_metadata = source.parent / f"{backup_id}_metadata.json"
            if source_metadata.exists():
                dest_metadata = self.backup_dir / f"{backup_id}_metadata.json"
                shutil.copy2(source_metadata, dest_metadata)

            logger.info(f"Backup imported: {backup_id}")
            return backup_id

        except Exception as e:
            logger.exception(f"Error importing backup: {e}")
            return None

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA-256 checksum of a file.

        Args:
            filepath: Path to file

        Returns:
            Hexadecimal checksum string
        """
        sha256 = hashlib.sha256()

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

        return sha256.hexdigest()
