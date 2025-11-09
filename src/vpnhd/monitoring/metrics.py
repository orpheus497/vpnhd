"""Prometheus metrics definitions for VPNHD."""

from typing import Any, Dict

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
)

# =============================================================================
# Server Metrics
# =============================================================================

# VPN server information
vpn_server_info = Info(
    "vpnhd_server", "VPN server information", ["version", "provider", "interface", "hostname"]
)

# VPN server uptime in seconds
vpn_server_uptime_seconds = Gauge("vpnhd_server_uptime_seconds", "VPN server uptime in seconds")

# VPN server status (0=down, 1=up)
vpn_server_status = Gauge("vpnhd_server_status", "VPN server status (0=down, 1=up)", ["interface"])

# =============================================================================
# Client Metrics
# =============================================================================

# Number of active VPN clients
vpn_clients_active = Gauge("vpnhd_clients_active", "Number of active VPN clients")

# Total VPN clients configured
vpn_clients_total = Gauge("vpnhd_clients_total", "Total number of configured VPN clients")

# Client connection/disconnection events
vpn_client_connections_total = Counter(
    "vpnhd_client_connections_total",
    "Total number of client connection events",
    ["client_name", "event_type"],  # event_type: connected, disconnected
)

# Client information
vpn_client_info = Info(
    "vpnhd_client", "VPN client information", ["client_name", "internal_ip", "allowed_ips"]
)

# =============================================================================
# Network Traffic Metrics
# =============================================================================

# Total bytes received from clients
vpn_traffic_received_bytes_total = Counter(
    "vpnhd_traffic_received_bytes_total",
    "Total bytes received from VPN clients",
    ["client_name", "interface"],
)

# Total bytes transmitted to clients
vpn_traffic_transmitted_bytes_total = Counter(
    "vpnhd_traffic_transmitted_bytes_total",
    "Total bytes transmitted to VPN clients",
    ["client_name", "interface"],
)

# Current bandwidth usage (bytes/sec)
vpn_bandwidth_bytes_per_second = Gauge(
    "vpnhd_bandwidth_bytes_per_second",
    "Current bandwidth usage in bytes per second",
    ["client_name", "interface", "direction"],  # direction: rx, tx
)

# Network latency in milliseconds
vpn_latency_milliseconds = Histogram(
    "vpnhd_latency_milliseconds",
    "VPN network latency in milliseconds",
    ["client_name"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
)

# Packet loss percentage
vpn_packet_loss_ratio = Gauge(
    "vpnhd_packet_loss_ratio", "Packet loss ratio (0-1)", ["client_name", "interface"]
)

# =============================================================================
# WireGuard-Specific Metrics
# =============================================================================

# WireGuard handshake timestamp (Unix time)
wireguard_handshake_timestamp_seconds = Gauge(
    "vpnhd_wireguard_handshake_timestamp_seconds",
    "Last successful WireGuard handshake timestamp",
    ["client_name", "public_key"],
)

# WireGuard peer keepalive interval
wireguard_keepalive_seconds = Gauge(
    "vpnhd_wireguard_keepalive_seconds",
    "WireGuard persistent keepalive interval in seconds",
    ["client_name"],
)

# WireGuard endpoint information
wireguard_endpoint_info = Info(
    "vpnhd_wireguard_endpoint",
    "WireGuard peer endpoint information",
    ["client_name", "endpoint_ip", "endpoint_port"],
)

# =============================================================================
# DDNS Metrics
# =============================================================================

# DDNS update events
ddns_updates_total = Counter(
    "vpnhd_ddns_updates_total",
    "Total number of DDNS update attempts",
    ["provider", "record_type", "status"],  # status: success, failure
)

# Current registered IP addresses
ddns_registered_ip = Info(
    "vpnhd_ddns_registered_ip",
    "Currently registered IP addresses with DDNS",
    ["provider", "record_type", "ip_address"],
)

# Last successful DDNS update timestamp
ddns_last_update_timestamp_seconds = Gauge(
    "vpnhd_ddns_last_update_timestamp_seconds",
    "Timestamp of last successful DDNS update",
    ["provider", "record_type"],
)

# DDNS update duration
ddns_update_duration_seconds = Histogram(
    "vpnhd_ddns_update_duration_seconds",
    "DDNS update duration in seconds",
    ["provider"],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10, 30],
)

# =============================================================================
# Security Metrics
# =============================================================================

