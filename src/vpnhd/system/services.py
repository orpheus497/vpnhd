"""Service management utilities for VPNHD."""

from typing import Optional, List
from enum import Enum

from ..utils.logging import get_logger
from .commands import execute_command, check_command_exists


class ServiceStatus(Enum):
    """Service status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ServiceManager:
    """Manages systemd services."""

    def __init__(self):
        """Initialize service manager."""
        self.logger = get_logger("ServiceManager")
        self.init_system = self._detect_init_system()

    def _detect_init_system(self) -> str:
        """
        Detect init system (systemd, sysvinit, etc.).

        Returns:
            str: Init system name
        """
        if check_command_exists("systemctl"):
            return "systemd"
        elif check_command_exists("service"):
            return "sysvinit"
        else:
            self.logger.warning("Could not detect init system")
            return "unknown"

    def start_service(self, service_name: str) -> bool:
        """
        Start a service.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service started successfully
        """
        self.logger.info(f"Starting service: {service_name}")

        if self.init_system == "systemd":
            cmd = f"systemctl start {service_name}"
        elif self.init_system == "sysvinit":
            cmd = f"service {service_name} start"
        else:
            self.logger.error(f"Unsupported init system: {self.init_system}")
            return False

        result = execute_command(cmd, sudo=True, check=False)

        if result.success:
            self.logger.info(f"Service {service_name} started successfully")
        else:
            self.logger.error(f"Failed to start service {service_name}")

        return result.success

    def stop_service(self, service_name: str) -> bool:
        """
        Stop a service.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service stopped successfully
        """
        self.logger.info(f"Stopping service: {service_name}")

        if self.init_system == "systemd":
            cmd = f"systemctl stop {service_name}"
        elif self.init_system == "sysvinit":
            cmd = f"service {service_name} stop"
        else:
            self.logger.error(f"Unsupported init system: {self.init_system}")
            return False

        result = execute_command(cmd, sudo=True, check=False)

        if result.success:
            self.logger.info(f"Service {service_name} stopped successfully")
        else:
            self.logger.error(f"Failed to stop service {service_name}")

        return result.success

    def restart_service(self, service_name: str) -> bool:
        """
        Restart a service.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service restarted successfully
        """
        self.logger.info(f"Restarting service: {service_name}")

        if self.init_system == "systemd":
            cmd = f"systemctl restart {service_name}"
        elif self.init_system == "sysvinit":
            cmd = f"service {service_name} restart"
        else:
            self.logger.error(f"Unsupported init system: {self.init_system}")
            return False

        result = execute_command(cmd, sudo=True, check=False)

        if result.success:
            self.logger.info(f"Service {service_name} restarted successfully")
        else:
            self.logger.error(f"Failed to restart service {service_name}")

        return result.success

    def reload_service(self, service_name: str) -> bool:
        """
        Reload a service configuration.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service reloaded successfully
        """
        self.logger.info(f"Reloading service: {service_name}")

        if self.init_system == "systemd":
            cmd = f"systemctl reload {service_name}"
        elif self.init_system == "sysvinit":
            cmd = f"service {service_name} reload"
        else:
            self.logger.error(f"Unsupported init system: {self.init_system}")
            return False

        result = execute_command(cmd, sudo=True, check=False)

        if result.success:
            self.logger.info(f"Service {service_name} reloaded successfully")
        else:
            self.logger.warning(f"Failed to reload service {service_name}, trying restart")
            return self.restart_service(service_name)

        return result.success

    def enable_service(self, service_name: str) -> bool:
        """
        Enable a service to start on boot.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service enabled successfully
        """
        self.logger.info(f"Enabling service: {service_name}")

        if self.init_system == "systemd":
            cmd = f"systemctl enable {service_name}"
        elif self.init_system == "sysvinit":
            cmd = f"update-rc.d {service_name} defaults"
        else:
            self.logger.error(f"Unsupported init system: {self.init_system}")
            return False

        result = execute_command(cmd, sudo=True, check=False)

        if result.success:
            self.logger.info(f"Service {service_name} enabled successfully")
        else:
            self.logger.error(f"Failed to enable service {service_name}")

        return result.success

    def disable_service(self, service_name: str) -> bool:
        """
        Disable a service from starting on boot.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service disabled successfully
        """
        self.logger.info(f"Disabling service: {service_name}")

        if self.init_system == "systemd":
            cmd = f"systemctl disable {service_name}"
        elif self.init_system == "sysvinit":
            cmd = f"update-rc.d {service_name} remove"
        else:
            self.logger.error(f"Unsupported init system: {self.init_system}")
            return False

        result = execute_command(cmd, sudo=True, check=False)

        if result.success:
            self.logger.info(f"Service {service_name} disabled successfully")
        else:
            self.logger.error(f"Failed to disable service {service_name}")

        return result.success

    def get_service_status(self, service_name: str) -> ServiceStatus:
        """
        Get the status of a service.

        Args:
            service_name: Name of the service

        Returns:
            ServiceStatus: Current status of the service
        """
        if self.init_system == "systemd":
            result = execute_command(
                f"systemctl is-active {service_name}", check=False, capture_output=True
            )

            if result.success:
                status = result.stdout.strip()
                if status == "active":
                    return ServiceStatus.ACTIVE
                elif status == "inactive":
                    return ServiceStatus.INACTIVE
                elif status == "failed":
                    return ServiceStatus.FAILED

        elif self.init_system == "sysvinit":
            result = execute_command(
                f"service {service_name} status", check=False, capture_output=True
            )

            if result.success:
                if "running" in result.stdout.lower():
                    return ServiceStatus.ACTIVE
                else:
                    return ServiceStatus.INACTIVE

        return ServiceStatus.UNKNOWN

    def is_service_active(self, service_name: str) -> bool:
        """
        Check if a service is active/running.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service is active
        """
        status = self.get_service_status(service_name)
        return status == ServiceStatus.ACTIVE

    def is_service_enabled(self, service_name: str) -> bool:
        """
        Check if a service is enabled to start on boot.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service is enabled
        """
        if self.init_system == "systemd":
            result = execute_command(
                f"systemctl is-enabled {service_name}", check=False, capture_output=True
            )
            return result.success

        return False

    def daemon_reload(self) -> bool:
        """
        Reload systemd daemon configuration.

        Returns:
            bool: True if reload succeeded
        """
        if self.init_system == "systemd":
            self.logger.info("Reloading systemd daemon")
            result = execute_command("systemctl daemon-reload", sudo=True, check=False)
            return result.success

        return True  # Not needed for other init systems

    def list_services(self, pattern: Optional[str] = None) -> List[str]:
        """
        List services.

        Args:
            pattern: Optional pattern to filter services

        Returns:
            List[str]: List of service names
        """
        if self.init_system == "systemd":
            cmd = "systemctl list-units --type=service --all --no-pager --plain"
            if pattern:
                cmd += f" | grep {pattern}"

            result = execute_command(cmd, check=False, capture_output=True)

            if result.success:
                services = []
                for line in result.stdout.split("\n"):
                    if line.strip() and not line.startswith("UNIT"):
                        parts = line.split()
                        if parts:
                            service_name = parts[0]
                            if service_name.endswith(".service"):
                                services.append(service_name)
                return services

        return []

    def get_service_logs(self, service_name: str, lines: int = 50) -> Optional[str]:
        """
        Get recent logs for a service.

        Args:
            service_name: Name of the service
            lines: Number of log lines to retrieve

        Returns:
            Optional[str]: Log output or None if failed
        """
        if self.init_system == "systemd":
            result = execute_command(
                f"journalctl -u {service_name} -n {lines} --no-pager",
                sudo=True,
                check=False,
                capture_output=True,
            )

            if result.success:
                return result.stdout

        return None
