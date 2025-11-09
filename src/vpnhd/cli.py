"""Main CLI entry point for VPNHD."""

import sys
from pathlib import Path

import click

from .__version__ import __version__
from .backup import BackupManager
from .client import ClientManager
from .config.manager import ConfigManager
from .phases import get_phase_class
from .testing import PerformanceTester
from .ui.display import Display
from .ui.menus import MainMenu
from .ui.prompts import Prompts
from .utils.constants import APP_NAME, APP_VERSION
from .utils.logging import get_logger, setup_logging


@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", "-c", type=click.Path(), help="Path to config file")
@click.pass_context
def main(ctx, verbose, config):
    """VPNHD - VPN Helper Daemon

    Privacy-first automation for setting up a complete WireGuard-based home VPN system.
    """
    # Setup logging
    setup_logging(verbose=verbose)
    logger = get_logger("CLI")

    # Initialize components
    config_path = Path(config) if config else None
    config_manager = ConfigManager(config_path)
    display = Display()
    prompts = Prompts()

    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = config_manager
    ctx.obj["display"] = display
    ctx.obj["prompts"] = prompts
    ctx.obj["logger"] = logger

    # Load configuration
    if not config_manager.load():
        logger.warning("Could not load configuration, using defaults")

    # If no subcommand, run interactive mode
    if ctx.invoked_subcommand is None:
        run_interactive(config_manager, display, prompts)


def run_interactive(config_manager: ConfigManager, display: Display, prompts: Prompts):
    """Run interactive mode with main menu."""
    logger = get_logger("Interactive")

    try:
        while True:
            # Show main menu
            menu = MainMenu(config_manager)
            choice = menu.show()

            if choice == "0":  # Exit
                display.info("Goodbye!")
                sys.exit(0)

            elif choice == "1":  # Continue to next phase
                next_phase = config_manager.get_next_phase()
                if next_phase == 0:
                    display.success("All phases complete! Your VPN is ready.")
                    prompts.pause()
                else:
                    execute_phase(next_phase, config_manager, display, prompts)

            elif choice == "2":  # Jump to specific phase
                phase_num = menu.show_phase_selection()
                if phase_num:
                    execute_phase(phase_num, config_manager, display, prompts)

            elif choice == "3":  # Review configuration
                menu.show_configuration_review()

            elif choice == "4":  # Show phase details
                phase_num = menu.show_phase_selection()
                if phase_num:
                    menu.show_phase_details(phase_num)

            elif choice == "5":  # Troubleshooting
                menu.show_troubleshooting()

            elif choice == "6":  # View guide documentation
                display.info("Guide documentation is located in .devdocs/")
                prompts.pause()

    except KeyboardInterrupt:
        display.newline()
        display.warning("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Error in interactive mode")
        display.error(f"Error: {e}")
        sys.exit(1)


def execute_phase(
    phase_number: int, config_manager: ConfigManager, display: Display, prompts: Prompts
):
    """Execute a specific phase."""
    logger = get_logger(f"Phase{phase_number}")

    try:
        # Get phase class
        phase_class = get_phase_class(phase_number)
        if not phase_class:
            display.error(f"Invalid phase number: {phase_number}")
            return

        # Create phase instance
        phase = phase_class(config_manager, display, prompts)

        # Check if already complete
        if phase.is_complete():
            if not prompts.confirm(
                f"Phase {phase_number} is already complete. Run again?", default=False
            ):
                return

        # Check prerequisites
        if not phase.check_prerequisites():
            display.error("Prerequisites not met")
            prompts.pause()
            return

        # Confirm execution
        if not prompts.confirm(
            f"Ready to execute Phase {phase_number}: {phase.name}?", default=True
        ):
            return

        # Execute phase
        display.newline()
        display.heading(f"Executing Phase {phase_number}: {phase.name}", style="cyan bold")
        display.newline()

        success = phase.execute()

        if success:
            display.newline()
            display.success(f"Phase {phase_number} completed successfully!")
            display.newline()
        else:
            display.newline()
            display.error(f"Phase {phase_number} failed")
            if phase.error_message:
                display.error(f"Error: {phase.error_message}")
            display.newline()

        prompts.pause()

    except Exception as e:
        logger.exception(f"Error executing phase {phase_number}")
        display.error(f"Error: {e}")
        prompts.pause()


