#!/usr/bin/env python3
"""Setup configuration for VPNHD package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from __version__.py
version_file = Path(__file__).parent / "src" / "vpnhd" / "__version__.py"
version = "1.0.0"  # Default version

if version_file.exists():
    # Parse version from __version__.py
    version_content = version_file.read_text(encoding="utf-8")
    for line in version_content.split("\n"):
        if line.startswith('__version__'):
            version = line.split('"')[1]
            break

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []

if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").split("\n")
        if line.strip() and not line.startswith("#")
    ]

# Read development requirements
dev_requirements_file = Path(__file__).parent / "requirements-dev.txt"
dev_requirements = []

if dev_requirements_file.exists():
    dev_requirements = [
        line.strip()
        for line in dev_requirements_file.read_text(encoding="utf-8").split("\n")
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="vpnhd",
    version=version,
    description="Privacy-first home VPN setup automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="orpheus497",
    author_email="vpnhd@example.com",
    url="https://github.com/orpheus497/vpnhd",
    license="GPL-3.0",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "vpnhd=vpnhd.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords=[
        "vpn",
        "wireguard",
        "privacy",
        "security",
        "home-network",
        "automation",
        "cli",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/orpheus497/vpnhd/issues",
        "Documentation": "https://github.com/orpheus497/vpnhd/tree/main/docs",
        "Source Code": "https://github.com/orpheus497/vpnhd",
    },
    include_package_data=True,
    zip_safe=False,
)
