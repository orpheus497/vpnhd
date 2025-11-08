# VPNHD Frequently Asked Questions

## Table of Contents

1. [General Questions](#general-questions)
2. [Installation and Setup](#installation-and-setup)
3. [Usage and Operations](#usage-and-operations)
4. [Security and Privacy](#security-and-privacy)
5. [Technical Details](#technical-details)
6. [Troubleshooting](#troubleshooting)
7. [Development](#development)

## General Questions

### What is VPNHD?

VPNHD is an automated, privacy-focused home VPN setup tool. It guides you through creating your own VPN system using WireGuard, allowing you to:

- Securely access your home network remotely
- Create a private network between your devices
- Control your own infrastructure (no corporate servers)
- Maintain complete privacy (zero telemetry)

### Why should I use VPNHD instead of commercial VPN services?

**VPNHD advantages**:

- **Privacy**: Your traffic stays on YOUR hardware, you control everything
- **No subscription fees**: One-time setup
- **No central authority**: You're not trusting a company with your data
- **Full transparency**: Open source code you can audit
- **Your devices stay connected**: Remote access to home network
- **Educational**: Learn how VPNs actually work
- **No bandwidth limits**: Use as much as you want

**Commercial VPN disadvantages**:

- Data goes through their servers (you must trust them)
- Monthly/yearly fees
- Bandwidth throttling
- Can see your activity (despite privacy claims)
- Marketing hype vs actual security
- Can't access home network (only external browsing)

### Is VPNHD for beginners or advanced users?

**VPNHD is explicitly designed for beginners!**

- No Linux knowledge required
- ELI5 explanations throughout
- Step-by-step interactive guidance
- Clear error messages and help
- Comprehensive documentation

Advanced users will also appreciate the automation saving time.

### How is VPNHD different from setting up WireGuard manually?

| Aspect | Manual Setup | VPNHD |
|--------|--------------|-------|
| Time | 2-3 hours | 30 minutes (with system setup) |
| Complexity | Very high | Simple (interactive) |
| Error-prone | Very (many manual steps) | Low (automated validation) |
| Configuration template | Must create manually | Pre-built, tested |
| Troubleshooting | Manual (difficult) | Built-in diagnostics |
| Documentation | External references | Integrated guide |
| Learning | Steep learning curve | Guided education |

### What's the philosophy behind VPNHD?

VPNHD is built on these principles:

1. **Privacy is a right**: You control your data, not corporations
2. **Free software**: Open source ensures transparency and freedom
3. **Simplicity**: Complex things should be made easy
4. **Learning**: Users should understand what they're using
5. **Trust through code**: You can read and verify everything

### Can I see the source code?

Absolutely! VPNHD is 100% open source under GPL-3.0. You can:

- View all code on GitHub
- Audit for security
- Modify for your needs
- Contribute improvements
- Share with others

## Installation and Setup

### What are the minimum system requirements?

**Server**:
- Debian 12+ (Bookworm) x86_64
- 512MB RAM (1GB recommended)
- 8GB disk space
- Static local IP address
- Any x86_64 CPU

**Clients**:
- Fedora 38+ or Pop!_OS 22.04+ or Android 8+
- Python 3.10+ (for installation)
- Network access to server (for setup)

### Why Debian? Can I use Ubuntu, CentOS, etc.?

Currently VPNHD targets Debian 12 only because:

- Debian is stable and widely available
- Package management is straightforward
- WSL Debian support is excellent
- Future versions will support more distributions

### Do I need to install Debian fresh or can I use existing?

You can use existing Debian 12, but:

- VPNHD assumes a dedicated server
- Existing services might conflict
- Configuration assumes no previous WireGuard setup
- Root access required

**Recommended**: Fresh Debian installation

### How long does installation take?

**Time breakdown**:

- System dependencies: 5-10 minutes
- Python dependencies: 2-3 minutes
- Phase 1-8 setup: 30 minutes total
- Router configuration: 10-15 minutes
- **Total: 1-2 hours** for complete setup

### Can I run VPNHD on a VPS or cloud server?

Yes! VPNHD works on any Debian 12 server:

- Linode, DigitalOcean, Hetzner, etc.
- AWS EC2, Google Cloud, Azure (Linux VMs)
- Proxmox VE containers
- Virtual machines
- Home server hardware

**Note**: VPS solutions lack local network access (Phase 1 adapted for VPS).

### Do I need to uninstall/remove anything first?

If you're setting up fresh Debian:
- No uninstallation needed
- Dependencies will be installed automatically

If upgrading existing setup:
- Back up `/etc/wireguard/` first
- Back up `~/.config/vpnhd/config.json`
- VPNHD can update gracefully

## Usage and Operations

### How do I start VPNHD after installation?

```bash
# Interactive setup
sudo vpnhd

# Continue from last phase
sudo vpnhd --continue

# Jump to specific phase
sudo vpnhd --phase 3
```

### Can I skip phases or go out of order?

**Yes and no**:

- **Can skip**: Jump to any phase with `--phase` flag
- **Should not skip**: Phases depend on previous setup
- **Recommended**: Go through sequentially for first time
- **Advanced**: Can jump once familiar with the process

### What if I stop setup mid-phase?

VPNHD has automatic checkpointing:

- Progress is saved at phase completion
- Can restart from same point
- Configuration persists
- Logs track what was done

Just run `sudo vpnhd --continue` to resume.

### How do I access my home network remotely?

After VPNHD setup:

1. Connect to VPN from remote location
2. Use local IP addresses (192.168.x.x)
3. SSH into server or other machines
4. Access network services normally

Example:
```bash
# Connect to VPN first
sudo systemctl start wg-quick@wg0

# Then SSH to home server
ssh user@192.168.1.10
```

### Can I update VPNHD after installation?

Yes, but carefully:

```bash
# Back up current config
cp ~/.config/vpnhd/config.json ~/.config/vpnhd/config.json.backup

# Pull latest version
git pull origin main

# Reinstall
sudo pip install -e .

# Test
vpnhd --version
sudo vpnhd --validate-config
```

### Can multiple people use the same VPNHD setup?

Yes! But consider:

- Each user needs separate SSH key
- Each machine needs separate WireGuard config
- VPNHD is per-installation (not multi-user)
- Configuration must be shared or replicated

## Security and Privacy

### Is my traffic encrypted?

Yes! WireGuard provides:

- **Military-grade encryption**: ChaCha20-Poly1305
- **Perfect forward secrecy**: Keys can't decrypt past traffic
- **Authenticated**: Can't inject fake packets
- **Modern cryptography**: Designed in 2015+
- **Verified**: Security audited by independent researchers

### Can my VPN provider see my traffic?

**With VPNHD**: No external VPN provider involved! Traffic stays between your devices.

**What's encrypted**:
- All data between VPN clients and server
- Server doesn't decrypt or inspect
- Server doesn't log traffic

**What's not encrypted**:
- Local network traffic (192.168.x.x)
- DNS queries (if not configured)
- Traffic after leaving your VPN

### Is my data backed up automatically?

No automatic backup! **You must back up**:

```bash
# Backup configuration
cp ~/.config/vpnhd/config.json ~/backup/

# Backup WireGuard keys (VERY IMPORTANT!)
sudo cp /etc/wireguard/privatekey ~/backup/

# Backup SSH keys
cp ~/.ssh/id_* ~/backup/
```

**Store backups**:
- Offline/encrypted storage
- Multiple copies
- Test restore procedures

### Should I store backups in the cloud?

Backups in cloud (encrypted):
- **Pros**: Accessible anywhere, redundant
- **Cons**: Cloud provider can see data if not encrypted

**Recommendation**:
- Encrypt locally before uploading
- Use password-protected encrypted archive
- Consider air-gapped offline backup primary

### Is VPNHD vulnerable to attacks?

VPNHD security is based on:

- **Tested cryptography**: WireGuard, OpenSSH (both widely audited)
- **Least privilege**: UFW firewall + fail2ban
- **Key-based auth**: No password-based attacks
- **Open source**: Code can be audited
- **Regular updates**: Security patches from upstream

**Potential risks**:
- Unpatched Debian system (your responsibility)
- Weak firewall configuration (VPNHD handles this)
- Key compromise (protect your backups)
- Network misconfiguration (VPNHD validates)

### Do I need antivirus on VPNHD?

No! Linux servers rarely need antivirus:

- Malware requires execution
- File permissions prevent unauthorized execution
- UFW firewall blocks unwanted connections
- SSH key auth prevents brute force
- fail2ban stops automated attacks

**Real protections**:
- Keep system updated
- Use strong SSH keys
- Limit network exposure
- Monitor logs regularly

### Can my ISP see my VPN traffic?

**Yes**: ISP sees encrypted packets but not content:

- Sees: IP addresses, packet sizes, timing
- Doesn't see: VPN data, websites, DNS queries

**To hide VPN usage from ISP**:
- This is advanced and out of VPNHD scope
- Some countries require this
- VPN bridges can help (research separately)

## Technical Details

### What is WireGuard?

WireGuard is modern VPN protocol that:

- Uses modern cryptography (ChaCha20, Poly1305)
- Has ~4000 lines of code (vs OpenVPN ~100k)
- Is faster than older VPN protocols
- Is designed by security professionals
- Is integrated into Linux kernel (since 5.6)
- Is well-audited and trusted

### What is Debian?

Debian is:

- A Linux distribution
- Completely free and open source
- Extremely stable and reliable
- Used as base for Ubuntu, Raspberry Pi OS, etc.
- Backed by large community
- Excellent package management (apt)

### What's the difference between client types?

**Fedora (Phase 4)**:
- Always-on VPN (auto-starts at boot)
- Acts as admin/primary interface
- Can reach entire VPN and local network

**Pop!_OS (Phase 5)**:
- On-demand VPN (manual start)
- Network-isolated when not using VPN
- Good for sensitive activities

**Android (Phase 6)**:
- Mobile VPN access
- Termux for SSH remote control
- Can manage entire network from phone

### Can I use different client OS?

Currently supported:
- Fedora
- Pop!_OS
- Android (via Termux)

Future support:
- macOS
- Windows
- More Linux distributions

To use different OS:
- Manually configure WireGuard
- Follow official WireGuard documentation
- Use configuration provided by VPNHD

### How does IP forwarding work?

IP forwarding allows server to route traffic between clients:

```
Client A (10.0.0.2)
    |
    | [Server does forwarding]
    |
Client B (10.0.0.3)
```

Without IP forwarding, clients can't reach each other. VPNHD enables this.

### What are the default network addresses?

```
LAN Network:    192.168.0.0/24 (or 192.168.1.0/24)
VPN Network:    10.0.0.0/24
VPN Server:     10.0.0.1
VPN Clients:    10.0.0.2 onwards
WireGuard Port: 51820 (UDP)
SSH Port:       22 (TCP, restricted to VPN)
```

You can customize VPN network during Phase 2.

## Troubleshooting

### Common error: "WireGuard service failed to start"

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#wireguard-service-fails-to-start-on-boot)

### Common error: "Cannot connect to server"

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#client-wont-connect-to-server)

### Common error: "SSH permission denied"

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#ssh-permission-denied-publickey)

### Common error: "Port forwarding not working"

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#port-forwarding-not-working)

### Where are the logs?

Logs are stored in:

```bash
# VPNHD logs
~/.config/vpnhd/logs/

# System logs
/var/log/syslog
/var/log/auth.log

# WireGuard logs
sudo journalctl -u wg-quick@wg0

# SSH logs
sudo journalctl -u ssh

# Firewall logs
/var/log/ufw.log
```

### How do I reset and start over?

```bash
# Reset VPNHD configuration
sudo vpnhd --reset

# Or completely uninstall
sudo bash scripts/uninstall.sh

# Then reinstall
sudo bash scripts/install.sh
```

### My VPN connection drops frequently

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#all-clients-disconnect-randomly)

## Development

### Can I contribute to VPNHD?

Yes! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Testing requirements
- Code standards
- Pull request process
- How to report issues

### How can I report bugs?

Report issues with:

1. VPNHD version: `vpnhd --version`
2. Exact error message (copy-paste)
3. Steps to reproduce
4. Expected vs actual behavior
5. Relevant logs (sanitized)
6. System info: `uname -a`

Create issue on GitHub: https://github.com/orpheus497/vpnhd/issues

### How can I request new features?

Feature requests welcome! Please include:

1. **What**: What feature would you like?
2. **Why**: Why is it important?
3. **How**: How would you use it?
4. **Benefit**: Who benefits?

Create issue with label "enhancement" on GitHub.

### Can I fork and modify VPNHD?

Absolutely! GPL-3.0 license allows:

- Modification
- Redistribution
- Private use
- Commercial use

**Requirement**: Derivative works must also be GPL-3.0

### How is VPNHD developed?

VPNHD uses:

- **Language**: Python 3.10+
- **CLI Framework**: Click
- **UI Library**: Rich
- **Testing**: pytest
- **CI/CD**: GitHub Actions
- **Version Control**: Git

### Where is VPNHD hosted?

- **Source Code**: GitHub (github.com/orpheus497/vpnhd)
- **Releases**: GitHub Releases
- **Package**: PyPI (python-packages)
- **Issues/PRs**: GitHub

### What's the roadmap?

**Version 1.0.0** (current):
- Complete 8-phase setup
- Full documentation
- Core features stable

**Future versions**:
- IPv6 support
- Additional client OS
- Web management interface (optional)
- Multi-server federation
- Performance monitoring
- Automated backups

### How often is VPNHD updated?

- **Security fixes**: ASAP (within days)
- **Bug fixes**: Monthly or as needed
- **Features**: Quarterly releases planned
- **Maintenance**: Continuous

## Still Have Questions?

- **Check**: [USER_GUIDE.md](USER_GUIDE.md)
- **Troubleshoot**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Contribute**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Report issues**: GitHub Issues
- **Read**: Integrated documentation (`vpnhd --help`)

---

**Last Updated**: November 2025
**Version**: 1.0.0

Can't find answer? Create an issue on GitHub with your question!
