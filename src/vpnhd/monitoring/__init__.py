"""Monitoring and metrics collection for VPNHD."""

from .metrics import (
    get_all_metrics,
    get_metric_by_name,
    # Server metrics
    vpn_server_info,
    vpn_server_uptime_seconds,
    vpn_server_status,
    # Client metrics
    vpn_clients_active,
    vpn_clients_total,
    # Traffic metrics
    vpn_traffic_received_bytes_total,
    vpn_traffic_transmitted_bytes_total,
    vpn_bandwidth_bytes_per_second,
    # Error metrics
    vpn_errors_total,
)
from .collector import MetricsCollector
from .exporter import MetricsExporter

__all__ = [
    # Functions
    "get_all_metrics",
    "get_metric_by_name",
    # Classes
    "MetricsCollector",
    "MetricsExporter",
    # Key metrics (commonly used)
    "vpn_server_info",
    "vpn_server_uptime_seconds",
    "vpn_server_status",
    "vpn_clients_active",
    "vpn_clients_total",
    "vpn_traffic_received_bytes_total",
    "vpn_traffic_transmitted_bytes_total",
    "vpn_bandwidth_bytes_per_second",
    "vpn_errors_total",
]
