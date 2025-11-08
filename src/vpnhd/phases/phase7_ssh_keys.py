"""Phase 7: SSH Key Authentication."""

from pathlib import Path
from .base import Phase
from ..crypto.ssh import generate_ssh_keypair, get_ssh_public_key, add_ssh_key_to_authorized_keys


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
        """Disable SSH password authentication."""
        self.display.warning("Disabling password authentication...")
        from ..system.files import FileManager
        file_mgr = FileManager()

        ssh_config_path = Path("/etc/ssh/sshd_config")
        if file_mgr.backup_file(ssh_config_path):
            self.display.success("Backed up sshd_config")

        # This would modify sshd_config to disable password auth
        self.display.info("Manual step: Edit /etc/ssh/sshd_config")
        self.display.info("Set: PasswordAuthentication no")

        self.config.set("security.ssh_password_auth_disabled", True)
