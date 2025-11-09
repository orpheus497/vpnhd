"""Data models for multi-server management."""

import ipaddress
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ServerConnection(BaseModel):
    """SSH connection information for a VPN server."""

    host: str = Field(..., description="Server hostname or IP address")
    port: int = Field(default=22, ge=1, le=65535, description="SSH port")
    username: str = Field(default="root", description="SSH username")
    key_path: Optional[str] = Field(None, description="Path to SSH private key")
    password: Optional[str] = Field(None, description="SSH password (not recommended)")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate hostname or IP address."""
        if not v:
            raise ValueError("Host cannot be empty")

        # Try to parse as IP address
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass

        # Validate as hostname (basic check)
        if not all(c.isalnum() or c in ".-" for c in v):
            raise ValueError(f"Invalid hostname: {v}")

        return v


class ServerStatus(BaseModel):
    """Current status of a VPN server."""

    online: bool = Field(default=False, description="Server reachable via SSH")
    vpn_running: bool = Field(default=False, description="VPN service running")
    last_check: Optional[datetime] = Field(None, description="Last status check time")
    uptime: Optional[int] = Field(None, description="Server uptime in seconds")
    active_clients: int = Field(default=0, description="Number of active clients")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    disk_usage: Optional[float] = Field(None, description="Disk usage percentage")
    error_message: Optional[str] = Field(None, description="Error message if check failed")


class ServerMetrics(BaseModel):
    """Performance metrics for a VPN server."""

    total_clients: int = Field(default=0, description="Total configured clients")
    active_clients: int = Field(default=0, description="Currently active clients")
    bytes_received: int = Field(default=0, description="Total bytes received")
    bytes_transmitted: int = Field(default=0, description="Total bytes transmitted")
    bandwidth_rx: float = Field(default=0.0, description="Receive bandwidth (bytes/sec)")
    bandwidth_tx: float = Field(default=0.0, description="Transmit bandwidth (bytes/sec)")
    avg_latency: Optional[float] = Field(None, description="Average latency (ms)")
    collected_at: Optional[datetime] = Field(None, description="Metrics collection time")


class ServerProfile(BaseModel):
    """Complete profile for a managed VPN server."""

    # Identity
    name: str = Field(..., description="Unique server name/identifier")
    description: Optional[str] = Field(None, description="Server description")
    tags: List[str] = Field(default_factory=list, description="Server tags for grouping")

    # Connection
    connection: ServerConnection = Field(..., description="SSH connection details")

    # VPN Configuration
    vpn_interface: str = Field(default="wg0", description="WireGuard interface name")
    vpn_port: int = Field(default=51820, ge=1, le=65535, description="VPN listen port")
    vpn_subnet: str = Field(default="10.66.66.0/24", description="VPN IPv4 subnet")
    vpn_ipv6_subnet: Optional[str] = Field(None, description="VPN IPv6 subnet")

    # DDNS Configuration
    ddns_enabled: bool = Field(default=False, description="DDNS enabled")
    ddns_provider: Optional[str] = Field(None, description="DDNS provider")
    ddns_domain: Optional[str] = Field(None, description="DDNS domain name")

    # Status and Metrics
    status: ServerStatus = Field(default_factory=ServerStatus, description="Current server status")
    metrics: ServerMetrics = Field(default_factory=ServerMetrics, description="Server metrics")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Profile creation time")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Profile last update time"
    )
    enabled: bool = Field(default=True, description="Server enabled for management")
    is_primary: bool = Field(default=False, description="Primary server flag")

    @field_validator("vpn_subnet", "vpn_ipv6_subnet")
    @classmethod
    def validate_subnet(cls, v: Optional[str]) -> Optional[str]:
        """Validate VPN subnet."""
        if v is None:
            return v

        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid subnet: {e}")

        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate server name."""
        if not v:
            raise ValueError("Server name cannot be empty")

        # Only allow alphanumeric, hyphens, underscores
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(
                "Server name can only contain letters, numbers, hyphens, and underscores"
            )

        return v

    def update_status(self, **kwargs) -> None:
        """Update server status fields.

        Args:
            **kwargs: Status fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.status, key):
                setattr(self.status, key, value)

        self.status.last_check = datetime.now()
        self.updated_at = datetime.now()

    def update_metrics(self, **kwargs) -> None:
        """Update server metrics fields.

        Args:
            **kwargs: Metric fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)

        self.metrics.collected_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerProfile":
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            ServerProfile instance
        """
        return cls(**data)


class ServerGroup(BaseModel):
    """Logical grouping of servers."""

    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    server_names: List[str] = Field(
        default_factory=list, description="List of server names in this group"
    )
    tags: List[str] = Field(default_factory=list, description="Group tags")
    created_at: datetime = Field(default_factory=datetime.now, description="Group creation time")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate group name."""
        if not v:
            raise ValueError("Group name cannot be empty")

        if not all(c.isalnum() or c in "-_ " for c in v):
            raise ValueError(
                "Group name can only contain letters, numbers, hyphens, " "underscores, and spaces"
            )

        return v


class ServerOperation(BaseModel):
    """Record of an operation performed on a server."""

    server_name: str = Field(..., description="Target server name")
    operation: str = Field(..., description="Operation type")
    status: str = Field(..., description="Operation status (success, failure, pending)")
    message: Optional[str] = Field(None, description="Operation message")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional operation details"
    )
    started_at: datetime = Field(default_factory=datetime.now, description="Operation start time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")
    duration: Optional[float] = Field(None, description="Operation duration in seconds")

    def complete(self, status: str, message: Optional[str] = None) -> None:
        """Mark operation as complete.

        Args:
            status: Final status
            message: Optional completion message
        """
        self.status = status
        if message:
            self.message = message

        self.completed_at = datetime.now()
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()


class SyncConfiguration(BaseModel):
    """Configuration synchronization settings."""

    enabled: bool = Field(default=True, description="Sync enabled")
    sync_clients: bool = Field(default=True, description="Sync client configurations")
    sync_settings: bool = Field(default=True, description="Sync server settings")
    sync_keys: bool = Field(default=False, description="Sync WireGuard keys")
    sync_interval: int = Field(
        default=300, description="Automatic sync interval in seconds (0 = manual only)"
    )
    conflict_resolution: str = Field(
        default="newest", description="Conflict resolution strategy (newest, oldest, manual)"
    )
    excluded_servers: List[str] = Field(
        default_factory=list, description="Servers excluded from sync"
    )

    @field_validator("conflict_resolution")
    @classmethod
    def validate_conflict_resolution(cls, v: str) -> str:
        """Validate conflict resolution strategy."""
        valid_strategies = {"newest", "oldest", "manual"}
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid conflict resolution strategy: {v}. " f"Must be one of {valid_strategies}"
            )
        return v
