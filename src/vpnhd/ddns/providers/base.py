"""Base interface for DDNS providers."""

from abc import ABC, abstractmethod

from ...utils.logging import get_logger

logger = get_logger(__name__)


class DDNSProvider(ABC):
    """Abstract base class for DDNS providers."""

    def __init__(self, config_manager):
        """Initialize provider with config manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = logger

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass

    @abstractmethod
    async def update_record(self, ip_address: str, record_type: str = "A") -> bool:
        """Update DNS record with new IP address.

        Args:
            ip_address: New IP address
            record_type: DNS record type ('A' for IPv4, 'AAAA' for IPv6)

        Returns:
            bool: True if update successful
        """
        pass

    @abstractmethod
    async def verify_record(self, expected_ip: str) -> bool:
        """Verify DNS record matches expected IP.

        Args:
            expected_ip: Expected IP address

        Returns:
            bool: True if record matches
        """
        pass

    async def supports_ipv6(self) -> bool:
        """Check if provider supports IPv6 (AAAA records).

        Returns:
            bool: True if IPv6 is supported
        """
        # Default implementation - providers can override
        return True
