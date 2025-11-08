"""Base notification channel interface."""

from abc import ABC, abstractmethod
from ...utils.logging import get_logger
from ..events import NotificationEvent

logger = get_logger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    def __init__(self, config_manager):
        """Initialize notification channel.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logger

    @abstractmethod
    async def send(self, event: NotificationEvent) -> bool:
        """Send notification via this channel.

        Args:
            event: Notification event to send

        Returns:
            bool: True if notification sent successfully
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Get channel name."""
        pass

    def should_send(self, event: NotificationEvent) -> bool:
        """Determine if notification should be sent based on config.

        Args:
            event: Notification event

        Returns:
            bool: True if should send notification
        """
        # Check if notifications are enabled
        if not self.config.get("notifications.enabled", False):
            return False

        # Check event-specific filters
        event_type = event.event_type

        if event_type == "client_connected":
            return self.config.get("notifications.notify_on_client_connect", True)
        elif event_type == "client_disconnected":
            return self.config.get("notifications.notify_on_client_disconnect", False)
        elif event_type == "security_alert":
            return self.config.get("notifications.notify_on_security_alert", True)
        elif event_type == "backup_complete":
            return self.config.get("notifications.notify_on_backup_complete", False)
        elif event_type == "key_rotation":
            return self.config.get("notifications.notify_on_key_rotation", True)
        elif event_type == "error":
            return self.config.get("notifications.notify_on_error", True)

        # Default: send all notifications
        return True
