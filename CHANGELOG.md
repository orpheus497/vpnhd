# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- WireGuard server peer management with automatic client registration
- ServerConfigManager module for adding/removing peers and reloading WireGuard
- QR code generation for mobile clients using qrencode
- qrcode.py module with terminal and file-based QR code generation
- Automated SSH configuration management (SSHConfigManager)
- Programmatic sshd_config modification for disabling password authentication
- fail2ban custom jail configuration for SSH and WireGuard protection
- Fail2banConfigManager with SSH and WireGuard jail creation
- Distribution-agnostic Linux client support (Phases 4 and 5)
- Support for Fedora, Ubuntu, Debian, Pop!_OS, elementary OS, Linux Mint, CentOS, RHEL, Arch, and Manjaro
- Mobile client support for both Android and iOS with QR code scanning
- Rollback functionality for all phases with state tracking
- Verify methods for all phases to validate successful completion
- Template path constants using absolute paths from utils/constants.py
- QR code directory path configuration
- fail2ban configuration constants (ban times, max retries)
- Supported client distributions mapping with package managers
- WireGuard package names per distribution
- Security validators module (security/validators.py) with comprehensive input validation functions
- Custom exception hierarchy (exceptions.py) for structured error handling
- Hostname validation (is_valid_hostname) with RFC compliance
- IP address validation (is_valid_ip, is_valid_ipv4) for both IPv4 and IPv6
- CIDR notation validation (is_valid_cidr) for network configurations
- Port number validation (is_valid_port) ensuring 1-65535 range
- MAC address validation (is_valid_mac_address) supporting colon and hyphen separators
- Path safety validation (is_safe_path) to prevent directory traversal attacks
- WireGuard key format validation (is_valid_wireguard_key) for base64 encoded keys
- Input sanitization functions (sanitize_hostname, sanitize_filename)
- VPNHDError base exception class and specialized exceptions
- ConfigurationError, PhaseError, ValidationError exception classes
- NetworkError, SystemCommandError, SecurityError exception classes
- Interface name validator (is_valid_interface_name) preventing command injection through interface parameters
- Package name validator (is_valid_package_name) following Debian/RPM naming conventions
- Netmask validator (is_valid_netmask) supporting both CIDR and dotted decimal notation
- Interface and package name sanitizers for safe string handling
- Debian 13 (Trixie) support with updated version detection
- Python 3.11 minimum version requirement for Debian 13 compatibility
- Python version constants (PYTHON_MIN_VERSION, PYTHON_MIN_VERSION_TUPLE)

### Changed
- Phase 4 renamed from "Fedora Client" to "Linux Desktop Client (Always-On)"
- Phase 5 renamed from "Pop!_OS Client" to "Linux Desktop Client (On-Demand)"
- Phase 6 renamed from "Termux/Android" to "Mobile Client (Android/iOS)"
- Phase 4, 5, 6 now support multiple Linux distributions instead of being distribution-specific
- Phase 7 now automatically disables SSH password authentication (not just manual instructions)
- Phase 8 now creates custom fail2ban jails for SSH and WireGuard protection
- Configuration schema updated with new phase names and rollback data tracking
- Client configuration keys changed from distribution-specific to role-based
- VPN client IP assignments changed to role-based (linux_desktop_always_on, linux_desktop_on_demand, mobile)
- Template paths now use absolute paths from constants module
- Phase names updated to be distribution-agnostic in constants.py
- execute_command() function signature changed to accept Union[str, List[str]] for enhanced security
- Command execution switched from shell=True to shell=False to prevent injection attacks
- run_command_with_input() updated with array-based command execution
- .gitignore updated to exclude .dev-docs/ directory containing AI-generated documentation

