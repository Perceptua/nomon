# nomon - Setup & Progress

## Project Overview
Scripts for Raspberry Pi microcontroller & peripherals with HAT (Hardware Attached on Top) module support.

---

## ✅ Setup Completed

### Core Configuration Files
- **pyproject.toml** - Complete project metadata, dependencies, and tool configurations
  - Python >= 3.8 support
  - Configured for setuptools build system
  - Tool configs for black, ruff, mypy, pytest

### Dependency Management
- **requirements.txt** - Production dependencies
  - gpiozero >= 2.0 (high-level GPIO abstraction)
  - pigpio >= 1.78 (low-level GPIO daemon)
  - smbus2 >= 0.4.1 (I2C communication)
  - pyserial >= 3.5 (serial communication)
  - spidev >= 3.5 (conditional on Linux only)

- **requirements-dev.txt** - Development dependencies
  - pytest + pytest-cov (testing)
  - black (code formatting)
  - ruff (linting)
  - mypy (type checking)
  - sphinx (documentation)

### Project Structure
- **tests/** directory with example test
- **src/nomon/__init__.py** - Package initialization with version metadata
- **Makefile** - Common development commands:
  - `make install-dev` - Install with dev dependencies
  - `make test` - Run tests with coverage
  - `make lint` - Check code style
  - `make format` - Format code
  - `make type-check` - Run type checking
  - `make clean` - Remove generated files

### Development Tools
- **.editorconfig** - Consistent editor formatting
- **MANIFEST.in** - Package distribution metadata
- **.gitignore** - Already configured for Python projects

### Environment Setup
- Dependencies installed and verified (`pip install -e ".[dev]"` successful)
- spidev configured as Linux-only (avoids Visual Studio compilation on Windows)

---

---

## 🎯 Current Focus

### Phase 1: Raspberry Pi Camera Module ✅ COMPLETE

**Camera Implementation** (`src/nomon/camera.py`)
- ✅ Still image capture via `capture_image(filename)`
- ✅ Video recording via `start_recording(filename)` / `stop_recording()`
- ✅ Live streaming via `get_frame_generator()` 
- ✅ Encoder selection (H264 @ 5Mbps or MJPEG)
- ✅ Context manager support for clean resource management
- ✅ Full type hints and docstrings
- ✅ 20 comprehensive tests (all passing)

**Hardware Integration**
- ✅ OV5647 sensor specifications discovered and documented
  - Default video: 1280x720 @ 30 fps (practical balance)
  - Maximum resolution: 2592x1944 @ 15.63 fps
  - Dual encoder support: H264, MJPEG
- ✅ Hardware discovery guide in CAMERA_DISCOVERY.md

**Security Hardening**
- ✅ Filename-only validation (no path-like components allowed)
- ✅ Path traversal protection (blocks `..`, `./`, absolute paths)
- ✅ Hidden file protection (rejects filenames starting with `.`)
- ✅ Directory containment enforcement (all files saved to configured directory)
- ✅ Security tests validating attack prevention

**API Design**
- Constructor: `Camera(camera_index, width, height, fps, encoder, directory)`
  - Defaults optimized for OV5647: 1280x720 @ 30fps H264
  - Optional directory parameter for file storage control
- Methods accept plain filenames only: `capture_image("photo.jpg")`
- Raises `ValueError` on invalid filename attempts
- Comprehensive error messages for debugging

**Test Coverage** (20 tests)
- Initialization with defaults and custom parameters
- Image capture success and error cases
- Video recording with H264 and MJPEG encoders
- Double-start recording prevention
- Context manager cleanup
- Frame generator functionality
- Path traversal attack prevention
- Filename validation (separators, absolute paths, traversal)

### Phase 1.5: Camera Web Streaming ✅ COMPLETE

**Implementation Complete**
- ✅ Architecture: MJPEG over HTTP (multipart/x-mixed-replace)
- ✅ Optional dependency strategy: Flask in `[web]` optional group
- ✅ API design: `StreamServer` class with `start()` and `start_background()` methods
- ✅ Code implementation with full type hints and docstrings
- ✅ 14 comprehensive tests (all passing)
- ✅ HTML viewer page with responsive CSS
- ✅ Documentation and usage examples in SETUP.md

**StreamServer Class** (`src/nomon/streaming.py`)
- Access at `http://localhost:8000` (default, configurable)
- Endpoints:
  - `GET /` - HTML page with live stream viewer
  - `GET /stream` - MJPEG stream (multipart/x-mixed-replace)
- Thread-safe frame sharing from Camera to HTTP response
- Constructor parameters: host, port, camera_index, width, height, fps, encoder
- Full type hints and docstrings
- Security: localhost binding by default, port validation
- Methods:
  - `start()` - Run server (blocking)
  - `start_background()` - Run server in daemon thread
  - `close()` - Clean up camera resources

**HTML Viewer Page**
- Simple HTML with embedded CSS styling
- `<img>` tag pointed to `/stream` endpoint for continuous playback
- Displays camera resolution, frame rate, and encoder type
- Responsive layout for mobile and desktop viewing
- Dark theme for comfortable streaming experience

**Test Coverage** (14 tests)
- Server initialization with defaults and custom parameters
- Port validation (valid range 1-65535)
- Flask availability check (RuntimeError when not installed)
- Route registration (/ and /stream endpoints)
- HTML template rendering with correct parameters
- MJPEG stream endpoint configuration (multipart/x-mixed-replace mimetype)
- Server lifecycle (start, background thread, close)
- Camera integration and cleanup
- Debug mode handling

**Dependencies**
- Flask >= 2.0 in `[web]` optional dependencies
- Installation: `pip install nomon[web]` or `uv add ".[web]"`
- Not required for core camera functionality

**Rationale**
- MJPEG chosen for compatibility and simplicity:
  - Works in any browser without plugins or external libraries
  - No transcoding needed (Camera.get_frame_generator provides frames)
  - Simple multipart/x-mixed-replace HTTP protocol
  - Suitable for LAN verification on local network
- Flask chosen for minimal overhead:
  - Single-purpose streaming server (two endpoints)
  - No complex configuration required
  - Cross-platform (development on Windows/Mac, production on RPi)
  - Optional dependency keeps nomon lightweight for users who don't need streaming

### Phase 2: Remote Microcontroller Operations ✅ COMPLETE

**Communication Protocol Implementation** (`src/nomon/protocol.py`, `src/nomon/server.py`, `src/nomon/client.py`)

**Protocol Design**
- ✅ JSON-based message protocol (newline-delimited)
- ✅ Three message types: CommandMessage, ResponseMessage, NotificationMessage
- ✅ UUID-based request/response matching
- ✅ Cross-platform compatibility (Windows, Linux, macOS)
- ✅ No external network library dependencies (uses stdlib `socket`)

**Server Implementation** (`CommandServer`)
- ✅ TCP server listening on port 5555 (configurable)
- ✅ Supports blocking (`start()`) and background mode (`start_background()`)
- ✅ Command execution: capture_image, start_recording, stop_recording, get_status
- ✅ Status reporting: camera configuration, recording state
- ✅ Error handling with detailed error messages
- ✅ Thread-safe client connection handling
- ✅ Graceful shutdown and resource cleanup

**Client Implementation** (`CameraClient`)
- ✅ High-level API: `capture_image()`, `start_recording()`, `stop_recording()`, `get_status()`
- ✅ Automatic message serialization and parsing
- ✅ Connection management with timeout support
- ✅ Context manager support (`with` statement)
- ✅ Error propagation with readable error messages
- ✅ Windows PC compatibility (fully testable without hardware)

**Message Serialization** (`MessageHandler`)
- ✅ JSON encoding/decoding with validation
- ✅ Message type detection and routing
- ✅ Round-trip serialization (serialize → parse → serialize)
- ✅ Comprehensive error messages for invalid messages

**Test Coverage** (45 tests, 51% overall coverage)
- Protocol Message Tests (27 tests)
  - Command, Response, and Notification message creation
  - Serialization and deserialization
  - Round-trip encoding verification
  - Error handling for malformed JSON/messages
  - Message validation and type checking
- Server Tests (9 tests)
  - Command execution for all supported operations
  - Missing parameter detection
  - Exception handling
  - Status reporting with correct camera info
- Client Tests (9 tests)
  - Connection success and failure
  - Command sending and response parsing
  - Error response propagation
  - Context manager lifecycle
  - Timeout handling
  - All high-level methods (capture, recording, status)

**Testing on Windows PC**
- ✅ All tests run on Windows without Raspberry Pi hardware
- ✅ picamera2 mocked at module import
- ✅ Socket communication mocked for client/server tests
- ✅ Can be extended with real network tests once Pi is online

**Documentation**
- ✅ PHASE2_COMMUNICATION.md - Complete protocol specification
- ✅ Usage examples for client and server
- ✅ Deployment checklist
- ✅ Troubleshooting guide
- ✅ Future enhancement ideas

### Phase 3: HTTP REST API & Authentication (Next)
- HTTP REST wrapper around Phase 2 protocol
- TLS/SSL encryption
- JWT token or API key authentication
- CORS support for web and mobile clients
- Mobile app ready

### Phase 4: HAT Control & Peripherals (Future)
- Identify specific HAT module(s)
- Implement driver/interface layers
- Sensor integration and actuator control

---

## 🚀 Getting Started

### Using the Camera Module
```python
from pathlib import Path
from nomon.camera import Camera

# Initialize with custom directory
camera = Camera(
    width=1280, 
    height=720, 
    fps=30, 
    encoder="h264",
    directory=Path("./videos")
)

# Capture still image (filename only, no paths)
camera.capture_image("photo.jpg")

# Record video
camera.start_recording("video.mp4")
# ... recording ...
camera.stop_recording()

# Stream frames
for frame in camera.get_frame_generator():
    process_frame(frame)

# Context manager for cleanup
with Camera() as cam:
    cam.capture_image("snap.jpg")
    # Automatic cleanup on exit
```

### Using the Web Streaming Server
```python
from nomon.streaming import StreamServer

# Start streaming server
server = StreamServer(
    host="localhost",
    port=8000,
    width=1280,
    height=720,
    fps=30,
    encoder="h264"
)

# Navigate to http://localhost:8000 in your browser
server.start()  # This blocks until server is stopped (Ctrl+C)
```

Or run in background:
```python
from nomon.streaming import StreamServer

server = StreamServer()
thread = server.start_background()

# ... do other work while server runs ...

server.close()  # Clean up when done
```

### Using Remote Camera Control (Phase 2)

**On Raspberry Pi (Server)**
```python
from nomon.server import CommandServer

# Start command server listening for client requests
server = CommandServer(
    host="0.0.0.0",  # Accept connections from any IP
    port=5555,       # Default port
    width=1280,
    height=720,
    fps=30,
    encoder="h264"
)

# Block and listen for client commands
server.start()

# Or run in background
# server.start_background()
# ... other work ...
# server.close()
```

**On Windows PC (Client)**
```python
from nomon import CameraClient

# Connect to the Raspberry Pi server
client = CameraClient("192.168.1.100", port=5555)
client.connect()

# Send commands and get responses
try:
    # Capture an image
    result = client.capture_image("photo.jpg")
    print(f"Captured: {result['filename']}")
    
    # Record a video
    client.start_recording("video.h264")
    # ... recording for a while ...
    client.stop_recording()
    
    # Check camera status
    status = client.get_status()
    print(f"Recording: {status['is_recording']}")
    
except RuntimeError as e:
    print(f"Camera error: {e}")
finally:
    client.close()
```

**Using Context Manager (Recommended)**
```python
from nomon import CameraClient

# Automatic connection and cleanup
with CameraClient("192.168.1.100") as client:
    client.capture_image("snap.jpg")
    client.start_recording("video.h264")
    # ... do other work ...
    client.stop_recording()
    # Automatically closes on exit
```


```bash
# Install with dev dependencies (no web streaming)
uv add . --dev

# Or with pip
pip install -e ".[dev]"
```

### With Web Streaming Support
```bash
# Install with dev and web dependencies
uv add ".[dev,web]"

# Or with pip
pip install -e ".[dev,web]"
```

### Running Tests
```bash
make test           # Run with coverage report
pytest tests/ -v    # Verbose test output
```

### Code Quality
```bash
make format         # Format code with black & ruff
make lint           # Check code style
make type-check     # Type checking
```

### On Raspberry Pi
spidev and picamera2 will automatically install when dependencies are installed on Linux systems.

---

## 📝 Design Principles & Notes

**Keep this codebase minimal.** Let the standard library and imported packages do the heavy lifting. This repo should be focused on **interacting with a microcontroller & peripherals** rather than defining broad patterns for such interactions.

- Cross-platform development: Code works on Windows/Mac for testing, hardware-ready on RPi
- All tool configurations (black, ruff, mypy) are pre-configured in pyproject.toml
- Test infrastructure ready for unit and integration tests
- Security is built-in: filename validation prevents path traversal and directory escape attacks
- Camera module is production-ready and fully tested with 20 test cases
