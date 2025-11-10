# System Environment Check

A Python-based application that allows clients to download and run pre-built system check executables on different operating systems (Windows, Linux, macOS). The executable performs environment checks and automatically sends results back to the server.

## Features

- **Cross-platform support**: Windows, Linux, and macOS
- **Double-click to run**: No installation required, just download and execute
- **Automated checks**:
  - Virtual machine detection
  - Remote desktop connections (RDP)
  - Remote access tools (TeamViewer, AnyDesk, etc.)
  - Multiple monitors
  - Multiple keyboards and mice
  - External peripherals
- **Secure credential embedding**: Credentials are embedded in the executable during download
- **Web interface**: Easy-to-use interface for generating download links
- **RESTful API**: Server API for session management and result collection

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
│   └── index.html                   # Web interface
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

You need to build the client executables for each platform you want to support. The build process must be run on each target platform.

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

**Note**: To build for all platforms, you'll need to run the build script on each operating system and collect the executables in the `executables/` directory.

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

The server will start on `http://localhost:5000`

### Using the Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. Click "Generate Download Link"
3. A download link will be created with embedded credentials
4. Click "Download System Check Client" to download the executable
5. The downloaded file will be specific to your operating system

### Running the Client Executable

**Method 1: Double-click (Recommended)**
- Simply double-click the downloaded executable
- It will run the system checks and send results to the server
- A console window will show the progress

**Method 2: Command Line**

```bash
# On Linux/macOS:
./system_check_client

# On Windows:
system_check_client.exe
```

### Viewing Results

Results are automatically displayed on the web interface after the client completes the checks. You can also:

1. Check the session status via API:
   ```bash
   curl http://localhost:5000/api/sessions/<session_id>
   ```

2. View stored results in `server/results/<session_id>.json`

## API Endpoints

### Create Session

**POST** `/api/sessions/create`

Creates a new session and returns credentials.

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "token": "secure-token",
  "server_url": "http://localhost:5000",
  "download_url": "http://localhost:5000/api/download/{session_id}/{token}"
}
```

### Download Executable

**GET** `/api/download/<session_id>/<token>`

Downloads the executable with embedded credentials. Automatically detects the client's OS from the User-Agent header.

**Query Parameters:**
- `os` (optional): Override OS detection (`windows`, `linux`, `darwin`)

### Submit Results

**POST** `/api/sessions/<session_id>/result`

Receives system check results from the client.

**Request Body:**
```json
{
  "token": "secure-token",
  "results": {
    "timestamp": "2025-01-01T00:00:00Z",
    "status": "PASS",
    "virtual_machine": false,
    "is_rdp": false,
    "remote_access_tools": [],
    "multiple_monitors": false,
    "multiple_keyboards": false,
    "multiple_mice": false
  },
  "client_version": "0.3.0"
}
```

### Get Session

**GET** `/api/sessions/<session_id>`

Retrieves session information and results.

### List Sessions

**GET** `/api/sessions`

Lists all sessions.

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

6. **External Peripherals**
   - USB devices
   - Bluetooth devices

## Development

### Testing the Client Locally

For development and testing, you can run the client directly without building:

```bash
cd client
python system_check_client.py --server http://localhost:5000 --session-id test-session --token test-token
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
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables

You can configure the server using environment variables:

- `FLASK_ENV`: Set to `production` for production
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)

### Security Considerations

1. **Use HTTPS**: In production, always use HTTPS to protect credentials in transit
2. **Token Security**: Tokens are generated using `secrets.token_urlsafe()` for cryptographic security
3. **Session Storage**: For production, consider using a database instead of in-memory storage
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **CORS**: Configure CORS appropriately for your use case

## Troubleshooting

### Executable Not Found

If you get "Executable not found" error when downloading:
1. Make sure you've built the executable for the target OS
2. Check that the executable exists in `executables/` directory
3. Verify the executable has the correct name for the OS

### Build Fails

If PyInstaller build fails:
1. Ensure all dependencies are installed: `pip install -r client_requirements.txt`
2. Try cleaning previous builds: `rm -rf build dist *.spec`
3. Check Python version compatibility (Python 3.8+ recommended)

### Client Cannot Connect to Server

1. Verify the server is running
2. Check firewall settings
3. Ensure the correct server URL is being used
4. For local testing, use `http://localhost:5000` or `http://127.0.0.1:5000`

### Results Not Received

1. Check the client console output for errors
2. Verify the session ID and token are correct
3. Check server logs for errors
4. Ensure the server endpoint is accessible from the client

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues and questions, please open an issue on GitHub or contact [your contact information].
