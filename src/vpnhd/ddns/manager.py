"""DDNS manager for coordinating dynamic DNS updates."""

import asyncio
from typing import Optional, Dict, Any, Type
from datetime import datetime
from ..utils.logging import get_logger
from ..config.manager import ConfigManager
from .providers.base import DDNSProvider
from .providers.cloudflare import CloudflareDDNS
from .providers.duckdns import DuckDNS
from .providers.noip import NoIPDDNS
from .detector import IPChangeDetector

logger = get_logger(__name__)


class DDNSManager:
    """Manage dynamic DNS updates across multiple providers."""

    # Registry of available DDNS providers
    PROVIDERS: Dict[str, Type[DDNSProvider]] = {
        "cloudflare": CloudflareDDNS,
        "duckdns": DuckDNS,
        "noip": NoIPDDNS,
    }

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        auto_update: bool = True,
        check_interval: int = 300,  # 5 minutes
    ):
        """Initialize DDNS manager.

        Args:
            config_manager: Configuration manager instance
            auto_update: Enable automatic IP monitoring and updates
            check_interval: Seconds between IP checks
        """
        self.config = config_manager or ConfigManager()
        self.logger = logger
        self.auto_update = auto_update
        self.check_interval = check_interval

        # DDNS provider instance
        self.provider: Optional[DDNSProvider] = None
        self._initialize_provider()

        # IP change detector
        self.detector = IPChangeDetector(config_manager=self.config, check_interval=check_interval)

        # Register IP change callbacks
        if self.provider:
            self.detector.on_ipv4_change(self._on_ipv4_change)
            self.detector.on_ipv6_change(self._on_ipv6_change)

        # Update history
        self.update_history: list[Dict[str, Any]] = []
        self.last_ipv4_update: Optional[datetime] = None
        self.last_ipv6_update: Optional[datetime] = None

    def _initialize_provider(self) -> None:
        """Initialize DDNS provider from configuration."""
        provider_name = self.config.get("server.ddns_provider")

        if not provider_name:
            self.logger.info("No DDNS provider configured")
            return

        if provider_name not in self.PROVIDERS:
            self.logger.error(
                f"Unknown DDNS provider: {provider_name}. "
                f"Available: {', '.join(self.PROVIDERS.keys())}"
            )
            return

        try:
            provider_class = self.PROVIDERS[provider_name]
            self.provider = provider_class(self.config)
            self.logger.info(f"Initialized DDNS provider: {provider_name}")
        except Exception as e:
            self.logger.exception(f"Failed to initialize DDNS provider {provider_name}: {e}")

    async def _on_ipv4_change(self, new_ip: str, old_ip: Optional[str]) -> None:
        """Handle IPv4 address change.

        Args:
            new_ip: New IPv4 address
            old_ip: Previous IPv4 address
        """
        if not self.provider:
            return

        self.logger.info(f"Updating IPv4 DNS record: {old_ip} -> {new_ip}")

        try:
            success = await self.provider.update_record(new_ip, record_type="A")

            if success:
                self.last_ipv4_update = datetime.now()
                self._add_to_history(
                    {
                        "timestamp": self.last_ipv4_update,
                        "record_type": "A",
                        "old_ip": old_ip,
                        "new_ip": new_ip,
                        "success": True,
                        "provider": self.provider.provider_name,
                    }
                )

                # Verify update
                await asyncio.sleep(5)  # Wait for DNS propagation
                verified = await self.provider.verify_record(new_ip)
                if verified:
                    self.logger.info(f"IPv4 DNS record verified: {new_ip}")
                else:
                    self.logger.warning(f"IPv4 DNS record verification failed for {new_ip}")
            else:
                self.logger.error(f"Failed to update IPv4 DNS record to {new_ip}")
                self._add_to_history(
                    {
                        "timestamp": datetime.now(),
                        "record_type": "A",
                        "old_ip": old_ip,
                        "new_ip": new_ip,
                        "success": False,
                        "provider": self.provider.provider_name,
                    }
                )
        except Exception as e:
            self.logger.exception(f"Error updating IPv4 DNS record: {e}")

    async def _on_ipv6_change(self, new_ip: str, old_ip: Optional[str]) -> None:
        """Handle IPv6 address change.

        Args:
            new_ip: New IPv6 address
            old_ip: Previous IPv6 address
        """
        if not self.provider:
            return

        # Check if provider supports IPv6
        if not await self.provider.supports_ipv6():
            self.logger.warning(f"Provider {self.provider.provider_name} does not support IPv6")
            return

        self.logger.info(f"Updating IPv6 DNS record: {old_ip} -> {new_ip}")

        try:
            success = await self.provider.update_record(new_ip, record_type="AAAA")

            if success:
                self.last_ipv6_update = datetime.now()
                self._add_to_history(
                    {
                        "timestamp": self.last_ipv6_update,
                        "record_type": "AAAA",
                        "old_ip": old_ip,
                        "new_ip": new_ip,
                        "success": True,
                        "provider": self.provider.provider_name,
                    }
                )

                # Verify update
                await asyncio.sleep(5)  # Wait for DNS propagation
                verified = await self.provider.verify_record(new_ip)
                if verified:
                    self.logger.info(f"IPv6 DNS record verified: {new_ip}")
                else:
                    self.logger.warning(f"IPv6 DNS record verification failed for {new_ip}")
            else:
                self.logger.error(f"Failed to update IPv6 DNS record to {new_ip}")
                self._add_to_history(
                    {
                        "timestamp": datetime.now(),
                        "record_type": "AAAA",
                        "old_ip": old_ip,
                        "new_ip": new_ip,
                        "success": False,
                        "provider": self.provider.provider_name,
                    }
                )
        except Exception as e:
            self.logger.exception(f"Error updating IPv6 DNS record: {e}")

    def _add_to_history(self, entry: Dict[str, Any]) -> None:
        """Add entry to update history.

        Args:
            entry: Update history entry
        """
        self.update_history.append(entry)
        # Keep only last 100 entries
        if len(self.update_history) > 100:
            self.update_history = self.update_history[-100:]

    async def update_dns(
        self, ip_address: Optional[str] = None, record_type: str = "A", force: bool = False
    ) -> bool:
        """Manually update DNS record.

        Args:
            ip_address: IP address to update (auto-detect if None)
            record_type: 'A' for IPv4, 'AAAA' for IPv6
            force: Force update even if IP hasn't changed

        Returns:
            bool: True if update successful
        """
        if not self.provider:
            self.logger.error("No DDNS provider configured")
            return False

        # Auto-detect IP if not provided
        if ip_address is None:
            if record_type == "A":
                ip_address = await self.detector.get_public_ipv4()
            elif record_type == "AAAA":
                ip_address = await self.detector.get_public_ipv6()
            else:
                self.logger.error(f"Invalid record type: {record_type}")
                return False

        if not ip_address:
            self.logger.error(f"Could not detect {record_type} address")
            return False

        # Check if update needed
        if not force:
            if record_type == "A" and ip_address == self.detector.current_ipv4:
                self.logger.info(f"IPv4 address unchanged: {ip_address}")
                return True
            elif record_type == "AAAA" and ip_address == self.detector.current_ipv6:
                self.logger.info(f"IPv6 address unchanged: {ip_address}")
                return True

        # Perform update
        try:
            success = await self.provider.update_record(ip_address, record_type)

            if success:
                # Update detector state
                if record_type == "A":
                    self.detector.current_ipv4 = ip_address
                    self.last_ipv4_update = datetime.now()
                else:
                    self.detector.current_ipv6 = ip_address
                    self.last_ipv6_update = datetime.now()

                self.logger.info(f"Successfully updated {record_type} record to {ip_address}")
                return True
            else:
                self.logger.error(f"Failed to update {record_type} record to {ip_address}")
                return False

        except Exception as e:
            self.logger.exception(f"Error updating DNS: {e}")
            return False

    async def verify_dns(self, ip_address: str) -> bool:
        """Verify DNS record matches expected IP.

        Args:
            ip_address: Expected IP address

        Returns:
            bool: True if record matches
        """
        if not self.provider:
            self.logger.error("No DDNS provider configured")
            return False

        try:
            return await self.provider.verify_record(ip_address)
        except Exception as e:
            self.logger.exception(f"Error verifying DNS: {e}")
            return False

    async def start(self) -> None:
        """Start DDNS manager with automatic monitoring."""
        if not self.provider:
            self.logger.warning("Cannot start DDNS manager: no provider configured")
            return

        if not self.auto_update:
            self.logger.info("DDNS manager started (auto-update disabled)")
            return

        self.logger.info("Starting DDNS manager with automatic updates")

        # Start IP monitoring
        await self.detector.start_monitoring()

    async def stop(self) -> None:
        """Stop DDNS manager."""
        self.logger.info("Stopping DDNS manager")

        # Stop IP monitoring
        await self.detector.stop_monitoring()

    async def get_status(self) -> Dict[str, Any]:
        """Get current DDNS manager status.

        Returns:
            Dict with status information
        """
        detector_status = await self.detector.get_status()

        return {
            "enabled": self.provider is not None,
            "provider": self.provider.provider_name if self.provider else None,
            "auto_update": self.auto_update,
            "detector": detector_status,
            "last_ipv4_update": (
                self.last_ipv4_update.isoformat() if self.last_ipv4_update else None
            ),
            "last_ipv6_update": (
                self.last_ipv6_update.isoformat() if self.last_ipv6_update else None
            ),
            "update_history_size": len(self.update_history),
            "recent_updates": self.update_history[-5:] if self.update_history else [],
        }

    def get_recent_updates(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent update history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of update history entries
        """
        return self.update_history[-limit:] if self.update_history else []

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available DDNS providers.

        Returns:
            List of provider names
        """
        return list(cls.PROVIDERS.keys())

    @classmethod
    def get_provider_info(cls, provider_name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific provider.

        Args:
            provider_name: Provider name

        Returns:
            Dict with provider information or None
        """
        if provider_name not in cls.PROVIDERS:
            return None

        provider_class = cls.PROVIDERS[provider_name]
        return {
            "name": provider_name,
            "class": provider_class.__name__,
            "description": provider_class.__doc__ or "",
        }
