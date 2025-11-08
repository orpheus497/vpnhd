"""Performance testing module for VPNHD.

This module provides comprehensive performance testing for VPN connections including
bandwidth, latency, jitter, packet loss, and connection stability measurements.
"""

import time
import subprocess
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from ..utils.logging import get_logger
from ..system.commands import execute_command

logger = get_logger(__name__)


@dataclass
class BandwidthResult:
    """Bandwidth test result."""

    download_mbps: float
    upload_mbps: float
    test_duration: float
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class LatencyResult:
    """Latency test result."""

    min_ms: float
    max_ms: float
    avg_ms: float
    stddev_ms: float
    packet_loss_percent: float
    packets_sent: int
    packets_received: int
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ConnectionStabilityResult:
    """Connection stability test result."""

    test_duration_seconds: int
    successful_pings: int
    failed_pings: int
    total_pings: int
    uptime_percent: float
    disconnections: int
    avg_latency_ms: float
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PerformanceReport:
    """Complete performance test report."""

    bandwidth: Optional[BandwidthResult]
    latency: Optional[LatencyResult]
    stability: Optional[ConnectionStabilityResult]
    test_date: str
    vpn_interface: str
    test_server: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bandwidth": asdict(self.bandwidth) if self.bandwidth else None,
            "latency": asdict(self.latency) if self.latency else None,
            "stability": asdict(self.stability) if self.stability else None,
            "test_date": self.test_date,
            "vpn_interface": self.vpn_interface,
            "test_server": self.test_server,
        }


