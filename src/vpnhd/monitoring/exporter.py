"""Prometheus metrics HTTP exporter for VPNHD."""

import asyncio
import signal
from typing import Optional
from prometheus_client import REGISTRY, generate_latest
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from ..utils.logging import get_logger
from ..config.manager import ConfigManager
from .collector import MetricsCollector

logger = get_logger(__name__)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/metrics":
            # Generate Prometheus metrics
            try:
                metrics_output = generate_latest(REGISTRY)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.end_headers()
                self.wfile.write(metrics_output)
            except Exception as e:
                logger.error(f"Error generating metrics: {e}")
                self.send_error(500, f"Error generating metrics: {e}")

        elif self.path == "/health":
            # Health check endpoint
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        elif self.path == "/":
            # Root path - provide basic info
            html = """
            <html>
            <head><title>VPNHD Metrics Exporter</title></head>
            <body>
            <h1>VPNHD Prometheus Metrics Exporter</h1>
            <p>Available endpoints:</p>
            <ul>
                <li><a href="/metrics">/metrics</a> - Prometheus metrics</li>
                <li><a href="/health">/health</a> - Health check</li>
            </ul>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        """Override to use custom logger."""
        logger.debug(f"{self.address_string()} - {format % args}")


class MetricsExporter:
    """Prometheus metrics HTTP exporter."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        port: Optional[int] = None,
        host: str = "0.0.0.0",
        collection_interval: int = 15,
    ):
        """Initialize metrics exporter.

        Args:
            config_manager: Configuration manager instance
            port: HTTP server port (default from config or 9100)
            host: HTTP server host
            collection_interval: Metrics collection interval in seconds
        """
        self.config = config_manager or ConfigManager()
        self.logger = logger

        # Server configuration
        self.port = port or self.config.get("monitoring.prometheus_port", 9100)
        self.host = host
        self.collection_interval = collection_interval

        # HTTP server
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

        # Metrics collector
        self.collector = MetricsCollector(
            config_manager=self.config, collection_interval=collection_interval
        )

        # Running state
        self._running = False

    def start(self) -> None:
        """Start metrics exporter (synchronous)."""
        if self._running:
            self.logger.warning("Metrics exporter already running")
            return

        self._running = True

        try:
            # Start HTTP server
            self.server = HTTPServer((self.host, self.port), MetricsHandler)
            self.logger.info(f"Starting metrics exporter on {self.host}:{self.port}")

            # Run server in separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            self.logger.info(f"Metrics available at http://{self.host}:{self.port}/metrics")

        except Exception as e:
            self.logger.exception(f"Failed to start metrics exporter: {e}")
            self._running = False
            raise

    def stop(self) -> None:
        """Stop metrics exporter (synchronous)."""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping metrics exporter")

        # Stop HTTP server
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

        # Wait for server thread
        if self.server_thread:
            self.server_thread.join(timeout=5)
            self.server_thread = None

    async def start_async(self) -> None:
        """Start metrics exporter and collector (async)."""
        # Start HTTP server
        self.start()

        # Start metrics collector
        await self.collector.start()

    async def stop_async(self) -> None:
        """Stop metrics exporter and collector (async)."""
        # Stop metrics collector
        await self.collector.stop()

        # Stop HTTP server
        self.stop()

    async def run_forever(self) -> None:
        """Run metrics exporter indefinitely."""
        # Start exporter and collector
        await self.start_async()

        try:
            # Keep running until interrupted
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            await self.stop_async()

    def is_running(self) -> bool:
        """Check if exporter is running.

        Returns:
            bool: True if running
        """
        return self._running


async def main_async() -> None:
    """Main entry point for async metrics exporter."""
    # Setup logging
    from ..utils.logging import setup_logging

    setup_logging(log_level="INFO")

    # Load configuration
    config = ConfigManager()

    # Create exporter
    port = config.get("monitoring.prometheus_port", 9100)
    collection_interval = config.get("monitoring.collection_interval", 15)

    exporter = MetricsExporter(
        config_manager=config, port=port, collection_interval=collection_interval
    )

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info(f"Received signal {sig}")
        asyncio.create_task(exporter.stop_async())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    # Run exporter
    logger.info("Starting VPNHD metrics exporter")
    logger.info(f"Metrics will be available at http://0.0.0.0:{port}/metrics")

    await exporter.run_forever()


def main() -> None:
    """Main entry point for metrics exporter CLI."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Exporter stopped by user")
    except Exception as e:
        logger.exception(f"Exporter failed: {e}")
        raise


if __name__ == "__main__":
    main()
