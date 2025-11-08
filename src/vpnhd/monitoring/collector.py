"""Metrics collector for gathering VPN statistics."""

import asyncio
import time
import psutil
from typing import Optional, Dict
from pathlib import Path

from ..utils.logging import get_logger
from ..config.manager import ConfigManager
from ..utils.command import execute_command_async
from . import metrics

logger = get_logger(__name__)


class MetricsCollector:
    """Collect and update Prometheus metrics for VPNHD."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        collection_interval: int = 15,  # 15 seconds default
    ):
        """Initialize metrics collector.

        Args:
            config_manager: Configuration manager instance
            collection_interval: Seconds between metric collections
        """
        self.config = config_manager or ConfigManager()
        self.collection_interval = collection_interval
        self.logger = logger

        # Collector state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time = time.time()

        # Previous traffic stats for rate calculation
        self._prev_traffic: Dict[str, Dict[str, int]] = {}

    async def collect_all_metrics(self) -> None:
        """Collect all metrics."""
        try:
            await asyncio.gather(
                self._collect_server_metrics(),
                self._collect_client_metrics(),
                self._collect_traffic_metrics(),
                self._collect_wireguard_metrics(),
                self._collect_system_metrics(),
                self._collect_disk_metrics(),
                return_exceptions=True
            )
        except Exception as e:
            self.logger.exception(f"Error collecting metrics: {e}")
            metrics.vpn_errors_total.labels(
                category='metrics',
                severity='error'
            ).inc()

    async def _collect_server_metrics(self) -> None:
        """Collect server-level metrics."""
        try:
            # Server info
            from .. import __version__
            interface = self.config.get('network.vpn.interface', 'wg0')
            hostname = self.config.get('server.ddns_domain', 'unknown')

            metrics.vpn_server_info.info({
                'version': __version__.__version__,
                'provider': 'wireguard',
                'interface': interface,
                'hostname': hostname,
            })

            # Server uptime
            uptime = time.time() - self._start_time
            metrics.vpn_server_uptime_seconds.set(uptime)

            # Server status (check if WireGuard interface exists)
            result = await execute_command_async(
                ['ip', 'link', 'show', interface],
                check=False
            )
            status = 1 if result.success else 0
            metrics.vpn_server_status.labels(interface=interface).set(status)

        except Exception as e:
            self.logger.error(f"Error collecting server metrics: {e}")

    async def _collect_client_metrics(self) -> None:
        """Collect client connection metrics."""
        try:
            # Get all configured clients
            clients = self.config.get('clients', {})
            total_clients = len(clients)
            metrics.vpn_clients_total.set(total_clients)

            # Get active clients from WireGuard
            active_count = await self._count_active_clients()
            metrics.vpn_clients_active.set(active_count)

            # Update client info
            for client_name, client_data in clients.items():
                metrics.vpn_client_info.info({
                    'client_name': client_name,
                    'internal_ip': client_data.get('internal_ip', 'unknown'),
                    'allowed_ips': ','.join(client_data.get('allowed_ips', [])),
                })

        except Exception as e:
            self.logger.error(f"Error collecting client metrics: {e}")

    async def _count_active_clients(self) -> int:
        """Count number of active WireGuard clients.

        Returns:
            int: Number of active clients
        """
        try:
            interface = self.config.get('network.vpn.interface', 'wg0')
            result = await execute_command_async(
                ['wg', 'show', interface, 'peers'],
                check=False
            )

            if result.success:
                peers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return len(peers)

            return 0
        except Exception as e:
            self.logger.error(f"Error counting active clients: {e}")
            return 0

    async def _collect_traffic_metrics(self) -> None:
        """Collect network traffic metrics."""
        try:
            interface = self.config.get('network.vpn.interface', 'wg0')

            # Get WireGuard statistics
            result = await execute_command_async(
                ['wg', 'show', interface, 'transfer'],
                check=False
            )

            if not result.success:
                return

            # Parse transfer statistics
            # Format: <public_key>\t<received_bytes>\t<transmitted_bytes>
            current_time = time.time()
            lines = result.stdout.strip().split('\n')

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split('\t')
                if len(parts) != 3:
                    continue

                public_key = parts[0].strip()
                received = int(parts[1].strip())
                transmitted = int(parts[2].strip())

                # Find client name for this public key
                client_name = await self._get_client_name_by_pubkey(public_key)
                if not client_name:
                    client_name = public_key[:8]  # Use truncated key as fallback

                # Update total counters
                metrics.vpn_traffic_received_bytes_total.labels(
                    client_name=client_name,
                    interface=interface
                ).inc(received)

                metrics.vpn_traffic_transmitted_bytes_total.labels(
                    client_name=client_name,
                    interface=interface
                ).inc(transmitted)

                # Calculate bandwidth (bytes/sec) using previous values
                if client_name in self._prev_traffic:
                    prev_data = self._prev_traffic[client_name]
                    time_delta = current_time - prev_data['timestamp']

                    if time_delta > 0:
                        rx_rate = (received - prev_data['received']) / time_delta
                        tx_rate = (transmitted - prev_data['transmitted']) / time_delta

                        metrics.vpn_bandwidth_bytes_per_second.labels(
                            client_name=client_name,
                            interface=interface,
                            direction='rx'
                        ).set(max(0, rx_rate))

                        metrics.vpn_bandwidth_bytes_per_second.labels(
                            client_name=client_name,
                            interface=interface,
                            direction='tx'
                        ).set(max(0, tx_rate))

                # Store current values for next calculation
                self._prev_traffic[client_name] = {
                    'received': received,
                    'transmitted': transmitted,
                    'timestamp': current_time,
                }

        except Exception as e:
            self.logger.error(f"Error collecting traffic metrics: {e}")

    async def _get_client_name_by_pubkey(self, public_key: str) -> Optional[str]:
        """Get client name by public key.

        Args:
            public_key: WireGuard public key

        Returns:
            Optional[str]: Client name or None
        """
        try:
            clients = self.config.get('clients', {})
            for client_name, client_data in clients.items():
                if client_data.get('public_key') == public_key:
                    return client_name
            return None
        except Exception:
            return None

    async def _collect_wireguard_metrics(self) -> None:
        """Collect WireGuard-specific metrics."""
        try:
            interface = self.config.get('network.vpn.interface', 'wg0')

            # Get latest handshakes
            result = await execute_command_async(
                ['wg', 'show', interface, 'latest-handshakes'],
                check=False
            )

            if result.success:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line.strip():
                        continue

                    parts = line.split('\t')
                    if len(parts) != 2:
                        continue

                    public_key = parts[0].strip()
                    handshake_time = int(parts[1].strip())

                    client_name = await self._get_client_name_by_pubkey(public_key)
                    if not client_name:
                        client_name = public_key[:8]

                    if handshake_time > 0:
                        metrics.wireguard_handshake_timestamp_seconds.labels(
                            client_name=client_name,
                            public_key=public_key[:16]  # Truncate for label
                        ).set(handshake_time)

            # Get endpoints
            result = await execute_command_async(
                ['wg', 'show', interface, 'endpoints'],
                check=False
            )

            if result.success:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line.strip():
                        continue

                    parts = line.split('\t')
                    if len(parts) != 2:
                        continue

                    public_key = parts[0].strip()
                    endpoint = parts[1].strip()

                    if endpoint and endpoint != '(none)':
                        client_name = await self._get_client_name_by_pubkey(public_key)
                        if not client_name:
                            client_name = public_key[:8]

                        # Parse endpoint (format: IP:PORT)
                        if ':' in endpoint:
                            endpoint_ip, endpoint_port = endpoint.rsplit(':', 1)
                            metrics.wireguard_endpoint_info.info({
                                'client_name': client_name,
                                'endpoint_ip': endpoint_ip,
                                'endpoint_port': endpoint_port,
                            })

        except Exception as e:
            self.logger.error(f"Error collecting WireGuard metrics: {e}")

    async def _collect_system_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics.vpn_cpu_usage_percent.labels(process='vpnhd').set(cpu_percent)

            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            metrics.vpn_memory_usage_bytes.labels(process='vpnhd').set(memory_info.rss)

            # Try to get WireGuard process stats
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
                try:
                    if 'wireguard' in proc.info['name'].lower() or proc.info['name'] == 'wg':
                        metrics.vpn_cpu_usage_percent.labels(
                            process='wireguard'
                        ).set(proc.info['cpu_percent'] or 0)

                        if proc.info['memory_info']:
                            metrics.vpn_memory_usage_bytes.labels(
                                process='wireguard'
                            ).set(proc.info['memory_info'].rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    async def _collect_disk_metrics(self) -> None:
        """Collect disk usage metrics."""
        try:
            # Config directory
            config_path = Path.home() / '.config' / 'vpnhd'
            if config_path.exists():
                config_size = sum(
                    f.stat().st_size for f in config_path.rglob('*') if f.is_file()
                )
                metrics.vpn_disk_usage_bytes.labels(
                    path=str(config_path),
                    type='config'
                ).set(config_size)

            # Logs directory (if exists)
            log_path = Path('/var/log/vpnhd')
            if log_path.exists():
                log_size = sum(
                    f.stat().st_size for f in log_path.rglob('*') if f.is_file()
                )
                metrics.vpn_disk_usage_bytes.labels(
                    path=str(log_path),
                    type='logs'
                ).set(log_size)

            # Backups directory (if configured)
            backup_path = self.config.get('backup.directory')
            if backup_path:
                backup_path = Path(backup_path)
                if backup_path.exists():
                    backup_size = sum(
                        f.stat().st_size for f in backup_path.rglob('*') if f.is_file()
                    )
                    metrics.vpn_disk_usage_bytes.labels(
                        path=str(backup_path),
                        type='backups'
                    ).set(backup_size)

        except Exception as e:
            self.logger.error(f"Error collecting disk metrics: {e}")

    async def start(self) -> None:
        """Start metrics collection."""
        if self._running:
            self.logger.warning("Metrics collector already running")
            return

        self._running = True
        self.logger.info(
            f"Starting metrics collector (interval: {self.collection_interval}s)"
        )

        # Initial collection
        await self.collect_all_metrics()

        # Start collection loop
        self._task = asyncio.create_task(self._collection_loop())

    async def stop(self) -> None:
        """Stop metrics collection."""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping metrics collector")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                # Expected when task is cancelled
                pass
            self._task = None

    async def _collection_loop(self) -> None:
        """Continuous metrics collection loop."""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval)
                await self.collect_all_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in metrics collection loop: {e}")
                # Continue collecting despite errors
                await asyncio.sleep(5)

    def record_phase_execution(
        self,
        phase_name: str,
        duration: float,
        status: str = 'success'
    ) -> None:
        """Record phase execution metrics.

        Args:
            phase_name: Name of the phase
            duration: Execution duration in seconds
            status: Execution status (success, failure, skipped)
        """
        metrics.vpn_phase_duration_seconds.labels(
            phase_name=phase_name
        ).observe(duration)

        metrics.vpn_phase_executions_total.labels(
            phase_name=phase_name,
            status=status
        ).inc()

        metrics.vpn_last_phase_execution_timestamp_seconds.labels(
            phase_name=phase_name
        ).set(time.time())

    def record_notification(
        self,
        channel: str,
        event_type: str,
        status: str,
        duration: Optional[float] = None
    ) -> None:
        """Record notification metrics.

        Args:
            channel: Notification channel (email, webhook)
            event_type: Type of event
            status: Delivery status
            duration: Delivery duration in seconds
        """
        metrics.vpn_notifications_total.labels(
            channel=channel,
            event_type=event_type,
            status=status
        ).inc()

        if duration is not None:
            metrics.vpn_notification_duration_seconds.labels(
                channel=channel
            ).observe(duration)

    def record_ddns_update(
        self,
        provider: str,
        record_type: str,
        status: str,
        duration: Optional[float] = None
    ) -> None:
        """Record DDNS update metrics.

        Args:
            provider: DDNS provider name
            record_type: Record type (A, AAAA)
            status: Update status
            duration: Update duration in seconds
        """
        metrics.ddns_updates_total.labels(
            provider=provider,
            record_type=record_type,
            status=status
        ).inc()

        if status == 'success':
            metrics.ddns_last_update_timestamp_seconds.labels(
                provider=provider,
                record_type=record_type
            ).set(time.time())

        if duration is not None:
            metrics.ddns_update_duration_seconds.labels(
                provider=provider
            ).observe(duration)

    def record_client_connection(
        self,
        client_name: str,
        event_type: str
    ) -> None:
        """Record client connection event.

        Args:
            client_name: Client name
            event_type: Event type (connected, disconnected)
        """
        metrics.vpn_client_connections_total.labels(
            client_name=client_name,
            event_type=event_type
        ).inc()

    def record_error(self, category: str, severity: str = 'error') -> None:
        """Record an error.

        Args:
            category: Error category
            severity: Error severity
        """
        metrics.vpn_errors_total.labels(
            category=category,
            severity=severity
        ).inc()
