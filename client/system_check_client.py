#!/usr/bin/env python3
"""
System Check Client - Simplified Version
Runs system environment checks and reports results to server.
No authentication required - generates unique run ID per execution.
"""

import platform
import json
import argparse
import requests
from datetime import datetime
from typing import Dict, Any
import subprocess
import os
import sys
import uuid
import webbrowser

VERSION = "1.0.0"

# Default server URL (can be overridden)
DEFAULT_SERVER = "http://localhost:8000"

# ----------------------------------------------
# System Detection Functions
# ----------------------------------------------

def detect_remote_tools():
    """Detects if any remote-access software is running."""
    tools = []
    known_tools = ["anydesk", "teamviewer", "vnc", "rustdesk", "ultraviewer", "chrome remote desktop"]
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["tasklist"], capture_output=True, text=True)
        else:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for tool in known_tools:
            if tool.lower().replace(" ", "") in result.stdout.lower().replace(" ", ""):
                tools.append(tool)
    except Exception as e:
        print("Error checking remote tools:", e)
    return tools

def check_multiple_monitors():
    """Check if multiple monitors are connected."""
    try:
        sys_platform = platform.system()
        if sys_platform == "Windows":
            result = subprocess.run(
                ["powershell", "-Command", "(Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorBasicDisplayParams).Count"],
                capture_output=True, text=True, timeout=10
            )
            count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 1
            return count > 1

        elif sys_platform == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ["system_profiler", "-json", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                data = json.loads(result.stdout)
                displays = data.get("SPDisplaysDataType", [])

                monitor_count = 0
                for gpu in displays:
                    if "spdisplays_ndrvs" in gpu:
                        monitor_count += len(gpu["spdisplays_ndrvs"])

                print(f"[DEBUG] macOS monitors detected: {monitor_count}")
                return monitor_count > 1

            except (json.JSONDecodeError, KeyError, subprocess.TimeoutExpired) as e:
                print(f"[DEBUG] JSON method failed: {e}")
                return False

        elif sys_platform == "Linux":
            result = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True, timeout=10)
            return "Monitors: 1" not in result.stdout

    except Exception as e:
        print(f"Error checking monitors: {e}")
        return False

    return False

def count_devices(device_type):
    """Count active external devices (mouse, keyboard, etc.) ignoring internal/ghost entries."""
    try:
        sys_platform = platform.system()
        if sys_platform == "Windows":
            cmd = [
                "powershell",
                "-Command",
                f"Get-PnpDevice -Class {device_type} | Select-Object Status, FriendlyName"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            names = lines[2:]  # skip headers

            if device_type.lower() == "mouse":
                ok_devices = [
                    line for line in names
                    if "ok" in line.lower()
                    and not any(k in line.lower() for k in ["elan", "touchpad"])
                ]
                return len(ok_devices)
            elif device_type.lower() == "keyboard":
                ok_devices = [
                    line for line in names
                    if "ok" in line.lower()
                    and not any(k in line.lower() for k in ["hid", "internal", "ps/2"])
                ]
                return len(ok_devices)

        elif sys_platform == "Linux":
            result = subprocess.run(["xinput", "list"], capture_output=True, text=True, timeout=10)
            lines = result.stdout.lower().splitlines()
            if device_type.lower() == "mouse":
                return len([l for l in lines if "mouse" in l and "touchpad" not in l])
            if device_type.lower() == "keyboard":
                return len([l for l in lines if "keyboard" in l])

        elif sys_platform == "Darwin":
            result = subprocess.run(["system_profiler", "SPUSBDataType"], capture_output=True, text=True, timeout=10)
            text = result.stdout.lower()
            if device_type.lower() == "mouse":
                return text.count("mouse")
            if device_type.lower() == "keyboard":
                return text.count("keyboard")

    except Exception as e:
        print("Device count error:", e)
        return 1

    return 1

def check_virtual_machine():
    """Detect if system is running inside a virtual machine.
    Ignores local hypervisors like WSL2 or Docker Desktop."""
    try:
        sys_platform = platform.system()
        if sys_platform == "Windows":
            result = subprocess.run(["systeminfo"], capture_output=True, text=True, timeout=15)
            text = result.stdout.lower()

            vm_keywords = ["vmware", "virtualbox", "qemu", "parallels"]
            if any(k in text for k in vm_keywords):
                return True

            if "hyper-v requirements" in text and "a hypervisor has been detected" in text:
                return False
            return False

        elif sys_platform == "Darwin":  # macOS
            result = subprocess.run(["sysctl", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=10)
            text = result.stdout.lower()
            vm_keywords = ["virtualbox", "vmware", "parallels"]
            return any(k in text for k in vm_keywords)

        elif sys_platform == "Linux":
            result = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=10)
            text = result.stdout.lower().strip()
            return text not in ["", "none"]

    except Exception as e:
        print("VM detection error:", e)
        return False

def is_rdp_session():
    """Check if the current session is a remote desktop session."""
    try:
        if platform.system() == "Windows":
            return os.environ.get("SESSIONNAME", "").startswith("RDP")

        elif platform.system() == "Darwin":
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10)
            return "screensharingd" in result.stdout.lower()

        elif platform.system() == "Linux":
            result = subprocess.run(["who"], capture_output=True, text=True, timeout=10)
            return "(:0)" not in result.stdout

    except Exception as e:
        print("RDP check error:", e)
        return False

    return False

