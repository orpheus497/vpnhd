"""Duck DNS provider implementation."""

import httpx
from typing import Optional
from .base import DDNSProvider
from ...utils.logging import get_logger

logger = get_logger(__name__)


class DuckDNS(DDNSProvider):
    """Duck DNS dynamic DNS provider (https://www.duckdns.org)."""

    API_BASE = "https://www.duckdns.org/update"

    @property
    def provider_name(self) -> str:
        return "duckdns"

    def __init__(self, config_manager):
        """Initialize Duck DNS provider.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)
        self.api_token = self.config.get("server.ddns_api_token")
        self.domain = self.config.get("server.ddns_domain")

        # Duck DNS uses subdomains (e.g., "myhost" for "myhost.duckdns.org")
        if self.domain and self.domain.endswith('.duckdns.org'):
            self.subdomain = self.domain.replace('.duckdns.org', '')
        else:
            self.subdomain = self.domain

        if not all([self.api_token, self.subdomain]):
            self.logger.warning("Duck DNS configuration incomplete")

    async def update_record(self, ip_address: str, record_type: str = 'A') -> bool:
        """Update Duck DNS record.

        Duck DNS automatically detects IPv4/IPv6 based on the request source,
        or you can specify ip= (IPv4) or ipv6= (IPv6) parameters.

        Args:
            ip_address: New IP address
            record_type: 'A' for IPv4, 'AAAA' for IPv6

        Returns:
            bool: True if update successful
        """
        if not all([self.api_token, self.subdomain]):
            self.logger.error("Duck DNS configuration incomplete")
            return False

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params = {
                    'domains': self.subdomain,
                    'token': self.api_token,
                    'verbose': 'true'
                }

                # Add IP parameter based on record type
                if record_type == 'AAAA':
                    params['ipv6'] = ip_address
                else:
                    params['ip'] = ip_address

                response = await client.get(self.API_BASE, params=params)
                response.raise_for_status()

                # Duck DNS returns "OK" or "KO" followed by details
                result = response.text.strip()

                if result.startswith('OK'):
                    self.logger.info(
                        f"Duck DNS {record_type} record updated: "
                        f"{self.subdomain}.duckdns.org -> {ip_address}"
                    )
                    return True
                else:
                    self.logger.error(f"Duck DNS update failed: {result}")
                    return False

        except Exception as e:
            self.logger.exception(f"Duck DNS update failed: {e}")
            return False

    async def verify_record(self, expected_ip: str) -> bool:
        """Verify Duck DNS record matches expected IP.

        Args:
            expected_ip: Expected IP address

        Returns:
            bool: True if record matches
        """
        try:
            import dns.resolver

            domain = f"{self.subdomain}.duckdns.org"
            record_type = 'AAAA' if ':' in expected_ip else 'A'

            answers = dns.resolver.resolve(domain, record_type)

            for rdata in answers:
                if str(rdata) == expected_ip:
                    self.logger.info(f"Duck DNS record verified: {domain} = {expected_ip}")
                    return True

            self.logger.warning(f"Duck DNS record mismatch for {domain}")
            return False
        except Exception as e:
            self.logger.error(f"Duck DNS verification failed: {e}")
            return False

    async def supports_ipv6(self) -> bool:
        """Check if Duck DNS supports IPv6.

        Returns:
            bool: True (Duck DNS supports both IPv4 and IPv6)
        """
        return True

    async def clear_ip(self, record_type: str = 'A') -> bool:
        """Clear Duck DNS IP address (set to empty).

        Args:
            record_type: 'A' for IPv4, 'AAAA' for IPv6

        Returns:
            bool: True if successful
        """
        if not all([self.api_token, self.subdomain]):
            self.logger.error("Duck DNS configuration incomplete")
            return False

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params = {
                    'domains': self.subdomain,
                    'token': self.api_token,
                    'clear': 'true',
                    'verbose': 'true'
                }

                response = await client.get(self.API_BASE, params=params)
                response.raise_for_status()

                result = response.text.strip()

                if result.startswith('OK'):
                    self.logger.info(f"Duck DNS {record_type} record cleared")
                    return True
                else:
                    self.logger.error(f"Duck DNS clear failed: {result}")
                    return False

        except Exception as e:
            self.logger.exception(f"Duck DNS clear failed: {e}")
            return False
