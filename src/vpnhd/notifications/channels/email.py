"""Email notification channel."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from .base import NotificationChannel
from ..events import NotificationEvent
from ...utils.logging import get_logger

logger = get_logger(__name__)


class EmailChannel(NotificationChannel):
    """Email notification channel using SMTP."""

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(self, event: NotificationEvent) -> bool:
        """Send notification via email.

        Args:
            event: Notification event to send

        Returns:
            bool: True if email sent successfully
        """
        if not self.should_send(event):
            return True

        # Get SMTP configuration
        smtp_host = self.config.get("notifications.smtp_host")
        smtp_port = self.config.get("notifications.smtp_port", 587)
        smtp_username = self.config.get("notifications.smtp_username")
        smtp_password = self.config.get("notifications.smtp_password")
        smtp_use_tls = self.config.get("notifications.smtp_use_tls", True)
        email_to = self.config.get("notifications.email_to", [])
        email_from = self.config.get("notifications.email_from", smtp_username)

        if not all([smtp_host, smtp_username, smtp_password, email_to]):
            self.logger.warning("Email configuration incomplete, skipping notification")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._create_subject(event)
            msg['From'] = email_from
            msg['To'] = ', '.join(email_to)

            # Create email body
            text_body = self._format_text_body(event)
            html_body = self._format_html_body(event)

            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(email_from, email_to, msg.as_string())

            self.logger.info(f"Email notification sent to {len(email_to)} recipients")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to send email notification: {e}")
            return False

    def _create_subject(self, event: NotificationEvent) -> str:
        """Create email subject line.

        Args:
            event: Notification event

        Returns:
            str: Email subject
        """
        severity_prefix = {
            'debug': '[DEBUG]',
            'info': '[INFO]',
            'warning': '[WARNING]',
            'error': '[ERROR]',
            'critical': '[CRITICAL]'
        }
        prefix = severity_prefix.get(event.severity, '[INFO]')
        return f"[VPNHD] {prefix} {event.event_type.replace('_', ' ').title()}"

    def _format_text_body(self, event: NotificationEvent) -> str:
        """Format plain text email body.

        Args:
            event: Notification event

        Returns:
            str: Plain text email body
        """
        body = f"""
VPNHD Notification
==================

Event Type: {event.event_type}
Severity: {event.severity.upper()}
Timestamp: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{event.message}

"""
        if event.details:
            body += "Details:\n"
            for key, value in event.details.items():
                body += f"  {key}: {value}\n"

        body += """
---
This is an automated notification from VPNHD.
To configure notifications, use: vpnhd config notifications
"""
        return body

    def _format_html_body(self, event: NotificationEvent) -> str:
        """Format HTML email body.

        Args:
            event: Notification event

        Returns:
            str: HTML email body
        """
        severity_colors = {
            'debug': '#9E9E9E',
            'info': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'critical': '#9C27B0'
        }
        color = severity_colors.get(event.severity, '#2196F3')

        html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .header h2 {{ margin: 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .details {{ background-color: white; padding: 15px; margin-top: 15px; border-left: 4px solid {color}; }}
        .details table {{ width: 100%; border-collapse: collapse; }}
        .details td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .details td:first-child {{ font-weight: bold; width: 30%; }}
        .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 5px 5px; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; background-color: {color}; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>VPNHD Notification</h2>
            <p><span class="badge">{event.severity.upper()}</span> {event.event_type.replace('_', ' ').title()}</p>
        </div>
        <div class="content">
            <p><strong>Timestamp:</strong> {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Message:</strong></p>
            <p>{event.message}</p>
"""

        if event.details:
            html += """
            <div class="details">
                <strong>Details:</strong>
                <table>
"""
            for key, value in event.details.items():
                html += f"<tr><td>{key}:</td><td>{value}</td></tr>\n"

            html += """
                </table>
            </div>
"""

        html += """
        </div>
        <div class="footer">
            <p>This is an automated notification from VPNHD v2.0.0</p>
            <p>To configure notifications, use: <code>vpnhd config notifications</code></p>
        </div>
    </div>
</body>
</html>
"""
        return html