### Fixed
- Template path resolution issues in Phases 2, 4, 5, and 6
- Server configuration not being updated when clients are added
- WireGuard server not reloading when new peers are added
- SSH password authentication requiring manual configuration file edits
- fail2ban lacking custom jail configurations for enhanced security
- Command injection vulnerabilities by removing shell=True from subprocess.run() calls
- Unsafe command execution enabling arbitrary code injection through user inputs
- Missing input validation allowing malicious hostnames, IPs, and paths
- Bare except clauses in phase4, phase5, and phase6 verify() methods catching SystemExit
- Missing capture_output parameter in phase8_security.py verify() method
- Command injection in files.py chmod and rm commands using f-strings
- Command injection in fail2ban_config.py across 5 fail2ban-client commands
- Command injection in ssh_config.py service discovery using shell pipe
- Command injection in commands.py get_command_version() using f-string
- Missing input validation in network/testing.py ping_host() and traceroute()
- Missing port validation in phase8_security.py _configure_ufw() method
- Method name mismatch in ssh_config.py calling restart() instead of restart_service()
- Command injection in network/testing.py check_port_forwarding() using shell pipe
- Command injection in network/testing.py measure_latency() using f-string
- Command injection in network/testing.py test_vpn_connectivity() using f-string
- Missing input validation in test_connectivity() and test_port_open()
- **CRITICAL**: Private key exposure in process list (crypto/wireguard.py)
- dnf/yum check-update exit code 100 misinterpreted as failure (packages.py)
- ServiceStatus enum compared to string instead of enum value (fail2ban_config.py)
- TOCTOU race condition in file creation (utils/helpers.py)
- Imports inside functions reducing performance (4 instances removed)
- Code duplication between phase4 and phase5 (~150 lines of duplicate logic)
- Command injection in files.py across 7 file operation methods (mv, cat, cp, chmod, chown, tee)
- **CRITICAL**: Command injection in network/interfaces.py bring_interface_up() using f-string (Line 34)
- **CRITICAL**: Command injection in network/interfaces.py bring_interface_down() using f-string (Line 54)
- **CRITICAL**: Command injection in network/interfaces.py set_ip_address() using f-string (Line 76)
- **CRITICAL**: Command injection in network/interfaces.py add_route() using f-string concatenation (Lines 165-167)
- **CRITICAL**: Command injection in network/interfaces.py delete_route() using f-string (Line 187)
- **CRITICAL**: Command injection in network/interfaces.py flush_interface() using f-string (Line 207)
- **CRITICAL**: Command injection in network/interfaces.py get_interface_stats() using f-string (Line 225)
- **CRITICAL**: Command injection in network/interfaces.py enable_ip_forwarding() using shell pipe (Lines 105, 112)
- **CRITICAL**: Command injection in system/packages.py is_package_installed() for apt/dpkg (Line 78)
- **CRITICAL**: Command injection in system/packages.py is_package_installed() for dnf/yum (Line 86)
- **CRITICAL**: Command injection in system/packages.py is_package_installed() for pacman (Line 94)
- **CRITICAL**: Command injection in system/packages.py install_package() using f-string concatenation (Lines 122-137)
- **CRITICAL**: Command injection in system/packages.py update_package_cache() using f-string (Lines 190, 195, 201)
- **CRITICAL**: Command injection in system/packages.py upgrade_packages() using f-string concatenation (Lines 222-234)
- **CRITICAL**: Command injection in system/packages.py remove_package() using f-string concatenation (Lines 328-343)
- Debian 11 (Bullseye) removed from supported versions list (EOL approaching)
- Debian 13 (Trixie) missing from supported versions

### Removed
- Deprecated phase4_fedora.py (replaced by distribution-agnostic phase4_linux_client.py)
- Deprecated phase5_popos.py (replaced by distribution-agnostic phase5_linux_client_ondemand.py)
- Deprecated phase6_termux.py (replaced by distribution-agnostic phase6_mobile.py)
- Legacy phase imports and exports from phases/__init__.py

### Enhanced
- Phase 4 (Linux Desktop Client Always-On) now automatically adds peer to server
- Phase 5 (Linux Desktop Client On-Demand) now automatically adds peer to server with isolation
- Phase 6 (Mobile Client) now generates QR codes and automatically adds peer to server
- Phase 7 (SSH Keys) now includes automated sshd_config modification and rollback support
- Phase 8 (Security Hardening) now creates fail2ban jails for both SSH and WireGuard

### Technical
- Added ServerConfigManager class with peer management methods
- Added SSHConfigManager class with automated configuration modification
- Added Fail2banConfigManager class with jail creation and management
- Added QR code generation utilities with terminal display support
- Updated crypto/__init__.py to export ServerConfigManager and QR code functions
- Updated system/__init__.py to export SSHConfigManager and Fail2banConfigManager
- Updated phases/__init__.py to reference new phase classes
- Maintained backward compatibility with legacy phase imports (deprecated)
- Added comprehensive logging throughout new modules
- Added error handling and validation for all new functionality
- Implemented shlex.split() for safe command parsing from strings
- Commands now passed as arrays to subprocess.run() preventing shell interpretation
- Added Union type support in execute_command() maintaining backward compatibility
- Created security module with dedicated validators for all input types
- Implemented custom exception hierarchy replacing bare except clauses
- Added detailed security documentation in command execution function docstrings
- Integrated security validators into network testing and firewall configuration
- Replaced bare except with specific Exception handling in all phase verify() methods
- Converted all remaining f-string commands to secure array format
- Eliminated shell pipe usage in ssh_config.py using systemctl exit codes
- Added proper logging for exception cases instead of silent failures
- Removed 217 lines of deprecated code reducing maintenance burden
- Cleaned up phase module exports to only include active implementations
- Fixed method name mismatch preventing AttributeError in SSH service restart
- Moved 4 function-level imports to module level improving performance
- Fixed TOCTOU race condition using atomic file creation (open with 'x' mode)
- Improved code organization following Python best practices
- Created distribution_helpers module extracting common distribution selection logic
- Eliminated ~150 lines of duplicated code between phase4 and phase5
- Centralized WireGuard installation instructions in reusable helper functions
- Converted all file operation commands in files.py to array format (7 methods)
- Eliminated shell pipe usage in append_to_file() using stdin-based tee command

