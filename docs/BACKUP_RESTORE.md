# Backup & Restore Guide

Complete guide to backing up and restoring VPN configurations with VPNHD.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Creating Backups](#creating-backups)
- [Restoring Backups](#restoring-backups)
- [Managing Backups](#managing-backups)
- [Best Practices](#best-practices)
- [Disaster Recovery](#disaster-recovery)
- [Advanced Topics](#advanced-topics)

## Overview

VPNHD provides comprehensive backup and restore functionality to protect your VPN configuration and ensure business continuity.

### What Gets Backed Up

Backups can include:

1. **VPNHD Configuration** (`~/.config/vpnhd/config.json`)
   - Network settings
   - Server information
   - Phase completion status

2. **Client Database** (`~/.config/vpnhd/clients.json`)
   - Client metadata
   - Device information
   - All client configurations

3. **WireGuard Configuration** (`/etc/wireguard/wg0.conf`)
   - Server keys
   - Peer configurations
   - Network settings

4. **SSH Keys** (`~/.ssh/vpnhd_*`)
   - VPN-related SSH keys
   - Authentication credentials

### Backup Architecture

```
┌─────────────────────────────────────────────────┐
│            Backup System                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Source Components                       │  │
│  ├──────────────────────────────────────────┤  │
│  │  - ~/.config/vpnhd/config.json           │  │
│  │  - ~/.config/vpnhd/clients.json          │  │
│  │  - /etc/wireguard/wg0.conf (if readable) │  │
│  │  - ~/.ssh/vpnhd_*                        │  │
│  └──────────────────────────────────────────┘  │
│                    │                             │
│                    ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │  Backup Archive (tar.gz)                 │  │
│  ├──────────────────────────────────────────┤  │
│  │  - Compressed with gzip                  │  │
│  │  - SHA-256 checksum                      │  │
│  │  - Metadata JSON                         │  │
│  └──────────────────────────────────────────┘  │
│                    │                             │
│                    ▼                             │
│  ┌──────────────────────────────────────────┐  │
│  │  Storage Location                        │  │
│  ├──────────────────────────────────────────┤  │
│  │  ~/.config/vpnhd/backups/                │  │
│  │    - backup_YYYYMMDD_HHMMSS.tar.gz       │  │
│  │    - backup_YYYYMMDD_HHMMSS_metadata.json│  │
│  └──────────────────────────────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Backup Metadata

Each backup includes comprehensive metadata:

```json
{
  "backup_id": "backup_20251108_104530",
  "created_at": "2025-11-08T10:45:30",
  "description": "Pre-upgrade backup",
  "version": "1.0.0",
  "size_bytes": 127456,
  "checksum": "a1b2c3d4e5f6789...",
  "includes": [
    "vpnhd_config",
    "client_database",
    "wireguard_config",
    "ssh_keys"
  ]
}
```

## Quick Start

### Create Your First Backup

```bash
# Create a full backup
vpnhd backup create --description "Initial backup"
```

### List Backups

```bash
vpnhd backup list
```

### Restore from Backup

```bash
# List backups to find the ID
vpnhd backup list

# Restore
vpnhd backup restore backup_20251108_104530
```

### Export for Safekeeping

```bash
# Export to USB drive
vpnhd backup export backup_20251108_104530 /mnt/usb/vpnhd-backups
```

## Creating Backups

### Full Backup

Create a complete backup of all components:

```bash
vpnhd backup create --description "Full system backup"
```

**Includes:**
- VPNHD configuration
- Client database
- WireGuard configuration (if readable)
- SSH keys

### Selective Backups

#### Configuration Only

```bash
vpnhd backup create --description "Config only" --no-wireguard --no-ssh --no-clients
```

**Use case:** Quick configuration backup before changes

#### Clients Only

```bash
vpnhd backup create --description "Client database" --no-wireguard --no-ssh --no-config
```

**Use case:** Before bulk client operations

#### Everything Except WireGuard

```bash
vpnhd backup create --description "No WireGuard" --no-wireguard
```

**Use case:** When WireGuard config requires sudo access

### Backup Output

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
  - WireGuard configuration (requires sudo)
  - SSH keys
```

### When to Create Backups

**Before:**
- Major configuration changes
- System upgrades
- Adding/removing multiple clients
- Changing network settings
- Server maintenance

**Regular Schedule:**
- Daily (automated)
- Before each phase completion
- Before troubleshooting
- After significant changes

## Restoring Backups

### Full Restore

Restore all components from a backup:

```bash
vpnhd backup restore backup_20251108_104530
```

**What happens:**
1. Backup integrity verified (SHA-256 checksum)
2. Archive extracted to temporary directory
3. Current files backed up (`.bak` extension)
4. Files restored from backup
5. Temporary directory cleaned up

### Selective Restore

#### Configuration Only

```bash
vpnhd backup restore backup_20251108_104530 --no-wireguard --no-ssh --no-clients
```

**Use case:** Restore only VPNHD settings

#### Clients Only

```bash
vpnhd backup restore backup_20251108_104530 --no-wireguard --no-ssh --no-config
```

**Use case:** Restore client database after accidental deletion

#### Skip Verification

```bash
vpnhd backup restore backup_20251108_104530 --skip-verify
```

**Warning:** Only use if checksum verification fails but you trust the backup.

### Restore Output

```
Restoring backup: backup_20251108_104530

Verifying backup integrity... ✓
Checksum verified

Restoring components:
  - VPNHD configuration... ✓ (backed up to config.json.bak)
  - Client database... ✓ (backed up to clients.json.bak)
  - WireGuard configuration... ⚠️  (requires sudo)
  - SSH keys... ✓

Backup restored successfully!

Note: WireGuard configuration requires manual sudo operation.
Extracted file: /tmp/restore/wireguard/wg0.conf
Manual command: sudo cp /tmp/restore/wireguard/wg0.conf /etc/wireguard/wg0.conf
```

### WireGuard Configuration Restore

WireGuard configuration (`/etc/wireguard/wg0.conf`) requires root access.

**Manual restore:**

```bash
# After running backup restore command
sudo cp /tmp/restore/wireguard/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl restart wg-quick@wg0
```

**Automated restore (as root):**

```bash
# Run as root
sudo vpnhd backup restore backup_20251108_104530
```

## Managing Backups

### Listing Backups

#### Table Format (Default)

```bash
vpnhd backup list
```

Output:
```
╭───────────────────────── VPN Backups ─────────────────────────╮
│ Backup ID               │ Date       │ Size    │ Description  │
├─────────────────────────┼────────────┼─────────┼──────────────┤
│ backup_20251108_104530  │ 2025-11-08 │ 124.5KB │ Pre-upgrade  │
│ backup_20251107_093015  │ 2025-11-07 │ 118.2KB │ Daily backup │
│ backup_20251106_150000  │ 2025-11-06 │ 115.8KB │ Manual       │
╰─────────────────────────┴────────────┴─────────┴──────────────╯
```

#### JSON Format

```bash
vpnhd backup list --format json
```

**Use case:** Scripting and automation

### Verifying Backups

Verify backup integrity without restoring:

```bash
vpnhd backup verify backup_20251108_104530
```

Output:
```
Verifying backup: backup_20251108_104530

Checksum verification... ✓
Archive integrity... ✓
Metadata validation... ✓

Backup is valid and intact.
```

**What it checks:**
1. SHA-256 checksum matches
2. tar.gz archive can be opened
3. Metadata file is valid JSON

**When to verify:**
- After creating backup
- Before restoring backup
- Periodically for stored backups
- After transferring backups

### Deleting Backups

#### Delete with Confirmation

```bash
vpnhd backup delete backup_20251106_150000
```

Prompts:
```
Are you sure you want to delete backup 'backup_20251106_150000'? [y/N]:
```

#### Force Delete (No Confirmation)

```bash
vpnhd backup delete backup_20251106_150000 --force
```

**Warning:** This permanently deletes the backup archive and metadata.

### Cleaning Up Old Backups

Automatically remove old backups, keeping only recent ones:

```bash
# Keep 10 most recent backups (default)
vpnhd backup cleanup

# Keep only 5 most recent backups
vpnhd backup cleanup --keep 5

# Keep 20 backups
vpnhd backup cleanup --keep 20
```

Output:
```
Cleaning up old backups...

Keeping 10 most recent backups
Deleted 3 old backups:
  - backup_20251101_120000 (127 KB)
  - backup_20251102_093000 (119 KB)
  - backup_20251103_150000 (122 KB)

Total space freed: 368 KB
Cleanup completed!
```

**Use case:** Automated cleanup in scheduled tasks

## Best Practices

### Backup Strategy

#### 3-2-1 Rule

Follow the 3-2-1 backup rule:

- **3** copies of your data (original + 2 backups)
- **2** different storage media
- **1** copy offsite

**Example implementation:**

```bash
# 1. Create backup
vpnhd backup create --description "Daily backup"

# 2. Keep local copy (automatically saved)

# 3. Export to external drive (2nd medium)
vpnhd backup export backup_20251108_104530 /mnt/usb/vpnhd-backups

# 4. Copy to cloud/remote server (offsite)
scp ~/.config/vpnhd/backups/backup_20251108_104530.* \
    user@remote-server:/backups/vpnhd/
```

#### Backup Frequency

**Recommended schedule:**

- **Daily:** Automated backup (retention: 7 days)
- **Weekly:** Exported to external storage (retention: 4 weeks)
- **Monthly:** Offsite backup (retention: 12 months)
- **Before changes:** Manual backup before any major changes

**Cron example:**

```bash
# Daily backup at 2 AM
0 2 * * * vpnhd backup create --description "Automated daily backup" && vpnhd backup cleanup --keep 7

# Weekly export on Sundays at 3 AM
0 3 * * 0 vpnhd backup export $(vpnhd backup list --format json | jq -r '.[0].backup_id') /mnt/usb/vpnhd-backups
```

### Naming and Documentation

#### Use Descriptive Names

**Good:**
```bash
vpnhd backup create --description "Pre-upgrade to Debian 13"
vpnhd backup create --description "Before adding 10 new clients"
vpnhd backup create --description "Post-security-hardening"
```

**Avoid:**
```bash
vpnhd backup create --description "backup"
vpnhd backup create --description "test"
vpnhd backup create  # (no description)
```

#### Backup Log

Maintain a backup log:

```bash
# /var/log/vpnhd-backups.log
2025-11-08 10:45:30 - backup_20251108_104530 - Pre-upgrade to Debian 13
2025-11-07 02:00:15 - backup_20251107_020015 - Automated daily backup
2025-11-06 15:30:00 - backup_20251106_153000 - Before client migration
```

### Storage Management

#### Monitor Disk Space

```bash
# Check backup directory size
du -sh ~/.config/vpnhd/backups

# Check individual backup sizes
vpnhd backup list
```

#### Storage Locations

**Local storage:**
- `~/.config/vpnhd/backups/` - Default location
- Pros: Fast access
- Cons: Same disk as original data

**External storage:**
- USB drive: `/mnt/usb/vpnhd-backups/`
- Network share: `/mnt/nas/backups/vpnhd/`
- Pros: Physical separation
- Cons: May not be always available

**Cloud/Remote storage:**
- Remote server via SCP/SFTP
- Cloud storage (S3, Google Drive, etc.)
- Pros: Offsite protection
- Cons: Network dependency, potential costs

### Security Considerations

#### Backup Encryption

Backups contain sensitive information (keys, configurations).

**Encrypt before external storage:**

```bash
# Create backup
vpnhd backup create --description "Secure backup"

# Encrypt with GPG
gpg --encrypt --recipient your-email@example.com \
    ~/.config/vpnhd/backups/backup_20251108_104530.tar.gz

# Export encrypted file
cp ~/.config/vpnhd/backups/backup_20251108_104530.tar.gz.gpg \
   /mnt/usb/secure-backups/
```

**Decrypt when needed:**

```bash
# Decrypt
gpg --decrypt backup_20251108_104530.tar.gz.gpg > backup_20251108_104530.tar.gz

# Import and restore
vpnhd backup import backup_20251108_104530.tar.gz
vpnhd backup restore backup_20251108_104530
```

#### Access Control

Protect backup files:

```bash
# Restrict permissions
chmod 600 ~/.config/vpnhd/backups/*.tar.gz
chmod 600 ~/.config/vpnhd/backups/*_metadata.json

# Set directory permissions
chmod 700 ~/.config/vpnhd/backups
```

### Testing Restores

#### Periodic Restore Testing

Test restore procedures quarterly:

```bash
# 1. Create test backup
vpnhd backup create --description "Restore test $(date +%Y-%m-%d)"

# 2. Document current state
vpnhd client list > /tmp/before-restore.txt

# 3. Make a minor change (e.g., add test client)
vpnhd client add restore-test --description "Test client"

# 4. Restore backup
vpnhd backup restore backup_YYYYMMDD_HHMMSS

# 5. Verify restoration
vpnhd client list > /tmp/after-restore.txt
diff /tmp/before-restore.txt /tmp/after-restore.txt

# 6. Clean up
rm /tmp/before-restore.txt /tmp/after-restore.txt
```

**Document results:** Keep a log of successful restore tests.

## Disaster Recovery

### Complete System Loss

#### Scenario: Server Hard Drive Failure

**Prerequisites:**
- Recent backup exported to external storage
- New server with Debian 12/13 installed
- VPNHD installed on new server

**Recovery procedure:**

```bash
# 1. Install VPNHD on new server
git clone https://github.com/orpheus497/vpnhd.git
cd vpnhd
sudo bash scripts/install.sh

# 2. Import backup from external storage
vpnhd backup import /mnt/usb/vpnhd-backups/backup_20251108_104530.tar.gz

# 3. Restore configuration
vpnhd backup restore backup_20251108_104530

# 4. Restore WireGuard config (requires sudo)
sudo cp /tmp/restore/wireguard/wg0.conf /etc/wireguard/wg0.conf
sudo chmod 600 /etc/wireguard/wg0.conf

# 5. Start WireGuard
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# 6. Verify restoration
vpnhd client list
vpnhd client stats

# 7. Test connectivity
vpnhd performance latency
```

**Recovery Time Objective (RTO):** ~30 minutes (depending on backup size and network)

**Recovery Point Objective (RPO):** Last backup (daily = 24 hours max data loss)

### Partial Data Loss

#### Scenario: Accidental Client Database Deletion

```bash
# Oh no! Accidentally deleted clients.json
rm ~/.config/vpnhd/clients.json

# Recovery:
# 1. Find most recent backup
vpnhd backup list

# 2. Restore only client database
vpnhd backup restore backup_20251108_104530 \
  --no-wireguard --no-ssh --no-config

# 3. Verify restoration
vpnhd client list
```

#### Scenario: Corrupted WireGuard Configuration

```bash
# WireGuard config corrupted
sudo cat /etc/wireguard/wg0.conf  # Garbled output

# Recovery:
# 1. Find most recent backup
vpnhd backup list

# 2. Restore only WireGuard config
sudo vpnhd backup restore backup_20251108_104530 \
  --no-ssh --no-config --no-clients

# 3. Restart WireGuard
sudo systemctl restart wg-quick@wg0

# 4. Verify
sudo wg show
```

### Migration to New Server

#### Complete Server Migration

```bash
# On old server:
# 1. Create final backup
vpnhd backup create --description "Migration to new server"

# 2. Export to portable storage
vpnhd backup export backup_20251108_104530 /mnt/usb/migration/

# 3. Verify export
ls -lh /mnt/usb/migration/

# On new server:
# 1. Install VPNHD
# (See installation instructions)

# 2. Import backup
vpnhd backup import /mnt/usb/migration/backup_20251108_104530.tar.gz

# 3. Restore all components
sudo vpnhd backup restore backup_20251108_104530

# 4. Update DNS/IP if changed
# Edit ~/.config/vpnhd/config.json

# 5. Start services
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# 6. Verify
vpnhd client list
vpnhd client stats
vpnhd performance latency
```

**Note:** If server IP address changed, clients will need updated configurations.

## Advanced Topics

### Automated Backup Systems

#### Systemd Timer for Daily Backups

**Create service file:** `/etc/systemd/system/vpnhd-backup.service`

```ini
[Unit]
Description=VPNHD Daily Backup
After=network.target

[Service]
Type=oneshot
User=vpnhd
ExecStart=/usr/local/bin/vpnhd backup create --description "Automated daily backup"
ExecStartPost=/usr/local/bin/vpnhd backup cleanup --keep 7
```

**Create timer file:** `/etc/systemd/system/vpnhd-backup.timer`

```ini
[Unit]
Description=VPNHD Daily Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable vpnhd-backup.timer
sudo systemctl start vpnhd-backup.timer

# Check status
systemctl status vpnhd-backup.timer
systemctl list-timers vpnhd-backup.timer
```

### Backup to Remote Server

#### Automated Remote Backup

```bash
#!/bin/bash
# /usr/local/bin/vpnhd-remote-backup.sh

# Create local backup
BACKUP_ID=$(vpnhd backup create --description "Remote backup $(date +%Y-%m-%d)" | grep "Backup ID:" | awk '{print $3}')

if [ -z "$BACKUP_ID" ]; then
  echo "Error: Backup creation failed"
  exit 1
fi

# Export to temp location
TEMP_DIR=$(mktemp -d)
vpnhd backup export "$BACKUP_ID" "$TEMP_DIR"

# Upload to remote server
scp "$TEMP_DIR/$BACKUP_ID"* user@remote-server:/backups/vpnhd/

# Cleanup
rm -rf "$TEMP_DIR"

# Cleanup old remote backups (keep last 30)
ssh user@remote-server "cd /backups/vpnhd && ls -t backup_*.tar.gz | tail -n +31 | xargs rm -f"

echo "Remote backup completed: $BACKUP_ID"
```

### Backup to Cloud Storage

#### AWS S3 Example

```bash
#!/bin/bash
# Requires: aws-cli configured

# Create backup
BACKUP_ID=$(vpnhd backup create --description "Cloud backup" | grep "Backup ID:" | awk '{print $3}')

# Upload to S3
aws s3 cp ~/.config/vpnhd/backups/${BACKUP_ID}.tar.gz \
  s3://my-vpnhd-backups/${BACKUP_ID}.tar.gz \
  --storage-class GLACIER

aws s3 cp ~/.config/vpnhd/backups/${BACKUP_ID}_metadata.json \
  s3://my-vpnhd-backups/${BACKUP_ID}_metadata.json

# Lifecycle policy will automatically delete old backups
```

### Differential Backups

While VPNHD doesn't natively support differential backups, you can implement them:

```bash
#!/bin/bash
# Differential backup using rsync

BACKUP_DIR=/backup/vpnhd-differential
BASELINE_DIR=$BACKUP_DIR/baseline
DIFF_DIR=$BACKUP_DIR/$(date +%Y%m%d)

# Create baseline (weekly)
if [ ! -d "$BASELINE_DIR" ] || [ $(date +%u) -eq 1 ]; then
  vpnhd backup create --description "Weekly baseline"
  LATEST=$(vpnhd backup list --format simple | head -1 | awk '{print $1}')
  vpnhd backup export "$LATEST" "$BASELINE_DIR"
fi

# Create differential (daily)
mkdir -p "$DIFF_DIR"
rsync -av --link-dest="$BASELINE_DIR" \
  ~/.config/vpnhd/ \
  "$DIFF_DIR/"
```

### Monitoring Backup Health

#### Backup Health Check Script

```bash
#!/bin/bash
# /usr/local/bin/vpnhd-backup-health.sh

# Check backup age
LATEST_BACKUP=$(vpnhd backup list --format json | jq -r '.[0].created_at')
LATEST_EPOCH=$(date -d "$LATEST_BACKUP" +%s)
NOW_EPOCH=$(date +%s)
AGE_HOURS=$(( (NOW_EPOCH - LATEST_EPOCH) / 3600 ))

if [ $AGE_HOURS -gt 48 ]; then
  echo "WARNING: Latest backup is $AGE_HOURS hours old"
  echo "Latest backup: $LATEST_BACKUP" | mail -s "VPNHD Backup Warning" admin@example.com
fi

# Verify latest backup
LATEST_ID=$(vpnhd backup list --format json | jq -r '.[0].backup_id')
if ! vpnhd backup verify "$LATEST_ID"; then
  echo "ERROR: Latest backup verification failed" | mail -s "VPNHD Backup Error" admin@example.com
fi

# Check disk space
BACKUP_SIZE=$(du -sb ~/.config/vpnhd/backups | awk '{print $1}')
DISK_AVAIL=$(df ~/.config/vpnhd/backups | tail -1 | awk '{print $4 * 1024}')

if [ $BACKUP_SIZE -gt $(( DISK_AVAIL / 2 )) ]; then
  echo "WARNING: Backup directory using >50% of available disk space" | \
    mail -s "VPNHD Disk Space Warning" admin@example.com
fi
```

---

## Summary

Key takeaways:

1. **Backup regularly** - Automate daily backups
2. **Follow 3-2-1 rule** - Multiple copies on different media, one offsite
3. **Use descriptive names** - Document what and why
4. **Verify backups** - Test restoration periodically
5. **Secure backups** - Encrypt sensitive backups
6. **Cleanup old backups** - Maintain reasonable retention
7. **Test disaster recovery** - Have a documented recovery procedure

**Essential commands:**

```bash
# Create backup
vpnhd backup create --description "Description here"

# List backups
vpnhd backup list

# Restore backup
vpnhd backup restore <backup-id>

# Verify backup
vpnhd backup verify <backup-id>

# Export backup
vpnhd backup export <backup-id> <destination>

# Cleanup old backups
vpnhd backup cleanup --keep 10
```

For more information:
- [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
- [User Guide](USER_GUIDE.md) - General VPNHD usage
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
