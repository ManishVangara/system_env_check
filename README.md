# System Environment Check - Simplified

A Python-based application that provides pre-built system check executables for Windows, Linux, and macOS. Users can download, double-click to run, and view results using a unique Run ID. **No registration or authentication required!**

## Features

- **Single executable per OS**: Build once, use for everyone
- **No session management**: No tokens, credentials, or authentication
- **Double-click to run**: No installation required
- **Unique Run IDs**: Each execution generates a unique identifier for viewing results
- **Automated checks**:
  - Virtual machine detection
  - Remote desktop connections (RDP)
  - Remote access tools (TeamViewer, AnyDesk, etc.)
  - Multiple monitors
  - Multiple keyboards and mice
  - System information collection
- **Web interface**: Simple download and results viewing
- **RESTful API**: Server API for result collection

## How It Works

### Simplified Workflow

```
1. User visits web interface
2. Downloads pre-built executable (same file for everyone)
3. Double-clicks to run
4. Client generates unique Run ID
5. Client runs system checks
6. Client sends results to server
7. User views results using Run ID
```

**Key Difference**: No credential embedding! Each executable is a standalone file that generates its own unique Run ID when executed.

## Project Structure

```
system_env_check/
├── client/
│   └── system_check_client.py      # Client executable source code
├── server/
│   ├── app.py                       # Flask server application
│   └── results/                     # Stored results (created at runtime)
├── build_scripts/
│   ├── build_client.py              # Python build script
│   ├── build_all.sh                 # Unix build script
│   └── build_all.bat                # Windows build script
├── templates/
│   ├── index.html                   # Main download page
│   └── results.html                 # Results viewing page
├── static/                          # Static files (if any)
├── executables/                     # Built executables (created after build)
├── requirements.txt                 # Server dependencies
├── client_requirements.txt          # Client build dependencies
└── README.md                        # This file
```

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd system_env_check
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Server Dependencies

```bash
pip install -r requirements.txt
```

### 4. Build Client Executables

You need to build the client executable for each platform you want to support. The build process must be run on each target platform.

#### On Linux:

```bash
# Install build dependencies
pip install -r client_requirements.txt

# Build
./build_scripts/build_all.sh
```

This creates: `executables/system_check_client_linux`

#### On macOS:

```bash
# Install build dependencies
pip install -r client_requirements.txt

# Build
./build_scripts/build_all.sh
```

This creates: `executables/system_check_client_macos`

#### On Windows:

```cmd
REM Install build dependencies
pip install -r client_requirements.txt

REM Build
build_scripts\build_all.bat
```

This creates: `executables\system_check_client.exe`

**Note**: Build once per platform. The same executable works for all users!

## Usage

### Starting the Server

```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Start the server
python server/app.py
```

The server will start on `http://localhost:8000`

### Using the Web Interface

1. Open your browser and navigate to `http://localhost:8000`
2. Click the download button for your operating system
3. The executable will download (same file for everyone!)
4. Run the downloaded executable:
   - **Windows**: Double-click `system_check_client.exe`
   - **Linux/macOS**: Make executable (`chmod +x system_check_client`) and run
5. The client will display a unique **Run ID**
6. Copy the Run ID and paste it in the web interface to view results

### Running the Client Executable

**Method 1: Double-click (Recommended)**
- Simply double-click the downloaded executable
- Copy the Run ID displayed in the console window
- View results on the web interface

**Method 2: Command Line**

```bash
# On Linux/macOS:
./system_check_client

# On Windows:
system_check_client.exe

# With custom server:
./system_check_client --server http://your-server.com:8000

# Save results locally without sending to server:
./system_check_client --save-only
```

### Configuration File (Optional)

You can create a `config.json` file next to the executable to set a default server:

```json
{
  "server": "http://your-server.com:8000"
}
```

### Viewing Results

**Option 1**: Use the Run ID
- Copy the Run ID from the client window
- Paste it in the web interface input box
- Click "View Results"

**Option 2**: Direct URL
- Navigate to: `http://localhost:8000/results/<run-id>`

**Option 3**: Recent Results
- The homepage shows the 5 most recent results
- Click on any result to view details

## API Endpoints

### Download Executable

**GET** `/download` or `/download/<os_type>`

Downloads the pre-built executable for the specified OS.

**Parameters:**
- `os_type` (optional): `windows`, `linux`, or `darwin`
- Auto-detects OS from User-Agent if not specified

**Example:**
```bash
curl -O http://localhost:8000/download/windows
```

