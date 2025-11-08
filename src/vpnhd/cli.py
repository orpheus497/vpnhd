"""Main CLI entry point for VPNHD."""

import sys
import click
from pathlib import Path

from .config.manager import ConfigManager
from .ui.display import Display
from .ui.prompts import Prompts
from .ui.menus import MainMenu
from .phases import get_phase_class
from .utils.logging import setup_logging, get_logger
from .utils.constants import APP_NAME, APP_VERSION
from .__version__ import __version__


@click.group(invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
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
    ctx.obj['config'] = config_manager
    ctx.obj['display'] = display
    ctx.obj['prompts'] = prompts
    ctx.obj['logger'] = logger

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

            if choice == '0':  # Exit
                display.info("Goodbye!")
                sys.exit(0)

            elif choice == '1':  # Continue to next phase
                next_phase = config_manager.get_next_phase()
                if next_phase == 0:
                    display.success("All phases complete! Your VPN is ready.")
                    prompts.pause()
                else:
                    execute_phase(next_phase, config_manager, display, prompts)

            elif choice == '2':  # Jump to specific phase
                phase_num = menu.show_phase_selection()
                if phase_num:
                    execute_phase(phase_num, config_manager, display, prompts)

            elif choice == '3':  # Review configuration
                menu.show_configuration_review()

            elif choice == '4':  # Show phase details
                phase_num = menu.show_phase_selection()
                if phase_num:
                    menu.show_phase_details(phase_num)

            elif choice == '5':  # Troubleshooting
                menu.show_troubleshooting()

            elif choice == '6':  # View guide documentation
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


def execute_phase(phase_number: int, config_manager: ConfigManager, display: Display, prompts: Prompts):
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
            if not prompts.confirm(f"Phase {phase_number} is already complete. Run again?", default=False):
                return

        # Check prerequisites
        if not phase.check_prerequisites():
            display.error("Prerequisites not met")
            prompts.pause()
            return

        # Confirm execution
        if not prompts.confirm(f"Ready to execute Phase {phase_number}: {phase.name}?", default=True):
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
    display = ctx.obj['display']
    display.print(f"{APP_NAME} version {__version__}", style="cyan bold")


@main.command()
@click.argument('phase_number', type=int)
@click.pass_context
def run_phase(ctx, phase_number):
    """Run a specific phase."""
    config_manager = ctx.obj['config']
    display = ctx.obj['display']
    prompts = ctx.obj['prompts']

    execute_phase(phase_number, config_manager, display, prompts)


@main.command()
@click.pass_context
def status(ctx):
    """Show current status."""
    config_manager = ctx.obj['config']
    display = ctx.obj['display']

    display.heading("VPNHD Status", style="cyan bold")
    display.newline()

    for phase_num in range(1, 9):
        phase_info = config_manager.get_phase_info(phase_num)
        if phase_info:
            display.phase_status(
                phase_num,
                phase_info['name'],
                phase_info['completed']
            )

    completion = config_manager.get_completion_percentage()
    display.newline()
    display.print(f"Progress: {completion:.0f}% complete", style="yellow")


@main.command()
@click.pass_context
def reset(ctx):
    """Reset configuration to defaults."""
    config_manager = ctx.obj['config']
    display = ctx.obj['display']
    prompts = ctx.obj['prompts']

    if prompts.confirm("Are you sure you want to reset all configuration?", default=False):
        if config_manager.reset():
            display.success("Configuration reset to defaults")
        else:
            display.error("Failed to reset configuration")


@main.command()
@click.argument('output_path', type=click.Path())
@click.pass_context
def export_config(ctx, output_path):
    """Export configuration to file."""
    config_manager = ctx.obj['config']
    display = ctx.obj['display']

    if config_manager.export_config(Path(output_path)):
        display.success(f"Configuration exported to {output_path}")
    else:
        display.error("Failed to export configuration")


if __name__ == '__main__':
    main()
