"""Phase 7: SSH Key Authentication."""

from pathlib import Path
from .base import Phase
from ..crypto.ssh import (
    generate_ssh_keypair,
    get_ssh_public_key,
    add_ssh_key_to_authorized_keys,
    test_ssh_key_auth,
)
from ..system.ssh_config import SSHConfigManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class Phase7SSHKeys(Phase):
    """Phase 7: SSH Key Authentication Setup."""

    @property
    def name(self) -> str:
        return "SSH Key Authentication"

    @property
    def number(self) -> int:
        return 7

    @property
    def description(self) -> str:
        return "Set up SSH key-based authentication and disable password login."

    @property
    def long_description(self) -> str:
        return """SSH keys are like a super secure password that can't be guessed.
        They use cryptography to prove who you are without typing a password."""

    def check_prerequisites(self) -> bool:
        return self.config.is_phase_complete(1)

    def execute(self) -> bool:
        try:
            self.show_introduction()

            # SSH key path
            ssh_key_path = Path.home() / ".ssh" / "id_ed25519"

            # Check if key exists
            if not ssh_key_path.exists():
                if self.prompts.confirm("Generate new SSH key?", default=True):
                    self.display.info("Generating SSH keypair...")
                    generate_ssh_keypair(ssh_key_path, key_type="ed25519")
                    self.display.success("SSH key generated")

            # Get public key
            public_key = get_ssh_public_key(ssh_key_path)
            if not public_key:
                raise Exception("Could not read SSH public key")

            self.display.heading("SSH Public Key")
            self.display.code_block(public_key, "text")

            # Add to authorized_keys
            if self.prompts.confirm("Add key to local authorized_keys?", default=True):
                add_ssh_key_to_authorized_keys(public_key)
                self.display.success("Key added to authorized_keys")

            self.config.set("phases.phase7_ssh_keys.ssh_key_path", str(ssh_key_path))
            self.config.set("security.ssh_key_auth_enabled", True)

            # Disable password authentication
            if self.prompts.confirm("Disable SSH password authentication?", default=False):
                self._disable_password_auth()

            self.mark_complete("SSH keys configured")
            self.config.save()
            return True

        except Exception as e:
            self.mark_failed(str(e))
            return False

    def _disable_password_auth(self) -> None:
        """Disable SSH password authentication programmatically."""
        self.display.warning("Disabling password authentication...")

        ssh_config_mgr = SSHConfigManager()

        # Create backup
        backup_path = ssh_config_mgr.backup_ssh_config()
        if backup_path:
            self.display.success(f"Backed up sshd_config to {backup_path}")
            self.config.set("phases.phase7_ssh_keys.sshd_config_backup", backup_path)
        else:
            self.display.error("Failed to backup sshd_config")
            if not self.prompts.confirm("Continue without backup?", default=False):
                return

        # Disable password authentication
        if ssh_config_mgr.disable_password_auth():
            self.display.success("SSH password authentication disabled successfully")
            self.config.set("security.ssh_password_auth_disabled", True)
        else:
            self.display.error("Failed to disable password authentication")
            self.display.info("You may need to manually edit /etc/ssh/sshd_config")
            self.display.info("Set: PasswordAuthentication no")

    def verify(self) -> bool:
        """Verify that SSH keys are properly configured."""
        ssh_key_path = Path(
            self.config.get("phases.phase7_ssh_keys.ssh_key_path", "~/.ssh/id_ed25519")
        )
        ssh_key_path = ssh_key_path.expanduser()
        return ssh_key_path.exists()

    def rollback(self) -> bool:
        """Rollback SSH key configuration changes."""
        try:
            # Restore sshd_config if backup exists
            backup_path = self.config.get("phases.phase7_ssh_keys.sshd_config_backup")
            if backup_path:
                ssh_config_mgr = SSHConfigManager()
                if ssh_config_mgr.restore_ssh_config(backup_path):
                    logger.info("Restored sshd_config from backup")
                else:
                    logger.error("Failed to restore sshd_config")
                    return False

            self.config.set("security.ssh_password_auth_disabled", False)
            self.config.save()
            return True
        except Exception as e:
            logger.exception(f"Error during rollback: {e}")
            return False
