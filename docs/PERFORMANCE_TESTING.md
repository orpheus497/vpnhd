# Performance Testing Guide

Complete guide to testing and monitoring VPN performance with VPNHD.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Types](#test-types)
- [Understanding Results](#understanding-results)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

VPNHD provides comprehensive performance testing capabilities to help you:

- **Measure latency** - Round-trip time for packets
- **Test stability** - Connection reliability over time
- **Assess bandwidth** - Upload and download speeds (optional with iperf3)
- **Track trends** - Historical performance analysis
- **Diagnose issues** - Identify connection problems

### Why Test Performance?

1. **Establish Baseline** - Know your normal performance levels
2. **Detect Issues** - Identify problems before they become critical
3. **Verify Changes** - Confirm that configuration changes improved performance
4. **Capacity Planning** - Understand VPN load and capacity
5. **Troubleshooting** - Diagnose connection and performance problems

### Test Architecture

```
┌──────────────────────────────────────────────────┐
│        Performance Testing System                │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────────┐                                │
│  │ Latency Test │ ──► ping -c 10 test_server    │
│  └──────────────┘     - Min/Avg/Max/StdDev      │
│                       - Packet loss              │
│                                                   │
│  ┌──────────────┐                                │
│  │Stability Test│ ──► ping -c 1 (every 1s)      │
│  └──────────────┘     - Uptime percentage       │
│                       - Disconnection count      │
│                                                   │
│  ┌──────────────┐                                │
│  │Bandwidth Test│ ──► iperf3 -c server          │
│  └──────────────┘     - Download/Upload speed   │
│         (optional)                                │
│                                                   │
│  ┌──────────────┐                                │
│  │   Reports    │ ──► JSON files                │
│  └──────────────┘     - Historical data         │
│                       - Trend analysis           │
│                                                   │
└──────────────────────────────────────────────────┘
```

### Report Storage

Performance reports are saved to `~/.config/vpnhd/performance/`:

```
~/.config/vpnhd/performance/
├── performance_report_20251108_104530.json
├── performance_report_20251107_143015.json
└── performance_report_20251106_091542.json
```

## Quick Start

### Run Your First Test

```bash
# Quick latency test
vpnhd performance latency

# Quick stability test (60 seconds)
vpnhd performance stability --duration 60

# Full test suite
vpnhd performance full
```

### View Results

```bash
# List recent tests
vpnhd performance list

# View aggregated statistics
vpnhd performance stats
```

### Interpret Results

**Good Performance:**
- Latency < 50ms
- Packet loss < 1%
- Uptime > 99%

**Acceptable Performance:**
- Latency 50-100ms
- Packet loss 1-5%
- Uptime 95-99%

**Poor Performance:**
- Latency > 100ms
- Packet loss > 5%
- Uptime < 95%

## Test Types

### Latency Test

Measures round-trip time for packets using ICMP ping.

#### Basic Latency Test

```bash
vpnhd performance latency
```

**Default settings:**
- Packets: 10
- Timeout: 5 seconds
- Server: 8.8.8.8 (Google DNS)

#### Custom Latency Test

```bash
# Test with 20 packets
vpnhd performance latency --count 20

# Test specific server
vpnhd performance latency --server 1.1.1.1

# Custom timeout (10 seconds)
vpnhd performance latency --timeout 10

# Comprehensive test
vpnhd performance latency --count 50 --server 1.1.1.1 --timeout 10
```

#### Example Output

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

#### What the Results Mean

- **Minimum**: Best-case latency (fastest packet)
- **Average**: Typical latency (most important metric)
- **Maximum**: Worst-case latency (slowest packet)
- **Std Deviation**: Variability in latency (lower is better)
- **Packet Loss**: Percentage of lost packets (should be 0%)

**Interpreting Standard Deviation:**
- < 5ms: Excellent stability
- 5-10ms: Good stability
- 10-20ms: Moderate variability
- \> 20ms: High variability (potential issues)

### Stability Test

Measures connection reliability over an extended period.

#### Basic Stability Test

```bash
# Default: 5 minutes (300 seconds)
vpnhd performance stability
```

**Default settings:**
- Duration: 300 seconds (5 minutes)
- Interval: 1 second (ping every second)
- Server: 8.8.8.8

#### Custom Stability Test

```bash
# Quick 60-second test
vpnhd performance stability --duration 60

# Long-duration test (1 hour)
vpnhd performance stability --duration 3600

# 10-minute test with 5-second intervals
vpnhd performance stability --duration 600 --interval 5

# Comprehensive overnight test
vpnhd performance stability --duration 28800 --interval 10
```

#### Example Output

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

#### What the Results Mean

- **Total Pings**: Number of ping attempts
- **Successful/Failed**: Connection success rate
- **Uptime**: Percentage of time connection was active
- **Disconnections**: Number of times connection dropped
- **Avg Latency**: Average latency during the test

**Interpreting Disconnections:**
- 0-1: Excellent stability
- 2-5: Good (occasional hiccups)
- 6-10: Moderate (investigate)
- \> 10: Poor (serious issues)

### Bandwidth Test

Measures upload and download speeds using iperf3.

**Requirements:**
- iperf3 must be installed
- Access to an iperf3 server

#### Setup iperf3 Server

**Option 1: Use Public Server**
```bash
# Many public iperf3 servers available
# Search for: "public iperf3 servers"
```

**Option 2: Run Your Own**
```bash
# On a separate machine:
sudo apt install iperf3
iperf3 -s
```

#### Run Bandwidth Test

```bash
# As part of full test suite
vpnhd performance full --bandwidth --iperf-server speedtest.example.com
```

**Note:** Bandwidth testing is optional and only available as part of the full test suite.

#### Example Output

```
╭─────────── Bandwidth Test Results ───────────╮
│ Test Server      : speedtest.example.com     │
│ Test Duration    : 10 seconds                │
│                                               │
│ Download Speed   : 95.3 Mbps                 │
│ Upload Speed     : 48.7 Mbps                 │
╰───────────────────────────────────────────────╯
```

### Full Test Suite

Runs comprehensive performance testing.

#### Basic Full Test

```bash
# Latency + Stability (without bandwidth)
vpnhd performance full
```

**Default settings:**
- Latency: 20 packets
- Stability: 60 seconds
- Bandwidth: Disabled

#### Full Test with Bandwidth

```bash
vpnhd performance full --bandwidth --iperf-server speedtest.example.com
```

#### Custom Full Test

```bash
vpnhd performance full \
  --latency-count 50 \
  --stability-duration 300 \
  --bandwidth \
  --iperf-server speedtest.example.com
```

#### Example Output

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

## Understanding Results

### Report Structure

Performance reports are saved as JSON files:

```json
{
  "test_date": "2025-11-08T10:45:30",
  "vpn_interface": "wg0",
  "test_server": "8.8.8.8",
  "latency": {
    "min_ms": 12.3,
    "max_ms": 21.4,
    "avg_ms": 15.7,
    "stddev_ms": 2.8,
    "packet_loss_percent": 0.0,
    "packets_sent": 20,
    "packets_received": 20,
    "timestamp": "2025-11-08T10:45:30"
  },
  "stability": {
    "test_duration_seconds": 60,
    "successful_pings": 59,
    "failed_pings": 1,
    "total_pings": 60,
    "uptime_percent": 98.3,
    "disconnections": 1,
    "avg_latency_ms": 16.2,
    "timestamp": "2025-11-08T10:46:45"
  },
  "bandwidth": null
}
```

### Viewing Historical Reports

#### List All Reports

```bash
vpnhd performance list
```

Output:
```
Recent Performance Reports:

1. 2025-11-08 10:45:30 - Latency: 15.7ms, Uptime: 99.3%
2. 2025-11-07 14:30:15 - Latency: 14.2ms, Uptime: 100.0%
3. 2025-11-06 09:15:42 - Latency: 16.8ms, Uptime: 98.7%

Total Reports: 15
```

#### View Aggregated Statistics

```bash
vpnhd performance stats
```

Output:
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

### Performance Trends

Monitor performance over time:

```bash
# Create a trend report script
#!/bin/bash
echo "Date,Avg_Latency,Uptime" > performance_trend.csv

for report in ~/.config/vpnhd/performance/*.json; do
  date=$(jq -r '.test_date' "$report")
  latency=$(jq -r '.latency.avg_ms' "$report")
  uptime=$(jq -r '.stability.uptime_percent' "$report")
  echo "$date,$latency,$uptime" >> performance_trend.csv
done

# Analyze with your favorite tool (Excel, pandas, etc.)
```

## Best Practices

### Regular Testing Schedule

#### Daily Quick Check
```bash
#!/bin/bash
# Daily quick performance check
vpnhd performance latency --count 20 > /var/log/vpnhd-daily.log 2>&1
```

#### Weekly Comprehensive Test
```bash
#!/bin/bash
# Weekly full performance test
vpnhd performance full --stability-duration 300 > /var/log/vpnhd-weekly.log 2>&1
```

#### Monthly Deep Analysis
```bash
#!/bin/bash
# Monthly extended stability test
vpnhd performance stability --duration 3600 > /var/log/vpnhd-monthly.log 2>&1
```

### Baseline Establishment

After initial VPN setup:

```bash
# Run comprehensive tests over 1 week
for i in {1..7}; do
  vpnhd performance full --stability-duration 600
  sleep 86400  # Wait 24 hours
done

# Review statistics
vpnhd performance stats
```

Document your baseline:
- Average latency: _____ms
- Typical uptime: _____%
- Normal packet loss: _____%

### Test Timing

**Best times to test:**
- Off-peak hours for baseline
- Peak hours for capacity testing
- Before/after configuration changes

**Avoid testing during:**
- Network maintenance windows
- Known ISP issues
- Major internet events (DDOS, outages)

### Interpreting Performance Changes

#### Sudden Latency Increase

**Possible causes:**
- ISP routing changes
- Network congestion
- VPN server load
- Hardware issues

**Investigation:**
```bash
# Test direct connection (without VPN)
ping -c 10 8.8.8.8

# Compare with VPN connection
vpnhd performance latency --count 10

# Check server load
uptime
top
```

#### Gradual Latency Increase

**Possible causes:**
- Growing network congestion
- Server resource exhaustion
- Client count increase

**Investigation:**
```bash
# Check client count
vpnhd client stats

# Review historical trends
vpnhd performance stats

# Monitor server resources
htop
iftop
```

#### Stability Issues

**Possible causes:**
- Router problems
- ISP instability
- Firewall interference
- Hardware failure

**Investigation:**
```bash
# Test stability over longer period
vpnhd performance stability --duration 3600

# Check system logs
journalctl -u wg-quick@wg0

# Review firewall logs
sudo tail -f /var/log/ufw.log
```

### Server Selection

#### Default Server (8.8.8.8)

Google's public DNS - reliable and globally distributed.

#### Alternative Servers

```bash
# Cloudflare DNS
vpnhd performance latency --server 1.1.1.1

# Quad9 DNS
vpnhd performance latency --server 9.9.9.9

# Your own server
vpnhd performance latency --server your-server.example.com
```

**Recommendation:** Use a geographically close, reliable server for consistent results.

## Troubleshooting

### Test Failures

#### "ping: command not found"

**Solution:**
```bash
sudo apt install iputils-ping
```

#### "iperf3: command not found"

**Solution:**
```bash
sudo apt install iperf3
```

Or skip bandwidth testing:
```bash
vpnhd performance full  # Without --bandwidth flag
```

#### "Permission denied"

Some tests may require root:
```bash
sudo vpnhd performance latency
```

### Inconsistent Results

#### High Variability

**Cause:** Network conditions changing during test

**Solutions:**
- Run longer tests (more packets/longer duration)
- Test multiple times and average results
- Test at consistent times of day

#### Different Results on Different Days

**Cause:** Normal network variation

**Solutions:**
- Establish baseline with multiple tests
- Focus on trends, not individual tests
- Consider time-of-day and day-of-week patterns

### Test Hangs or Times Out

#### Latency Test Hangs

**Cause:** Server unreachable or timeout too short

**Solutions:**
```bash
# Increase timeout
vpnhd performance latency --timeout 10

# Try different server
vpnhd performance latency --server 1.1.1.1
```

#### Stability Test Too Long

**Cause:** Long duration test

**Solutions:**
```bash
# Use Ctrl+C to cancel (results up to that point are lost)
# Or run shorter tests:
vpnhd performance stability --duration 60
```

### Understanding Poor Results

#### High Latency (>100ms)

**Possible causes:**
1. Geographic distance
2. ISP routing
3. VPN overhead
4. Server load

**Diagnostics:**
```bash
# Test without VPN
ping -c 10 8.8.8.8

# Test with VPN
vpnhd performance latency

# Compare results
```

#### Packet Loss (>1%)

**Possible causes:**
1. Network congestion
2. Hardware issues
3. Firewall blocking
4. MTU problems

**Diagnostics:**
```bash
# Check MTU
ip link show wg0

# Test with different packet sizes
ping -c 10 -s 1400 8.8.8.8  # Smaller packets
ping -c 10 -s 1200 8.8.8.8  # Even smaller
```

#### Low Uptime (<99%)

**Possible causes:**
1. Unstable internet connection
2. Router issues
3. VPN server problems
4. Power/hardware issues

**Diagnostics:**
```bash
# Long-term stability test
vpnhd performance stability --duration 3600

# Check system logs
journalctl -u wg-quick@wg0 --since "1 hour ago"

# Monitor in real-time
watch -n 1 'wg show'
```

## Advanced Topics

### Automated Testing and Alerts

#### Daily Test with Email Alerts

```bash
#!/bin/bash
# /usr/local/bin/vpn-daily-test.sh

REPORT=$(vpnhd performance full --latency-count 30 --stability-duration 120)
LATENCY=$(echo "$REPORT" | grep "Average" | awk '{print $3}' | sed 's/ms//')

if (( $(echo "$LATENCY > 50" | bc -l) )); then
  echo "$REPORT" | mail -s "VPN Performance Alert: High Latency" admin@example.com
fi
```

**Crontab:**
```bash
# Run daily at 3 AM
0 3 * * * /usr/local/bin/vpn-daily-test.sh
```

### Integration with Monitoring Systems

#### Prometheus Exporter

```python
#!/usr/bin/env python3
import json
import subprocess
from prometheus_client import start_http_server, Gauge
import time

# Define metrics
latency_gauge = Gauge('vpn_latency_ms', 'VPN latency in milliseconds')
uptime_gauge = Gauge('vpn_uptime_percent', 'VPN uptime percentage')

def collect_metrics():
    # Run performance test
    result = subprocess.run(
        ['vpnhd', 'performance', 'full'],
        capture_output=True,
        text=True
    )

    # Parse latest report
    # (Implementation depends on output format)
    # Update Prometheus gauges
    latency_gauge.set(15.7)  # Example value
    uptime_gauge.set(99.3)   # Example value

if __name__ == '__main__':
    start_http_server(8000)
    while True:
        collect_metrics()
        time.sleep(300)  # Every 5 minutes
```

### Graphing Performance Data

#### Using Python/Matplotlib

```python
#!/usr/bin/env python3
import json
import glob
import matplotlib.pyplot as plt
from datetime import datetime

# Load all reports
reports = []
for file in sorted(glob.glob('~/.config/vpnhd/performance/*.json')):
    with open(file) as f:
        reports.append(json.load(f))

# Extract data
dates = [datetime.fromisoformat(r['test_date']) for r in reports]
latencies = [r['latency']['avg_ms'] for r in reports if r['latency']]
uptimes = [r['stability']['uptime_percent'] for r in reports if r['stability']]

# Create plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(dates, latencies, 'b-')
ax1.set_ylabel('Latency (ms)')
ax1.set_title('VPN Latency Over Time')
ax1.grid(True)

ax2.plot(dates, uptimes, 'g-')
ax2.set_ylabel('Uptime (%)')
ax2.set_xlabel('Date')
ax2.set_title('VPN Uptime Over Time')
ax2.grid(True)

plt.tight_layout()
plt.savefig('vpn_performance.png')
print("Graph saved to vpn_performance.png")
```

### Performance Comparison

#### Before/After Configuration Changes

```bash
#!/bin/bash
# Test before change
echo "Testing BEFORE configuration change..."
vpnhd performance full --stability-duration 300
cp ~/.config/vpnhd/performance/performance_report_*.json before.json

# Make configuration changes here
# ...

# Test after change
echo "Testing AFTER configuration change..."
vpnhd performance full --stability-duration 300
cp ~/.config/vpnhd/performance/performance_report_*.json after.json

# Compare
echo "Comparison:"
echo "Before: $(jq -r '.latency.avg_ms' before.json)ms latency"
echo "After: $(jq -r '.latency.avg_ms' after.json)ms latency"
```

### Load Testing

#### Simulate Multiple Clients

```bash
#!/bin/bash
# Add multiple test clients
for i in {1..10}; do
  vpnhd client add test-client-$i --device-type desktop
done

# Run performance test
vpnhd performance full --stability-duration 600

# Remove test clients
for i in {1..10}; do
  vpnhd client remove test-client-$i --force
done
```

### Custom Test Servers

#### Test Specific Endpoints

```bash
# Test latency to your office
vpnhd performance latency --server office.example.com

# Test latency to cloud provider
vpnhd performance latency --server ec2-instance.amazonaws.com

# Test latency to home server
vpnhd performance latency --server home.dyndns.org
```

---

## Summary

Key takeaways:

1. **Establish baseline** performance with initial tests
2. **Regular testing** helps detect issues early
3. **Latency < 50ms** and **uptime > 99%** are good targets
4. **Trends matter** more than individual test results
5. **Long-duration tests** provide better stability insights
6. **Save reports** for historical analysis
7. **Automate testing** for continuous monitoring

For more information:
- [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [User Guide](USER_GUIDE.md) - General VPNHD usage