def run_system_check() -> Dict[str, Any]:
    """Run a full system check and return results."""
    print("Running system checks...")

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "remote_access_tools": detect_remote_tools(),
        "is_rdp": is_rdp_session(),
        "multiple_monitors": check_multiple_monitors(),
        "multiple_keyboards": count_devices("Keyboard") > 1,
        "multiple_mice": count_devices("Mouse") > 1,
        "virtual_machine": check_virtual_machine()
    }

    # Final decision
    if any([
        result["remote_access_tools"],
        result["is_rdp"],
        result["multiple_monitors"],
        result["multiple_keyboards"],
        result["multiple_mice"],
        result["virtual_machine"]
    ]):
        result["status"] = "FAIL"
    else:
        result["status"] = "PASS"

    print("-" * 50)
    for key, value in result.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("-" * 50)

    return result

# ----------------------------------------------
# Server Communication
# ----------------------------------------------

def get_server_url(args: argparse.Namespace) -> str:
    """Determine server URL from arguments or config file."""

    # Priority 1: Command-line argument
    if args.server:
        return args.server.rstrip('/')

    # Priority 2: Config file
    try:
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        config_path = os.path.join(application_path, "config.json")

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            if "server" in config:
                print(f"Using server from config.json: {config['server']}")
                return config["server"].rstrip('/')
    except Exception as e:
        print(f"Note: Could not read config.json: {e}")

    # Priority 3: Default
    print(f"Using default server: {DEFAULT_SERVER}")
    return DEFAULT_SERVER

def send_results_to_server(server_url: str, run_id: str, results: Dict[str, Any]) -> bool:
    """Send check results to the server."""
    try:
        print(f"\nSending results to server: {server_url}/api/results")

        endpoint = f"{server_url}/api/results"
        payload = {
            "run_id": run_id,
            "results": results,
            "client_version": VERSION
        }

        response = requests.post(
            endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✓ Results sent successfully!")
            return True
        else:
            print(f"✗ Server returned error: {response.status_code}")
            print(f"  Message: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Is the server running?")
        print(f"   Server URL: {server_url}")
        return False
    except requests.exceptions.Timeout:
        print("✗ Connection to server timed out.")
        return False
    except Exception as e:
        print(f"✗ Error sending results: {e}")
        return False

# ----------------------------------------------
# Main Entry Point
# ----------------------------------------------

def main():
    print("=" * 60)
    print(f"System Check Client v{VERSION}")
    print("=" * 60)
    print()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="System Check Client")
    parser.add_argument("--server", help="Server URL (default: http://localhost:5000)")
    parser.add_argument("--save-only", action="store_true", help="Only save results to file, don't send to server")
    args = parser.parse_args()

    # Generate unique run ID
    run_id = str(uuid.uuid4())
    print(f"Run ID: {run_id}")
    print()

    # Get server URL
    server_url = get_server_url(args)
    print()

    # Run system checks
    try:
        results = run_system_check()
    except Exception as e:
        print(f"\n✗ Error running system checks: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Save results locally
    try:
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        results_file = os.path.join(application_path, f"result_{run_id}.json")
        with open(results_file, 'w') as f:
            json.dump({
                "run_id": run_id,
                "results": results,
                "client_version": VERSION
            }, f, indent=2)
        print(f"\n✓ Results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠ Could not save results to file: {e}")

    # Send to server (unless save-only mode)
    if args.save_only:
        print("\n(Save-only mode: Results not sent to server)")
        success = True
    else:
        success = send_results_to_server(server_url, run_id, results)

    print()
    if success:
        print("=" * 60)
        print("✓ System check completed successfully!")
        print("=" * 60)
        print()
        print(f"Your Run ID: {run_id}")
        print()

        results_url = f"{server_url}/results/{run_id}"
        print("Opening results in your browser...")
        print(f"{results_url}")
        print()

        # Automatically open results page in browser
        try:
            webbrowser.open(results_url)
            print("✓ Browser opened successfully!")
        except Exception as e:
            print(f"⚠ Could not open browser automatically: {e}")
            print(f"Please manually visit: {results_url}")
        print()
    else:
        print("=" * 60)
        print("✗ System check completed but failed to send results")
        print("=" * 60)
        print()
        print(f"Your Run ID: {run_id}")
        print("Results were saved locally.")
        print()

    input("Press Enter to exit...")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
