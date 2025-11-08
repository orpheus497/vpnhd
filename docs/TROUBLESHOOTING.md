# VPNHD Troubleshooting Guide

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [WireGuard Connection Problems](#wireguard-connection-problems)
3. [SSH Issues](#ssh-issues)
4. [Firewall and Port Forwarding](#firewall-and-port-forwarding)
5. [Configuration Problems](#configuration-problems)
6. [System Integration Issues](#system-integration-issues)
7. [Performance Issues](#performance-issues)
8. [Getting Help](#getting-help)

## Installation Issues

### Issue: "Python 3.10+ required" error

**Symptoms**: VPNHD installer refuses to run

**Cause**: Python version is older than 3.10

**Solution**:

```bash
# Check Python version
python3 --version

# If older than 3.10, install newer version:
# On Debian:
sudo apt install python3.11

# Verify new version
python3.11 --version

# Run installer with correct Python:
python3.11 -m pip install -r requirements.txt
```

### Issue: "wireguard-tools not found"

**Symptoms**: Installation fails at system dependency check

**Cause**: Package manager not updated or package unavailable

**Solution**:

```bash
# Update package list
sudo apt update

# Try installing WireGuard manually
sudo apt install wireguard-tools wireguard

# Verify installation
sudo wg --version

# Then retry VPNHD installation
sudo bash scripts/install.sh
```

### Issue: "Permission denied" during installation

**Symptoms**: Installation fails with permission error

**Cause**: Not running with sudo

**Solution**:

```bash
# Installation REQUIRES root
sudo bash scripts/install.sh

# Or for Python installation:
sudo pip install -r requirements.txt
sudo python3 setup.py install
```

### Issue: "ModuleNotFoundError: No module named 'rich'"

**Symptoms**: VPNHD starts but immediately crashes

**Cause**: Python dependencies not installed

**Solution**:

```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually:
pip install rich click pyyaml jsonschema python-dotenv netifaces jinja2

# Verify installation
python3 -c "import rich; print('Rich installed successfully')"
```

### Issue: "vpnhd command not found" after installation

**Symptoms**: `vpnhd --help` doesn't work

**Cause**: Command not in PATH or installation incomplete

**Solution**:

```bash
# Verify VPNHD installed
python3 -m vpnhd --version

# If that works, use full path:
sudo python3 -m vpnhd

# Or reinstall to ensure PATH is updated:
sudo pip install -e .
```

## WireGuard Connection Problems

### Issue: "Cannot connect to VPN after phase 2"

**Symptoms**: Client cannot reach 10.0.0.1, timeout errors

**Cause**: WireGuard service not running or not listening

**Solution**:

```bash
# Check if WireGuard is running
sudo systemctl status wg-quick@wg0

# If stopped, start it
sudo systemctl start wg-quick@wg0

# Check if listening on correct port
sudo ss -ulnp | grep 51820

# View WireGuard interface
sudo wg show

# Check configuration file
cat /etc/wireguard/wg0.conf
```

### Issue: "Client won't connect to server"

**Symptoms**: Client configuration created but connection fails

**Cause**: Multiple possible causes (firewall, keys, configuration)

**Solution**:

```bash
# On server: Verify listening
sudo wg show wg0

# On client: Check configuration
wg-quick show wg0

# Check endpoint is correct
grep Endpoint /etc/wireguard/wg0.conf

# Verify keys exist
ls -la /etc/wireguard/privatekey

# Test connectivity to endpoint
ping [SERVER_PUBLIC_IP]

# Enable verbose logging
sudo wg set wg0 fwmark 0xca6c
```

### Issue: "VPN works on server but not on client"

**Symptoms**: Server shows connected, client cannot ping VPN IPs

**Cause**: Client configuration missing or incorrect peer settings

**Solution**:

```bash
# Verify client config has server's peer info
cat /etc/wireguard/wg0.conf | grep -A5 "\[Peer\]"

# Check that endpoint points to server public IP
grep "Endpoint" /etc/wireguard/wg0.conf

# Ensure AllowedIPs includes VPN network
grep "AllowedIPs" /etc/wireguard/wg0.conf
# Should be: AllowedIPs = 10.0.0.0/24

# Restart WireGuard on client
sudo systemctl restart wg-quick@wg0

# Check connection status
ip link show wg0
```

### Issue: "Connected to VPN but can't reach server"

**Symptoms**: VPN shows connected but can't ping 10.0.0.1

**Cause**: IP forwarding disabled on server or firewall blocking

**Solution**:

```bash
# Server: Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward
# Should output: 1

# If not enabled:
sudo echo 1 > /proc/sys/net/ipv4/ip_forward

# Or permanently:
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Check firewall isn't blocking
sudo ufw status
sudo ufw allow in on wg0

# Test connectivity
sudo wg show wg0
```

### Issue: "All clients disconnect randomly"

**Symptoms**: VPN connection drops periodically, needs restart

**Cause**: Router timeout, WireGuard service restart needed, or configuration issue

**Solution**:

```bash
# Check WireGuard service logs
sudo journalctl -u wg-quick@wg0 -n 50

# Verify service is set to auto-start
sudo systemctl is-enabled wg-quick@wg0

# Enable auto-start if needed
sudo systemctl enable wg-quick@wg0

# Check for network interface issues
ip link show wg0

# Restart WireGuard properly
sudo systemctl restart wg-quick@wg0

# Monitor for disconnects
watch -n 1 'sudo wg show'
```

### Issue: "Slow VPN speeds"

**Symptoms**: VPN is working but very slow

**Cause**: Network congestion, CPU limitations, or encryption overhead

**Solution**:

```bash
# Test local network speed first
sudo iperf3 -s  # On server
iperf3 -c [SERVER_IP]  # On client

# Test through VPN
iperf3 -c 10.0.0.1 -p 5201  # Through VPN

# Check server load
top
ps aux | grep -i wireguard

# Check for packet loss
ping -c 100 10.0.0.1 | tail -5

# Enable WireGuard debug
sudo sysctl -w net.wireguard.message_interval=0

# Check MTU settings
ip link show | grep mtu
# If below 1420, may cause issues
```

## SSH Issues

### Issue: "SSH connection refused on port 22"

**Symptoms**: `ssh: connect to host ... port 22: Connection refused`

**Cause**: SSH service not running or firewall blocking

**Solution**:

```bash
# Check SSH service status
sudo systemctl status ssh

# Start SSH if stopped
sudo systemctl start ssh

# Enable auto-start
sudo systemctl enable ssh

# Check SSH is listening
sudo ss -tlnp | grep :22

# Verify firewall allows SSH
sudo ufw status
sudo ufw allow 22/tcp  # If needed

# Test SSH connectivity
ssh -v user@server  # Verbose to see what's failing
```

### Issue: "Permission denied (publickey)" on SSH

**Symptoms**: Cannot SSH even with correct keys and password auth disabled

**Cause**: SSH keys not installed on server or permissions wrong

**Solution**:

```bash
# On client: Verify key exists
ls -la ~/.ssh/id_rsa

# Check key permissions (must be 600)
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# On server: Verify public key installed
cat ~/.ssh/authorized_keys

# Check authorized_keys permissions (must be 600)
chmod 600 ~/.ssh/authorized_keys

# Verify SSH config allows publickey auth
grep "PubkeyAuthentication" /etc/ssh/sshd_config
# Should be: PubkeyAuthentication yes

# If needed, add your public key:
echo "YOUR_PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys

# Restart SSH to apply changes
sudo systemctl restart ssh

# Test with specific key
ssh -i ~/.ssh/id_rsa user@server
```

### Issue: "SSH password login doesn't work"

**Symptoms**: Can't SSH with password even though service running

**Cause**: Password authentication disabled (expected behavior in phase 7)

**Solution**:

```bash
# This is correct behavior after Phase 7!
# SSH passwords are disabled for security

# To re-enable (NOT RECOMMENDED):
sudo nano /etc/ssh/sshd_config
# Find: PasswordAuthentication no
# Change to: PasswordAuthentication yes
# Save with Ctrl+X, Y, Enter

sudo systemctl restart ssh

# Generate SSH keys instead:
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server

# Then use keys for login (more secure)
ssh -i ~/.ssh/id_ed25519 user@server
```

### Issue: "SSH times out connecting through VPN"

**Symptoms**: SSH works on local network but times out over VPN

**Cause**: VPN issue (see WireGuard issues) or SSH config issue

**Solution**:

```bash
# First, verify VPN is working
ping 10.0.0.1

# If VPN works but SSH times out, check routing
traceroute 10.0.0.1

# Try SSH with verbose output to see where it hangs
ssh -vvv user@10.0.0.1

# Check server's SSH service on VPN IP
sudo ss -tlnp | grep 22

# Check firewall allows SSH on VPN interface
sudo ufw status
sudo ufw allow in on wg0 to any port 22

# Restart SSH service
sudo systemctl restart ssh
```

## Firewall and Port Forwarding

### Issue: "Port forwarding not working"

**Symptoms**: Can't connect from outside network, external connectivity test fails

**Cause**: Router not configured, port not forwarded, or firewall blocking

**Solution**:

```bash
# On server: Verify WireGuard listening
sudo ss -ulnp | grep 51820
# Should show: 0.0.0.0:51820

# Check firewall allows the port
sudo ufw status
sudo ufw allow 51820/udp

# Get your public IP
curl ifconfig.me

# From external network, test port
# (Ask friend with different internet)
sudo nc -u -l 51820 -vvv  # On server
echo "test" > /dev/udp/YOUR_PUBLIC_IP/51820  # From external

# In router, verify port forward settings:
# - Protocol: UDP
# - External Port: 51820
# - Internal IP: [server's local IP]
# - Internal Port: 51820
# - Status: Enabled/Active

# Some routers require:
- Save/Apply after changes
- Reboot after changing rules
- Check if UPnP can replace manual configuration
```

### Issue: "UFW firewall blocking WireGuard"

**Symptoms**: WireGuard works locally but fails after enabling firewall

**Cause**: Firewall rules too restrictive

**Solution**:

```bash
# Check firewall status
sudo ufw status

# Allow WireGuard before enabling firewall
sudo ufw allow 51820/udp

# Allow SSH (prevent lockout!)
sudo ufw allow 22/tcp

# Allow VPN network traffic
sudo ufw allow in on wg0

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status numbered

# If blocked, temporarily disable to diagnose
sudo ufw disable

# View default policy
sudo ufw show added
```

### Issue: "fail2ban blocking legitimate connections"

**Symptoms**: Connections work then suddenly fail, repeated failed connection attempts

**Cause**: fail2ban banned your IP after too many failed attempts

**Solution**:

```bash
# Check fail2ban status
sudo fail2ban-client status

# View SSH jail specifically
sudo fail2ban-client status sshd

# Unban an IP (if you know it)
sudo fail2ban-client set sshd unbanip YOUR_IP

# View banned IPs
sudo iptables -L -n | grep DROP

# Reduce fail2ban sensitivity (if too aggressive)
sudo nano /etc/fail2ban/jail.local
# Adjust: maxretry = 10  (increase from 5)
# Adjust: findtime = 3600  (increase from 1 hour)

sudo systemctl restart fail2ban

# Monitor fail2ban logs
sudo tail -f /var/log/fail2ban.log
```

## Configuration Problems

### Issue: "Configuration file corrupted or missing"

**Symptoms**: VPNHD won't start or says "Invalid configuration"

**Cause**: Config file deleted, corrupted, or permissions wrong

**Solution**:

```bash
# Verify config location
ls -la ~/.config/vpnhd/

# Check if file exists
cat ~/.config/vpnhd/config.json

# If missing or corrupted, reset:
sudo vpnhd --reset

# If permissions wrong:
sudo chown $USER:$USER ~/.config/vpnhd/config.json
sudo chmod 600 ~/.config/vpnhd/config.json

# Backup before resetting
cp ~/.config/vpnhd/config.json ~/.config/vpnhd/config.json.backup
```

### Issue: "Cannot read/write configuration"

**Symptoms**: "Permission denied" when accessing config

**Cause**: Incorrect file permissions or ownership

**Solution**:

```bash
# Check permissions
ls -la ~/.config/vpnhd/config.json

# Fix ownership (should be your user)
sudo chown $USER:$USER ~/.config/vpnhd/config.json

# Fix permissions
chmod 600 ~/.config/vpnhd/config.json

# Verify directory permissions
ls -la ~/.config/vpnhd/
chmod 700 ~/.config/vpnhd/

# Try operation again
sudo vpnhd --review
```

### Issue: "Configuration incomplete, missing required fields"

**Symptoms**: VPNHD says configuration invalid

**Cause**: Incomplete setup or manual editing removed required fields

**Solution**:

```bash
# Don't manually edit config!
# Instead, run phases to complete it properly:

# Continue from last completed phase
sudo vpnhd --continue

# Or jump to specific phase
sudo vpnhd --phase 2

# View what's configured
sudo vpnhd --review

# Validate configuration
sudo vpnhd --validate-config
```

## System Integration Issues

### Issue: "WireGuard service fails to start on boot"

**Symptoms**: Reboot and VPN is down, manual `systemctl start` works

**Cause**: Service not enabled for auto-start

**Solution**:

```bash
# Enable WireGuard auto-start
sudo systemctl enable wg-quick@wg0

# Verify it's enabled
sudo systemctl is-enabled wg-quick@wg0
# Should output: enabled

# Check for startup errors
sudo systemctl status wg-quick@wg0

# View startup logs
sudo journalctl -u wg-quick@wg0 -b

# If still fails, check dependencies
systemctl list-dependencies wg-quick@wg0

# Manually test startup behavior
sudo systemctl stop wg-quick@wg0
sudo systemctl start wg-quick@wg0
sudo systemctl status wg-quick@wg0
```

### Issue: "Cannot access /etc/wireguard/wg0.conf"

**Symptoms**: "Permission denied" when trying to view WireGuard config

**Cause**: File permissions or not running as root

**Solution**:

```bash
# Must run as root to view/edit
sudo cat /etc/wireguard/wg0.conf

# Check permissions
sudo ls -la /etc/wireguard/wg0.conf
# Should be: -rw------- root root

# Fix if needed:
sudo chmod 600 /etc/wireguard/wg0.conf
sudo chown root:root /etc/wireguard/wg0.conf

# Always edit with sudo
sudo nano /etc/wireguard/wg0.conf

# Never chmod 644 (world readable - security risk!)
```

### Issue: "Network interface missing after reboot"

**Symptoms**: WireGuard doesn't start, says "interface wg0 not found"

**Cause**: WireGuard kernel module not loaded

**Solution**:

```bash
# Load WireGuard module
sudo modprobe wireguard

# Verify loaded
lsmod | grep wireguard

# Make persistent
echo "wireguard" | sudo tee -a /etc/modules

# Restart WireGuard
sudo systemctl restart wg-quick@wg0

# For persistent loading on boot:
# (Should be automatic with systemd)
```

## Performance Issues

### Issue: "High CPU usage from WireGuard"

**Symptoms**: High CPU usage, especially when high traffic

**Cause**: CPU-intensive encryption or traffic amplification

**Solution**:

```bash
# Monitor CPU usage
top -p $(pgrep -f wireguard)

# Check actual traffic
sudo wg show wg0

# Monitor throughput
sudo iftop -i wg0

# If high CPU with low traffic, check for:
# - Routing loops (traffic going in circles)
# - Broadcast storms
# - DDoS attack

# Check kernel offloading
sudo ethtool -k eth0 | grep -i offload

# Enable offloading if available:
sudo ethtool -K eth0 tx-checksumming on
```

### Issue: "High memory usage on server"

**Symptoms**: Memory fills up over time

**Cause**: Memory leak or too many connections

**Solution**:

```bash
# Check memory usage
free -h

# Monitor for memory leak
watch -n 5 'free -h'

# Check which processes use memory
ps aux --sort=-%mem | head -10

# Restart WireGuard if needed
sudo systemctl restart wg-quick@wg0

# Check for connection leaks
sudo wg show wg0 | grep -i transfer

# If persistent, may need kernel update:
sudo apt update
sudo apt upgrade
```

## Performance Optimization

### Increase WireGuard Performance

```bash
# Increase network buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728

# Make persistent:
echo "net.core.rmem_max=134217728" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=134217728" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Increase UDP buffer sizes
echo "net.ipv4.udp_mem=65536 131072 262144" | sudo tee -a /etc/sysctl.conf
```

## Getting Help

### Collecting Diagnostic Information

Before asking for help, gather:

```bash
# System information
uname -a
cat /etc/os-release

# VPNHD version
vpnhd --version

# Configuration (sanitized - remove public IP)
sudo vpnhd --review

# WireGuard status
sudo wg show

# System status
systemctl status wg-quick@wg0
systemctl status ssh

# Recent logs
sudo journalctl -u wg-quick@wg0 -n 50
sudo journalctl -u ssh -n 50

# Firewall status
sudo ufw status numbered
```

### How to Report Issues

1. **Include version information**: `vpnhd --version`
2. **Include OS and version**: `uname -a`
3. **Include exact error message**: Copy complete error
4. **Include steps to reproduce**: List what you did
5. **Include diagnostic output**: Run `sudo vpnhd --diagnose`
6. **Include relevant logs**: From `~/.config/vpnhd/logs/`
7. **Don't include**: Private keys, passwords, or sensitive IPs

### Resources

- **VPNHD Logs**: `~/.config/vpnhd/logs/`
- **System Logs**: `/var/log/`
- **WireGuard Logs**: `sudo journalctl -u wg-quick@wg0`
- **SSH Logs**: `sudo journalctl -u ssh`
- **UFW Logs**: `/var/log/ufw.log`
- **fail2ban Logs**: `/var/log/fail2ban.log`

### When to Seek Help

Seek help via GitHub Issues if:
- Error persists after trying solutions
- Error is not documented here
- Configuration file is corrupted
- System behaves unexpectedly

See [docs/FAQ.md](FAQ.md) for frequently asked questions.

---

**Can't find your issue?** Check the [FAQ](FAQ.md) or create a GitHub issue with diagnostic information.
