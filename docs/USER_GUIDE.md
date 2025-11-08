# VPNHD User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Phase-by-Phase Walkthrough](#phase-by-phase-walkthrough)
4. [Configuration Guide](#configuration-guide)
5. [Command Reference](#command-reference)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

## Introduction

VPNHD (VPN Helper Daemon) is a comprehensive, interactive tool designed to automate the setup of a privacy-focused home VPN system. It guides you through 8 sequential phases, from initial server installation through security hardening.

### Who Should Use This Guide

This guide is for anyone who wants to set up a home VPN but lacks advanced networking or system administration knowledge. VPNHD handles the complexity while keeping you informed every step of the way.

### What You'll Learn

By completing VPNHD setup, you'll understand:

- How VPN networks work in practice
- WireGuard configuration fundamentals
- Network routing and forwarding
- Firewall security principles
- SSH key-based authentication
- System hardening best practices

### Time Estimate

- **First-time setup**: 4-6 hours (spread across multiple sessions)
- **Phase 1 (Server)**: 1-2 hours
- **Phases 2-3 (WireGuard)**: 1-2 hours
- **Phases 4-6 (Clients)**: 1-2 hours
- **Phases 7-8 (Security)**: 1-2 hours

## Getting Started

### System Requirements

#### Server Requirements
- **OS**: Debian 12+ (Bookworm) x86_64
- **CPU**: Any modern x86_64 processor (ARM not supported in v1.0.0)
- **RAM**: 512MB minimum (1GB recommended)
- **Storage**: 8GB minimum free space
- **Network**: Static local IP address (DHCP reservation)
- **Internet**: Broadband connection with port forwarding capability

#### Client Requirements
- **Fedora Client**: Fedora 38+ (always-on admin machine)
- **Pop!_OS Client**: Pop!_OS 22.04+ (on-demand isolated machine)
- **Android Client**: Android 8+ with Termux app
- **Network**: Same local network as server (for setup phase)

### Pre-Installation Checklist

Before starting VPNHD, ensure you have:

- [ ] Administrator access to your router
- [ ] At least 2 machines for setup (1 server, 1+ clients)
- [ ] A dedicated machine for the server (can be repurposed hardware)
- [ ] Debian 12 installation media or USB drive
- [ ] Python 3.10 or higher installed
- [ ] Stable internet connection
- [ ] Ethernet connection for server (recommended)

### Installation

#### Quick Installation (Automated)

```bash
# Clone the repository
git clone https://github.com/orpheus497/vpnhd.git
cd vpnhd

# Run installer as root
sudo bash scripts/install.sh

# Verify installation
vpnhd --help
```

#### Manual Installation

```bash
# Install system dependencies
sudo apt update
sudo apt install -y wireguard-tools openssh-client ufw fail2ban python3-pip

# Install Python dependencies
pip install -r requirements.txt

# Install VPNHD
sudo python3 setup.py install

# Verify
vpnhd --help
```

### First Launch

```bash
# Start VPNHD
sudo vpnhd

# You'll see the main menu:
# [1] Continue to next phase
# [2] Jump to specific phase
# [3] Review configuration
# [4] Show phase details
# [5] Troubleshooting
# [6] View guide documentation
# [7] Exit
```

## Phase-by-Phase Walkthrough

### Phase 1: Debian Server Installation

**Goal**: Install and validate a Debian 12 server with SSH enabled

**Overview**:
- Validate current machine is running Debian
- Verify SSH is enabled
- Check system requirements
- Create initial configuration

**What Happens**:

1. VPNHD checks if your machine is running Debian 12+
2. Verifies SSH is installed and running
3. Gathers system information (hostname, IP, network interfaces)
4. Validates hardware meets minimum requirements
5. Creates initial configuration file

**If You're Starting Fresh**:

If you don't yet have Debian installed, VPNHD will guide you through the installation process:

1. Boot from Debian 12 installation media
2. Follow the graphical installer
3. Key settings:
   - Use the entire disk (VPNHD assumes dedicated hardware)
   - Configure network with DHCP (you'll set static IP later)
   - **IMPORTANT**: Enable SSH server during software selection
   - Create a user account for day-to-day use

After Debian installation, run `sudo vpnhd` again to proceed with Phase 1 validation.

**Key Information Needed**:

- Server hostname (e.g., `vpn-server`)
- Server's local IP address (will be auto-detected)
- Network interface name (will be auto-detected)
- Root/sudo access confirmation

**Exit Criteria**:

Phase 1 is complete when:
- Debian 12+ is installed and running
- SSH is confirmed enabled and accessible
- System meets minimum requirements
- Initial configuration is saved

### Phase 2: WireGuard Server Setup

**Goal**: Install and configure WireGuard server for VPN connectivity

**Overview**:
- Install WireGuard tools
- Generate server key pair
- Create server configuration
- Enable IP forwarding
- Configure NAT/masquerading

**What Happens**:

1. VPNHD checks and installs WireGuard tools
2. Generates secure cryptographic keys for the server
3. Creates the WireGuard configuration file
4. Enables kernel IP forwarding
5. Starts the WireGuard service
6. Tests connectivity and logs results

**Key Concepts** (ELI5):

- **WireGuard**: Software that creates a secure tunnel between your server and clients
- **Key Pair**: Two related files (public and private) that identify the server securely
- **IP Forwarding**: Tells the kernel to pass traffic between clients
- **Masquerading**: Makes it look like traffic comes from the server itself

**Key Information Needed**:

- VPN subnet range (default: `10.0.0.0/24` - you can customize)
- Server's listening port (default: `51820` - can customize)
- Network interface to use (auto-detected)

**Configuration Details**:

```
VPN Subnet: 10.0.0.0/24
  Server Address: 10.0.0.1/24
  Client Range: 10.0.0.2 - 10.0.0.254

WireGuard Port: 51820 (UDP)
Network Interface: eth0 (or your interface)
```

**Exit Criteria**:

Phase 2 is complete when:
- WireGuard is installed and running
- Server configuration is saved
- IP forwarding is enabled
- Service is listening on the configured port

### Phase 3: Router Port Forwarding

**Goal**: Configure router to forward VPN traffic to the server

**Overview**:
- Provide router configuration instructions
- Confirm port forwarding is active
- Test external connectivity

**What Happens**:

1. VPNHD determines your server's public IP
2. Guides you through router configuration
3. Waits while you configure port forwarding
4. Tests that the port is accessible externally
5. Confirms successful setup

**Router Configuration Steps**:

1. Access your router's web interface (typically `192.168.1.1` or `192.168.0.1`)
2. Find Port Forwarding settings (usually under Advanced or NAT)
3. Create a new port forward:
   - External Port: `51820`
   - Internal IP: Your server's local IP (e.g., `192.168.1.10`)
   - Internal Port: `51820`
   - Protocol: UDP
4. Save and apply settings

**Exit Criteria**:

Phase 3 is complete when:
- External port forwarding is confirmed active
- VPNHD can reach the server from outside
- Connection test succeeds

### Phase 4: Fedora Client Setup (Always-On)

**Goal**: Configure Fedora as always-on VPN admin client

**Overview**:
- Install WireGuard on Fedora machine
- Generate client key pair
- Create client configuration
- Configure auto-start on boot
- Test connectivity

**What Happens**:

1. VPNHD generates a new client key pair
2. Creates client configuration with server's public information
3. Provides QR code for easy setup (can be scanned by other devices)
4. Guides you through Fedora WireGuard installation
5. Configures auto-start
6. Tests connection

**Usage Pattern**:

- This machine stays connected to VPN at all times
- Use it to manage other systems remotely
- Acts as an admin/control center
- Should be a dedicated machine or primary workstation

**Key Information Needed**:

- Which Fedora machine to configure
- Network interface name on Fedora (usually `eth0` or `wlan0`)
- Client IP assignment (auto-assigned by VPNHD)

**Configuration Steps**:

1. VPNHD generates unique configuration for Fedora
2. Provides instructions for installing WireGuard on Fedora
3. Shows how to enable and start the VPN
4. Explains how to verify connection

**Exit Criteria**:

Phase 4 is complete when:
- WireGuard is installed on Fedora
- Client can ping server's VPN address (10.0.0.1)
- Client can reach other clients through VPN
- Connection persists across reboots (if auto-start configured)

### Phase 5: Pop!_OS Client Setup (On-Demand)

**Goal**: Configure Pop!_OS as on-demand, isolated VPN client

**Overview**:
- Install WireGuard on Pop!_OS machine
- Generate client key pair
- Create client configuration
- Configure on-demand activation only
- Test connectivity and isolation

**What Happens**:

1. VPNHD generates second client key pair
2. Creates client configuration for Pop!_OS
3. Provides QR code for optional Android setup
4. Guides through Pop!_OS WireGuard installation
5. Configures NOT to auto-start (on-demand only)
6. Tests connection and isolation

**Usage Pattern**:

- This machine connects to VPN only when explicitly enabled
- Used for sensitive activities or testing
- Network-isolated from Fedora when not connected
- Can safely browse without VPN when disconnected

**Key Differences from Phase 4**:

- **Not** configured for auto-start
- User manually connects when needed
- Provides isolation without full-time VPN commitment
- Useful for privacy-sensitive applications

**Exit Criteria**:

Phase 5 is complete when:
- WireGuard is installed on Pop!_OS
- Client configuration exists and can connect
- Connection can be manually started and stopped
- Isolation works as expected

### Phase 6: Android/Termux Client Setup

**Goal**: Configure Android phone for VPN and remote control via Termux

**Overview**:
- Generate Android client configuration
- Provide WireGuard app setup instructions
- Configure Termux for SSH access from phone
- Test remote connectivity

**What Happens**:

1. VPNHD generates third client key pair for Android
2. Creates a QR code you can scan with WireGuard app
3. Provides Termux installation instructions
4. Configures SSH server on phone via Termux
5. Tests that phone can reach all systems

**Android Setup Steps**:

1. Install WireGuard app from Play Store
2. Launch VPNHD on another machine, get to Phase 6
3. Point phone at QR code displayed by VPNHD
4. WireGuard automatically configures
5. Toggle VPN on - connection established!

**Termux Setup Steps**:

1. Install Termux from F-Droid (not Play Store - more privacy!)
2. Run: `pkg install openssh`
3. Generate SSH key on Termux
4. Copy public key to server
5. Access server and other machines via SSH from phone

**Exit Criteria**:

Phase 6 is complete when:
- Android WireGuard app is connected
- Phone has VPN IP address (10.0.0.x)
- Termux SSH server is running
- Phone can SSH into server and Fedora machine

### Phase 7: SSH Key-Based Authentication

**Goal**: Enable secure key-based SSH authentication, disable passwords

**Overview**:
- Generate SSH key pairs for all systems
- Deploy public keys to server
- Disable password authentication
- Verify key-based access works
- Set up SSH config for easy access

**What Happens**:

1. VPNHD generates SSH key pairs if they don't exist
2. Gathers public keys from all clients
3. Installs public keys on server
4. Updates SSH configuration to disable passwords
5. Tests secure authentication from each client
6. Provides SSH config for easy access

**Security Impact**:

- Passwords cannot be brute-forced over SSH
- Only authorized machines can access server
- Enables secure automation without passwords
- Protects against common SSH attacks

**Key Configuration**:

SSH will be restricted to:
- Key-based authentication only
- Port: 22 (default)
- No password login allowed
- No root login (use sudo)

**Exit Criteria**:

Phase 7 is complete when:
- SSH keys are generated on all systems
- Public keys are installed on server
- Password authentication is disabled
- All systems can successfully SSH with keys

### Phase 8: Security Hardening

**Goal**: Configure firewall and intrusion prevention

**Overview**:
- Install and configure UFW firewall
- Install and configure fail2ban
- Restrict SSH to VPN network only
- Isolate Pop!_OS client (allow VPN only)
- Perform final security verification

**What Happens**:

1. VPNHD installs UFW firewall if needed
2. Creates firewall rules:
   - Allow SSH from VPN network only
   - Allow WireGuard port (UDP 51820)
   - Allow essential services
   - Block everything else
3. Installs fail2ban for intrusion prevention
4. Configures fail2ban rules for SSH
5. Runs comprehensive security verification
6. Provides hardening report

**Firewall Rules**:

```
SSH:       Allowed from 10.0.0.0/24 (VPN) only
WireGuard: Allowed UDP 51820 from anywhere
HTTP:      Blocked (not needed)
HTTPS:     Blocked (not needed)
Other:     Blocked by default
```

**Exit Criteria**:

Phase 8 is complete when:
- Firewall is active and rules applied
- fail2ban is running
- SSH is restricted to VPN network
- All security tests pass
- System is hardened and secure

## Configuration Guide

### Configuration File Location

VPNHD stores all configuration in: `~/.config/vpnhd/config.json`

### Configuration Structure

```json
{
  "version": "1.0.0",
  "server": {
    "hostname": "vpn-server",
    "local_ip": "192.168.1.10",
    "public_ip": "203.0.113.1",
    "wireguard_port": 51820,
    "network_interface": "eth0"
  },
  "vpn_network": {
    "subnet": "10.0.0.0/24",
    "server_address": "10.0.0.1",
    "clients": {
      "fedora": "10.0.0.2",
      "pop-os": "10.0.0.3",
      "android": "10.0.0.4"
    }
  },
  "phases_completed": [1, 2, 3],
  "security": {
    "ssh_enabled": true,
    "firewall_enabled": true,
    "fail2ban_enabled": false
  }
}
```

### Modifying Configuration

**Important**: Directly editing the configuration file is not recommended. Use VPNHD commands instead:

```bash
# Review current configuration
sudo vpnhd --review

# Re-run a specific phase to update configuration
sudo vpnhd --phase 2
```

### Customizable Values

These values can be customized before Phase 2:

| Setting | Default | Range | Notes |
|---------|---------|-------|-------|
| VPN Subnet | 10.0.0.0/24 | Any private range | Choose something not in use |
| WireGuard Port | 51820 | 1024-65535 | UDP, must be same on all systems |
| Server Hostname | vpn-server | Any valid hostname | Used in configuration |
| Network Interface | Auto-detected | eth0, wlan0, etc. | Interface that reaches internet |

### System Integration

VPNHD integrates with:

- **WireGuard**: `/etc/wireguard/wg0.conf`
- **Systemd**: Service unit for WireGuard
- **UFW**: Firewall rules and policies
- **fail2ban**: Intrusion prevention filter
- **SSH**: System SSH configuration

## Command Reference

### Basic Commands

```bash
# Start interactive setup
sudo vpnhd

# Continue from last completed phase
sudo vpnhd --continue

# Jump to specific phase (1-8)
sudo vpnhd --phase 4

# Review current configuration
sudo vpnhd --review

# Show version
vpnhd --version

# Show help
vpnhd --help
```

### Troubleshooting Commands

```bash
# Show detailed diagnostics
sudo vpnhd --diagnose

# Check VPN connectivity
sudo vpnhd --test-vpn

# View error logs
vpnhd --logs

# Validate configuration
sudo vpnhd --validate-config
```

### Management Commands

```bash
# Generate new keys (advanced)
sudo vpnhd --generate-keys

# Reset configuration
sudo vpnhd --reset

# Uninstall completely
sudo bash scripts/uninstall.sh
```

## Examples

### Example 1: First-Time Setup (Complete Walkthrough)

```bash
# Session 1: Install Debian and begin setup
$ sudo vpnhd
Main Menu:
  [1] Continue to next phase
  [2] Jump to specific phase
  [3] Review configuration
  [4] Show phase details
  [5] Troubleshooting
  [6] View guide documentation
  [7] Exit

Choose option: 1

Starting Phase 1: Debian Server Installation
Checking system requirements...
✓ Debian 12.1 detected
✓ SSH is running
✓ System meets minimum requirements
✓ Configuration created

Phase 1 complete! Server is ready for WireGuard setup.

# Session 2: Configure WireGuard
$ sudo vpnhd
[Continue to Phase 2]

Setting up WireGuard server...
✓ WireGuard tools installed
✓ Server keys generated
✓ Configuration file created
✓ IP forwarding enabled
✓ WireGuard service started

Phase 2 complete! Now configure router port forwarding.

# Session 3: Configure Router
$ sudo vpnhd
[Continue to Phase 3]

Router Configuration:
  External Port: 51820
  Internal IP: 192.168.1.10
  Protocol: UDP

Configure your router and press Enter...
[After router configuration]

✓ Port forwarding confirmed
✓ External connectivity verified

Phase 3 complete!
```

### Example 2: Adding a New Client

```bash
# Already completed Phase 4 (Fedora)?
# Skip to Phase 5 (Pop!_OS) directly:

$ sudo vpnhd --phase 5

Setting up Pop!_OS client...
Client configuration generated. Scan this QR code or copy the config:

[QR Code displayed]

Install WireGuard on Pop!_OS and load this configuration.
Connection test passed!

Phase 5 complete!
```

### Example 3: Troubleshooting Connection Issues

```bash
# Run diagnostic
$ sudo vpnhd --diagnose

Checking system configuration...
✓ Debian 12.1 running
✓ WireGuard installed
✗ WireGuard service not running
  Action: sudo systemctl start wg-quick@wg0

✓ Firewall configured
✓ SSH keys installed

Found 1 issue. Run the suggested action above.
```

### Example 4: Reviewing Configuration Before Changes

```bash
$ sudo vpnhd --review

Current Configuration:
  Version: 1.0.0
  Server: vpn-server (192.168.1.10)
  Public IP: 203.0.113.1
  VPN Subnet: 10.0.0.0/24

Clients:
  - Fedora (10.0.0.2): Connected
  - Pop!_OS (10.0.0.3): Disconnected
  - Android (10.0.0.4): Connected

Completed Phases: 1, 2, 3, 4, 6
Pending: Phase 5 (Pop!_OS), Phase 7 (SSH Keys), Phase 8 (Security)
```

## Best Practices

### Security Practices

1. **Keep Keys Safe**
   - Don't share private keys
   - Back up keys in secure location
   - Use strong passphrases for SSH keys

2. **Regular Updates**
   - Keep Debian updated: `sudo apt update && sudo apt upgrade`
   - Keep WireGuard updated
   - Monitor security advisories

3. **Monitor Access**
   - Review SSH logs: `sudo journalctl -u ssh`
   - Check WireGuard connections: `sudo wg show`
   - Monitor fail2ban: `sudo fail2ban-client status`

### Performance Practices

1. **Network Optimization**
   - Use Ethernet for server (faster, more reliable)
   - Monitor VPN throughput: `iftop -i wg0`
   - Check kernel forwarding: `cat /proc/sys/net/ipv4/ip_forward`

2. **Resource Monitoring**
   - Monitor CPU usage during high load
   - Check disk space regularly
   - Monitor memory usage on low-RAM systems

### Operational Practices

1. **Backups**
   - Back up `~/.config/vpnhd/` regularly
   - Save WireGuard keys securely
   - Document your configuration

2. **Documentation**
   - Keep notes on your custom settings
   - Document any firewall rules you add
   - Write down recovery procedures

3. **Testing**
   - Test backups regularly
   - Test disaster recovery procedures
   - Test client reconnection after network changes

### Troubleshooting Best Practices

1. **Before Taking Action**
   - Check the logs: `vpnhd --logs`
   - Run diagnostics: `sudo vpnhd --diagnose`
   - Review the Troubleshooting guide

2. **Information Gathering**
   - Note exact error messages
   - Record system versions
   - Capture timestamps of failures

3. **Making Changes**
   - Change one thing at a time
   - Document your changes
   - Test after each change
   - Keep backups before major changes

---

**Need Help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and [FAQ.md](FAQ.md) for frequently asked questions.
