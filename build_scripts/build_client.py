#!/usr/bin/env python3
"""
Build script for creating standalone executables for different platforms.
"""

import os
import sys
import platform
import subprocess
import shutil

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CLIENT_DIR = os.path.join(PROJECT_ROOT, 'client')
EXECUTABLES_DIR = os.path.join(PROJECT_ROOT, 'executables')
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')
DIST_DIR = os.path.join(PROJECT_ROOT, 'dist')

# Client script
CLIENT_SCRIPT = os.path.join(CLIENT_DIR, 'system_check_client.py')

def clean_build_dirs():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")

    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            print(f"  Removing {dir_path}")
            shutil.rmtree(dir_path)

    print("✓ Cleaned build directories\n")

def ensure_executables_dir():
    """Ensure executables directory exists."""
    if not os.path.exists(EXECUTABLES_DIR):
        os.makedirs(EXECUTABLES_DIR)
        print(f"✓ Created {EXECUTABLES_DIR}\n")

def build_executable():
    """Build the executable for the current platform."""
    print("=" * 60)
    print("Building System Check Client Executable")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    print()

    # Check if client script exists
    if not os.path.exists(CLIENT_SCRIPT):
        print(f"✗ Error: Client script not found at {CLIENT_SCRIPT}")
        sys.exit(1)

    # Clean previous builds
    clean_build_dirs()

    # Ensure executables directory exists
    ensure_executables_dir()

    # PyInstaller options
    pyinstaller_args = [
        'pyinstaller',
        '--onefile',                    # Single file executable
        '--clean',                       # Clean cache
        '--noconfirm',                   # Don't ask for confirmation
        '--name', 'system_check_client', # Output name
        '--console',                     # Console application
        '--add-data', f'{CLIENT_SCRIPT}:.',  # Include the script
    ]

    # Platform-specific options
    current_platform = platform.system().lower()

    if current_platform == 'windows':
        pyinstaller_args.extend([
            '--icon', 'NONE',  # No icon for now
        ])
        output_name = 'system_check_client.exe'
    elif current_platform == 'darwin':  # macOS
        output_name = 'system_check_client_macos'
    else:  # Linux
        output_name = 'system_check_client_linux'

    # Add the client script as the main file
    pyinstaller_args.append(CLIENT_SCRIPT)

    print("Running PyInstaller...")
    print(f"Command: {' '.join(pyinstaller_args)}\n")

    try:
        # Run PyInstaller
        result = subprocess.run(
            pyinstaller_args,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )

        print(result.stdout)
        print("✓ PyInstaller build completed\n")

    except subprocess.CalledProcessError as e:
        print("✗ PyInstaller build failed:")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

    # Move executable to executables directory
    dist_executable = os.path.join(DIST_DIR, 'system_check_client')
    if current_platform == 'windows':
        dist_executable += '.exe'

    if not os.path.exists(dist_executable):
        print(f"✗ Error: Executable not found at {dist_executable}")
        sys.exit(1)

    final_path = os.path.join(EXECUTABLES_DIR, output_name)

    print(f"Moving executable to {final_path}...")
    shutil.move(dist_executable, final_path)

    # Make executable on Unix systems
    if current_platform in ['linux', 'darwin']:
        os.chmod(final_path, 0o755)

    print(f"✓ Executable created: {final_path}\n")

    # Get file size
    file_size = os.path.getsize(final_path)
    file_size_mb = file_size / (1024 * 1024)

    print("=" * 60)
    print("Build Summary")
    print("=" * 60)
    print(f"Platform: {current_platform}")
    print(f"Output: {output_name}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"Location: {final_path}")
    print("=" * 60)
    print()

    # Clean up build artifacts (optional)
    print("Cleaning up build artifacts...")
    clean_build_dirs()

    # Remove spec file
    spec_file = os.path.join(PROJECT_ROOT, 'system_check_client.spec')
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"  Removed {spec_file}")

    print("✓ Cleanup completed\n")
    print("=" * 60)
    print("✓ Build completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    build_executable()