### Security
- Eliminated 52 critical command injection vulnerabilities across codebase (37 previously + 15 new)
- **CRITICAL FIX**: Eliminated 8 command injection vulnerabilities in network/interfaces.py
- **CRITICAL FIX**: Eliminated 7 command injection vulnerabilities in system/packages.py
- **CRITICAL FIX**: Eliminated private key exposure in process listings (stdin-based key derivation)
- Implemented comprehensive input validation framework preventing injection attacks
- Created structured exception handling replacing unsafe bare except clauses
- Added security-focused logging throughout command execution paths
- Validated all dependencies as 100% FOSS and royalty-free
- Fixed 3 bare except clauses that could hide SystemExit and KeyboardInterrupt
- Added hostname/IP validation preventing malicious input in network operations
- Added port range validation preventing invalid or privileged port usage
- Added interface name validation for VPN operations preventing command injection
- Added package name validation for package manager operations preventing command injection
- Added netmask validation supporting both CIDR and dotted decimal formats
- Eliminated all shell pipe usage replacing with native command options or Python file I/O
- Converted all f-string command construction to safe array format in network and package modules
- Ensured no shell=True usage in any subprocess operations
- Extended validation coverage to all network testing functions
- Private keys now transmitted via stdin only, never in command arguments
- Type-safe enum comparisons for service status checks
- All network interface operations now validate interface names before command execution
- All package manager operations now validate package names before command execution
- Network routing operations now validate CIDR blocks and gateway IPs

### Documentation
- Updated README.md with distribution-agnostic language
- Updated phase descriptions to reflect multi-distribution support
- Updated example workflow with clearer phase purposes
- Updated system requirements to list multiple supported distributions
- Added documentation for QR code usage
- Added documentation for automated SSH configuration
- Added documentation for fail2ban custom jails

## [v1.0.0] - 2025-11-08

### Added
- Complete 8-phase VPN setup automation
- Phase 1: Debian installation guide and validation
- Phase 2: WireGuard server configuration
- Phase 3: Router port forwarding assistance
- Phase 4: Fedora client setup (always-on)
- Phase 5: Pop!_OS client setup (on-demand, isolated)
- Phase 6: Termux/Android setup with QR code generation
- Phase 7: SSH key authentication setup
- Phase 8: Security hardening (UFW + fail2ban)
- Interactive terminal UI with Rich library
- Configuration management and validation with JSON schema
- Network discovery and validation utilities
- Automatic network interface detection
- Cryptographic key generation (WireGuard + SSH)
- Jinja2-based configuration templating
- Comprehensive error handling and rollback mechanisms
- Detailed logging and progress tracking
- Phase prerequisite checking
- Configuration backup and restore
- Complete test suite with pytest
- User documentation (User Guide, Troubleshooting, FAQ)
- Installation and uninstallation scripts
- GitHub Actions CI/CD workflow
- Code quality tools (black, flake8, mypy, isort)

### Security
- SSH key-only authentication enforcement
- UFW firewall configuration with secure defaults
- fail2ban intrusion prevention setup
- Zero external dependencies (privacy-first)
- FOSS-only ecosystem
- No telemetry or tracking
- Secure file permissions for private keys (0600)
- Input validation and sanitization
- Command injection prevention

### Documentation
- Complete README with installation and usage
- Comprehensive USER_GUIDE.md
- Detailed TROUBLESHOOTING.md
- FAQ.md for common questions
- CONTRIBUTING.md for contributors
- Inline code documentation with docstrings
- Systems Design Document (SDD)
- Technical Specifications
- Project Requirements Document

### Performance
- Cached network discovery
- Minimal system command calls
- Efficient configuration validation
- Progressive UI updates

### Developer Experience
- Type hints throughout codebase
- PEP 8 compliant code
- Comprehensive test coverage
- Pre-commit hooks support
- EditorConfig for consistency
- Development dependencies in requirements-dev.txt

## [0.1.0] - Development

### Added
- Initial project structure
- Core modules framework
- Basic CLI skeleton
- Configuration schema design
- Phase interface definition

---

[Unreleased]: https://github.com/orpheus497/vpnhd/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/orpheus497/vpnhd/releases/tag/v1.0.0
[0.1.0]: https://github.com/orpheus497/vpnhd/releases/tag/v0.1.0
