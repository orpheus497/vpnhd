"""Configuration manager for VPNHD."""

from pathlib import Path
from typing import Any, Optional, Dict, List
import shutil

from ..utils.constants import CONFIG_FILE, BACKUP_DIR
from ..utils.helpers import (
    ensure_directory_exists,
    read_json_file,
    write_json_file,
    get_timestamp,
    get_timestamp_filename,
    get_nested_value,
    set_nested_value
)
from ..utils.logging import get_logger
from .schema import get_default_config
from .validator import ConfigValidator


class ConfigManager:
    """Manages application configuration state."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file (default: ~/.config/vpnhd/config.json)
        """
        self.config_path = config_path or CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self.logger = get_logger("ConfigManager")
        self.validator = ConfigValidator()

        # Ensure config directory exists
        ensure_directory_exists(self.config_path.parent)
        ensure_directory_exists(BACKUP_DIR)

    def load(self) -> bool:
        """
        Load configuration from file.

        Returns:
            bool: True if loaded successfully
        """
        try:
            if not self.config_path.exists():
                self.logger.info("Configuration file not found, creating default configuration")
                self.config = get_default_config()
                return self.save()

            data = read_json_file(self.config_path)
            if data is None:
                self.logger.error("Failed to read configuration file")
                return False

            self.config = data
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            bool: True if saved successfully
        """
        try:
            # Update last modified timestamp
            self.config['last_modified'] = get_timestamp()

            # Write to file
            if write_json_file(self.config_path, self.config):
                self.logger.info(f"Configuration saved to {self.config_path}")
                return True
            else:
                self.logger.error("Failed to write configuration file")
                return False

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Dot-notation key (e.g., "network.lan.router_ip")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return get_nested_value(self.config, key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.

        Args:
            key: Dot-notation key (e.g., "network.lan.router_ip")
            value: Value to set
        """
        set_nested_value(self.config, key, value)

    def mark_phase_complete(self, phase_number: int, notes: str = "") -> None:
        """
        Mark a phase as completed.

        Args:
            phase_number: Phase number (1-8)
            notes: Optional notes about completion
        """
        if not self.validator.validate_phase_number(phase_number):
            self.logger.error(f"Invalid phase number: {phase_number}")
            return

        from ..utils.constants import PHASE_KEYS

        phase_key = PHASE_KEYS.get(phase_number)
        if not phase_key:
            return

        phase_path = f"phases.{phase_key}"
        self.set(f"{phase_path}.completed", True)
        self.set(f"{phase_path}.date_completed", get_timestamp())
        if notes:
            self.set(f"{phase_path}.notes", notes)

        self.logger.info(f"Phase {phase_number} marked as complete")

    def is_phase_complete(self, phase_number: int) -> bool:
        """
        Check if a phase is completed.

        Args:
            phase_number: Phase number (1-8)

        Returns:
            bool: True if phase is completed
        """
        if not self.validator.validate_phase_number(phase_number):
            return False

        from ..utils.constants import PHASE_KEYS

        phase_key = PHASE_KEYS.get(phase_number)
        if not phase_key:
            return False

        return self.get(f"phases.{phase_key}.completed", False)

    def get_next_phase(self) -> int:
        """
        Get the next incomplete phase number.

        Returns:
            int: Next phase number (1-8), or 0 if all complete
        """
        for phase_num in range(1, 9):
            if not self.is_phase_complete(phase_num):
                return phase_num
        return 0  # All phases complete

    def get_completion_percentage(self) -> float:
        """
        Get overall completion percentage.

        Returns:
            float: Completion percentage (0-100)
        """
        completed = sum(1 for i in range(1, 9) if self.is_phase_complete(i))
        return (completed / 8) * 100

    def validate(self) -> bool:
        """
        Validate configuration against schema.

        Returns:
            bool: True if valid
        """
        valid, errors = self.validator.validate_full_config(self.config)

        if not valid:
            self.logger.error("Configuration validation failed:")
            for error in errors:
                self.logger.error(f"  - {error}")

        return valid

    def backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Create backup of current configuration.

        Args:
            backup_name: Optional backup filename (default: timestamped)

        Returns:
            Optional[Path]: Path to backup file or None if failed
        """
        try:
            if not self.config_path.exists():
                self.logger.warning("No configuration file to backup")
                return None

            # Generate backup filename
            if backup_name:
                backup_file = BACKUP_DIR / backup_name
            else:
                timestamp = get_timestamp_filename()
                backup_file = BACKUP_DIR / f"config_backup_{timestamp}.json"

            # Copy current config to backup
            shutil.copy2(self.config_path, backup_file)

            self.logger.info(f"Configuration backed up to {backup_file}")
            return backup_file

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None

    def restore(self, backup_path: Path) -> bool:
        """
        Restore configuration from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if restored successfully
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            # Backup current config before restoring
            self.backup("pre_restore_backup.json")

            # Copy backup to config location
            shutil.copy2(backup_path, self.config_path)

            # Reload configuration
            success = self.load()

            if success:
                self.logger.info(f"Configuration restored from {backup_path}")
            else:
                self.logger.error("Failed to load restored configuration")

            return success

        except Exception as e:
            self.logger.error(f"Error restoring configuration: {e}")
            return False

    def reset(self) -> bool:
        """
        Reset configuration to default values.

        Returns:
            bool: True if reset successfully
        """
        try:
            # Backup current config
            self.backup("pre_reset_backup.json")

            # Load default configuration
            self.config = get_default_config()

            # Save to file
            success = self.save()

            if success:
                self.logger.info("Configuration reset to defaults")

            return success

        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False

    def export_config(self, export_path: Path) -> bool:
        """
        Export configuration to a file.

        Args:
            export_path: Path to export file

        Returns:
            bool: True if exported successfully
        """
        try:
            if write_json_file(export_path, self.config):
                self.logger.info(f"Configuration exported to {export_path}")
                return True
            else:
                self.logger.error("Failed to export configuration")
                return False

        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False

    def import_config(self, import_path: Path) -> bool:
        """
        Import configuration from a file.

        Args:
            import_path: Path to import file

        Returns:
            bool: True if imported successfully
        """
        try:
            data = read_json_file(import_path)
            if data is None:
                self.logger.error("Failed to read import file")
                return False

            # Validate imported config
            validator = ConfigValidator()
            valid, errors = validator.validate_full_config(data)

            if not valid:
                self.logger.error("Imported configuration is invalid:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return False

            # Backup current config
            self.backup("pre_import_backup.json")

            # Load imported config
            self.config = data

            # Save to file
            success = self.save()

            if success:
                self.logger.info(f"Configuration imported from {import_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False

    def get_phase_info(self, phase_number: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific phase.

        Args:
            phase_number: Phase number (1-8)

        Returns:
            Optional[Dict[str, Any]]: Phase information or None if invalid
        """
        if not self.validator.validate_phase_number(phase_number):
            return None

        from ..utils.constants import PHASE_KEYS, PHASE_NAMES

        phase_key = PHASE_KEYS.get(phase_number)
        if not phase_key:
            return None

        phase_data = self.get(f"phases.{phase_key}", {})

        return {
            "number": phase_number,
            "name": PHASE_NAMES.get(phase_number),
            "key": phase_key,
            "completed": phase_data.get("completed", False),
            "date_completed": phase_data.get("date_completed"),
            "notes": phase_data.get("notes", ""),
            **phase_data
        }

    def get_all_phases_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all phases.

        Returns:
            List[Dict[str, Any]]: List of phase information dictionaries
        """
        return [self.get_phase_info(i) for i in range(1, 9) if self.get_phase_info(i)]

    def __repr__(self) -> str:
        """String representation of ConfigManager."""
        return f"ConfigManager(config_path={self.config_path}, phases_complete={sum(1 for i in range(1, 9) if self.is_phase_complete(i))}/8)"
