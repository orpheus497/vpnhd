"""Event type definitions for the event bus."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EventType(Enum):
    """Types of events that can be emitted."""

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Phase events
    PHASE_STARTED = "phase.started"
    PHASE_COMPLETED = "phase.completed"
    PHASE_FAILED = "phase.failed"

    # Network events
    IP_CHANGED = "network.ip_changed"
    INTERFACE_UP = "network.interface_up"
    INTERFACE_DOWN = "network.interface_down"

    # Client events
    CLIENT_ADDED = "client.added"
    CLIENT_REMOVED = "client.removed"
    CLIENT_CONNECTED = "client.connected"
    CLIENT_DISCONNECTED = "client.disconnected"
    CLIENT_ENABLED = "client.enabled"
    CLIENT_DISABLED = "client.disabled"

    # Security events
    KEY_ROTATION_STARTED = "security.key_rotation_started"
    KEY_ROTATION_COMPLETED = "security.key_rotation_completed"
    KEY_ROTATION_FAILED = "security.key_rotation_failed"

    # Monitoring events
    METRIC_THRESHOLD_EXCEEDED = "monitoring.threshold_exceeded"
    HEALTH_CHECK_FAILED = "monitoring.health_check_failed"
    PERFORMANCE_DEGRADED = "monitoring.performance_degraded"

    # DDNS events
    DDNS_UPDATE_STARTED = "ddns.update_started"
    DDNS_UPDATE_COMPLETED = "ddns.update_completed"
    DDNS_UPDATE_FAILED = "ddns.update_failed"


@dataclass
class Event:
    """Base event class."""

    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: Optional[str] = None

    def __post_init__(self):
        """Ensure timestamp is set."""
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class SystemEvent(Event):
    """System-level events."""

    def __init__(self, event_type: EventType, data: Dict[str, Any], source: str = "system"):
        super().__init__(event_type=event_type, timestamp=datetime.now(), data=data, source=source)


@dataclass
class PhaseEvent(Event):
    """Phase execution events."""

    phase_number: int
    phase_name: str

    def __init__(
        self,
        event_type: EventType,
        phase_number: int,
        phase_name: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            source=f"phase_{phase_number}",
        )
        self.phase_number = phase_number
        self.phase_name = phase_name


@dataclass
class ClientEvent(Event):
    """Client-related events."""

    client_name: str

    def __init__(
        self, event_type: EventType, client_name: str, data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            event_type=event_type, timestamp=datetime.now(), data=data or {}, source="client_manager"
        )
        self.client_name = client_name


@dataclass
class IPChangeEvent(Event):
    """IP address change events."""

    old_ip: Optional[str]
    new_ip: str
    ip_version: int  # 4 or 6

    def __init__(
        self, old_ip: Optional[str], new_ip: str, ip_version: int, data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            event_type=EventType.IP_CHANGED,
            timestamp=datetime.now(),
            data=data or {},
            source="ip_detector",
        )
        self.old_ip = old_ip
        self.new_ip = new_ip
        self.ip_version = ip_version


@dataclass
class KeyRotationEvent(Event):
    """Key rotation events."""

    key_type: str  # "wireguard" or "ssh"

    def __init__(self, event_type: EventType, key_type: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(
            event_type=event_type, timestamp=datetime.now(), data=data or {}, source="key_rotation"
        )
        self.key_type = key_type


@dataclass
class MonitoringEvent(Event):
    """Monitoring and metrics events."""

    metric_name: str
    value: float
    threshold: Optional[float] = None

    def __init__(
        self,
        event_type: EventType,
        metric_name: str,
        value: float,
        threshold: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            source="monitoring",
        )
        self.metric_name = metric_name
        self.value = value
        self.threshold = threshold