@main.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    display = ctx.obj["display"]
    display.print(f"{APP_NAME} version {__version__}", style="cyan bold")


@main.command()
@click.argument("phase_number", type=int)
@click.pass_context
def run_phase(ctx, phase_number):
    """Run a specific phase."""
    config_manager = ctx.obj["config"]
    display = ctx.obj["display"]
    prompts = ctx.obj["prompts"]

    execute_phase(phase_number, config_manager, display, prompts)


@main.command()
@click.pass_context
def status(ctx):
    """Show current status."""
    config_manager = ctx.obj["config"]
    display = ctx.obj["display"]

    display.heading("VPNHD Status", style="cyan bold")
    display.newline()

    for phase_num in range(1, 9):
        phase_info = config_manager.get_phase_info(phase_num)
        if phase_info:
            display.phase_status(phase_num, phase_info["name"], phase_info["completed"])

    completion = config_manager.get_completion_percentage()
    display.newline()
    display.print(f"Progress: {completion:.0f}% complete", style="yellow")


@main.command()
@click.pass_context
def reset(ctx):
    """Reset configuration to defaults."""
    config_manager = ctx.obj["config"]
    display = ctx.obj["display"]
    prompts = ctx.obj["prompts"]

    if prompts.confirm("Are you sure you want to reset all configuration?", default=False):
        if config_manager.reset():
            display.success("Configuration reset to defaults")
        else:
            display.error("Failed to reset configuration")


@main.command()
@click.argument("output_path", type=click.Path())
@click.pass_context
def export_config(ctx, output_path):
    """Export configuration to file."""
    config_manager = ctx.obj["config"]
    display = ctx.obj["display"]

    if config_manager.export_config(Path(output_path)):
        display.success(f"Configuration exported to {output_path}")
    else:
        display.error("Failed to export configuration")


# ==============================================================================
# Client Management Commands
# ==============================================================================


@main.group()
@click.pass_context
def client(ctx):
    """Manage VPN clients."""
    # Initialize client manager if not already in context
    if "client_manager" not in ctx.obj:
        ctx.obj["client_manager"] = ClientManager(ctx.obj["config"])


