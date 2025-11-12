#!/usr/bin/env python3
"""
System Check Server - Simplified Version
Serves pre-built executables and collects system check results.
No authentication required - results identified by run ID.
"""

from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from typing import Dict, Any
import platform as sys_platform

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
CORS(app)

# Configuration
EXECUTABLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'executables')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

# Ensure directories exist
os.makedirs(EXECUTABLES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ----------------------------------------------
# Helper Functions
# ----------------------------------------------

def get_executable_path(os_type: str) -> str:
    """Get the path to the executable for the given OS."""
    executable_names = {
        'windows': 'system_check_client.exe',
        'linux': 'system_check_client_linux',
        'darwin': 'system_check_client_macos'
    }

    filename = executable_names.get(os_type.lower())
    if not filename:
        return None

    return os.path.join(EXECUTABLES_DIR, filename)

def load_all_results() -> list:
    """Load all results from the results directory."""
    results = []

    if not os.path.exists(RESULTS_DIR):
        return results

    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(RESULTS_DIR, filename), 'r') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    # Sort by timestamp (most recent first)
    results.sort(key=lambda x: x.get('received_at', ''), reverse=True)
    return results

# ----------------------------------------------
# API Endpoints
# ----------------------------------------------

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/download')
@app.route('/download/<os_type>')
def download_executable(os_type: str = None):
    """Download the executable for the specified OS."""
    try:
        # Detect client OS from User-Agent if not specified
        if not os_type:
            user_agent = request.headers.get('User-Agent', '').lower()

            if 'windows' in user_agent or 'win32' in user_agent or 'win64' in user_agent:
                os_type = 'windows'
                download_name = 'system_check_client.exe'
            elif 'mac' in user_agent or 'darwin' in user_agent:
                os_type = 'darwin'
                download_name = 'system_check_client'
            elif 'linux' in user_agent:
                os_type = 'linux'
                download_name = 'system_check_client'
            else:
                # Default to current server OS for testing
                os_type = sys_platform.system().lower()
                download_name = 'system_check_client'
        else:
            # OS type specified in URL
            if os_type == 'windows':
                download_name = 'system_check_client.exe'
            else:
                download_name = 'system_check_client'

        # Get executable path
        executable_path = get_executable_path(os_type)

        if not executable_path or not os.path.exists(executable_path):
            return jsonify({
                'success': False,
                'error': f'Executable not found for OS: {os_type}. Please build executables first.',
                'hint': f'Run: python build_scripts/build_client.py (on {os_type} machine)'
            }), 404

        # Send file directly (no credential embedding needed)
        return send_file(
            executable_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        print(f"Error in download_executable: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/results', methods=['POST'])
def receive_result():
    """Receive system check results from client."""
    try:
        data = request.get_json()

        run_id = data.get('run_id')
        results = data.get('results', {})
        client_version = data.get('client_version')

        if not run_id:
            return jsonify({
                'success': False,
                'error': 'Missing run_id'
            }), 400

        # Prepare result data
        result_data = {
            'run_id': run_id,
            'results': results,
            'client_version': client_version,
            'received_at': datetime.utcnow().isoformat() + 'Z',
            'client_ip': request.remote_addr
        }

        # Save to individual result file
        result_file = os.path.join(RESULTS_DIR, f"{run_id}.json")
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        print(f"✓ Received results for run ID: {run_id}")
        print(f"  Status: {results.get('status', 'unknown')}")
        print(f"  Saved to: {result_file}")

        return jsonify({
            'success': True,
            'message': 'Results received successfully',
            'run_id': run_id,
            'view_url': f'/results/{run_id}'
        }), 200

    except Exception as e:
        print(f"Error in receive_result: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/results/<run_id>', methods=['GET'])
def get_result(run_id: str):
    """Get results for a specific run ID."""
    try:
        result_file = os.path.join(RESULTS_DIR, f"{run_id}.json")

        if not os.path.exists(result_file):
            return jsonify({
                'success': False,
                'error': 'Results not found for this run ID'
            }), 404

        with open(result_file, 'r') as f:
            data = json.load(f)

        return jsonify({
            'success': True,
            'data': data
        }), 200

    except Exception as e:
        print(f"Error in get_result: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/results', methods=['GET'])
def list_results():
    """List all results."""
    try:
        results = load_all_results()

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        }), 200

    except Exception as e:
        print(f"Error in list_results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/results/<run_id>')
def view_result(run_id: str):
    """View results page for a specific run ID."""
    return render_template('results.html', run_id=run_id)

# ----------------------------------------------
# Static Files
# ----------------------------------------------

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)

# ----------------------------------------------
# Health Check
# ----------------------------------------------

@app.route('/health')
def health():
    """Health check endpoint."""

    # Check if executables exist
    executables = {}
    for os_type in ['windows', 'linux', 'darwin']:
        exe_path = get_executable_path(os_type)
        executables[os_type] = os.path.exists(exe_path) if exe_path else False

    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'executables_available': executables,
        'results_count': len(load_all_results())
    }), 200

# ----------------------------------------------
# Main Entry Point
# ----------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("System Check Server v1.0.0")
    print("=" * 60)
    print(f"Executables directory: {EXECUTABLES_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print()

    # Check for available executables
    print("Available executables:")
    for os_type in ['windows', 'linux', 'darwin']:
        exe_path = get_executable_path(os_type)
        if exe_path and os.path.exists(exe_path):
            print(f"  ✓ {os_type}: {os.path.basename(exe_path)}")
        else:
            print(f"  ✗ {os_type}: not built")

    print()
    print("=" * 60)
    print("Starting server on http://0.0.0.0:5000")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
