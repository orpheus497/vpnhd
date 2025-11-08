"""Phase implementations for VPNHD setup process."""

from .base import Phase, PhaseStatus
from .phase1_debian import Phase1Debian
from .phase2_wireguard_server import Phase2WireGuardServer
from .phase3_router import Phase3Router
from .phase4_linux_client import Phase4LinuxClient
from .phase5_linux_client_ondemand import Phase5LinuxClientOnDemand
from .phase6_mobile import Phase6Mobile
from .phase7_ssh_keys import Phase7SSHKeys
from .phase8_security import Phase8Security

__all__ = [
    "Phase",
    "PhaseStatus",
    "Phase1Debian",
    "Phase2WireGuardServer",
    "Phase3Router",
    "Phase4LinuxClient",
    "Phase5LinuxClientOnDemand",
    "Phase6Mobile",
    "Phase7SSHKeys",
    "Phase8Security",
]


def get_phase_class(phase_number: int):
    """
    Get phase class by number.

    Args:
        phase_number: Phase number (1-8)

    Returns:
        Phase class or None
    """
    phases = {
        1: Phase1Debian,
        2: Phase2WireGuardServer,
        3: Phase3Router,
        4: Phase4LinuxClient,
        5: Phase5LinuxClientOnDemand,
        6: Phase6Mobile,
        7: Phase7SSHKeys,
        8: Phase8Security,
    }

    return phases.get(phase_number)
