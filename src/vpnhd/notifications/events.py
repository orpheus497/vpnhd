"""Notification event definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any


class EventType(str, Enum):
    """Types of notification events."""

    CLIENT_CONNECTED = "client_connected"
    CLIENT_DISCONNECTED = "client_disconnected"
    CLIENT_ADDED = "client_added"
    CLIENT_REMOVED = "client_removed"
    KEY_ROTATION = "key_rotation"
    SECURITY_ALERT = "security_alert"
    BACKUP_COMPLETE = "backup_complete"
    BACKUP_FAILED = "backup_failed"
    DDNS_UPDATE = "ddns_update"
    PHASE_COMPLETE = "phase_complete"
    PHASE_FAILED = "phase_failed"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EventSeverity(str, Enum):
    """Event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NotificationEvent:
    """Notification event data."""

    event_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "vpnhd"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_type': self.event_type,
            'message': self.message,
            'details': self.details,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)

    @property
    def is_critical(self) -> bool:
        """Check if event is critical."""
        return self.severity in (EventSeverity.CRITICAL, EventSeverity.ERROR)
