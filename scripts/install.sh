#!/bin/bash
# VPNHD Installation Script
# Installs VPNHD and all dependencies for Debian-based systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.10"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
        echo "Usage: sudo bash scripts/install.sh"
        exit 1
    fi
}

# Check OS
check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" != "debian" && "$ID" != "ubuntu" ]]; then
            print_warning "VPNHD is tested on Debian/Ubuntu. You're using: $NAME"
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
}

# Check Python version
check_python() {
    print_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

    if (( $(echo "$PYTHON_VERSION < $PYTHON_MIN_VERSION" | bc -l) )); then
        print_error "Python $PYTHON_MIN_VERSION+ required, found Python $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION found"
}

# Install system dependencies
install_system_deps() {
    print_header "Installing System Dependencies"

    print_info "Updating package lists..."
    apt-get update -qq || {
        print_error "Failed to update package lists"
        exit 1
    }

    print_info "Installing required packages..."
    local packages=(
        "python3"
        "python3-pip"
        "python3-dev"
        "wireguard-tools"
        "wireguard"
        "openssh-client"
        "openssh-server"
        "ufw"
        "fail2ban"
        "git"
        "curl"
    )

    for package in "${packages[@]}"; do
        if dpkg -l | grep -q "^ii  $package"; then
            print_success "$package already installed"
        else
            print_info "Installing $package..."
            apt-get install -y "$package" > /dev/null 2>&1 || {
                print_error "Failed to install $package"
                exit 1
            }
            print_success "Installed $package"
        fi
    done
}

# Install Python dependencies
install_python_deps() {
    print_header "Installing Python Dependencies"

    print_info "Upgrading pip..."
    python3 -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1 || {
        print_error "Failed to upgrade pip"
        exit 1
    }
    print_success "pip upgraded"

    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        print_info "Installing requirements from requirements.txt..."
        python3 -m pip install -r "$PROJECT_ROOT/requirements.txt" || {
            print_error "Failed to install Python dependencies"
            exit 1
        }
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found at $PROJECT_ROOT"
    fi
}

# Install VPNHD package
install_vpnhd() {
    print_header "Installing VPNHD"

    if [[ -f "$PROJECT_ROOT/setup.py" ]]; then
        print_info "Installing VPNHD from setup.py..."
        cd "$PROJECT_ROOT"
        python3 -m pip install -e . > /dev/null 2>&1 || {
            print_error "Failed to install VPNHD"
            exit 1
        }
        print_success "VPNHD installed"
    else
        print_warning "setup.py not found at $PROJECT_ROOT"
        print_info "Trying alternative installation method..."
        cd "$PROJECT_ROOT"
        python3 setup.py install > /dev/null 2>&1 || {
            print_error "Failed to install VPNHD"
            exit 1
        }
        print_success "VPNHD installed"
    fi
}

# Create configuration directory
setup_config_dir() {
    print_header "Setting Up Configuration Directory"

    # Create config directory for regular user if available
    if [[ -n "$SUDO_USER" ]]; then
        CONFIG_DIR="/home/$SUDO_USER/.config/vpnhd"
        print_info "Creating config directory for user $SUDO_USER..."
        mkdir -p "$CONFIG_DIR"
        mkdir -p "$CONFIG_DIR/logs"
        chown -R "$SUDO_USER:$SUDO_USER" "$CONFIG_DIR"
        chmod 700 "$CONFIG_DIR"
        print_success "Configuration directory created at $CONFIG_DIR"
    else
        CONFIG_DIR="/root/.config/vpnhd"
        mkdir -p "$CONFIG_DIR"
        mkdir -p "$CONFIG_DIR/logs"
        print_success "Configuration directory created at $CONFIG_DIR"
    fi
}

# Enable required services
enable_services() {
    print_header "Configuring Services"

    # Enable SSH
    print_info "Enabling SSH service..."
    systemctl enable ssh > /dev/null 2>&1
    systemctl start ssh > /dev/null 2>&1
    print_success "SSH enabled"

    # Enable fail2ban
    print_info "Enabling fail2ban service..."
    systemctl enable fail2ban > /dev/null 2>&1
    systemctl start fail2ban > /dev/null 2>&1
    print_success "fail2ban enabled"
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"

    print_info "Checking Python packages..."
    python3 -c "import rich; import click; import yaml; import jsonschema; import jinja2; import netifaces" 2>/dev/null && \
        print_success "All Python packages verified" || {
        print_error "Some Python packages are missing"
        exit 1
    }

    print_info "Checking system commands..."
    for cmd in python3 pip wireguard ssh ufw fail2ban-client; do
        if command -v "$cmd" &> /dev/null; then
            print_success "$cmd available"
        else
            print_error "$cmd not found"
            exit 1
        fi
    done

    print_info "Checking VPNHD command..."
    if python3 -m vpnhd --version &> /dev/null; then
        VPNHD_VERSION=$(python3 -m vpnhd --version 2>/dev/null | head -1 || echo "1.0.0")
        print_success "VPNHD version $VPNHD_VERSION"
    else
        print_warning "VPNHD command not working yet (might need PATH update)"
    fi
}

# Show next steps
show_next_steps() {
    print_header "Installation Complete!"

    echo -e "\n${GREEN}VPNHD has been successfully installed!${NC}\n"

    echo "Next steps:"
    echo "1. Start the interactive setup:"
    echo -e "   ${BLUE}sudo vpnhd${NC}"
    echo ""
    echo "2. Or continue from last completed phase:"
    echo -e "   ${BLUE}sudo vpnhd --continue${NC}"
    echo ""
    echo "3. For help, run:"
    echo -e "   ${BLUE}vpnhd --help${NC}"
    echo ""
    echo "Documentation:"
    echo "  - User Guide: docs/USER_GUIDE.md"
    echo "  - Troubleshooting: docs/TROUBLESHOOTING.md"
    echo "  - FAQ: docs/FAQ.md"
    echo ""

    if [[ -n "$SUDO_USER" ]]; then
        echo -e "${YELLOW}Note: Configuration will be stored in /home/$SUDO_USER/.config/vpnhd/${NC}"
    fi

    echo ""
}

# Main installation
main() {
    clear
    print_header "VPNHD Installation Script"

    echo "This script will install VPNHD and all dependencies."
    echo ""

    # Checks
    check_root
    check_os
    check_python

    # Installation
    install_system_deps
    install_python_deps
    install_vpnhd
    setup_config_dir
    enable_services

    # Verification and summary
    verify_installation
    show_next_steps
}

# Run main function
main "$@"

exit 0
