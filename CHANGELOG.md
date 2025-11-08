# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
