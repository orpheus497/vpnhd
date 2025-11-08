# VPNHD - VPN Helper Daemon

**Automate your privacy-focused home VPN setup**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FOSS](https://img.shields.io/badge/FOSS-100%25-green.svg)](https://www.gnu.org/philosophy/free-sw.html)

## Overview

VPNHD is an interactive command-line tool that automates the complete setup of a privacy-focused home VPN system using WireGuard. Born from a comprehensive step-by-step VPN setup guide, VPNHD transforms a complex, multi-phase manual process into an automated, beginner-friendly experience.

### Why VPNHD?

- **Privacy-First**: Zero external dependencies, no cloud services, no telemetry
- **FOSS-Only**: 100% Free and Open Source Software ecosystem
- **Beginner-Friendly**: Clear explanations, ELI5 messaging, guided setup
- **Production-Ready**: Complete error handling, validation, and rollback mechanisms
- **Self-Contained**: No external APIs or coordination servers required
- **Hardware-Agnostic**: Works with any x86_64 hardware

## Features

### Automated VPN Setup (8 Phases)

1. **Phase 1: Debian Server Installation** - Guided Debian installation and validation
2. **Phase 2: WireGuard Server** - Complete WireGuard server configuration
3. **Phase 3: Router Port Forwarding** - Assisted router configuration
4. **Phase 4: Fedora Client** - Always-on VPN client setup
5. **Phase 5: Pop!_OS Client** - On-demand, isolated client setup
6. **Phase 6: Termux/Android** - Mobile device configuration with QR codes
7. **Phase 7: SSH Keys** - Key-based authentication setup
8. **Phase 8: Security Hardening** - UFW firewall and fail2ban configuration

### Key Capabilities

- **Network Discovery**: Automatic network interface and configuration detection
- **Key Management**: Secure WireGuard and SSH key generation
- **Configuration Templates**: Jinja2-based configuration rendering
- **Progress Tracking**: Visual progress indicators and phase completion tracking
- **Rollback Support**: Automatic rollback on errors
- **Comprehensive Validation**: Input validation for IPs, hostnames, networks
- **Interactive UI**: Rich terminal interface with menus and help
- **Detailed Logging**: Complete logging for troubleshooting

## Installation

### System Requirements

- **Server**: Debian 12+ (Bookworm) x86_64
- **Clients**: Fedora, Pop!_OS, or Android (Termux)
- **Python**: 3.10 or higher
- **Root Access**: Required for system configuration

### Quick Install

```bash
# Clone the repository
git clone https://github.com/orpheus497/vpnhd.git
cd vpnhd

# Run the installation script
sudo bash scripts/install.sh

# Or install manually
pip install -r requirements.txt
python setup.py install
```

### Dependencies

VPNHD requires the following system packages:

- `wireguard-tools` - WireGuard VPN
- `openssh-client` - SSH connectivity
- `ufw` - Uncomplicated Firewall
- `fail2ban` - Intrusion prevention
- `python3-pip` - Python package manager

Python dependencies are automatically installed from `requirements.txt`.

## Quick Start

### First-Time Setup

```bash
# Start VPNHD
sudo vpnhd

# Follow the interactive prompts:
# 1. Select "Continue to next phase"
# 2. Complete Phase 1 (Debian server validation)
# 3. Continue through remaining phases
```

### Main Menu

```
╔══════════════════════════════════════════════════════════╗
║                 VPNHD - VPN Helper Daemon                 ║
║               Privacy-First Home VPN Setup                ║
╚══════════════════════════════════════════════════════════╝

Main Menu:
  [1] Continue to next phase
  [2] Jump to specific phase
  [3] Review configuration
  [4] Show phase details
  [5] Troubleshooting
  [6] View guide documentation
  [7] Exit
```

## Usage

### Basic Usage

```bash
# Start interactive setup
sudo vpnhd

# Continue from where you left off
sudo vpnhd --continue

# Jump to specific phase
sudo vpnhd --phase 2

# Review current configuration
sudo vpnhd --review

# Show help
vpnhd --help
```

### Configuration

VPNHD stores configuration in `~/.config/vpnhd/config.json`. This includes:

- Network settings (LAN and VPN subnets)
- Server information (hostname, IP, MAC address)
- Client configurations (Fedora, Pop!_OS, Termux)
- Security settings (SSH keys, firewall status)
- Phase completion status

### Example Workflow

1. **Install Debian server** (Phase 1)
2. **Configure WireGuard server** (Phase 2)
3. **Set up router port forwarding** (Phase 3)
4. **Connect Fedora laptop** (Phase 4)
5. **Connect Pop!_OS laptop** (Phase 5)
6. **Connect Android phone** (Phase 6)
7. **Enable SSH keys** (Phase 7)
8. **Harden security** (Phase 8)

Each phase guides you through the process with clear explanations and validation.

## Architecture

### Project Structure

```
vpnhd/
├── src/vpnhd/          # Main application package
│   ├── cli.py          # CLI entry point
│   ├── ui/             # User interface module
│   ├── config/         # Configuration management
│   ├── phases/         # Phase implementations
│   ├── network/        # Network utilities
│   ├── crypto/         # Cryptography (WireGuard, SSH)
│   ├── system/         # System commands and services
│   └── utils/          # General utilities
├── tests/              # Test suite
├── docs/               # User documentation
└── scripts/            # Helper scripts
```

### Technology Stack

- **Python 3.10+** - Core application
- **Rich** - Terminal UI and formatting
- **Click** - CLI framework
- **Jinja2** - Configuration templating
- **WireGuard** - VPN protocol
- **OpenSSH** - Secure remote access
- **UFW** - Firewall management
- **fail2ban** - Intrusion prevention

## Requirements

### Minimum System Requirements

- **CPU**: Any x86_64 processor
- **RAM**: 512MB minimum (1GB recommended)
- **Storage**: 8GB minimum
- **Network**: Ethernet connection (Wi-Fi supported but not recommended for server)

### Network Requirements

- **Static IP**: Server should have static local IP
- **Router Access**: Ability to configure port forwarding
- **Public IP**: Required for external VPN access (dynamic DNS supported)

### Knowledge Requirements

- **None!** VPNHD is designed for complete beginners
- ELI5 explanations for all concepts
- Step-by-step guidance throughout
- Comprehensive troubleshooting documentation

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete walkthrough
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ](docs/FAQ.md)** - Frequently asked questions
- **[Contributing](docs/CONTRIBUTING.md)** - Contribution guidelines

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on:

