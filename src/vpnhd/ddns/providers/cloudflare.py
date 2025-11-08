"""Cloudflare DDNS provider implementation."""

import httpx
from typing import Optional, List, Dict, Any
from .base import DDNSProvider
from ...utils.logging import get_logger

logger = get_logger(__name__)


class CloudflareDDNS(DDNSProvider):
    """Cloudflare dynamic DNS provider using Cloudflare API v4."""

    API_BASE = "https://api.cloudflare.com/client/v4"

    @property
    def provider_name(self) -> str:
        return "cloudflare"

    def __init__(self, config_manager):
        """Initialize Cloudflare provider.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)
        self.api_token = self.config.get("server.ddns_api_token")
        self.zone_id = self.config.get("server.ddns_zone_id")
        self.record_name = self.config.get("server.ddns_domain")

        if not all([self.api_token, self.zone_id, self.record_name]):
            self.logger.warning("Cloudflare configuration incomplete")

    async def update_record(self, ip_address: str, record_type: str = 'A') -> bool:
        """Update Cloudflare DNS record.

        Args:
            ip_address: New IP address
            record_type: 'A' for IPv4, 'AAAA' for IPv6

        Returns:
            bool: True if update successful
        """
        if not all([self.api_token, self.zone_id, self.record_name]):
            self.logger.error("Cloudflare configuration incomplete")
            return False

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-Type': 'application/json'
                }

                # Get existing record
                list_url = f"{self.API_BASE}/zones/{self.zone_id}/dns_records"
                params = {'type': record_type, 'name': self.record_name}

                response = await client.get(list_url, headers=headers, params=params)
                response.raise_for_status()

                result = response.json()
                if not result.get('success'):
                    self.logger.error(f"Cloudflare API error: {result.get('errors')}")
                    return False

                records = result.get('result', [])

                data = {
                    'type': record_type,
                    'name': self.record_name,
                    'content': ip_address,
                    'ttl': 120,  # 2 minutes
                    'proxied': False  # Direct DNS, no Cloudflare proxy
                }

                if records:
                    # Update existing record
                    record_id = records[0]['id']
                    update_url = f"{self.API_BASE}/zones/{self.zone_id}/dns_records/{record_id}"

                    response = await client.put(update_url, headers=headers, json=data)
                    response.raise_for_status()

                    result = response.json()
                    if result.get('success'):
                        self.logger.info(
                            f"Cloudflare {record_type} record updated: "
                            f"{self.record_name} -> {ip_address}"
                        )
                        return True
                else:
                    # Create new record
                    create_url = f"{self.API_BASE}/zones/{self.zone_id}/dns_records"

                    response = await client.post(create_url, headers=headers, json=data)
                    response.raise_for_status()

                    result = response.json()
                    if result.get('success'):
                        self.logger.info(
                            f"Cloudflare {record_type} record created: "
                            f"{self.record_name} -> {ip_address}"
                        )
                        return True

                self.logger.error(f"Cloudflare update failed: {result.get('errors')}")
                return False

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Cloudflare HTTP error: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            self.logger.exception(f"Cloudflare DNS update failed: {e}")
            return False

    async def verify_record(self, expected_ip: str) -> bool:
        """Verify Cloudflare DNS record matches expected IP.

        Args:
            expected_ip: Expected IP address

        Returns:
            bool: True if record matches
        """
        try:
            # Use DNS resolution to verify
            import dns.resolver

            record_type = 'AAAA' if ':' in expected_ip else 'A'
            answers = dns.resolver.resolve(self.record_name, record_type)

            for rdata in answers:
                if str(rdata) == expected_ip:
                    self.logger.info(f"Cloudflare DNS record verified: {self.record_name} = {expected_ip}")
                    return True

            self.logger.warning(f"Cloudflare DNS record mismatch for {self.record_name}")
            return False
        except dns.resolver.NXDOMAIN:
            self.logger.error(f"Cloudflare DNS record not found: {self.record_name}")
            return False
        except Exception as e:
            self.logger.error(f"Cloudflare DNS verification failed: {e}")
            return False

    async def get_zone_id(self, domain: str) -> Optional[str]:
        """Get Cloudflare zone ID for a domain.

        Args:
            domain: Domain name

        Returns:
            Optional[str]: Zone ID or None if not found
        """
        if not self.api_token:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    'Authorization': f'Bearer {self.api_token}',
                    'Content-Type': 'application/json'
                }

                url = f"{self.API_BASE}/zones"
                params = {'name': domain}

                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                result = response.json()
                if result.get('success') and result.get('result'):
                    zone_id = result['result'][0]['id']
                    self.logger.info(f"Found Cloudflare zone ID for {domain}: {zone_id}")
                    return zone_id

                return None
        except Exception as e:
            self.logger.error(f"Failed to get Cloudflare zone ID: {e}")
            return None
