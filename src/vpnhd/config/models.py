"""Pydantic models for configuration validation.

This module replaces the old jsonschema-based validation with Pydantic v2,
providing type-safe configuration management with better IDE support.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
import ipaddress


class NetworkLANConfig(BaseModel):
    """LAN network configuration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    subnet: str = Field(..., description="LAN subnet in CIDR notation")
    gateway: str = Field(..., description="Default gateway IP")
    server_ip: str = Field(..., description="Server IP address")

    @field_validator('subnet', 'gateway', 'server_ip')
    @classmethod
    def validate_ip(cls, v: str, info) -> str:
        """Validate IP addresses and CIDR notation."""
        if info.field_name == 'subnet':
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid subnet: {e}")
        else:
            try:
                ipaddress.ip_address(v)
            except ValueError as e:
                raise ValueError(f"Invalid IP address: {e}")
        return v


class NetworkVPNConfig(BaseModel):
    """VPN network configuration."""

    subnet: str = Field(default="10.66.66.0/24", description="VPN subnet")
    server_ip: str = Field(default="10.66.66.1", description="VPN server IP")
    port: int = Field(default=51820, ge=1, le=65535, description="WireGuard port")
    ipv6_enabled: bool = Field(default=False, description="Enable IPv6")
    ipv6_subnet: Optional[str] = Field(None, description="IPv6 subnet")
    ipv6_server_ip: Optional[str] = Field(None, description="IPv6 server IP")

    @field_validator('subnet', 'ipv6_subnet')
    @classmethod
    def validate_subnet(cls, v: Optional[str]) -> Optional[str]:
        """Validate subnet CIDR notation."""
        if v is None:
            return v
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid subnet: {e}")
        return v

    @field_validator('server_ip', 'ipv6_server_ip')
    @classmethod
    def validate_ip(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP addresses."""
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {e}")
        return v


class ServerConfig(BaseModel):
    """Server configuration."""

    hostname: str = Field(..., min_length=1, max_length=253)
    public_ip: str = Field(..., description="Public IPv4 address")
    public_ipv6: Optional[str] = Field(None, description="Public IPv6 address")
    mac_address: str = Field(..., pattern=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    os_version: str
    ddns_enabled: bool = Field(default=False)
    ddns_provider: Optional[str] = Field(None, description="DDNS provider name")
    ddns_domain: Optional[str] = Field(None, description="DDNS domain")
    ddns_api_token: Optional[str] = Field(None, description="DDNS API token")
    ddns_zone_id: Optional[str] = Field(None, description="Cloudflare zone ID")

    @field_validator('public_ip', 'public_ipv6')
    @classmethod
    def validate_public_ip(cls, v: Optional[str]) -> Optional[str]:
        """Validate public IP addresses."""
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
        except ValueError as e:
            raise ValueError(f"Invalid public IP: {e}")
        return v


class PhaseConfig(BaseModel):
    """Phase completion tracking."""

    completed: bool = Field(default=False)
    date_completed: Optional[datetime] = None
    notes: str = Field(default="")
    rollback_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('date_completed', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from string if needed."""
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""

    ssh_enabled: bool = Field(default=False)
    firewall_enabled: bool = Field(default=False)
    fail2ban_enabled: bool = Field(default=False)
    key_rotation_enabled: bool = Field(default=False)
    key_rotation_interval_days: int = Field(default=90, ge=30, le=365)
    audit_logging_enabled: bool = Field(default=True)
    rate_limiting_enabled: bool = Field(default=True)
    totp_enabled: bool = Field(default=False)
    config_encryption_enabled: bool = Field(default=False)


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    metrics_enabled: bool = Field(default=False)
    metrics_port: int = Field(default=9100, ge=1024, le=65535)
    realtime_monitoring_enabled: bool = Field(default=False)
    traffic_analysis_enabled: bool = Field(default=False)
    performance_testing_enabled: bool = Field(default=True)


class NotificationConfig(BaseModel):
    """Notification configuration."""

    enabled: bool = Field(default=False)

    # Email notifications
    email_enabled: bool = Field(default=False)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None  # Should be encrypted
    smtp_use_tls: bool = Field(default=True)
    email_to: List[str] = Field(default_factory=list)
    email_from: Optional[str] = None

    # Webhook notifications
    webhook_enabled: bool = Field(default=False)
    webhook_urls: List[str] = Field(default_factory=list)
    webhook_headers: Dict[str, str] = Field(default_factory=dict)

    # Event filters
    notify_on_client_connect: bool = Field(default=True)
    notify_on_client_disconnect: bool = Field(default=False)
    notify_on_security_alert: bool = Field(default=True)
    notify_on_backup_complete: bool = Field(default=False)
    notify_on_key_rotation: bool = Field(default=True)
    notify_on_error: bool = Field(default=True)


class VPNHDConfig(BaseModel):
    """Main VPNHD configuration model."""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            Path: lambda v: str(v) if v else None,
        }
    )

    version: str = Field(default="2.0.0")
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)

    # Network configuration
    network: Dict[str, Any] = Field(default_factory=dict)

    # Server configuration
    server: ServerConfig

    # Phase tracking
    phases: Dict[str, PhaseConfig] = Field(default_factory=dict)

    # Client configurations
    clients: Dict[str, Any] = Field(default_factory=dict)

    # Feature configurations
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format X.Y.Z")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be numeric")
        return v

    @field_validator('created_at', 'last_modified', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from string if needed."""
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    def update_last_modified(self) -> None:
        """Update last modified timestamp."""
        self.last_modified = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VPNHDConfig':
        """Create from dictionary."""
        return cls(**data)


class VPNHDSettings(BaseSettings):
    """Environment-based settings for VPNHD.

    These can be overridden via environment variables with VPNHD_ prefix.
    """

    model_config = ConfigDict(env_prefix='VPNHD_')

    config_dir: Path = Field(default=Path.home() / ".config" / "vpnhd")
    config_file: str = Field(default="config.json")
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="text")  # "text" or "json"
    debug: bool = Field(default=False)
    metrics_enabled: bool = Field(default=False)
    metrics_port: int = Field(default=9100)

    @property
    def config_path(self) -> Path:
        """Get full config file path."""
        return self.config_dir / self.config_file
