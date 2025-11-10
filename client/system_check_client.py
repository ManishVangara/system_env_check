#!/usr/bin/env python3
"""
System Check Client
Downloads and runs system environment checks, then reports results to server.
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
from urllib.parse import urlparse, parse_qs

VERSION = "0.3.0"

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
        "virtual_machine": check_virtual_machine(),
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
# Credential Management
# ----------------------------------------------

def parse_protocol_url(url_string: str) -> Dict[str, str]:
    """Parse systemcheck:// URL and extract credentials."""
    try:
        parsed = urlparse(url_string)

        if parsed.scheme != "systemcheck":
            raise ValueError(f"Invalid protocol: {parsed.scheme}. Expected 'systemcheck'")

        params = parse_qs(parsed.query)

        server = params.get("server", [None])[0]
        session_id = params.get("session_id", [None])[0]
        token = params.get("token", [None])[0]

        if not all([server, session_id, token]):
            raise ValueError("Missing required parameters: server, session_id, or token")

        return {
            "server": server,
            "session_id": session_id,
            "token": token
        }
    except Exception as e:
        print(f"Error parsing protocol URL: {e}")
        return None

def load_embedded_credentials() -> Dict[str, str]:
    """Load credentials embedded in the executable binary."""
    try:
        if getattr(sys, 'frozen', False):
            executable_path = sys.executable
        else:
            executable_path = os.path.abspath(__file__)

        with open(executable_path, 'rb') as f:
            data = f.read()

        marker_start = b"__SYSTEMCHECK_CREDS_START__"
        marker_end = b"__SYSTEMCHECK_CREDS_END__"

        start_pos = data.find(marker_start)
        end_pos = data.find(marker_end)

        if start_pos != -1 and end_pos != -1:
            creds_start = start_pos + len(marker_start)
            creds_data = data[creds_start:end_pos]

            credentials = json.loads(creds_data.decode('utf-8'))
            print("Using embedded credentials from executable")
            return credentials
        else:
            return None

    except Exception as e:
        print(f"Warning: Could not read embedded credentials: {e}")
        return None

def get_credentials(args: argparse.Namespace) -> Dict[str, str]:
    """Determine credentials source and return them.
    Priority: command-line args > embedded credentials > protocol URL > config.json
    """
    if args.server and args.session_id and args.token:
        print("Using credentials from command-line arguments")
        return {
            "server": args.server,
            "session_id": args.session_id,
            "token": args.token
        }

    embedded_creds = load_embedded_credentials()
    if embedded_creds:
        return embedded_creds

    if args.protocol_url and args.protocol_url.startswith("systemcheck://"):
        print("Detected protocol URL launch")
        credentials = parse_protocol_url(args.protocol_url)
        if credentials:
            print("Using credentials from protocol URL")
            return credentials
        else:
            print("✗ Failed to parse protocol URL")
            input("\nPress Enter to exit...")
            sys.exit(1)

    try:
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(application_path, "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        print("Using credentials from config.json")
        return {
            "server": config["server"],
            "session_id": config["session_id"],
            "token": config["token"]
        }
    except FileNotFoundError:
        print("✗ No credentials provided.")
        print("  Credentials should be embedded in the executable.")
        print("  For testing, you can pass --server, --session-id, and --token as arguments,")
        print("  or provide a config.json file.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"✗ Invalid or corrupted 'config.json': {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

# ----------------------------------------------
# Server Communication
# ----------------------------------------------

def send_results_to_server(server_url: str, session_id: str, token: str, results: Dict[str, Any]) -> bool:
    """Send check results to the server."""
    try:
        print(f"\nSending results to server: {server_url}/api/sessions/{session_id}/result")

        endpoint = f"{server_url}/api/sessions/{session_id}/result"
        payload = {
            "token": token,
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
    print("=" * 50)
    print(f"System Check Client v{VERSION}")
    print("=" * 50)
    print()

    parser = argparse.ArgumentParser(description="System Check Client")
    parser.add_argument("--server", help="Server URL")
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("protocol_url", nargs="?", help="systemcheck:// protocol URL")
    args = parser.parse_args()

    credentials = get_credentials(args)
    server_url = credentials["server"]
    session_id = credentials["session_id"]
    token = credentials["token"]

    try:
        results = run_system_check()
    except Exception as e:
        print(f"\n✗ Error running system checks: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    success = send_results_to_server(server_url, session_id, token, results)

    print()
    if success:
        print("=" * 50)
        print("✓ System check completed successfully!")
        print("=" * 50)
        print("\nYou can now check the candidate page in your browser.")
        print()
        input("Press Enter to exit...")
        sys.exit(0)
    else:
        print("=" * 50)
        print("✗ System check failed to submit results")
        print("=" * 50)
        print("\nPlease check server status and try again.")
        print()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