# Failed authentication attempts
vpn_auth_failures_total = Counter(
    "vpnhd_auth_failures_total",
    "Total number of failed authentication attempts",
    ["client_name", "reason"],
)

# Key rotation events
vpn_key_rotations_total = Counter(
    "vpnhd_key_rotations_total",
    "Total number of key rotation events",
    ["key_type"],  # key_type: wireguard, ssh
)

# Last key rotation timestamp
vpn_last_key_rotation_timestamp_seconds = Gauge(
    "vpnhd_last_key_rotation_timestamp_seconds", "Timestamp of last key rotation", ["key_type"]
)

# Security alerts
vpn_security_alerts_total = Counter(
    "vpnhd_security_alerts_total", "Total number of security alerts", ["severity", "alert_type"]
)

# =============================================================================
# System Resource Metrics
# =============================================================================

# CPU usage percentage
vpn_cpu_usage_percent = Gauge(
    "vpnhd_cpu_usage_percent",
    "VPN server CPU usage percentage",
    ["process"],  # process: vpnhd, wireguard
)

# Memory usage in bytes
vpn_memory_usage_bytes = Gauge(
    "vpnhd_memory_usage_bytes", "VPN server memory usage in bytes", ["process"]
)

# Disk usage for VPN data
vpn_disk_usage_bytes = Gauge(
    "vpnhd_disk_usage_bytes",
    "Disk space used by VPN data in bytes",
    ["path", "type"],  # type: config, logs, backups
)

# =============================================================================
# Configuration Metrics
# =============================================================================

# Configuration reload events
vpn_config_reloads_total = Counter(
    "vpnhd_config_reloads_total",
    "Total number of configuration reload events",
    ["status"],  # status: success, failure
)

# Last configuration reload timestamp
vpn_last_config_reload_timestamp_seconds = Gauge(
    "vpnhd_last_config_reload_timestamp_seconds", "Timestamp of last configuration reload"
)

# Configuration version
vpn_config_version = Info(
    "vpnhd_config_version", "Current configuration version", ["version", "checksum"]
)

# =============================================================================
# Backup and Restore Metrics
# =============================================================================

# Backup operations
vpn_backups_total = Counter(
    "vpnhd_backups_total",
    "Total number of backup operations",
    ["backup_type", "status"],  # backup_type: full, incremental
)

# Last backup timestamp
vpn_last_backup_timestamp_seconds = Gauge(
    "vpnhd_last_backup_timestamp_seconds", "Timestamp of last successful backup", ["backup_type"]
)

# Backup size in bytes
vpn_backup_size_bytes = Gauge(
    "vpnhd_backup_size_bytes", "Size of last backup in bytes", ["backup_type"]
)

# Restore operations
vpn_restores_total = Counter(
    "vpnhd_restores_total", "Total number of restore operations", ["status"]
)

# =============================================================================
# Phase Execution Metrics
# =============================================================================

# Phase execution duration
vpn_phase_duration_seconds = Histogram(
    "vpnhd_phase_duration_seconds",
    "Phase execution duration in seconds",
    ["phase_name"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300],
)

# Phase execution status
vpn_phase_executions_total = Counter(
    "vpnhd_phase_executions_total",
    "Total number of phase executions",
    ["phase_name", "status"],  # status: success, failure, skipped
)

# Last phase execution timestamp
vpn_last_phase_execution_timestamp_seconds = Gauge(
    "vpnhd_last_phase_execution_timestamp_seconds",
    "Timestamp of last phase execution",
    ["phase_name"],
)

# =============================================================================
# Notification Metrics
# =============================================================================

# Notification events
vpn_notifications_total = Counter(
    "vpnhd_notifications_total",
    "Total number of notification events",
    ["channel", "event_type", "status"],  # channel: email, webhook
)

