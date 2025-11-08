#!/bin/bash
# VPNHD Uninstallation Script
# Removes VPNHD and optionally its configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        echo "Usage: sudo bash scripts/uninstall.sh"
        exit 1
    fi
}

# Confirm uninstallation
confirm_uninstall() {
    print_header "VPNHD Uninstallation"

    echo "This will uninstall VPNHD."
    echo ""
    read -p "Keep configuration and keys? (y/n, default=y) " -n 1 -r KEEP_CONFIG
    echo

    if [[ -z "$KEEP_CONFIG" ]]; then
        KEEP_CONFIG="y"
    fi

    echo ""
    if [[ "$KEEP_CONFIG" =~ ^[Yy]$ ]]; then
        print_info "Configuration will be preserved at ~/.config/vpnhd/"
        print_warning "You can restore VPNHD later with the same configuration"
    else
        print_warning "Configuration and keys will be DELETED"
        read -p "Type 'DELETE' to confirm complete removal: " CONFIRM_DELETE
        if [[ "$CONFIRM_DELETE" != "DELETE" ]]; then
            echo "Cancelled."
            exit 0
        fi
    fi

    echo ""
    read -p "Proceed with uninstallation? (y/n, default=n) " -n 1 -r CONFIRM
    echo

    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        print_info "Uninstallation cancelled"
        exit 0
    fi
}

# Stop VPN services
stop_services() {
    print_header "Stopping Services"

    # Stop WireGuard if running
    if systemctl is-active --quiet wg-quick@wg0; then
        print_info "Stopping WireGuard..."
        systemctl stop wg-quick@wg0 > /dev/null 2>&1 || true
        print_success "WireGuard stopped"
    fi

    # Disable WireGuard auto-start
    if systemctl is-enabled --quiet wg-quick@wg0 2>/dev/null; then
        print_info "Disabling WireGuard auto-start..."
        systemctl disable wg-quick@wg0 > /dev/null 2>&1 || true
        print_success "WireGuard auto-start disabled"
    fi
}

# Remove WireGuard configuration
remove_wireguard_config() {
    print_header "Removing WireGuard Configuration"

    if [[ -f /etc/wireguard/wg0.conf ]]; then
        print_warning "Found WireGuard configuration at /etc/wireguard/wg0.conf"
        read -p "Remove WireGuard configuration? (y/n, default=y) " -n 1 -r REMOVE_WG
        echo

        if [[ -z "$REMOVE_WG" ]] || [[ "$REMOVE_WG" =~ ^[Yy]$ ]]; then
            rm -f /etc/wireguard/wg0.conf
            print_success "WireGuard configuration removed"
        else
            print_info "WireGuard configuration preserved"
        fi
    fi

    # Remove WireGuard keys
    if [[ -f /etc/wireguard/privatekey ]]; then
        print_warning "Found WireGuard private key at /etc/wireguard/privatekey"
        read -p "Remove WireGuard private key? (y/n, default=y) " -n 1 -r REMOVE_KEYS
        echo

        if [[ -z "$REMOVE_KEYS" ]] || [[ "$REMOVE_KEYS" =~ ^[Yy]$ ]]; then
            rm -f /etc/wireguard/privatekey
            rm -f /etc/wireguard/publickey
            print_success "WireGuard keys removed"
        else
            print_info "WireGuard keys preserved"
        fi
    fi
}

# Remove VPNHD package
remove_package() {
    print_header "Removing VPNHD Package"

    print_info "Removing VPNHD..."
    python3 -m pip uninstall -y vpnhd > /dev/null 2>&1 || {
        print_warning "VPNHD package not found in pip (might be OK)"
    }
    print_success "VPNHD package removed"
}

# Remove firewall rules (optional)
cleanup_firewall() {
    print_header "Firewall Configuration"

    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "Status: active"; then
            print_info "UFW firewall is active"
            read -p "Remove VPNHD-related firewall rules? (y/n, default=n) " -n 1 -r REMOVE_UFW
            echo

            if [[ "$REMOVE_UFW" =~ ^[Yy]$ ]]; then
                print_info "Resetting firewall to defaults..."
                ufw reset --force > /dev/null 2>&1 || true
                print_success "Firewall reset to defaults"
                print_warning "Note: You may need to reconfigure UFW manually"
            else
                print_info "Firewall configuration preserved"
            fi
        fi
    fi
}

# Remove configuration (if requested)
remove_configuration() {
    print_header "Configuration Management"

    if [[ -n "$SUDO_USER" ]]; then
        CONFIG_DIR="/home/$SUDO_USER/.config/vpnhd"
    else
        CONFIG_DIR="/root/.config/vpnhd"
    fi

    if [[ -d "$CONFIG_DIR" ]]; then
        if [[ "$KEEP_CONFIG" =~ ^[Nn]$ ]]; then
            print_warning "Removing configuration directory..."
            rm -rf "$CONFIG_DIR"
            print_success "Configuration directory removed"
        else
            print_info "Configuration preserved at $CONFIG_DIR"
            print_info "To restore VPNHD later, reinstall and configuration will be used"
        fi
    fi
}

# Show uninstallation summary
show_summary() {
    print_header "Uninstallation Complete"

    echo ""
    echo -e "${GREEN}VPNHD has been successfully uninstalled!${NC}"
    echo ""

    if [[ -n "$SUDO_USER" ]]; then
        CONFIG_DIR="/home/$SUDO_USER/.config/vpnhd"
    else
        CONFIG_DIR="/root/.config/vpnhd"
    fi

    if [[ -d "$CONFIG_DIR" ]]; then
        echo "Your configuration is preserved at:"
        echo "  $CONFIG_DIR"
        echo ""
        echo "To reinstall VPNHD with the same configuration:"
        echo -e "  ${BLUE}sudo bash scripts/install.sh${NC}"
        echo ""
    else
        echo "All VPNHD files have been removed."
        echo ""
        if [[ -f /etc/wireguard/wg0.conf ]]; then
            print_warning "Note: WireGuard configuration still exists at /etc/wireguard/wg0.conf"
        fi
    fi

    echo "To completely remove WireGuard and dependencies:"
    echo -e "  ${BLUE}sudo apt remove wireguard-tools wireguard fail2ban${NC}"
    echo ""
}

# Main uninstallation
main() {
    clear

    check_root
    confirm_uninstall

    [[ "$KEEP_CONFIG" =~ ^[Nn]$ ]] && stop_services
    [[ "$KEEP_CONFIG" =~ ^[Nn]$ ]] && remove_wireguard_config
    [[ "$KEEP_CONFIG" =~ ^[Nn]$ ]] && cleanup_firewall

    remove_package
    remove_configuration

    show_summary
}

# Run main function
main "$@"

exit 0
