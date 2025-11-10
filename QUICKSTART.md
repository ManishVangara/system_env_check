# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Quick Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install server dependencies
pip install -r requirements.txt
```

### 2. Build Client Executable (for your current OS)

```bash
# Install build dependencies
pip install -r client_requirements.txt

# Build for current platform
python build_scripts/build_client.py
```

This will create an executable in the `executables/` directory.

### 3. Start the Server

```bash
python server/app.py
```

The server will start on `http://localhost:5000`

### 4. Use the Application

1. Open your browser to `http://localhost:5000`
2. Click "Generate Download Link"
3. Download the executable
4. Double-click the executable to run it
5. View results on the web page

## One-Line Quick Test

After installing dependencies:

```bash
# Build client and start server
python build_scripts/build_client.py && python server/app.py
```

## Testing Without Building

For quick testing, you can run the client directly:

```bash
# In terminal 1: Start server
python server/app.py

# In terminal 2: Create a test config
echo '{"server": "http://localhost:5000", "session_id": "test", "token": "test123"}' > client/config.json

# Run client directly
cd client
python system_check_client.py
```

Note: This won't actually work because the session doesn't exist. Use the web interface to create a proper session.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Build executables for other platforms
- Deploy to production with gunicorn
- Customize the checks in `client/system_check_client.py`

## Common Issues

**Q: Build fails with "PyInstaller not found"**

A: Install build dependencies: `pip install -r client_requirements.txt`

**Q: Server shows "Template not found"**

A: Make sure you're running `python server/app.py` from the project root directory

**Q: Executable doesn't run**

A: On Linux/macOS, make sure it's executable: `chmod +x executables/system_check_client_*`
