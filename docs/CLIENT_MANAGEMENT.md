# Client Management Guide

Complete guide to managing VPN clients with VPNHD.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Managing Clients](#managing-clients)
- [Client Lifecycle](#client-lifecycle)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

VPNHD provides comprehensive client management capabilities that go beyond basic WireGuard configuration. The client management system includes:

- **Metadata Tracking**: Device type, OS, description, creation date
- **Real-time Status**: Connection state, data transfer, last handshake
- **Lifecycle Management**: Enable/disable clients without deleting them
- **Multiple Export Formats**: WireGuard config, QR codes, JSON metadata
- **Database-backed Storage**: Persistent client information in JSON database

### Architecture

```
┌─────────────────────────────────────────────────┐
│          Client Management System               │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────┐      ┌──────────────────┐  │
│  │ Client Database│      │ WireGuard Config │  │
│  │  (clients.json)│◄────►│     (wg0.conf)   │  │
│  └────────────────┘      └──────────────────┘  │
│          │                       │              │
│          ▼                       ▼              │
│  ┌────────────────┐      ┌──────────────────┐  │
│  │ Client Metadata│      │  Real-time Stats │  │
│  │  - Device Type │      │  - Connected     │  │
│  │  - OS          │      │  - Transfer      │  │
│  │  - Description │      │  - Handshake     │  │
│  └────────────────┘      └──────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Client Database

Client information is stored in `~/.config/vpnhd/clients.json`:

```json
{
  "laptop": {
    "name": "laptop",
    "public_key": "abc123...def456",
    "vpn_ip": "10.0.0.2",
    "allowed_ips": "10.0.0.2/32",
    "description": "Work laptop",
    "device_type": "desktop",
    "os": "fedora",
    "created_at": "2025-11-08T10:30:15",
    "enabled": true
  }
}
```

## Quick Start

### Adding Your First Client

```bash
# Add a desktop client
vpnhd client add laptop --description "Work laptop" --device-type desktop --os fedora

# Add a mobile client with QR code
vpnhd client add phone --device-type mobile --os android --generate-qr

# View all clients
vpnhd client list
```

### Connecting the Client

After adding a client, you'll need to configure it on the device:

**For Desktop/Server:**
```bash
# Export the configuration
vpnhd client export laptop laptop.conf

# Copy to the client device
scp laptop.conf user@laptop:/tmp/

# On the client device:
sudo cp /tmp/laptop.conf /etc/wireguard/wg0.conf
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

**For Mobile:**
```bash
# Generate QR code
vpnhd client export phone phone.conf --qr

# Open WireGuard app on phone
# Tap "+" → "Create from QR code"
# Scan the QR code displayed or saved as phone.png
```

### Checking Client Status

```bash
# Check if client is connected
vpnhd client status laptop

# View all client statistics
vpnhd client stats
```

## Managing Clients

### Adding Clients

#### Basic Client Addition

```bash
vpnhd client add <name>
```

This creates a client with:
- Auto-generated WireGuard keys
- Auto-assigned VPN IP address
- Default device type (desktop)
- Default OS (linux)

#### Advanced Client Addition

```bash
vpnhd client add server-backup \
  --description "Backup server in datacenter" \
  --device-type server \
  --os debian \
  --vpn-ip 10.0.0.100
```

Specify all metadata upfront for better organization.

#### Mobile Client with QR Code

```bash
vpnhd client add iphone \
  --description "Personal iPhone" \
  --device-type mobile \
  --os ios \
  --generate-qr
```

The `--generate-qr` flag creates a QR code that can be scanned directly from the terminal or saved as an image.

### Listing Clients

#### View All Clients

```bash
vpnhd client list
```

Output:
```
╭─────────────────────────── VPN Clients ───────────────────────────╮
│ Name      │ Device Type │ OS      │ VPN IP       │ Status    │    │
├───────────┼─────────────┼─────────┼──────────────┼───────────┼────┤
│ laptop    │ desktop     │ fedora  │ 10.0.0.2     │ Connected │ ✓  │
│ phone     │ mobile      │ android │ 10.0.0.3     │ Offline   │ ✓  │
│ server    │ server      │ debian  │ 10.0.0.4     │ Connected │ ✓  │
│ tablet    │ mobile      │ ios     │ 10.0.0.5     │ Offline   │ ✗  │
╰───────────┴─────────────┴─────────┴──────────────┴───────────┴────╯
```

#### Filter by Status

```bash
# Show only enabled clients
vpnhd client list --enabled

# Show only mobile devices
vpnhd client list --device-type mobile
```

#### JSON Output

```bash
vpnhd client list --format json
```

Useful for scripting and automation.

### Viewing Client Details

```bash
vpnhd client show laptop
```

Output:
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

### Checking Connection Status

```bash
vpnhd client status laptop
```

Output:
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

**Note:** Connection status is retrieved in real-time from WireGuard using `wg show dump`.

### Exporting Client Configuration

#### WireGuard Configuration File

```bash
vpnhd client export laptop laptop.conf
```

Creates a standard WireGuard configuration file that can be used on any WireGuard client.

#### QR Code for Mobile

```bash
vpnhd client export phone phone.conf --qr
```

Creates both:
- `phone.conf` - WireGuard configuration file
- `phone.png` - QR code image

#### QR Code Only

```bash
vpnhd client export phone phone.png --format qrcode
```

Generates only the QR code image without the configuration file.

#### JSON Metadata

```bash
vpnhd client export laptop laptop.json --format json
```

Exports all client metadata in JSON format for backup or analysis.

### Enabling and Disabling Clients

#### Disable a Client Temporarily

```bash
vpnhd client disable tablet
```

What happens:
1. Client marked as disabled in database
2. Client removed from WireGuard server configuration
3. WireGuard service restarted
4. Client can no longer connect
5. Client metadata preserved for future re-enabling

#### Re-enable a Client

```bash
vpnhd client enable tablet
```

What happens:
1. Client marked as enabled in database
2. Client added back to WireGuard server configuration
3. WireGuard service restarted
4. Client can connect again

**Use case:** Temporarily disable a lost/stolen device without losing its configuration.

### Removing Clients

#### Remove with Confirmation

```bash
vpnhd client remove old-laptop
```

You'll be prompted:
```
Are you sure you want to remove client 'old-laptop'? [y/N]:
```

#### Force Remove (No Confirmation)

```bash
vpnhd client remove old-laptop --force
```

**Warning:** This permanently deletes:
- Client keys
- Client metadata
- WireGuard configuration entry

The VPN IP address becomes available for reuse.

### Client Statistics

```bash
vpnhd client stats
```

Output:
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

## Client Lifecycle

### Complete Lifecycle Example

```bash
# 1. Add new client
vpnhd client add laptop --description "Work laptop" --os fedora

# 2. Export configuration
vpnhd client export laptop laptop.conf

# 3. Configure client device
# (Copy laptop.conf to the device and set up WireGuard)

# 4. Verify connection
vpnhd client status laptop

# 5. Monitor usage
vpnhd client show laptop

# 6. Temporarily disable (e.g., device lost)
vpnhd client disable laptop

# 7. Re-enable (e.g., device found)
vpnhd client enable laptop

# 8. Permanently remove (e.g., device decommissioned)
vpnhd client remove laptop
```

### IP Address Management

VPNHD automatically manages IP address assignment:

#### Auto-assignment
```bash
vpnhd client add laptop
# Assigns next available IP (e.g., 10.0.0.2)
```

#### Manual assignment
```bash
vpnhd client add server --vpn-ip 10.0.0.100
# Uses specified IP if available
```

#### IP Address Pool

Default VPN subnet: `10.0.0.0/24`
- `10.0.0.1` - Server (reserved)
- `10.0.0.2-254` - Available for clients

**IP addresses are reused** after client removal.

## Best Practices

### Naming Conventions

Use descriptive, meaningful names:

**Good:**
- `laptop-work`
- `phone-personal`
- `server-backup-nyc`
- `tablet-kids`

**Avoid:**
- `client1`, `client2` (not descriptive)
- `myphone` (ambiguous)
- `test` (unclear purpose)

### Metadata Organization

Always provide metadata for better organization:

```bash
vpnhd client add laptop-work \
  --description "Dell XPS 15 - Work laptop" \
  --device-type desktop \
  --os fedora

vpnhd client add phone-personal \
  --description "Pixel 8 - Personal phone" \
  --device-type mobile \
  --os android
```

### Device Type Guidelines

- **desktop**: Laptops, desktops, workstations
- **mobile**: Phones, tablets (iOS/Android)
- **server**: Servers, VMs, containers

This helps with filtering and organization.

### Regular Audits

Periodically review and clean up unused clients:

```bash
# List all clients
vpnhd client list

# Check for inactive clients
# (Look for "Offline" status with old handshake dates)

# Remove obsolete clients
vpnhd client remove old-device
```

### Security Practices

1. **Remove Lost/Stolen Devices Immediately**
   ```bash
   vpnhd client disable stolen-phone
   # Later, if not recovered:
   vpnhd client remove stolen-phone
   ```

2. **Regular Key Rotation** (Advanced)
   ```bash
   # Remove old client
   vpnhd client remove laptop

   # Add with same name but new keys
   vpnhd client add laptop

   # Reconfigure the device with new config
   ```

3. **Limit Client Scope**
   - Use allowed IPs to restrict access
   - Consider separate VPN servers for different security zones

### Mobile Devices

For mobile clients, always generate QR codes:

```bash
vpnhd client add phone --device-type mobile --os android --generate-qr
```

Advantages:
- Faster setup (scan vs manual entry)
- No transcription errors
- Better user experience

### Documentation

Keep notes in client descriptions:

```bash
vpnhd client add server-prod \
  --description "Production web server - Ubuntu 22.04 - Contact: admin@example.com"
```

## Troubleshooting

### Client Won't Connect

**Check client status:**
```bash
vpnhd client status laptop
```

**Common issues:**

1. **Client Disabled**
   ```bash
   vpnhd client enable laptop
   ```

2. **WireGuard Service Not Running**
   ```bash
   # On server:
   sudo systemctl status wg-quick@wg0

   # On client:
   sudo systemctl status wg-quick@wg0
   ```

3. **Firewall Blocking**
   ```bash
   # Check UFW status
   sudo ufw status

   # Ensure WireGuard port is open (default: 51820)
   sudo ufw allow 51820/udp
   ```

4. **Wrong Keys/Configuration**
   ```bash
   # Re-export and reconfigure
   vpnhd client export laptop laptop.conf
   # Copy to client and reload
   ```

### "Client Not Found" Error

```bash
vpnhd client show nonexistent
# Error: Client 'nonexistent' not found
```

**Solutions:**
- Check client name spelling
- List all clients to verify: `vpnhd client list`
- Client may have been deleted

### "IP Address Already in Use"

```bash
vpnhd client add laptop --vpn-ip 10.0.0.2
# Error: IP address 10.0.0.2 already assigned to client 'existing'
```

**Solutions:**
- Use auto-assignment (omit --vpn-ip)
- Choose a different IP address
- Remove the conflicting client if no longer needed

### QR Code Not Displaying

**Issue:** Terminal doesn't support QR code display

**Solutions:**
```bash
# Save to file instead
vpnhd client export phone phone.png --format qrcode

# Display with an image viewer
xdg-open phone.png
```

### Stale Connection Status

**Issue:** Client shows "Connected" but isn't really connected

**Cause:** WireGuard keeps showing connection until handshake timeout (120-180 seconds)

**Solution:** Wait for handshake timeout or check "Last Handshake" time:
```bash
vpnhd client status laptop
# Last Handshake: 5 minutes ago (stale - likely disconnected)
```

## Advanced Topics

### Scripting with Client Management

#### List All Connected Clients (JSON)

```bash
#!/bin/bash
vpnhd client list --format json | jq '.[] | select(.status == "Connected") | .name'
```

#### Automated Client Provisioning

```bash
#!/bin/bash
# Add multiple clients from a CSV file

while IFS=, read -r name device_type os description; do
  vpnhd client add "$name" \
    --device-type "$device_type" \
    --os "$os" \
    --description "$description"
done < clients.csv
```

Example `clients.csv`:
```csv
laptop-alice,desktop,fedora,Alice's work laptop
phone-bob,mobile,android,Bob's phone
server-prod,server,debian,Production web server
```

#### Daily Connection Report

```bash
#!/bin/bash
# Send daily email report of connected clients

OUTPUT=$(vpnhd client stats)
echo "$OUTPUT" | mail -s "VPN Daily Report" admin@example.com
```

### Integration with Configuration Management

#### Ansible Example

```yaml
- name: Add VPN client
  command: >
    vpnhd client add {{ client_name }}
    --device-type {{ device_type }}
    --os {{ client_os }}
    --description "{{ description }}"

- name: Export client configuration
  command: >
    vpnhd client export {{ client_name }} /tmp/{{ client_name }}.conf

- name: Fetch client configuration
  fetch:
    src: /tmp/{{ client_name }}.conf
    dest: ./configs/{{ client_name }}.conf
```

### Bulk Operations

#### Disable All Mobile Devices

```bash
#!/bin/bash
for client in $(vpnhd client list --device-type mobile --format simple | awk '{print $1}'); do
  vpnhd client disable "$client"
done
```

#### Re-export All Configurations

```bash
#!/bin/bash
mkdir -p /backup/vpn-configs
for client in $(vpnhd client list --format simple | awk '{print $1}'); do
  vpnhd client export "$client" "/backup/vpn-configs/${client}.conf"
done
```

### Custom Allowed IPs

By default, clients use `/32` (single IP). For advanced scenarios:

**Edit client database manually** (`~/.config/vpnhd/clients.json`):

```json
{
  "laptop": {
    "allowed_ips": "10.0.0.2/32, 192.168.1.0/24"
  }
}
```

**Then regenerate WireGuard config:**
```bash
# This would require a server config regeneration
# (Feature for future enhancement)
```

### Database Backup

Client database is critical for disaster recovery:

```bash
# Include in regular backups
vpnhd backup create --description "Daily backup"

# Or manually copy
cp ~/.config/vpnhd/clients.json /backup/clients-$(date +%Y%m%d).json
```

### Migration to New Server

```bash
# On old server:
vpnhd backup create --description "Migration backup"
vpnhd backup export backup_YYYYMMDD_HHMMSS /tmp/

# Transfer to new server
scp /tmp/backup_*.tar.gz newserver:/tmp/

# On new server:
vpnhd backup import /tmp/backup_YYYYMMDD_HHMMSS.tar.gz
vpnhd backup restore backup_YYYYMMDD_HHMMSS
```

---

## Summary

Key takeaways:

1. **Use descriptive names and metadata** for better organization
2. **Generate QR codes for mobile devices** for easier setup
3. **Regularly audit clients** and remove unused ones
4. **Disable instead of remove** for temporary situations
5. **Check real-time status** with `vpnhd client status`
6. **Backup client database** regularly
7. **Use `--force` cautiously** to avoid accidental deletions

For more information:
- [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
- [User Guide](USER_GUIDE.md) - General VPNHD usage
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
