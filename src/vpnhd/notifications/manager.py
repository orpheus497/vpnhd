"""Notification manager for alerts and events."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..utils.logging import get_logger
from ..config.manager import ConfigManager
from .channels.base import NotificationChannel
from .channels.email import EmailChannel
from .channels.webhook import WebhookChannel
from .events import NotificationEvent, EventType

logger = get_logger(__name__)


class NotificationManager:
    """Manage notifications across multiple channels."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize notification manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.channels: List[NotificationChannel] = []
        self._initialize_channels()

    def _initialize_channels(self):
        """Initialize enabled notification channels."""
        notification_config = self.config.get("notifications", {})

        if not notification_config.get("enabled", False):
            logger.info("Notifications disabled")
            return

        # Email channel
        if notification_config.get("email_enabled", False):
            email_channel = EmailChannel(self.config)
            self.channels.append(email_channel)
            logger.info("Email notifications enabled")

        # Webhook channel
        if notification_config.get("webhook_enabled", False):
            webhook_channel = WebhookChannel(self.config)
            self.channels.append(webhook_channel)
            logger.info("Webhook notifications enabled")

    async def send_notification(
        self,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ):
        """Send notification to all enabled channels.

        Args:
            event_type: Type of event (e.g., 'client_connected', 'key_rotation')
            message: Human-readable message
            details: Additional event details
            severity: Severity level ('info', 'warning', 'error', 'critical')
        """
        if not self.channels:
            logger.debug(f"No notification channels, skipping: {message}")
            return

        event = NotificationEvent(
            event_type=event_type,
            message=message,
            details=details or {},
            severity=severity,
            timestamp=datetime.now(),
        )

        logger.info(f"Sending notification: {event_type} - {message}")

        # Send to all channels concurrently
        tasks = [channel.send(event) for channel in self.channels]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Notification failed on channel {i}: {result}")

    async def send_client_connected(self, client_name: str, ip: str):
        """Send client connected notification.

        Args:
            client_name: Name of connected client
            ip: Client IP address
        """
        await self.send_notification(
            event_type=EventType.CLIENT_CONNECTED,
            message=f"Client '{client_name}' connected from {ip}",
            details={"client": client_name, "ip": ip},
            severity="info",
        )

    async def send_client_disconnected(self, client_name: str):
        """Send client disconnected notification.

        Args:
            client_name: Name of disconnected client
        """
        await self.send_notification(
            event_type=EventType.CLIENT_DISCONNECTED,
            message=f"Client '{client_name}' disconnected",
            details={"client": client_name},
            severity="info",
        )

    async def send_security_alert(self, alert_type: str, details: Dict[str, Any]):
        """Send security alert notification.

        Args:
            alert_type: Type of security alert
            details: Alert details
        """
        await self.send_notification(
            event_type=EventType.SECURITY_ALERT,
            message=f"Security alert: {alert_type}",
            details=details,
            severity="critical",
        )

    async def send_backup_complete(self, backup_id: str, size_kb: float):
        """Send backup completion notification.

        Args:
            backup_id: Backup identifier
            size_kb: Backup size in kilobytes
        """
        await self.send_notification(
            event_type=EventType.BACKUP_COMPLETE,
            message=f"Backup completed: {backup_id} ({size_kb:.2f} KB)",
            details={"backup_id": backup_id, "size_kb": size_kb},
            severity="info",
        )

    async def send_error(self, component: str, error_message: str):
        """Send error notification.

        Args:
            component: Component where error occurred
            error_message: Error message
        """
        await self.send_notification(
            event_type=EventType.ERROR,
            message=f"Error in {component}: {error_message}",
            details={"component": component, "error": error_message},
            severity="error",
        )

    async def send_key_rotation(
        self, key_type: str, success: bool, details: Optional[Dict[str, Any]] = None
    ):
        """Send key rotation notification.

        Args:
            key_type: Type of key rotated (wireguard, ssh)
            success: Whether rotation succeeded
            details: Additional details
        """
        severity = "info" if success else "error"
        status = "succeeded" if success else "failed"

        await self.send_notification(
            event_type=EventType.KEY_ROTATION,
            message=f"{key_type.upper()} key rotation {status}",
            details=details or {},
            severity=severity,
        )

    async def send_ddns_update(self, new_ip: str, new_ipv6: Optional[str] = None):
        """Send DDNS update notification.

        Args:
            new_ip: New IPv4 address
            new_ipv6: New IPv6 address (optional)
        """
        details = {"ipv4": new_ip}
        if new_ipv6:
            details["ipv6"] = new_ipv6

        await self.send_notification(
            event_type=EventType.DDNS_UPDATE,
            message=f"DNS updated - IP: {new_ip}" + (f", IPv6: {new_ipv6}" if new_ipv6 else ""),
            details=details,
            severity="info",
        )

    async def send_phase_complete(self, phase_number: int, phase_name: str):
        """Send phase completion notification.

        Args:
            phase_number: Phase number
            phase_name: Phase name
        """
        await self.send_notification(
            event_type=EventType.PHASE_COMPLETE,
            message=f"Phase {phase_number} ({phase_name}) completed successfully",
            details={"phase": phase_number, "name": phase_name},
            severity="info",
        )
