# Quick Start Guide - Simplified Version

Get up and running in 5 minutes!

## What's Different?

This simplified version **removes all session/credential management**:
- ✅ Single executable per OS (build once, use forever)
- ✅ No tokens or authentication
- ✅ Each run generates a unique Run ID
- ✅ Users view results by entering their Run ID

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

The server will start on `http://localhost:8000`

### 4. Test the Application

1. Open your browser to `http://localhost:8000`
2. Download the executable for your OS
3. Double-click the executable to run it
4. Copy the **Run ID** displayed in the console
5. Paste the Run ID in the web interface to view results

## One-Line Quick Test

After installing dependencies:

```bash
# Build client and start server (in separate terminals)
python build_scripts/build_client.py && python server/app.py
```

## Testing Without Building

For quick testing, you can run the client directly:

```bash
# In terminal 1: Start server
python server/app.py

# In terminal 2: Run client directly
cd client
python system_check_client.py
```

The client will:
1. Generate a unique Run ID
2. Run system checks
3. Send results to `http://localhost:8000` (default)
4. Display the Run ID for viewing results

## How It Works

```
┌─────────────┐
│  Web Page   │  1. User downloads executable
└─────┬───────┘     (same file for everyone)
      │
      ▼
┌─────────────┐
│ Executable  │  2. User runs it
│             │  3. Generates Run ID: a1b2c3d4-...
│             │  4. Runs system checks
│             │  5. Sends results to server
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Server    │  6. Stores results by Run ID
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  Web Page   │  7. User enters Run ID to view results
└─────────────┘
```

## Viewing Results

Three ways to view results:

1. **Enter Run ID**: Paste the Run ID in the input box on the homepage
2. **Direct URL**: Go to `http://localhost:8000/results/<run-id>`
3. **Recent Results**: Click on any result in the "Recent Results" section

## Command-Line Options

```bash
# Run with custom server
./system_check_client --server http://your-server.com:8000

# Save results locally without sending to server
./system_check_client --save-only

# View help
./system_check_client --help
```

## Configuration File

Create a `config.json` file next to the executable to set defaults:

```json
{
  "server": "http://your-server.com:8000"
}
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Build executables for other platforms (Windows, Linux, macOS)
- Deploy to production with gunicorn
- Customize the checks in `client/system_check_client.py`

## Common Issues

**Q: Build fails with "PyInstaller not found"**

A: Install build dependencies: `pip install -r client_requirements.txt`

**Q: Server shows "Executable not found"**

A: Build the executable first: `python build_scripts/build_client.py`

**Q: Client can't connect to server**

A: Make sure the server is running and accessible. Use `--server` flag if needed.

**Q: "Permission Denied" on Linux/macOS**

A: Make it executable: `chmod +x system_check_client`

## Key Differences from Previous Version

| Old (Session-Based) | New (Simplified) |
|---------------------|------------------|
| Session creation required | No sessions |
| Credentials embedded in executable | No credentials |
| Different executable per user | Same executable for everyone |
| Token expiration | Run IDs never expire |
| Complex workflow | Simple: download → run → view |
| Build on download | Build once |

The new approach is much simpler and more scalable!