class PerformanceTester:
    """Performance testing for VPN connections."""

    def __init__(self, vpn_interface: str = "wg0", test_server: str = "8.8.8.8"):
        """Initialize performance tester.

        Args:
            vpn_interface: VPN interface to test (default: wg0)
            test_server: Server to use for testing (default: 8.8.8.8)
        """
        self.vpn_interface = vpn_interface
        self.test_server = test_server
        self.results_dir = Path.home() / ".config" / "vpnhd" / "performance"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def test_latency(self, count: int = 10, timeout: int = 5) -> Optional[LatencyResult]:
        """Test latency using ping.

        Args:
            count: Number of ping packets to send
            timeout: Timeout for each ping in seconds

        Returns:
            LatencyResult or None if test fails
        """
        try:
            logger.info(f"Testing latency to {self.test_server} with {count} packets")

            # Run ping command
            result = execute_command(
                ["ping", "-c", str(count), "-W", str(timeout), self.test_server],
                capture_output=True,
                timeout=count * timeout + 10,
            )

            if not result.success:
                logger.error(f"Ping failed: {result.stderr}")
                return None

            # Parse ping output
            output = result.stdout

            # Extract statistics
            stats_line = None
            for line in output.split("\n"):
                if "min/avg/max" in line.lower() or "rtt" in line.lower():
                    stats_line = line
                    break

            if not stats_line:
                logger.error("Could not parse ping statistics")
                return None

            # Parse timing: min/avg/max/stddev
            # Example: "rtt min/avg/max/mdev = 10.123/15.456/20.789/2.345 ms"
            times_part = stats_line.split("=")[1].strip() if "=" in stats_line else stats_line
            times = times_part.split()[0].split("/")

            if len(times) < 4:
                logger.error(f"Invalid ping statistics format: {stats_line}")
                return None

            min_ms = float(times[0])
            avg_ms = float(times[1])
            max_ms = float(times[2])
            stddev_ms = float(times[3])

            # Extract packet loss
            packet_loss = 0.0
            packets_sent = count
            packets_received = count

            for line in output.split("\n"):
                if "packet loss" in line.lower():
                    # Example: "10 packets transmitted, 9 received, 10% packet loss"
                    parts = line.split(",")
                    for part in parts:
                        if "transmitted" in part:
                            packets_sent = int(part.split()[0])
                        elif "received" in part:
                            packets_received = int(part.split()[0])
                        elif "packet loss" in part or "loss" in part:
                            loss_str = part.split("%")[0].strip().split()[-1]
                            packet_loss = float(loss_str)
                    break

            result = LatencyResult(
                min_ms=min_ms,
                max_ms=max_ms,
                avg_ms=avg_ms,
                stddev_ms=stddev_ms,
                packet_loss_percent=packet_loss,
                packets_sent=packets_sent,
                packets_received=packets_received,
            )

            logger.info(f"Latency test complete: avg={avg_ms:.2f}ms, loss={packet_loss:.1f}%")
            return result

        except Exception as e:
            logger.exception(f"Error testing latency: {e}")
            return None

    def test_bandwidth_iperf(
        self, server: str, duration: int = 10, reverse: bool = False
    ) -> Optional[BandwidthResult]:
        """Test bandwidth using iperf3.

        Args:
            server: iperf3 server address
            duration: Test duration in seconds
            reverse: Test download (True) or upload (False)

        Returns:
            BandwidthResult or None if test fails
        """
        try:
            logger.info(f"Testing bandwidth with iperf3 server {server}")

            # Check if iperf3 is available
            check = execute_command(["which", "iperf3"], capture_output=True)
            if not check.success:
                logger.warning("iperf3 not installed, skipping bandwidth test")
                return None

            # Build iperf3 command
            cmd = ["iperf3", "-c", server, "-t", str(duration), "-J"]
            if reverse:
                cmd.append("-R")

            result = execute_command(cmd, capture_output=True, timeout=duration + 30)

            if not result.success:
                logger.error(f"iperf3 failed: {result.stderr}")
                return None

            # Parse JSON output
            data = json.loads(result.stdout)

            # Extract bandwidth
            if "end" in data and "sum_received" in data["end"]:
                download_bps = data["end"]["sum_received"]["bits_per_second"]
                upload_bps = data["end"]["sum_sent"]["bits_per_second"]
                download_mbps = download_bps / 1_000_000
                upload_mbps = upload_bps / 1_000_000
            else:
                logger.error("Could not parse iperf3 results")
                return None

            return BandwidthResult(
                download_mbps=download_mbps, upload_mbps=upload_mbps, test_duration=duration
            )

        except Exception as e:
            logger.exception(f"Error testing bandwidth: {e}")
            return None

    def test_connection_stability(
        self, duration_seconds: int = 300, interval_seconds: int = 1
    ) -> Optional[ConnectionStabilityResult]:
        """Test connection stability over time.

        Args:
            duration_seconds: Total test duration in seconds
            interval_seconds: Interval between pings in seconds

        Returns:
            ConnectionStabilityResult or None if test fails
        """
        try:
            logger.info(f"Testing connection stability for {duration_seconds} seconds")

            total_pings = duration_seconds // interval_seconds
            successful_pings = 0
            failed_pings = 0
            latencies = []
            disconnections = 0
            was_connected = True

            start_time = time.time()

            for i in range(total_pings):
                # Single ping
                result = execute_command(
                    ["ping", "-c", "1", "-W", "2", self.test_server], capture_output=True, timeout=5
                )

                if result.success:
                    successful_pings += 1

                    # Extract latency
                    for line in result.stdout.split("\n"):
                        if "time=" in line:
                            time_part = line.split("time=")[1].split()[0]
                            latency = float(time_part)
                            latencies.append(latency)
                            break

                    if not was_connected:
                        disconnections += 1
                        was_connected = True
                else:
                    failed_pings += 1
                    was_connected = False

                # Wait for next interval
                elapsed = time.time() - start_time
                next_ping_time = (i + 1) * interval_seconds
                sleep_time = next_ping_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

            total = successful_pings + failed_pings
            uptime_percent = (successful_pings / total * 100) if total > 0 else 0
            avg_latency = statistics.mean(latencies) if latencies else 0

            result = ConnectionStabilityResult(
                test_duration_seconds=duration_seconds,
                successful_pings=successful_pings,
                failed_pings=failed_pings,
                total_pings=total,
                uptime_percent=uptime_percent,
                disconnections=disconnections,
                avg_latency_ms=avg_latency,
            )

            logger.info(
                f"Stability test complete: uptime={uptime_percent:.1f}%, disconnections={disconnections}"
            )
            return result

        except Exception as e:
            logger.exception(f"Error testing connection stability: {e}")
            return None

    def run_full_test(
        self,
        include_bandwidth: bool = False,
        iperf_server: Optional[str] = None,
        latency_count: int = 20,
        stability_duration: int = 60,
    ) -> PerformanceReport:
        """Run complete performance test suite.

        Args:
            include_bandwidth: Include bandwidth test (requires iperf3 server)
            iperf_server: iperf3 server address
            latency_count: Number of ping packets for latency test
            stability_duration: Duration of stability test in seconds

        Returns:
            PerformanceReport with all test results
        """
        logger.info("Starting full performance test suite")

        # Latency test
        latency_result = self.test_latency(count=latency_count)

        # Bandwidth test (if requested)
        bandwidth_result = None
        if include_bandwidth and iperf_server:
            bandwidth_result = self.test_bandwidth_iperf(iperf_server)

        # Stability test
        stability_result = self.test_connection_stability(duration_seconds=stability_duration)

        report = PerformanceReport(
            bandwidth=bandwidth_result,
            latency=latency_result,
            stability=stability_result,
            test_date=datetime.now().isoformat(),
            vpn_interface=self.vpn_interface,
            test_server=self.test_server,
        )

        # Save report
        self.save_report(report)

        logger.info("Performance test suite complete")
        return report

    def save_report(self, report: PerformanceReport) -> Path:
        """Save performance report to file.

        Args:
            report: Performance report to save

        Returns:
            Path to saved report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_report_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        logger.info(f"Performance report saved to {filepath}")
        return filepath

    def load_report(self, filepath: str) -> Optional[PerformanceReport]:
        """Load performance report from file.

        Args:
            filepath: Path to report file

        Returns:
            PerformanceReport or None if loading fails
        """
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            bandwidth = BandwidthResult(**data["bandwidth"]) if data["bandwidth"] else None
            latency = LatencyResult(**data["latency"]) if data["latency"] else None
            stability = (
                ConnectionStabilityResult(**data["stability"]) if data["stability"] else None
            )

            return PerformanceReport(
                bandwidth=bandwidth,
                latency=latency,
                stability=stability,
                test_date=data["test_date"],
                vpn_interface=data["vpn_interface"],
                test_server=data["test_server"],
            )
        except Exception as e:
            logger.exception(f"Error loading report: {e}")
            return None

    def list_reports(self) -> List[Path]:
        """List all saved performance reports.

        Returns:
            List of paths to report files, sorted by date (newest first)
        """
        reports = list(self.results_dir.glob("performance_report_*.json"))
        reports.sort(reverse=True)
        return reports

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from all performance reports.

        Returns:
            Dictionary with aggregated statistics
        """
        reports = self.list_reports()

        if not reports:
            return {"total_reports": 0}

        latencies = []
        packet_losses = []
        uptimes = []

        for report_path in reports:
            report = self.load_report(str(report_path))
            if not report:
                continue

            if report.latency:
                latencies.append(report.latency.avg_ms)
                packet_losses.append(report.latency.packet_loss_percent)

            if report.stability:
                uptimes.append(report.stability.uptime_percent)

        stats = {
            "total_reports": len(reports),
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "avg_packet_loss": statistics.mean(packet_losses) if packet_losses else 0,
            "avg_uptime_percent": statistics.mean(uptimes) if uptimes else 0,
        }

        return stats
