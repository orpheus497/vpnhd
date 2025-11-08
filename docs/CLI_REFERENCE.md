# CLI Reference

Complete command-line interface reference for VPNHD.

## Table of Contents

- [Main Application](#main-application)
- [Client Management](#client-management)
- [Performance Testing](#performance-testing)
- [Backup & Restore](#backup--restore)
- [Common Options](#common-options)
- [Exit Codes](#exit-codes)

## Main Application

### vpnhd

Start the interactive VPNHD setup wizard.

```bash
vpnhd [OPTIONS]
```

**Options:**

- `--version` - Show version information and exit
- `--continue` - Continue from the last completed phase
- `--phase <number>` - Jump to a specific phase (1-8)
- `--review` - Review current configuration without making changes
- `--help` - Show help message and exit

**Examples:**

```bash
# Start interactive setup from beginning
sudo vpnhd

# Continue from last phase
sudo vpnhd --continue

# Jump to Phase 3 (Router Port Forwarding)
sudo vpnhd --phase 3

# Review current configuration
sudo vpnhd --review

# Show version
vpnhd --version
```

---

## Client Management

Manage VPN clients with comprehensive metadata tracking and real-time status monitoring.

### vpnhd client list

List all VPN clients with optional filtering.

```bash
vpnhd client list [OPTIONS]
```

**Options:**

- `--enabled` - Show only enabled clients
- `--device-type <type>` - Filter by device type (desktop, mobile, server)
- `--format <format>` - Output format: table (default), json, or simple

**Examples:**

```bash
# List all clients in table format
vpnhd client list

# List only enabled clients
vpnhd client list --enabled

# List mobile devices
vpnhd client list --device-type mobile

# Output as JSON
vpnhd client list --format json
```

**Output:**

```
╭─────────────────────────── VPN Clients ───────────────────────────╮
│ Name      │ Device Type │ OS      │ VPN IP       │ Status    │    │
├───────────┼─────────────┼─────────┼──────────────┼───────────┼────┤
│ laptop    │ desktop     │ fedora  │ 10.0.0.2     │ Connected │ ✓  │
│ phone     │ mobile      │ android │ 10.0.0.3     │ Offline   │ ✓  │
│ server    │ server      │ debian  │ 10.0.0.4     │ Connected │ ✓  │
╰───────────┴─────────────┴─────────┴──────────────┴───────────┴────╯
```

---

### vpnhd client add

Add a new VPN client with automatic key generation and IP assignment.

```bash
vpnhd client add <name> [OPTIONS]
```

**Arguments:**

- `<name>` - Unique client name (required)

**Options:**

- `--description <text>` - Human-readable description
- `--device-type <type>` - Device type: desktop (default), mobile, or server
- `--os <name>` - Operating system (e.g., fedora, ubuntu, android, ios)
- `--vpn-ip <ip>` - Manually specify VPN IP address (auto-assigned if not provided)
- `--generate-qr` - Generate QR code for easy mobile configuration

**Examples:**

```bash
# Add a Fedora desktop client
vpnhd client add laptop --description "Work laptop" --device-type desktop --os fedora

# Add an Android phone with QR code
vpnhd client add phone --device-type mobile --os android --generate-qr

# Add a server with specific IP
vpnhd client add backup-server --device-type server --os debian --vpn-ip 10.0.0.10

# Add a simple client with minimal options
vpnhd client add tablet
```

**What it does:**

1. Generates WireGuard keypair (private and public keys)
2. Auto-assigns next available VPN IP address (or uses specified IP)
3. Creates client configuration file
4. Updates server WireGuard configuration
5. Saves client metadata to database
6. Optionally generates QR code for mobile devices

---

### vpnhd client show

Display detailed information about a specific client.

```bash
vpnhd client show <name>
```

**Arguments:**

- `<name>` - Client name

**Examples:**

```bash
vpnhd client show laptop
```

**Output:**

```
╭───────────────── Client: laptop ─────────────────╮
│ Description    : Work laptop                     │
│ Device Type    : desktop                         │
│ OS             : fedora                          │
│ VPN IP         : 10.0.0.2                        │
│ Public Key     : abc123...def456                 │
│ Allowed IPs    : 10.0.0.2/32                     │
│ Created        : 2025-11-08 10:30:15             │
│ Status         : Enabled                         │
│ Connection     : Connected (5.2 MB transferred)  │
╰──────────────────────────────────────────────────╯
```

---

### vpnhd client status

Get real-time connection status for a client.

```bash
vpnhd client status <name>
```

**Arguments:**

- `<name>` - Client name

**Examples:**

```bash
vpnhd client status laptop
```

**Output:**

```
Client Status: laptop

Connection: Connected
Last Handshake: 45 seconds ago
Transfer:
  - Received: 3.2 MB
  - Sent: 1.8 MB
Endpoint: 192.168.1.100:51820
Allowed IPs: 10.0.0.2/32
```

---

### vpnhd client export

Export client configuration to a file.

```bash
vpnhd client export <name> <output-file> [OPTIONS]
```

**Arguments:**

- `<name>` - Client name
- `<output-file>` - Output file path

**Options:**

- `--qr` - Also generate QR code image
- `--format <format>` - Export format: wireguard (default), qrcode, or json

**Examples:**

```bash
# Export WireGuard configuration
vpnhd client export laptop laptop.conf

# Export with QR code for mobile
vpnhd client export phone phone.conf --qr

# Export as QR code only
vpnhd client export phone phone.png --format qrcode

# Export as JSON metadata
vpnhd client export laptop laptop.json --format json
```

---

### vpnhd client enable / disable

Enable or disable a client without deleting it.

```bash
vpnhd client enable <name>
vpnhd client disable <name>
```

**Arguments:**

- `<name>` - Client name

**Examples:**

```bash
# Disable a client temporarily
vpnhd client disable tablet

# Re-enable the client later
vpnhd client enable tablet
```

**What it does:**

- Updates client enabled status in database
- Updates server WireGuard configuration
- Restarts WireGuard service to apply changes

---

### vpnhd client remove

Remove a client completely.

```bash
vpnhd client remove <name> [OPTIONS]
```

**Arguments:**

- `<name>` - Client name

**Options:**

- `--force` - Skip confirmation prompt

**Examples:**

```bash
# Remove with confirmation
vpnhd client remove old-laptop

# Remove without confirmation
vpnhd client remove old-laptop --force
```

**Warning:** This action is irreversible. The client's keys and configuration will be permanently deleted.

---

### vpnhd client stats

Show statistics for all clients.

```bash
vpnhd client stats
```

**Examples:**

```bash
vpnhd client stats
```

**Output:**

```
VPN Client Statistics

Total Clients: 5
  - Enabled: 4
  - Disabled: 1

By Device Type:
  - Desktop: 2
  - Mobile: 2
  - Server: 1

By Status:
  - Connected: 3
  - Offline: 2

Total Transfer:
  - Received: 15.3 MB
  - Sent: 8.7 MB
```

---

## Performance Testing

Test and monitor VPN performance with latency, stability, and bandwidth measurements.

### vpnhd performance latency

Test network latency using ping.

```bash
vpnhd performance latency [OPTIONS]
```

**Options:**

- `--count <n>` - Number of ping packets to send (default: 10)
- `--timeout <seconds>` - Timeout for each ping (default: 5)
- `--server <ip>` - Server to ping (default: 8.8.8.8)

**Examples:**

```bash
# Basic latency test
vpnhd performance latency

# Test with 20 packets
vpnhd performance latency --count 20

# Test specific server with custom timeout
vpnhd performance latency --server 1.1.1.1 --timeout 10
```

**Output:**

```
╭──────────── Latency Test Results ────────────╮
│ Target Server    : 8.8.8.8                   │
│ Packets Sent     : 10                        │
│ Packets Received : 10                        │
│ Packet Loss      : 0.0%                      │
│                                               │
│ Latency Statistics:                          │
│   Minimum        : 12.3 ms                   │
│   Average        : 15.7 ms                   │
│   Maximum        : 21.4 ms                   │
│   Std Deviation  : 2.8 ms                    │
╰───────────────────────────────────────────────╯
```

---

### vpnhd performance stability

Test connection stability over time.

```bash
vpnhd performance stability [OPTIONS]
```

**Options:**

- `--duration <seconds>` - Test duration (default: 300)
- `--interval <seconds>` - Interval between pings (default: 1)
- `--server <ip>` - Server to ping (default: 8.8.8.8)

**Examples:**

```bash
# Basic stability test (5 minutes)
vpnhd performance stability

# Quick 60-second test
vpnhd performance stability --duration 60

# Long-duration test with 5-second intervals
vpnhd performance stability --duration 3600 --interval 5
```

**Output:**

```
╭────────── Connection Stability Test ──────────╮
│ Test Duration    : 300 seconds                │
│ Total Pings      : 300                        │
│ Successful       : 298                        │
│ Failed           : 2                          │
│ Uptime           : 99.3%                      │
│ Disconnections   : 1                          │
│ Avg Latency      : 16.2 ms                    │
╰────────────────────────────────────────────────╯
```

---

### vpnhd performance full

Run complete performance test suite.

```bash
vpnhd performance full [OPTIONS]
```

**Options:**

- `--bandwidth` - Include bandwidth test (requires iperf3 server)
- `--iperf-server <address>` - iperf3 server address (required if --bandwidth is set)
- `--latency-count <n>` - Number of ping packets for latency test (default: 20)
- `--stability-duration <seconds>` - Duration of stability test (default: 60)

**Examples:**

```bash
# Run latency and stability tests
vpnhd performance full

# Include bandwidth test
vpnhd performance full --bandwidth --iperf-server speedtest.example.com

# Custom test parameters
vpnhd performance full --latency-count 50 --stability-duration 300
```

**Output:**

```
╭─────────── Performance Test Report ───────────╮
│ Test Date        : 2025-11-08 10:45:30        │
│ VPN Interface    : wg0                        │
│ Test Server      : 8.8.8.8                    │
│                                                │
│ Latency Test:                                 │
│   Average        : 15.7 ms                    │
│   Packet Loss    : 0.0%                       │
│                                                │
│ Stability Test:                               │
│   Uptime         : 99.3%                      │
│   Disconnections : 1                          │
│                                                │
│ Bandwidth Test:                               │
│   Download       : 95.3 Mbps                  │
│   Upload         : 48.7 Mbps                  │
╰────────────────────────────────────────────────╯

Report saved to: ~/.config/vpnhd/performance/performance_report_20251108_104530.json
```

---

### vpnhd performance list

List all saved performance reports.

```bash
vpnhd performance list [OPTIONS]
```

**Options:**

- `--limit <n>` - Maximum number of reports to show (default: 10)

**Examples:**

```bash
# List recent reports
vpnhd performance list

# List last 20 reports
vpnhd performance list --limit 20
```

**Output:**

```
Recent Performance Reports:

1. 2025-11-08 10:45:30 - Latency: 15.7ms, Uptime: 99.3%
2. 2025-11-07 14:30:15 - Latency: 14.2ms, Uptime: 100.0%
3. 2025-11-06 09:15:42 - Latency: 16.8ms, Uptime: 98.7%

Total Reports: 3
```

---

### vpnhd performance stats

Show aggregated statistics from all performance reports.

```bash
vpnhd performance stats
```

**Examples:**

```bash
vpnhd performance stats
```

**Output:**

```
╭────── Performance Statistics ──────╮
│ Total Reports    : 15              │
│                                     │
│ Latency (Average):                 │
│   Mean           : 15.3 ms         │
│   Minimum        : 12.1 ms         │
│   Maximum        : 18.9 ms         │
│                                     │
│ Connection Quality:                │
│   Avg Packet Loss: 0.2%            │
│   Avg Uptime     : 99.5%           │
╰─────────────────────────────────────╯
```

---

## Backup & Restore

Create and restore backups of VPN configurations for disaster recovery.

### vpnhd backup create

Create a new backup of VPN configuration.

```bash
vpnhd backup create [OPTIONS]
```

**Options:**

- `--description <text>` - Backup description
- `--no-wireguard` - Exclude WireGuard configuration
- `--no-ssh` - Exclude SSH keys
- `--no-config` - Exclude VPNHD configuration
- `--no-clients` - Exclude client database

**Examples:**

```bash
# Create full backup
vpnhd backup create --description "Pre-upgrade backup"

# Backup only client database and config
vpnhd backup create --no-wireguard --no-ssh

# Quick config backup
vpnhd backup create --no-wireguard --no-ssh --no-clients
```

**Output:**

```
Creating backup...

Backup created successfully!

Backup ID: backup_20251108_104530
Size: 124.5 KB
Checksum: a1b2c3d4e5f6...
Location: ~/.config/vpnhd/backups/backup_20251108_104530.tar.gz

Included components:
  - VPNHD configuration
  - Client database
  - WireGuard configuration
  - SSH keys
```

---

### vpnhd backup list

List all available backups.

```bash
vpnhd backup list [OPTIONS]
```

**Options:**

- `--format <format>` - Output format: table (default) or json

**Examples:**

```bash
# List backups
vpnhd backup list

# List as JSON
vpnhd backup list --format json
```

**Output:**

```
╭───────────────────────── VPN Backups ─────────────────────────╮
│ Backup ID               │ Date       │ Size    │ Description  │
├─────────────────────────┼────────────┼─────────┼──────────────┤
│ backup_20251108_104530  │ 2025-11-08 │ 124.5KB │ Pre-upgrade  │
│ backup_20251107_093015  │ 2025-11-07 │ 118.2KB │ Daily backup │
│ backup_20251106_150000  │ 2025-11-06 │ 115.8KB │ Manual       │
╰─────────────────────────┴────────────┴─────────┴──────────────╯
```

---

### vpnhd backup restore

Restore from a backup.

```bash
vpnhd backup restore <backup-id> [OPTIONS]
```

**Arguments:**

- `<backup-id>` - Backup ID to restore

**Options:**

- `--no-wireguard` - Don't restore WireGuard configuration
- `--no-ssh` - Don't restore SSH keys
- `--no-config` - Don't restore VPNHD configuration
- `--no-clients` - Don't restore client database
- `--skip-verify` - Skip checksum verification (not recommended)

**Examples:**

```bash
# Full restore
vpnhd backup restore backup_20251108_104530

# Restore only client database
vpnhd backup restore backup_20251108_104530 --no-wireguard --no-ssh --no-config

# Restore without verification (not recommended)
vpnhd backup restore backup_20251108_104530 --skip-verify
```

**Output:**

```
Restoring backup: backup_20251108_104530

Verifying backup integrity... ✓
Checksum verified

Restoring components:
  - VPNHD configuration... ✓
  - Client database... ✓
  - WireGuard configuration... ⚠️  (requires sudo, see instructions)
  - SSH keys... ✓

Backup restored successfully!

Note: WireGuard configuration requires manual sudo operation.
See: /tmp/wireguard_restore_instructions.txt
```

---

### vpnhd backup verify

Verify backup integrity.

```bash
vpnhd backup verify <backup-id>
```

**Arguments:**

- `<backup-id>` - Backup ID to verify

**Examples:**

```bash
vpnhd backup verify backup_20251108_104530
```

**Output:**

```
Verifying backup: backup_20251108_104530

Checksum verification... ✓
Archive integrity... ✓
Metadata validation... ✓

Backup is valid and intact.
```

---

### vpnhd backup delete

Delete a backup.

```bash
vpnhd backup delete <backup-id> [OPTIONS]
```

**Arguments:**

- `<backup-id>` - Backup ID to delete

**Options:**

- `--force` - Skip confirmation prompt

**Examples:**

```bash
# Delete with confirmation
vpnhd backup delete backup_20251106_150000

# Delete without confirmation
vpnhd backup delete backup_20251106_150000 --force
```

---

### vpnhd backup export

Export a backup to external location.

```bash
vpnhd backup export <backup-id> <destination>
```

**Arguments:**

- `<backup-id>` - Backup ID to export
- `<destination>` - Destination directory path

**Examples:**

```bash
# Export to USB drive
vpnhd backup export backup_20251108_104530 /mnt/usb/vpnhd-backups

# Export to network share
vpnhd backup export backup_20251108_104530 /mnt/nas/backups
```

**Output:**

```
Exporting backup to /mnt/usb/vpnhd-backups...

Files exported:
  - backup_20251108_104530.tar.gz
  - backup_20251108_104530_metadata.json

Export completed successfully!
```

---

### vpnhd backup import

Import a backup from external location.

```bash
vpnhd backup import <source-path>
```

**Arguments:**

- `<source-path>` - Path to backup archive (.tar.gz)

**Examples:**

```bash
# Import from USB drive
vpnhd backup import /mnt/usb/vpnhd-backups/backup_20251108_104530.tar.gz

# Import from network share
vpnhd backup import /mnt/nas/backups/backup_20251108_104530.tar.gz
```

**Output:**

```
Importing backup from /mnt/usb/vpnhd-backups/backup_20251108_104530.tar.gz...

Backup imported successfully!
Backup ID: backup_20251108_104530
```

---

### vpnhd backup cleanup

Clean up old backups, keeping only the most recent.

```bash
vpnhd backup cleanup [OPTIONS]
```

**Options:**

- `--keep <n>` - Number of recent backups to keep (default: 10)

**Examples:**

```bash
# Keep 10 most recent backups
vpnhd backup cleanup

# Keep only 5 most recent backups
vpnhd backup cleanup --keep 5

# Keep 20 backups
vpnhd backup cleanup --keep 20
```

**Output:**

```
Cleaning up old backups...

Keeping 10 most recent backups
Deleted 3 old backups:
  - backup_20251101_120000
  - backup_20251102_093000
  - backup_20251103_150000

Cleanup completed!
```

---

## Common Options

These options are available across most commands:

- `--help` - Show command-specific help
- `--verbose` or `-v` - Enable verbose output
- `--quiet` or `-q` - Suppress non-error output
- `--config <path>` - Use alternate configuration file

---

## Exit Codes

VPNHD uses standard exit codes:

- `0` - Success
- `1` - General error
- `2` - Command-line usage error
- `3` - Configuration error
- `4` - Permission denied (requires sudo/root)
- `5` - Resource not found
- `130` - Interrupted by user (Ctrl+C)

**Example:**

```bash
vpnhd client add laptop
echo $?  # Prints exit code
```

---

## Environment Variables

- `VPNHD_CONFIG_DIR` - Override default config directory (~/.config/vpnhd)
- `VPNHD_LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `VPNHD_NO_COLOR` - Disable colored output

**Example:**

```bash
# Use custom config directory
export VPNHD_CONFIG_DIR=/etc/vpnhd
vpnhd client list

# Enable debug logging
export VPNHD_LOG_LEVEL=DEBUG
vpnhd backup create

# Disable colors for scripting
export VPNHD_NO_COLOR=1
vpnhd client list --format simple
```

---

## Tips and Best Practices

### Client Management

1. **Naming Convention**: Use descriptive names (laptop-work, phone-personal, server-backup)
2. **Device Types**: Properly categorize devices for better organization
3. **Regular Audits**: Periodically review and remove unused clients
4. **QR Codes**: Always generate QR codes for mobile devices for easy setup

### Performance Testing

1. **Baseline Tests**: Run initial tests to establish baseline performance
2. **Regular Monitoring**: Schedule periodic tests to track performance over time
3. **Problem Diagnosis**: Run stability tests when experiencing connection issues
4. **Save Reports**: Keep historical reports for performance trend analysis

### Backup & Restore

1. **Regular Backups**: Create backups before major changes
2. **External Storage**: Export important backups to external storage
3. **Verify Backups**: Periodically verify backup integrity
4. **Document Backups**: Use descriptive descriptions for easy identification
5. **Cleanup Policy**: Establish a retention policy (e.g., keep last 10 backups)
6. **Test Restores**: Periodically test restore procedures to ensure they work

---

For more information, see:
- [Client Management Guide](CLIENT_MANAGEMENT.md)
- [Performance Testing Guide](PERFORMANCE_TESTING.md)
- [Backup & Restore Guide](BACKUP_RESTORE.md)
- [User Guide](USER_GUIDE.md)
