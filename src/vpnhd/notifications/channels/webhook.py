"""Webhook notification channel."""

import httpx
from typing import Dict, Any
from .base import NotificationChannel
from ..events import NotificationEvent
from ...utils.logging import get_logger

logger = get_logger(__name__)


class WebhookChannel(NotificationChannel):
    """Webhook notification channel using HTTP POST."""

    @property
    def channel_name(self) -> str:
        return "webhook"

    async def send(self, event: NotificationEvent) -> bool:
        """Send notification via webhook.

        Args:
            event: Notification event to send

        Returns:
            bool: True if all webhooks succeeded
        """
        if not self.should_send(event):
            return True

        webhook_urls = self.config.get("notifications.webhook_urls", [])
        if not webhook_urls:
            self.logger.warning("No webhook URLs configured")
            return False

        custom_headers = self.config.get("notifications.webhook_headers", {})

        all_succeeded = True

        async with httpx.AsyncClient(timeout=10) as client:
            for url in webhook_urls:
                try:
                    # Prepare payload
                    payload = self._prepare_payload(event)

                    # Prepare headers
                    headers = {
                        'Content-Type': 'application/json',
                        'User-Agent': 'VPNHD/2.0.0',
                        **custom_headers
                    }

                    # Send POST request
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers
                    )

                    if response.status_code < 200 or response.status_code >= 300:
                        self.logger.error(
                            f"Webhook failed: {url} returned {response.status_code}"
                        )
                        all_succeeded = False
                    else:
                        self.logger.info(f"Webhook notification sent to {url}")

                except Exception as e:
                    self.logger.exception(f"Error sending webhook to {url}: {e}")
                    all_succeeded = False

        return all_succeeded

    def _prepare_payload(self, event: NotificationEvent) -> Dict[str, Any]:
        """Prepare webhook payload.

        Args:
            event: Notification event

        Returns:
            Dict containing payload data
        """
        return {
            'event_type': event.event_type,
            'severity': event.severity,
            'message': event.message,
            'details': event.details,
            'timestamp': event.timestamp.isoformat(),
            'source': 'VPNHD',
            'version': '2.0.0'
        }
