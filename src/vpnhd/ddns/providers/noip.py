"""No-IP DDNS provider implementation."""

import httpx
import base64
from typing import Optional
from .base import DDNSProvider
from ...utils.logging import get_logger

logger = get_logger(__name__)


class NoIPDDNS(DDNSProvider):
    """No-IP dynamic DNS provider (https://www.noip.com)."""

    API_BASE = "https://dynupdate.no-ip.com/nic/update"

    @property
    def provider_name(self) -> str:
        return "noip"

    def __init__(self, config_manager):
        """Initialize No-IP provider.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)
        self.username = self.config.get("server.ddns_username")
        self.password = self.config.get("server.ddns_password")
        self.hostname = self.config.get("server.ddns_domain")

        if not all([self.username, self.password, self.hostname]):
            self.logger.warning("No-IP configuration incomplete")

    async def update_record(self, ip_address: str, record_type: str = "A") -> bool:
        """Update No-IP DNS record.

        No-IP uses HTTP Basic Authentication and a simple update URL.

        Args:
            ip_address: New IP address
            record_type: 'A' for IPv4, 'AAAA' for IPv6

        Returns:
            bool: True if update successful
        """
        if not all([self.username, self.password, self.hostname]):
            self.logger.error("No-IP configuration incomplete")
            return False

        # No-IP primarily supports IPv4; IPv6 support varies by plan
        if record_type == "AAAA":
            self.logger.warning("No-IP IPv6 support may be limited depending on your plan")

        try:
            # Create HTTP Basic Auth header
            credentials = f"{self.username}:{self.password}"
            auth_token = base64.b64encode(credentials.encode()).decode()

            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    "Authorization": f"Basic {auth_token}",
                    "User-Agent": "VPNHD/2.0.0 no-ip-client",
                }

                params = {"hostname": self.hostname, "myip": ip_address}

                response = await client.get(self.API_BASE, headers=headers, params=params)

                # No-IP returns specific response codes
                result = response.text.strip()

                # Parse response
                if result.startswith("good") or result.startswith("nochg"):
                    # good: Update successful
                    # nochg: IP address is current
                    self.logger.info(
                        f"No-IP {record_type} record updated: "
                        f"{self.hostname} -> {ip_address} ({result})"
                    )
                    return True
                elif result == "nohost":
                    self.logger.error(f"No-IP error: Hostname {self.hostname} does not exist")
                    return False
                elif result == "badauth":
                    self.logger.error("No-IP error: Invalid username or password")
                    return False
                elif result == "badagent":
                    self.logger.error("No-IP error: Bad user agent")
                    return False
                elif result == "!donator":
                    self.logger.error("No-IP error: Feature requires paid account")
                    return False
                elif result == "abuse":
                    self.logger.error("No-IP error: Account blocked due to abuse")
                    return False
                elif result.startswith("911"):
                    self.logger.error("No-IP error: System error, try again later")
                    return False
                else:
                    self.logger.error(f"No-IP update failed: {result}")
                    return False

        except Exception as e:
            self.logger.exception(f"No-IP DNS update failed: {e}")
            return False

    async def verify_record(self, expected_ip: str) -> bool:
        """Verify No-IP DNS record matches expected IP.

        Args:
            expected_ip: Expected IP address

        Returns:
            bool: True if record matches
        """
        try:
            import dns.resolver

            record_type = "AAAA" if ":" in expected_ip else "A"
            answers = dns.resolver.resolve(self.hostname, record_type)

            for rdata in answers:
                if str(rdata) == expected_ip:
                    self.logger.info(f"No-IP DNS record verified: {self.hostname} = {expected_ip}")
                    return True

            self.logger.warning(f"No-IP DNS record mismatch for {self.hostname}")
            return False
        except Exception as e:
            self.logger.error(f"No-IP DNS verification failed: {e}")
            return False

    async def supports_ipv6(self) -> bool:
        """Check if No-IP supports IPv6.

        Returns:
            bool: Limited IPv6 support (depends on plan)
        """
        # No-IP has limited IPv6 support depending on the plan
        return False

    async def get_current_ip(self) -> Optional[str]:
        """Get current IP address registered with No-IP.

        This can be done by querying DNS for the hostname.

        Returns:
            Optional[str]: Current IP address or None
        """
        try:
            import dns.resolver

            answers = dns.resolver.resolve(self.hostname, "A")

            for rdata in answers:
                ip = str(rdata)
                self.logger.info(f"No-IP current IP: {ip}")
                return ip

            return None
        except Exception as e:
            self.logger.error(f"Failed to get current No-IP IP: {e}")
            return None