# Notification delivery duration
vpn_notification_duration_seconds = Histogram(
    "vpnhd_notification_duration_seconds",
    "Notification delivery duration in seconds",
    ["channel"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

# =============================================================================
# API and CLI Metrics
# =============================================================================

# API requests
vpn_api_requests_total = Counter(
    "vpnhd_api_requests_total",
    "Total number of API requests",
    ["endpoint", "method", "status_code"],
)

# API request duration
vpn_api_request_duration_seconds = Summary(
    "vpnhd_api_request_duration_seconds", "API request duration in seconds", ["endpoint", "method"]
)

# CLI command executions
vpn_cli_commands_total = Counter(
    "vpnhd_cli_commands_total", "Total number of CLI command executions", ["command", "status"]
)

# =============================================================================
# Error Metrics
# =============================================================================

# Total errors by category
vpn_errors_total = Counter(
    "vpnhd_errors_total",
    "Total number of errors",
    ["category", "severity"],  # category: network, config, system, etc.
)

# Error rate (errors per second)
vpn_error_rate = Gauge("vpnhd_error_rate", "Current error rate (errors per second)", ["category"])

# =============================================================================
# Helper Functions
# =============================================================================


def get_all_metrics() -> Dict[str, Any]:
    """Get all defined metrics as a dictionary.

    Returns:
        Dict mapping metric names to metric objects
    """
    return {
        # Server metrics
        "vpn_server_info": vpn_server_info,
        "vpn_server_uptime_seconds": vpn_server_uptime_seconds,
        "vpn_server_status": vpn_server_status,
        # Client metrics
        "vpn_clients_active": vpn_clients_active,
        "vpn_clients_total": vpn_clients_total,
        "vpn_client_connections_total": vpn_client_connections_total,
        "vpn_client_info": vpn_client_info,
        # Network traffic metrics
        "vpn_traffic_received_bytes_total": vpn_traffic_received_bytes_total,
        "vpn_traffic_transmitted_bytes_total": vpn_traffic_transmitted_bytes_total,
        "vpn_bandwidth_bytes_per_second": vpn_bandwidth_bytes_per_second,
        "vpn_latency_milliseconds": vpn_latency_milliseconds,
        "vpn_packet_loss_ratio": vpn_packet_loss_ratio,
        # WireGuard metrics
        "wireguard_handshake_timestamp_seconds": wireguard_handshake_timestamp_seconds,
        "wireguard_keepalive_seconds": wireguard_keepalive_seconds,
        "wireguard_endpoint_info": wireguard_endpoint_info,
        # DDNS metrics
        "ddns_updates_total": ddns_updates_total,
        "ddns_registered_ip": ddns_registered_ip,
        "ddns_last_update_timestamp_seconds": ddns_last_update_timestamp_seconds,
        "ddns_update_duration_seconds": ddns_update_duration_seconds,
        # Security metrics
        "vpn_auth_failures_total": vpn_auth_failures_total,
        "vpn_key_rotations_total": vpn_key_rotations_total,
        "vpn_last_key_rotation_timestamp_seconds": vpn_last_key_rotation_timestamp_seconds,
        "vpn_security_alerts_total": vpn_security_alerts_total,
        # System resource metrics
        "vpn_cpu_usage_percent": vpn_cpu_usage_percent,
        "vpn_memory_usage_bytes": vpn_memory_usage_bytes,
        "vpn_disk_usage_bytes": vpn_disk_usage_bytes,
        # Configuration metrics
        "vpn_config_reloads_total": vpn_config_reloads_total,
        "vpn_last_config_reload_timestamp_seconds": vpn_last_config_reload_timestamp_seconds,
        "vpn_config_version": vpn_config_version,
        # Backup and restore metrics
        "vpn_backups_total": vpn_backups_total,
        "vpn_last_backup_timestamp_seconds": vpn_last_backup_timestamp_seconds,
        "vpn_backup_size_bytes": vpn_backup_size_bytes,
        "vpn_restores_total": vpn_restores_total,
        # Phase execution metrics
        "vpn_phase_duration_seconds": vpn_phase_duration_seconds,
        "vpn_phase_executions_total": vpn_phase_executions_total,
        "vpn_last_phase_execution_timestamp_seconds": vpn_last_phase_execution_timestamp_seconds,
        # Notification metrics
        "vpn_notifications_total": vpn_notifications_total,
        "vpn_notification_duration_seconds": vpn_notification_duration_seconds,
        # API and CLI metrics
        "vpn_api_requests_total": vpn_api_requests_total,
        "vpn_api_request_duration_seconds": vpn_api_request_duration_seconds,
        "vpn_cli_commands_total": vpn_cli_commands_total,
        # Error metrics
        "vpn_errors_total": vpn_errors_total,
        "vpn_error_rate": vpn_error_rate,
    }


def get_metric_by_name(name: str) -> Any:
    """Get a specific metric by name.

    Args:
        name: Metric name

    Returns:
        Metric object or None if not found
    """
    all_metrics = get_all_metrics()
    return all_metrics.get(name)
