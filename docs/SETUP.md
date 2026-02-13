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

### Phase 2: Remote Microcontroller Operations (Next)
- Communication protocol design (HTTP, WebSocket, MQTT, etc.)
- Secure credential management
- Error handling for network reliability

### Phase 3: HAT Control & Peripherals (Future)
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

### Development Environment
```bash
# Install with dev dependencies
make install-dev

# Or with pip directly
pip install -e ".[dev]"
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