### Submit Results

**POST** `/api/results`

Receives system check results from the client.

**Request Body:**
```json
{
  "run_id": "a1b2c3d4-...",
  "results": {
    "timestamp": "2025-01-01T00:00:00Z",
    "status": "PASS",
    "virtual_machine": false,
    "is_rdp": false,
    "remote_access_tools": [],
    "multiple_monitors": false,
    "multiple_keyboards": false,
    "multiple_mice": false,
    "system_info": {
      "hostname": "my-computer",
      "platform": "Windows",
      "...": "..."
    }
  },
  "client_version": "1.0.0"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Results received successfully",
  "run_id": "a1b2c3d4-...",
  "view_url": "/results/a1b2c3d4-..."
}
```

### Get Results

**GET** `/api/results/<run_id>`

Retrieves results for a specific Run ID.

**Example:**
```bash
curl http://localhost:8000/api/results/a1b2c3d4-...
```

### List All Results

**GET** `/api/results`

Lists all results (most recent first).

**Example:**
```bash
curl http://localhost:8000/api/results
```

### Health Check

**GET** `/health`

Server health and status check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "executables_available": {
    "windows": true,
    "linux": false,
    "darwin": false
  },
  "results_count": 42
}
```

## System Checks Performed

1. **Virtual Machine Detection**
   - Detects VMware, VirtualBox, QEMU, Parallels
   - Ignores local hypervisors (WSL2, Docker Desktop)

2. **Remote Desktop Detection**
   - Windows: Checks for RDP session
   - macOS: Checks for screen sharing
   - Linux: Checks for remote X sessions

3. **Remote Access Tools**
   - AnyDesk
   - TeamViewer
   - VNC
   - RustDesk
   - UltraViewer
   - Chrome Remote Desktop

4. **Multiple Monitors**
   - Detects if more than one monitor is connected

5. **Multiple Input Devices**
   - Keyboards (excluding internal/HID keyboards)
   - Mice (excluding touchpads)

6. **System Information**
   - Hostname
   - Operating system and version
   - Architecture
   - Processor
   - Username

## Development

### Testing the Client Locally

For development and testing, you can run the client directly without building:

```bash
cd client
python system_check_client.py --server http://localhost:8000
```

### Manual Build

To build manually using PyInstaller:

```bash
pyinstaller --onefile --console --name system_check_client client/system_check_client.py
```

## Deployment

### Production Server

For production deployment, use a WSGI server like Gunicorn:

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
cd server
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Environment Variables

You can configure the server using environment variables:

- `FLASK_ENV`: Set to `production` for production
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)

### Security Considerations

1. **Use HTTPS**: In production, always use HTTPS
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **CORS**: Configure CORS appropriately for your use case
4. **Input Validation**: Server validates all incoming data
5. **File Storage**: Consider using a database for production instead of file-based storage

## Advantages of This Approach

### Compared to Session-Based System

✅ **Simpler**: No credential management, no session creation
✅ **More Scalable**: Same executable for all users
✅ **Easier Distribution**: Just host three files (one per OS)
✅ **No Expiration**: Run IDs don't expire
✅ **Offline Capable**: Can run with `--save-only` flag
✅ **Transparent**: Results include all system info
✅ **Build Once**: One build per OS, works forever

### Trade-offs

⚠️ **No Authentication**: Anyone can submit results (can add API keys if needed)
⚠️ **Public Results**: Run IDs are the only access control (use UUIDs for security)

## Troubleshooting

### Executable Not Found

If you get "Executable not found" error when downloading:
1. Make sure you've built the executable for the target OS
2. Check that the executable exists in `executables/` directory
3. Verify the server shows "✓" for that OS when starting

### Build Fails

If PyInstaller build fails:
1. Ensure all dependencies are installed: `pip install -r client_requirements.txt`
2. Try cleaning previous builds: `rm -rf build dist *.spec`
3. Check Python version compatibility (Python 3.8+ recommended)

### Client Cannot Connect to Server

1. Verify the server is running
2. Check firewall settings
3. Use `--server` flag to specify correct server URL
4. For local testing, use `http://localhost:8000`

### Results Not Received

1. Check the client console output for errors
2. Verify the server is accessible from the client
3. Check server logs for errors
4. Try using `--save-only` to test local functionality

### "Permission Denied" on Linux/macOS

Make the executable file executable:
```bash
chmod +x system_check_client
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues and questions, please open an issue on GitHub or contact [your contact information].
