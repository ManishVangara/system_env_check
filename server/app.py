#!/usr/bin/env python3
"""
System Check Server - FastAPI Version
Serves pre-built executables and collects system check results.
No authentication required - results identified by run ID.
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
from datetime import datetime
import platform as sys_platform

# Create FastAPI app
app = FastAPI(title="System Check Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXECUTABLES_DIR = os.path.join(BASE_DIR, 'executables')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Ensure directories exist
os.makedirs(EXECUTABLES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------------------------------------
# Pydantic Models
# ----------------------------------------------

class ResultSubmission(BaseModel):
    run_id: str
    results: Dict[str, Any]
    client_version: Optional[str] = None

# ----------------------------------------------
# Helper Functions
# ----------------------------------------------

def get_executable_path(os_type: str) -> Optional[str]:
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

def load_all_results() -> List[Dict[str, Any]]:
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
# Web Pages (HTML)
# ----------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/results/{run_id}", response_class=HTMLResponse)
async def view_result(request: Request, run_id: str):
    """View results page for a specific run ID."""
    return templates.TemplateResponse("results.html", {"request": request, "run_id": run_id})

@app.get("/interview/{run_id}", response_class=HTMLResponse)
async def interview(request: Request, run_id: str):
    """Interview page for a specific run ID."""
    # Check if the system check passed before allowing interview access
    try:
        result_file = os.path.join(RESULTS_DIR, f"{run_id}.json")

        if not os.path.exists(result_file):
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_title": "Results Not Found",
                    "error_message": f"No results found for Run ID: {run_id}",
                    "back_url": "/"
                },
                status_code=404
            )

        with open(result_file, 'r') as f:
            data = json.load(f)

        # Check if system check passed
        result_status = data.get('results', {}).get('status', 'UNKNOWN')

        if result_status != 'PASS':
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_title": "System Check Failed",
                    "error_message": "You must pass the system check before proceeding to the interview.",
                    "back_url": f"/results/{run_id}"
                },
                status_code=403
            )

        return templates.TemplateResponse("interview.html", {"request": request, "run_id": run_id})

    except Exception as e:
        print(f"Error checking interview eligibility: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Error",
                "error_message": "An error occurred while checking your eligibility.",
                "back_url": "/"
            },
            status_code=500
        )

# ----------------------------------------------
# Download Endpoints
# ----------------------------------------------

@app.get("/download")
@app.get("/download/{os_type}")
async def download_executable(request: Request, os_type: Optional[str] = None):
    """Download the executable for the specified OS."""
    try:
        # Detect client OS from User-Agent if not specified
        if not os_type:
            user_agent = request.headers.get('user-agent', '').lower()

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
            return JSONResponse(
                status_code=404,
                content={
                    'success': False,
                    'error': f'Executable not found for OS: {os_type}. Please build executables first.',
                    'hint': f'Run: python build_scripts/build_client.py (on {os_type} machine)'
                }
            )

        # Send file directly (no credential embedding needed)
        return FileResponse(
            path=executable_path,
            filename=download_name,
            media_type='application/octet-stream'
        )

    except Exception as e:
        print(f"Error in download_executable: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

# ----------------------------------------------
# API Endpoints
# ----------------------------------------------

@app.post("/api/results")
async def receive_result(request: Request, submission: ResultSubmission):
    """Receive system check results from client."""
    try:
        if not submission.run_id:
            raise HTTPException(
                status_code=400,
                detail="Missing run_id"
            )

        # Get client IP
        client_ip = request.client.host if request.client else 'unknown'

        # Prepare result data
        result_data = {
            'run_id': submission.run_id,
            'results': submission.results,
            'client_version': submission.client_version,
            'received_at': datetime.utcnow().isoformat() + 'Z',
            'client_ip': client_ip
        }

        # Save to individual result file
        result_file = os.path.join(RESULTS_DIR, f"{submission.run_id}.json")
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        print(f"✓ Received results for run ID: {submission.run_id}")
        print(f"  Status: {submission.results.get('status', 'unknown')}")
        print(f"  Saved to: {result_file}")

        return {
            'success': True,
            'message': 'Results received successfully',
            'run_id': submission.run_id,
            'view_url': f'/results/{submission.run_id}'
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in receive_result: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/{run_id}")
async def get_result(run_id: str):
    """Get results for a specific run ID."""
    try:
        result_file = os.path.join(RESULTS_DIR, f"{run_id}.json")

        if not os.path.exists(result_file):
            raise HTTPException(
                status_code=404,
                detail="Results not found for this run ID"
            )

        with open(result_file, 'r') as f:
            data = json.load(f)

        return {
            'success': True,
            'data': data
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results")
async def list_results():
    """List all results."""
    try:
        results = load_all_results()

        return {
            'success': True,
            'results': results,
            'count': len(results)
        }

    except Exception as e:
        print(f"Error in list_results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------
# Health Check
# ----------------------------------------------

@app.get("/health")
async def health():
    """Health check endpoint."""
    # Check if executables exist
    executables = {}
    for os_type in ['windows', 'linux', 'darwin']:
        exe_path = get_executable_path(os_type)
        executables[os_type] = os.path.exists(exe_path) if exe_path else False

    return {
        'status': 'healthy',
        'version': '1.0.0',
        'executables_available': executables,
        'results_count': len(load_all_results())
    }

# ----------------------------------------------
# Startup Event
# ----------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Print server information on startup."""
    print("=" * 60)
    print("System Check Server v1.0.0 (FastAPI)")
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
    print("Server started successfully!")
    print("=" * 60)

# ----------------------------------------------
# Main Entry Point
# ----------------------------------------------

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
