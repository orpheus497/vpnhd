"""IP change detection for DDNS updates."""

import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from ..config.manager import ConfigManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class IPChangeDetector:
    """Detect changes in public IP addresses for DDNS updates."""

    # Public IP detection services (using multiple for reliability)
    IPV4_SERVICES = [
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
    ]

    IPV6_SERVICES = [
        "https://api6.ipify.org",
        "https://v6.ident.me",
        "https://ifconfig.co",
    ]

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        check_interval: int = 300,  # 5 minutes default
    ):
        """Initialize IP change detector.

        Args:
            config_manager: Configuration manager instance
            check_interval: Seconds between IP checks
        """
        self.config = config_manager or ConfigManager()
        self.check_interval = check_interval
        self.logger = logger

        # Track current IPs
        self.current_ipv4: Optional[str] = None
        self.current_ipv6: Optional[str] = None
        self.last_check: Optional[datetime] = None

        # Callbacks for IP change events
        self.ipv4_change_callbacks: List[Callable[[str, Optional[str]], Awaitable[None]]] = []
        self.ipv6_change_callbacks: List[Callable[[str, Optional[str]], Awaitable[None]]] = []

        # Running state
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def get_public_ipv4(self) -> Optional[str]:
        """Detect current public IPv4 address.

        Tries multiple services for reliability.

        Returns:
            Optional[str]: IPv4 address or None
        """
        async with httpx.AsyncClient(timeout=10) as client:
            for service in self.IPV4_SERVICES:
                try:
                    response = await client.get(service)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        # Basic validation
                        if self._is_valid_ipv4(ip):
                            self.logger.debug(f"Detected public IPv4: {ip} (from {service})")
                            return ip
                except Exception as e:
                    self.logger.debug(f"Failed to get IPv4 from {service}: {e}")
                    continue

        self.logger.warning("Failed to detect public IPv4 from all services")
        return None

    async def get_public_ipv6(self) -> Optional[str]:
        """Detect current public IPv6 address.

        Tries multiple services for reliability.

        Returns:
            Optional[str]: IPv6 address or None
        """
        async with httpx.AsyncClient(timeout=10) as client:
            for service in self.IPV6_SERVICES:
                try:
                    response = await client.get(service)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        # Basic validation
                        if self._is_valid_ipv6(ip):
                            self.logger.debug(f"Detected public IPv6: {ip} (from {service})")
                            return ip
                except Exception as e:
                    self.logger.debug(f"Failed to get IPv6 from {service}: {e}")
                    continue

        self.logger.debug("No public IPv6 address detected")
        return None

    def _is_valid_ipv4(self, ip: str) -> bool:
        """Validate IPv4 address format."""
        import ipaddress

        try:
            addr = ipaddress.IPv4Address(ip)
            # Exclude private/reserved addresses
            return not (addr.is_private or addr.is_loopback or addr.is_reserved)
        except ValueError:
            return False

    def _is_valid_ipv6(self, ip: str) -> bool:
        """Validate IPv6 address format."""
        import ipaddress

        try:
            addr = ipaddress.IPv6Address(ip)
            # Exclude link-local, loopback, etc.
            return not (addr.is_loopback or addr.is_link_local or addr.is_private)
        except ValueError:
            return False

    async def check_for_changes(self) -> Dict[str, Any]:
        """Check for IP address changes.

        Returns:
            Dict with change information:
            {
                'ipv4_changed': bool,
                'ipv4_old': Optional[str],
                'ipv4_new': Optional[str],
                'ipv6_changed': bool,
                'ipv6_old': Optional[str],
                'ipv6_new': Optional[str],
            }
        """
        result = {
            "ipv4_changed": False,
            "ipv4_old": self.current_ipv4,
            "ipv4_new": None,
            "ipv6_changed": False,
            "ipv6_old": self.current_ipv6,
            "ipv6_new": None,
        }

        # Check IPv4
        new_ipv4 = await self.get_public_ipv4()
        if new_ipv4 and new_ipv4 != self.current_ipv4:
            result["ipv4_changed"] = True
            result["ipv4_new"] = new_ipv4
            self.logger.info(f"IPv4 change detected: {self.current_ipv4} -> {new_ipv4}")

            # Trigger callbacks
            for callback in self.ipv4_change_callbacks:
                try:
                    await callback(new_ipv4, self.current_ipv4)
                except Exception as e:
                    self.logger.exception(f"IPv4 change callback failed: {e}")

            self.current_ipv4 = new_ipv4

        # Check IPv6
        new_ipv6 = await self.get_public_ipv6()
        if new_ipv6 and new_ipv6 != self.current_ipv6:
            result["ipv6_changed"] = True
            result["ipv6_new"] = new_ipv6
            self.logger.info(f"IPv6 change detected: {self.current_ipv6} -> {new_ipv6}")

            # Trigger callbacks
            for callback in self.ipv6_change_callbacks:
                try:
                    await callback(new_ipv6, self.current_ipv6)
                except Exception as e:
                    self.logger.exception(f"IPv6 change callback failed: {e}")

            self.current_ipv6 = new_ipv6

        self.last_check = datetime.now()
        return result

    def on_ipv4_change(self, callback: Callable[[str, Optional[str]], Awaitable[None]]) -> None:
        """Register callback for IPv4 changes.

        Args:
            callback: Async function(new_ip, old_ip)
        """
        self.ipv4_change_callbacks.append(callback)

    def on_ipv6_change(self, callback: Callable[[str, Optional[str]], Awaitable[None]]) -> None:
        """Register callback for IPv6 changes.

        Args:
            callback: Async function(new_ip, old_ip)
        """
        self.ipv6_change_callbacks.append(callback)

    async def start_monitoring(self) -> None:
        """Start continuous IP monitoring."""
        if self._running:
            self.logger.warning("IP monitoring already running")
            return

        self._running = True
        self.logger.info(f"Starting IP monitoring (interval: {self.check_interval}s)")

        # Initial check
        await self.check_for_changes()

        # Create monitoring task
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop IP monitoring."""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping IP monitoring")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                # Expected when task is cancelled
                pass
            self._task = None

    async def _monitor_loop(self) -> None:
        """Continuous monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check_for_changes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in IP monitoring loop: {e}")
                # Continue monitoring despite errors
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def get_status(self) -> Dict[str, Any]:
        """Get current detector status.

        Returns:
            Dict with status information
        """
        return {
            "running": self._running,
            "current_ipv4": self.current_ipv4,
            "current_ipv6": self.current_ipv6,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_interval": self.check_interval,
            "ipv4_callbacks": len(self.ipv4_change_callbacks),
            "ipv6_callbacks": len(self.ipv6_change_callbacks),
        }