@client.command("list")
@click.option("--enabled", is_flag=True, help="Show only enabled clients")
@click.option(
    "--device-type",
    type=click.Choice(["desktop", "mobile", "server"]),
    help="Filter by device type",
)
@click.option("--os", help="Filter by operating system")
@click.option("--connected", is_flag=True, help="Show only connected clients")
@click.option(
    "--format",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_clients(ctx, enabled, device_type, os, connected, format):
    """List all VPN clients."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]

    # Get clients with filters
    clients = client_manager.list_clients(
        enabled_only=enabled, device_type=device_type, os_filter=os
    )

    # Filter by connection status if requested
    if connected:
        connected_names = client_manager.get_all_connected_clients()
        clients = [c for c in clients if c.name in connected_names]

    if not clients:
        display.info("No clients found")
        return

    if format == "json":
        import json

        output = [c.to_dict() for c in clients]
        click.echo(json.dumps(output, indent=2))
    elif format == "simple":
        for client in clients:
            status = "✓" if client.enabled else "✗"
            click.echo(f"{status} {client.name} ({client.vpn_ip}) - {client.device_type}")
    else:  # table
        from rich.console import Console
        from rich.table import Table

        table = Table(title="VPN Clients")
        table.add_column("Name", style="cyan")
        table.add_column("IP", style="yellow")
        table.add_column("Device", style="blue")
        table.add_column("OS", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Created", style="white")

        for client in clients:
            status = "Enabled" if client.enabled else "Disabled"
            created = client.created_at[:10] if client.created_at else "Unknown"
            table.add_row(
                client.name,
                client.vpn_ip,
                client.device_type or "Unknown",
                client.os or "Unknown",
                status,
                created,
            )

        Console().print(table)


@client.command("add")
@click.argument("name")
@click.option("--description", default="", help="Client description")
@click.option(
    "--device-type",
    type=click.Choice(["desktop", "mobile", "server"]),
    default="desktop",
    help="Device type",
)
@click.option("--os", default="linux", help="Operating system")
@click.option("--ip", help="Specific VPN IP address")
@click.option("--qr", is_flag=True, help="Generate QR code (for mobile clients)")
@click.pass_context
def add_client(ctx, name, description, device_type, os, ip, qr):
    """Add a new VPN client."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]

    display.info(f"Adding client '{name}'...")

    client_info = client_manager.add_client(
        name=name,
        description=description,
        device_type=device_type,
        os=os,
        vpn_ip=ip,
        generate_qr=qr,
    )

    if client_info:
        display.success(f"✓ Client '{name}' added successfully")
        display.print(f"  VPN IP: {client_info.vpn_ip}", style="yellow")
        display.print(f"  Public Key: {client_info.public_key[:32]}...", style="cyan")

        # Show next steps
        display.newline()
        display.heading("Next Steps:", style="cyan")
        display.print(f"  1. Export config: vpnhd client export {name}")
        if device_type == "mobile" and qr:
            display.print(f"  2. Scan QR code with WireGuard app")
        else:
            display.print(f"  2. Copy config to client device")
    else:
        display.error(f"Failed to add client '{name}'")
        sys.exit(1)


@client.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def remove_client(ctx, name, yes):
    """Remove a VPN client."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]
    prompts = ctx.obj["prompts"]

    # Check if client exists
    client = client_manager.get_client(name)
    if not client:
        display.error(f"Client '{name}' not found")
        sys.exit(1)

    # Confirm removal
    if not yes:
        display.warning(f"This will remove client '{name}' and revoke access")
        if not prompts.confirm("Continue?", default=False):
            display.info("Cancelled")
            return

    if client_manager.remove_client(name):
        display.success(f"✓ Client '{name}' removed successfully")
    else:
        display.error(f"Failed to remove client '{name}'")
        sys.exit(1)


@client.command("show")
@click.argument("name")
@click.option("--show-keys", is_flag=True, help="Display full keys")
@click.pass_context
def show_client(ctx, name, show_keys):
    """Show detailed information about a client."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]
    config_manager = ctx.obj["config"]

    client = client_manager.get_client(name)
    if not client:
        display.error(f"Client '{name}' not found")
        sys.exit(1)

    from rich.console import Console
    from rich.panel import Panel

    # Get connection status
    status = client_manager.get_client_status(name)
    connected = status.get("connected", False) if status else False

    # Build info text
    info_lines = [
        f"[cyan]Name:[/cyan] {client.name}",
        f"[cyan]VPN IP:[/cyan] {client.vpn_ip}",
        f"[cyan]Device Type:[/cyan] {client.device_type or 'Unknown'}",
        f"[cyan]OS:[/cyan] {client.os or 'Unknown'}",
        f"[cyan]Status:[/cyan] {'[green]Enabled[/green]' if client.enabled else '[red]Disabled[/red]'}",  # noqa: E501
        f"[cyan]Connected:[/cyan] {'[green]Yes[/green]' if connected else '[red]No[/red]'}",  # noqa: E501
        f"[cyan]Created:[/cyan] {client.created_at[:19] if client.created_at else 'Unknown'}",
    ]

    if client.description:
        info_lines.append(f"[cyan]Description:[/cyan] {client.description}")

    if show_keys:
        info_lines.append(f"[cyan]Public Key:[/cyan] {client.public_key}")
        private_key = config_manager.get(f"clients.{name}.private_key")
        if private_key:
            info_lines.append(f"[cyan]Private Key:[/cyan] {private_key}")
    else:
        info_lines.append(
            f"[cyan]Public Key:[/cyan] {client.public_key[:32]}... (use --show-keys for full)"
        )

    # Show connection details if connected
    if connected and status:
        info_lines.append("")
        info_lines.append("[yellow]Connection Details:[/yellow]")
        if status.get("endpoint"):
            info_lines.append(f"  [cyan]Endpoint:[/cyan] {status['endpoint']}")
        if status.get("latest_handshake"):
            info_lines.append(f"  [cyan]Last Handshake:[/cyan] {status['latest_handshake']}")
        if status.get("transfer_rx"):
            info_lines.append(f"  [cyan]Data Received:[/cyan] {status['transfer_rx']} bytes")
        if status.get("transfer_tx"):
            info_lines.append(f"  [cyan]Data Sent:[/cyan] {status['transfer_tx']} bytes")

    panel = Panel("\n".join(info_lines), title=f"Client: {name}", border_style="cyan")
    Console().print(panel)


@client.command("status")
@click.option("--all", is_flag=True, help="Show all clients (not just connected)")
@click.pass_context
def client_status(ctx, all):
    """Show connection status of clients."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]

    from rich.console import Console
    from rich.table import Table

    clients = client_manager.list_clients()

    table = Table(title="Client Connection Status")
    table.add_column("Name", style="cyan")
    table.add_column("IP", style="yellow")
    table.add_column("Connected", style="green")
    table.add_column("Endpoint", style="blue")
    table.add_column("Last Handshake", style="magenta")
    table.add_column("Transfer (RX/TX)", style="white")

    for client in clients:
        status = client_manager.get_client_status(client.name)
        connected = status.get("connected", False) if status else False

        # Skip disconnected clients unless --all specified
        if not connected and not all:
            continue

        conn_status = "[green]✓[/green]" if connected else "[red]✗[/red]"
        endpoint = status.get("endpoint", "-") if status and connected else "-"
        handshake = status.get("latest_handshake", "-") if status and connected else "-"

        if status and connected:
            rx = status.get("transfer_rx", "0")
            tx = status.get("transfer_tx", "0")
            transfer = f"{rx}/{tx}"
        else:
            transfer = "-"

        table.add_row(client.name, client.vpn_ip, conn_status, endpoint, handshake, transfer)

    Console().print(table)


@client.command("export")
@click.argument("name")
@click.option("--output", "-o", help="Output file path")
@click.option("--qr", is_flag=True, help="Also generate QR code")
@click.pass_context
def export_client_config(ctx, name, output, qr):
    """Export client configuration file."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]

    client = client_manager.get_client(name)
    if not client:
        display.error(f"Client '{name}' not found")
        sys.exit(1)

    # Export config file
    config_path = client_manager.export_client_config(name, output)
    if config_path:
        display.success(f"✓ Configuration exported to: {config_path}")
    else:
        display.error("Failed to export configuration")
        sys.exit(1)

    # Generate QR code if requested
    if qr:
        from ..crypto.qrcode import create_qr_with_metadata
        from ..utils.constants import QR_CODE_DIR

        config_text = Path(config_path).read_text()
        qr_path = create_qr_with_metadata(
            config_text=config_text, client_name=name, output_dir=QR_CODE_DIR
        )
        if qr_path:
            display.success(f"✓ QR code generated: {qr_path}")
        else:
            display.warning("Failed to generate QR code")


@client.command("enable")
@click.argument("name")
@click.pass_context
def enable_client(ctx, name):
    """Enable a client."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]

    if client_manager.enable_client(name):
        display.success(f"✓ Client '{name}' enabled")
    else:
        display.error(f"Failed to enable client '{name}'")
        sys.exit(1)


@client.command("disable")
@click.argument("name")
@click.pass_context
def disable_client(ctx, name):
    """Disable a client."""
    client_manager = ctx.obj["client_manager"]
    display = ctx.obj["display"]

    if client_manager.disable_client(name):
        display.success(f"✓ Client '{name}' disabled")
    else:
        display.error(f"Failed to disable client '{name}'")
        sys.exit(1)


@client.command("stats")
@click.pass_context
def client_stats(ctx):
    """Show client statistics."""
    client_manager = ctx.obj["client_manager"]

    from rich.console import Console
    from rich.panel import Panel

    stats = client_manager.get_statistics()

    lines = [
        f"[cyan]Total Clients:[/cyan] {stats['total']}",
        f"[cyan]Enabled:[/cyan] [green]{stats['enabled']}[/green]",
        f"[cyan]Disabled:[/cyan] [red]{stats['disabled']}[/red]",
        f"[cyan]Connected:[/cyan] [yellow]{stats['connected']}[/yellow]",
    ]

    if stats["by_device_type"]:
        lines.append("")
        lines.append("[yellow]By Device Type:[/yellow]")
        for dtype, count in stats["by_device_type"].items():
            lines.append(f"  {dtype}: {count}")

    if stats["by_os"]:
        lines.append("")
        lines.append("[yellow]By Operating System:[/yellow]")
        for os_name, count in stats["by_os"].items():
            lines.append(f"  {os_name}: {count}")

    panel = Panel("\n".join(lines), title="Client Statistics", border_style="cyan")
    Console().print(panel)


# ==============================================================================
# Performance Testing Commands
# ==============================================================================


@main.group()
@click.pass_context
def performance(ctx):
    """Performance testing for VPN connections."""
    if "perf_tester" not in ctx.obj:
        ctx.obj["perf_tester"] = PerformanceTester()


@performance.command("latency")
@click.option("--count", default=20, help="Number of ping packets")
@click.option("--server", default="8.8.8.8", help="Test server")
@click.pass_context
def test_latency(ctx, count, server):
    """Test VPN latency."""
    perf_tester = ctx.obj["perf_tester"]
    perf_tester.test_server = server
    display = ctx.obj["display"]

    display.info(f"Testing latency to {server} with {count} packets...")

    result = perf_tester.test_latency(count=count)

    if result:
        from rich.console import Console
        from rich.panel import Panel

        lines = [
            f"[cyan]Min:[/cyan] {result.min_ms:.2f} ms",
            f"[cyan]Avg:[/cyan] {result.avg_ms:.2f} ms",
            f"[cyan]Max:[/cyan] {result.max_ms:.2f} ms",
            f"[cyan]Std Dev:[/cyan] {result.stddev_ms:.2f} ms",
            f"[cyan]Packet Loss:[/cyan] {result.packet_loss_percent:.1f}%",
            f"[cyan]Packets:[/cyan] {result.packets_received}/{result.packets_sent}",
        ]

        panel = Panel(
            "\n".join(lines),
            title="Latency Test Results",
            border_style="green" if result.packet_loss_percent < 1 else "yellow",
        )
        Console().print(panel)
    else:
        display.error("Latency test failed")
        sys.exit(1)


@performance.command("stability")
@click.option("--duration", default=60, help="Test duration in seconds")
@click.option("--interval", default=1, help="Ping interval in seconds")
@click.option("--server", default="8.8.8.8", help="Test server")
@click.pass_context
def test_stability(ctx, duration, interval, server):
    """Test VPN connection stability."""
    perf_tester = ctx.obj["perf_tester"]
    perf_tester.test_server = server
    display = ctx.obj["display"]

    display.info(f"Testing connection stability for {duration} seconds...")

    result = perf_tester.test_connection_stability(
        duration_seconds=duration, interval_seconds=interval
    )

    if result:
        from rich.console import Console
        from rich.panel import Panel

        lines = [
            f"[cyan]Test Duration:[/cyan] {result.test_duration_seconds} seconds",
            f"[cyan]Total Pings:[/cyan] {result.total_pings}",
            f"[cyan]Successful:[/cyan] [green]{result.successful_pings}[/green]",
            f"[cyan]Failed:[/cyan] [red]{result.failed_pings}[/red]",
            f"[cyan]Uptime:[/cyan] {result.uptime_percent:.1f}%",
            f"[cyan]Disconnections:[/cyan] {result.disconnections}",
            f"[cyan]Avg Latency:[/cyan] {result.avg_latency_ms:.2f} ms",
        ]

        panel = Panel(
            "\n".join(lines),
            title="Connection Stability Results",
            border_style="green" if result.uptime_percent > 99 else "yellow",
        )
        Console().print(panel)
    else:
        display.error("Stability test failed")
        sys.exit(1)


@performance.command("full")
@click.option("--iperf-server", help="iperf3 server for bandwidth test")
@click.option("--latency-count", default=20, help="Ping count for latency")
@click.option("--stability-duration", default=60, help="Stability test duration")
@click.option("--server", default="8.8.8.8", help="Test server for ping tests")
@click.pass_context
def full_test(ctx, iperf_server, latency_count, stability_duration, server):
    """Run complete performance test suite."""
    perf_tester = ctx.obj["perf_tester"]
    perf_tester.test_server = server
    display = ctx.obj["display"]

    display.heading("Running Full Performance Test Suite", style="cyan bold")
    display.newline()

    report = perf_tester.run_full_test(
        include_bandwidth=bool(iperf_server),
        iperf_server=iperf_server,
        latency_count=latency_count,
        stability_duration=stability_duration,
    )

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Performance Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="yellow")

    if report.latency:
        table.add_row("Latency (avg)", f"{report.latency.avg_ms:.2f} ms")
        table.add_row("Packet Loss", f"{report.latency.packet_loss_percent:.1f}%")

    if report.stability:
        table.add_row("Uptime", f"{report.stability.uptime_percent:.1f}%")
        table.add_row("Disconnections", str(report.stability.disconnections))

    if report.bandwidth:
        table.add_row("Download", f"{report.bandwidth.download_mbps:.2f} Mbps")
        table.add_row("Upload", f"{report.bandwidth.upload_mbps:.2f} Mbps")

    Console().print(table)
    display.newline()
    display.success(f"Report saved to performance results directory")


@performance.command("list")
@click.pass_context
def list_reports(ctx):
    """List all performance reports."""
    perf_tester = ctx.obj["perf_tester"]

    reports = perf_tester.list_reports()

    if not reports:
        ctx.obj["display"].info("No performance reports found")
        return

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Performance Reports")
    table.add_column("Report File", style="cyan")
    table.add_column("Date", style="yellow")
    table.add_column("Size", style="green")

    for report_path in reports:
        date_str = report_path.stem.replace("performance_report_", "")
        size_kb = report_path.stat().st_size / 1024

        table.add_row(report_path.name, date_str, f"{size_kb:.2f} KB")

    Console().print(table)


# ==============================================================================
# Backup & Restore Commands
# ==============================================================================


@main.group()
@click.pass_context
def backup(ctx):
    """Backup and restore VPN configuration."""
    if "backup_manager" not in ctx.obj:
        ctx.obj["backup_manager"] = BackupManager()


@backup.command("create")
@click.option("--description", default="", help="Backup description")
@click.option("--no-wireguard", is_flag=True, help="Exclude WireGuard config")
@click.option("--no-ssh", is_flag=True, help="Exclude SSH keys")
@click.option("--no-config", is_flag=True, help="Exclude VPNHD config")
@click.option("--no-clients", is_flag=True, help="Exclude client database")
@click.pass_context
def create_backup(ctx, description, no_wireguard, no_ssh, no_config, no_clients):
    """Create a new backup."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]

    display.info("Creating backup...")

    backup_id = backup_manager.create_backup(
        description=description,
        include_wireguard=not no_wireguard,
        include_ssh=not no_ssh,
        include_config=not no_config,
        include_clients=not no_clients,
    )

    if backup_id:
        metadata = backup_manager.get_backup_metadata(backup_id)
        size_kb = metadata.size_bytes / 1024 if metadata else 0

        display.success(f"✓ Backup created: {backup_id}")
        display.print(f"  Size: {size_kb:.2f} KB", style="yellow")
        display.print(
            f"  Includes: {', '.join(metadata.includes) if metadata else 'N/A'}", style="cyan"
        )
    else:
        display.error("Failed to create backup")
        sys.exit(1)


@backup.command("list")
@click.pass_context
def list_backups(ctx):
    """List all backups."""
    backup_manager = ctx.obj["backup_manager"]

    backups = backup_manager.list_backups()

    if not backups:
        ctx.obj["display"].info("No backups found")
        return

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Backups")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="yellow")
    table.add_column("Size", style="green")
    table.add_column("Description", style="white")
    table.add_column("Includes", style="blue")

    for bkp in backups:
        size_kb = bkp.size_bytes / 1024
        created = bkp.created_at[:19] if bkp.created_at else "Unknown"
        includes = ", ".join(bkp.includes[:2])
        if len(bkp.includes) > 2:
            includes += f" (+{len(bkp.includes) - 2})"

        table.add_row(bkp.backup_id, created, f"{size_kb:.2f} KB", bkp.description or "-", includes)

    Console().print(table)


@backup.command("restore")
@click.argument("backup_id")
@click.option("--no-wireguard", is_flag=True, help="Do not restore WireGuard config")
@click.option("--no-ssh", is_flag=True, help="Do not restore SSH keys")
@click.option("--no-config", is_flag=True, help="Do not restore VPNHD config")
@click.option("--no-clients", is_flag=True, help="Do not restore client database")
@click.option("--skip-verification", is_flag=True, help="Skip checksum verification")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def restore_backup(
    ctx, backup_id, no_wireguard, no_ssh, no_config, no_clients, skip_verification, yes
):
    """Restore from a backup."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]
    prompts = ctx.obj["prompts"]

    # Confirm restore
    if not yes:
        display.warning(f"This will restore backup: {backup_id}")
        display.warning("Current configuration will be backed up first")
        if not prompts.confirm("Continue with restore?", default=False):
            display.info("Cancelled")
            return

    display.info(f"Restoring backup: {backup_id}...")

    success = backup_manager.restore_backup(
        backup_id=backup_id,
        restore_wireguard=not no_wireguard,
        restore_ssh=not no_ssh,
        restore_config=not no_config,
        restore_clients=not no_clients,
        verify_checksum=not skip_verification,
    )

    if success:
        display.success(f"✓ Backup {backup_id} restored successfully")
    else:
        display.error("Failed to restore backup")
        sys.exit(1)


@backup.command("verify")
@click.argument("backup_id")
@click.pass_context
def verify_backup(ctx, backup_id):
    """Verify backup integrity."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]

    display.info(f"Verifying backup: {backup_id}...")

    if backup_manager.verify_backup(backup_id):
        display.success(f"✓ Backup {backup_id} is valid")
    else:
        display.error(f"Backup {backup_id} verification failed")
        sys.exit(1)


@backup.command("delete")
@click.argument("backup_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_backup(ctx, backup_id, yes):
    """Delete a backup."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]
    prompts = ctx.obj["prompts"]

    if not yes:
        display.warning(f"This will permanently delete backup: {backup_id}")
        if not prompts.confirm("Continue?", default=False):
            display.info("Cancelled")
            return

    if backup_manager.delete_backup(backup_id):
        display.success(f"✓ Backup {backup_id} deleted")
    else:
        display.error("Failed to delete backup")
        sys.exit(1)


@backup.command("export")
@click.argument("backup_id")
@click.argument("destination")
@click.pass_context
def export_backup(ctx, backup_id, destination):
    """Export backup to external location."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]

    if backup_manager.export_backup(backup_id, destination):
        display.success(f"✓ Backup exported to: {destination}")
    else:
        display.error("Failed to export backup")
        sys.exit(1)


@backup.command("import")
@click.argument("source_path")
@click.pass_context
def import_backup(ctx, source_path):
    """Import backup from external location."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]

    backup_id = backup_manager.import_backup(source_path)

    if backup_id:
        display.success(f"✓ Backup imported: {backup_id}")
    else:
        display.error("Failed to import backup")
        sys.exit(1)


@backup.command("cleanup")
@click.option("--keep", default=10, help="Number of recent backups to keep")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def cleanup_backups(ctx, keep, yes):
    """Delete old backups, keeping only recent ones."""
    backup_manager = ctx.obj["backup_manager"]
    display = ctx.obj["display"]
    prompts = ctx.obj["prompts"]

    backups = backup_manager.list_backups()
    to_delete = len(backups) - keep

    if to_delete <= 0:
        display.info(f"No cleanup needed (only {len(backups)} backups)")
        return

    if not yes:
        display.warning(f"This will delete {to_delete} old backups")
        if not prompts.confirm("Continue?", default=False):
            display.info("Cancelled")
            return

    deleted = backup_manager.cleanup_old_backups(keep_count=keep)
    display.success(f"✓ Deleted {deleted} old backups")


if __name__ == "__main__":
    main()
