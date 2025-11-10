#!/usr/bin/env python3
"""
System Check Server
Serves pre-built executables and collects system check results.
"""

from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import uuid
import secrets
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
SESSIONS_FILE = os.path.join(os.path.dirname(__file__), 'sessions.json')

# Ensure directories exist
os.makedirs(EXECUTABLES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# In-memory session storage (use database in production)
sessions: Dict[str, Dict[str, Any]] = {}

def load_sessions():
    """Load sessions from file."""
    global sessions
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                sessions = json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
            sessions = {}
    else:
        sessions = {}

def save_sessions():
    """Save sessions to file."""
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print(f"Error saving sessions: {e}")

# Load sessions on startup
load_sessions()

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

def embed_credentials_in_executable(executable_path: str, credentials: Dict[str, str]) -> bytes:
    """Embed credentials into executable binary."""
    with open(executable_path, 'rb') as f:
        executable_data = f.read()

    # Create credentials JSON
    creds_json = json.dumps(credentials)

    # Create markers and embed
    marker_start = b"__SYSTEMCHECK_CREDS_START__"
    marker_end = b"__SYSTEMCHECK_CREDS_END__"

    embedded_data = executable_data + marker_start + creds_json.encode('utf-8') + marker_end

    return embedded_data

# ----------------------------------------------
# API Endpoints
# ----------------------------------------------

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/sessions/create', methods=['POST'])
def create_session():
    """Create a new session and return credentials."""
    try:
        data = request.get_json() or {}

        # Generate session credentials
        session_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)

        # Get server URL from request or use default
        server_url = data.get('server_url', request.host_url.rstrip('/'))

        # Store session info
        sessions[session_id] = {
            'session_id': session_id,
            'token': token,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'pending',
            'results': None,
            'metadata': data.get('metadata', {})
        }

        save_sessions()

        return jsonify({
            'success': True,
            'session_id': session_id,
            'token': token,
            'server_url': server_url,
            'download_url': f"{server_url}/api/download/{session_id}/{token}"
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/<session_id>/<token>')
def download_executable(session_id: str, token: str):
    """Download the executable with embedded credentials."""
    try:
        # Validate session and token
        session = sessions.get(session_id)
        if not session or session.get('token') != token:
            return jsonify({
                'success': False,
                'error': 'Invalid session or token'
            }), 401

        # Detect client OS from User-Agent
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

        # Allow OS override via query parameter
        os_override = request.args.get('os')
        if os_override:
            os_type = os_override.lower()

        # Get executable path
        executable_path = get_executable_path(os_type)

        if not executable_path or not os.path.exists(executable_path):
            return jsonify({
                'success': False,
                'error': f'Executable not found for OS: {os_type}. Please build executables first.'
            }), 404

        # Prepare credentials to embed
        server_url = request.host_url.rstrip('/')
        credentials = {
            'server': server_url,
            'session_id': session_id,
            'token': token
        }

        # Embed credentials in executable
        embedded_executable = embed_credentials_in_executable(executable_path, credentials)

        # Create temporary file and send
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(download_name)[1]) as tmp:
            tmp.write(embedded_executable)
            tmp_path = tmp.name

        # Update session status
        sessions[session_id]['status'] = 'downloaded'
        sessions[session_id]['downloaded_at'] = datetime.utcnow().isoformat() + 'Z'
        sessions[session_id]['os_type'] = os_type
        save_sessions()

        # Send file and clean up
        response = send_file(
            tmp_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/octet-stream'
        )

        # Schedule cleanup (note: in production, use a proper cleanup mechanism)
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(tmp_path)
            except:
                pass

        return response

    except Exception as e:
        print(f"Error in download_executable: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions/<session_id>/result', methods=['POST'])
def receive_result(session_id: str):
    """Receive system check results from client."""
    try:
        data = request.get_json()

        # Validate session and token
        session = sessions.get(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Invalid session'
            }), 401

        token = data.get('token')
        if session.get('token') != token:
            return jsonify({
                'success': False,
                'error': 'Invalid token'
            }), 401

        # Store results
        results = data.get('results', {})
        sessions[session_id]['results'] = results
        sessions[session_id]['status'] = 'completed'
        sessions[session_id]['completed_at'] = datetime.utcnow().isoformat() + 'Z'
        sessions[session_id]['client_version'] = data.get('client_version')

        save_sessions()

        # Also save to individual result file
        result_file = os.path.join(RESULTS_DIR, f"{session_id}.json")
        with open(result_file, 'w') as f:
            json.dump({
                'session': session,
                'results': results,
                'received_at': datetime.utcnow().isoformat() + 'Z'
            }, f, indent=2)

        return jsonify({
            'success': True,
            'message': 'Results received successfully'
        }), 200

    except Exception as e:
        print(f"Error in receive_result: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """Get session status and results."""
    session = sessions.get(session_id)

    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404

    # Don't expose the token in the response
    safe_session = {k: v for k, v in session.items() if k != 'token'}

    return jsonify({
        'success': True,
        'session': safe_session
    }), 200

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all sessions."""
    safe_sessions = [
        {k: v for k, v in session.items() if k != 'token'}
        for session in sessions.values()
    ]

    return jsonify({
        'success': True,
        'sessions': safe_sessions,
        'count': len(safe_sessions)
    }), 200

# ----------------------------------------------
# Static Files
# ----------------------------------------------

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)

# ----------------------------------------------
# Main Entry Point
# ----------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("System Check Server")
    print("=" * 60)
    print(f"Executables directory: {EXECUTABLES_DIR}")
    print(f"Results directory: {RESULTS_DIR}")
    print("=" * 60)
    print("\nStarting server on http://0.0.0.0:5000")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