- Code of conduct
- Development setup
- Testing requirements
- Pull request process
- Coding standards

## Credits

### Project Team

- **Author**: orpheus497

### Acknowledgments

This project automates the comprehensive VPN setup guide created by orpheus497. The guide represents months of research, testing, and documentation to create the most beginner-friendly, privacy-focused home VPN setup available.

### FOSS Attribution

This project is built entirely with Free and Open Source Software:

- **Python** - Python Software Foundation License
- **WireGuard** - GPL-2.0 License
- **Debian Linux** - Multiple FOSS licenses
- **Rich** - MIT License
- **Click** - BSD License
- **PyYAML** - MIT License
- **Jinja2** - BSD License
- **jsonschema** - MIT License
- **netifaces** - MIT License
- **UFW** - GPL-3.0 License
- **fail2ban** - GPL-2.0 License
- **OpenSSH** - BSD License

We are grateful to the maintainers and contributors of these projects.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

See [LICENSE](LICENSE) for the full license text.

### What This Means

- **Freedom to use**: Use VPNHD for any purpose
- **Freedom to study**: Access and study the source code
- **Freedom to modify**: Modify the code to suit your needs
- **Freedom to share**: Redistribute copies to help others
- **Copyleft**: Derivative works must also be GPL-3.0

### Why GPL-3.0?

We chose GPL-3.0 to ensure VPNHD remains free and open source forever, protecting user privacy and freedom.

## Support

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/orpheus497/vpnhd/issues)
- **Documentation**: [docs/](docs/)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **FAQ**: [docs/FAQ.md](docs/FAQ.md)

### Reporting Bugs

Please report bugs via GitHub Issues with:

1. VPNHD version (`vpnhd --version`)
2. Operating system and version
3. Steps to reproduce
4. Expected vs actual behavior
5. Relevant log files (`~/.config/vpnhd/logs/`)

### Security Issues

For security-related issues, please contact the maintainers directly rather than creating public issues.

## Roadmap

### Version 1.0.0 (Current)

- Complete 8-phase VPN setup automation
- Interactive terminal UI
- Configuration management
- All core features implemented

### Future Enhancements

- IPv6 support
- Additional client OS support (macOS, Windows)
- Web-based management interface (optional)
- Automated backup and restore
- VPN performance monitoring
- Multi-server support
- Dynamic DNS integration

## Philosophy

VPNHD is built on core principles:

1. **Privacy is a right, not a privilege**
2. **Free software protects freedom**
3. **Simplicity empowers users**
4. **Open source builds trust**
5. **Security through transparency**

---

**Made with privacy, for privacy.**

**Version 1.0.0** | **November 8, 2025**
