# VPNHD - VPN Helper Daemon

**Automate your privacy-focused home VPN setup**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Debian 13](https://img.shields.io/badge/debian-12%20|%2013-red.svg)](https://www.debian.org/)
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
4. **Phase 4: Linux Desktop Client (Always-On)** - Configure Linux desktop/laptop for always-on VPN (Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, etc.)
5. **Phase 5: Linux Desktop Client (On-Demand)** - Configure Linux desktop/laptop for on-demand VPN with isolation
6. **Phase 6: Mobile Client (Android/iOS)** - Mobile device configuration with QR codes for easy setup
7. **Phase 7: SSH Keys** - Automated key-based authentication setup with password auth disable
8. **Phase 8: Security Hardening** - UFW firewall and fail2ban with custom jails for SSH and WireGuard

### Key Capabilities

- **Network Discovery**: Automatic network interface and configuration detection using psutil
- **Key Management**: Secure WireGuard and SSH key generation
- **Configuration Templates**: Jinja2-based configuration rendering
- **Progress Tracking**: Visual progress indicators and phase completion tracking
- **Rollback Support**: Automatic rollback on errors
- **Comprehensive Validation**: Input validation for IPs, hostnames, networks
- **Interactive UI**: Rich terminal interface with menus and help
- **Detailed Logging**: Complete logging for troubleshooting

### Enterprise Features

- **Client Management**: Comprehensive client database with metadata tracking (device type, OS, connection status)
- **Performance Testing**: Latency, stability, and bandwidth testing with historical reporting
- **Backup & Restore**: Automated configuration backups with SHA-256 checksum verification
- **CI/CD Pipeline**: GitHub Actions workflows for automated testing and validation
- **Modern Dependencies**: Pure Python implementation with no external binary dependencies
- **Security Scanning**: Automated security analysis with Bandit and CodeQL

## Installation

### System Requirements

- **Server**: Debian 12 (Bookworm) or Debian 13 (Trixie) x86_64
- **Desktop Clients**: Any modern Linux distribution (Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, Linux Mint, Arch, Manjaro, etc.)
- **Mobile Clients**: Android or iOS devices
- **Python**: 3.11 or higher (required for Debian 13 compatibility)
- **Root Access**: Required for system configuration

**Note**: Python 3.11+ is required to ensure compatibility with Debian 13 (Trixie). Debian 12 (Bookworm) users should verify their Python version meets this requirement.

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

## Debian 13 (Trixie) Compatibility

VPNHD fully supports Debian 13 (Trixie), the latest stable release of Debian Linux.

### Key Compatibility Features

- **Native Debian 13 Support**: Full compatibility with Debian 13 (Trixie) and Debian 12 (Bookworm)
- **Python 3.11+ Requirement**: Updated minimum Python version to 3.11 for Debian 13 compatibility
- **Version Detection**: Automatic detection and validation of Debian 12 or 13
- **Package Management**: Updated package installation for both Debian releases
- **Security Hardening**: All security features fully compatible with Debian 13

### Upgrading from Debian 12 to Debian 13

If you're upgrading your server from Debian 12 to Debian 13:

1. **Verify Python Version**: Ensure Python 3.11+ is installed
   ```bash
   python3 --version  # Should show 3.11 or higher
   ```

2. **No VPNHD Changes Required**: VPNHD automatically detects the Debian version

3. **Test Your Configuration**: After OS upgrade, verify VPN connectivity
   ```bash
   sudo vpnhd --review  # Review current configuration
   ```

### Version-Specific Notes

- **Debian 12 (Bookworm)**: Fully supported, requires Python 3.11+
- **Debian 13 (Trixie)**: Fully supported, Python 3.11+ included by default
- **Debian 11 (Bullseye)**: No longer supported (use VPNHD v1.0 for Debian 11)

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
4. **Connect Linux desktop (always-on mode)** (Phase 4)
5. **Connect Linux laptop (on-demand mode)** (Phase 5)
6. **Connect mobile device via QR code** (Phase 6)
7. **Enable SSH key authentication** (Phase 7)
8. **Harden security with firewall and intrusion prevention** (Phase 8)

Each phase guides you through the process with clear explanations and validation.

## CLI Reference

### Main Application

```bash
# Start interactive setup
vpnhd

# Show version
vpnhd --version

# Continue from last phase
vpnhd --continue

# Jump to specific phase
vpnhd --phase <number>

# Review configuration
vpnhd --review
```

### Client Management

```bash
# List all clients
vpnhd client list [--enabled] [--device-type desktop|mobile|server] [--format table|json|simple]

# Add new client
vpnhd client add <name> [--description TEXT] [--device-type desktop|mobile|server]
                        [--os TEXT] [--vpn-ip IP] [--generate-qr]

# Show client details
vpnhd client show <name>

# Get client connection status
vpnhd client status <name>

# Export client configuration
vpnhd client export <name> <output-file> [--qr] [--format wireguard|qrcode|json]

# Enable/disable client
vpnhd client enable <name>
vpnhd client disable <name>

# Remove client
vpnhd client remove <name> [--force]

# Show client statistics
vpnhd client stats
```

### Performance Testing

```bash
# Test latency
vpnhd performance latency [--count 10] [--timeout 5] [--server IP]

# Test connection stability
vpnhd performance stability [--duration 300] [--interval 1] [--server IP]

# Run full performance test suite
vpnhd performance full [--bandwidth] [--iperf-server IP] [--latency-count 20]
                       [--stability-duration 60]

# List performance reports
vpnhd performance list [--limit 10]

# Show performance statistics
vpnhd performance stats
```

### Backup & Restore

```bash
# Create backup
vpnhd backup create [--description TEXT] [--no-wireguard] [--no-ssh]
                    [--no-config] [--no-clients]

# List all backups
vpnhd backup list [--format table|json]

# Restore from backup
vpnhd backup restore <backup-id> [--no-wireguard] [--no-ssh] [--no-config]
                                  [--no-clients] [--skip-verify]

# Verify backup integrity
vpnhd backup verify <backup-id>

# Delete backup
vpnhd backup delete <backup-id> [--force]

# Export backup to external location
vpnhd backup export <backup-id> <destination>

# Import backup from external location
vpnhd backup import <source-path>

# Clean up old backups
vpnhd backup cleanup [--keep 10]
```

For detailed command documentation, see [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md).

## Architecture

### Project Structure

```
vpnhd/
├── src/vpnhd/          # Main application package
│   ├── cli.py          # CLI entry point with command groups
│   ├── ui/             # User interface module
│   ├── config/         # Configuration management
│   ├── phases/         # Phase implementations
│   ├── network/        # Network utilities (psutil-based)
│   ├── crypto/         # Cryptography (WireGuard, SSH, QR codes)
│   ├── system/         # System commands and services
│   ├── client/         # Client management system
│   ├── testing/        # Performance testing module
│   ├── backup/         # Backup and restore module
│   └── utils/          # General utilities
├── tests/              # Test suite with pytest
├── docs/               # User documentation
├── scripts/            # Helper scripts
└── .github/            # CI/CD workflows
```

### Technology Stack

- **Python 3.11+** - Core application (Debian 13 compatible)
- **Rich** - Terminal UI and formatting
- **Click** - CLI framework and command groups
- **Jinja2** - Configuration templating
- **psutil** - Cross-platform network interface discovery
- **qrcode[pil]** - Pure Python QR code generation
- **WireGuard** - VPN protocol
- **OpenSSH** - Secure remote access
- **UFW** - Firewall management
- **fail2ban** - Intrusion prevention
- **pytest** - Testing framework
- **GitHub Actions** - CI/CD automation

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

### User Guides
- **[User Guide](docs/USER_GUIDE.md)** - Complete walkthrough
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Comprehensive command documentation
- **[Client Management](docs/CLIENT_MANAGEMENT.md)** - Client management guide with examples
- **[Performance Testing](docs/PERFORMANCE_TESTING.md)** - Performance testing and monitoring guide
- **[Backup & Restore](docs/BACKUP_RESTORE.md)** - Backup and disaster recovery guide

### Reference
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
- **psutil** - BSD License
- **qrcode** - BSD License
- **Pillow** - HPND License
- **pytest** - MIT License
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

### Version 2.0.0 (Current - Modernization Release)

- ✅ Complete 8-phase VPN setup automation
- ✅ Interactive terminal UI
- ✅ Configuration management
- ✅ **CI/CD Pipeline** - Automated testing, security scanning, and validation
- ✅ **Modern Dependencies** - Pure Python implementation (psutil, qrcode)
- ✅ **Client Management** - Comprehensive client database with metadata tracking
- ✅ **Performance Testing** - Latency, stability, and bandwidth monitoring
- ✅ **Automated Backup & Restore** - SHA-256 verified configuration backups
- ✅ **Enhanced Documentation** - Complete CLI reference and usage guides

### Future Enhancements

- IPv6 support
- Additional client OS support (macOS, Windows)
- Web-based management interface (optional)
- Multi-server support
- Dynamic DNS integration
- Automated update system
- Multi-language support

## Philosophy

VPNHD is built on core principles:

1. **Privacy is a right, not a privilege**
2. **Free software protects freedom**
3. **Simplicity empowers users**
4. **Open source builds trust**
5. **Security through transparency**

---

**Made with privacy, for privacy.**

**Version 2.0.0** | **November 8, 2025**
