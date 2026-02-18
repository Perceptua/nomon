"""Phase 2 Communication Protocol Documentation

## Overview

Phase 2 implements a complete TCP-based communication protocol for remote camera
control between a Raspberry Pi (server) and a Windows PC (client).

## Architecture

### Communication Flow

```
Windows PC (Client)                Raspberry Pi (Server)
    |                                   |
    |-- CommandMessage (JSON) -------> |
    |                                   | execute_command()
    |                                   | uses Camera API
    |                              <- ResponseMessage (JSON) --|
    |
    | (Repeat for each command)
```

### Protocol Design

- **Transport**: TCP/IP (newline-delimited JSON)
- **Serialization**: JSON with standardized message types
- **Message IDs**: UUID for request/response matching
- **Error Handling**: Explicit error status and messages

## Message Types

### 1. CommandMessage (Client → Server)

Request to execute a camera operation.

```json
{
    "type": "command",
    "id": "uuid-string",
    "command": "capture_image|start_recording|stop_recording|get_status",
    "params": {
        "filename": "photo.jpg"
    }
}
```

### 2. ResponseMessage (Server → Client)

Response with result or error.

```json
{
    "type": "response",
    "id": "matching-request-uuid",
    "status": "success|error",
    "data": {
        "filename": "photo.jpg",
        "message": "Image captured"
    },
    "error": null
}
```

Error response:
```json
{
    "type": "response",
    "id": "matching-request-uuid",
    "status": "error",
    "data": {},
    "error": "Invalid filename"
}
```

### 3. NotificationMessage (Server → Client)

Unsolicited event from server (reserved for future use).

```json
{
    "type": "notification",
    "id": "uuid-string",
    "event": "recording_started|recording_stopped|...",
    "data": {
        "filename": "video.h264"
    }
}
```

## Supported Commands

| Command | Parameters | Response Data | Usage |
|---------|-----------|---------------|-------|
| `capture_image` | `filename: str` | `filename, message` | Capture still image |
| `start_recording` | `filename: str` | `filename, message` | Begin recording video |
| `stop_recording` | (none) | `message` | Stop current recording |
| `get_status` | (none) | Camera settings, recording status | Query camera state |

## Implementation

### Core Modules

#### protocol.py
- `CommandMessage`: Request messages
- `ResponseMessage`: Response messages
- `NotificationMessage`: Event notification messages
- `MessageHandler`: JSON serialization/deserialization

#### server.py
- `CommandServer`: TCP server listening on port 5555
- Handles client connections
- Executes camera commands
- Sends replies with results or errors

#### client.py
- `CameraClient`: TCP client for connecting to remote server
- High-level methods: `capture_image()`, `start_recording()`, `stop_recording()`, `get_status()`
- Automatic message serialization and parsing
- Context manager support (`with` statement)

## Usage Examples

### Basic Usage (Windows Client)

```python
from nomon import CameraClient

# Connect to the Pi
client = CameraClient("192.168.1.100", port=5555)
client.connect()

# Capture an image
try:
    result = client.capture_image("photo.jpg")
    print(f"Image saved: {result['filename']}")
except RuntimeError as e:
    print(f"Error: {e}")

client.close()
```

### Context Manager (Windows Client)

```python
from nomon import CameraClient

# Automatically handles connect/disconnect
with CameraClient("192.168.1.100") as client:
    client.capture_image("photo.jpg")
    
    # Start recording
    client.start_recording("video.h264")
    
    # ... do other things ...
    
    # Stop recording
    client.stop_recording()
    
    # Check status
    status = client.get_status()
    print(f"Recording: {status['is_recording']}")
```

### Server Setup (Raspberry Pi)

```python
from nomon import CommandServer

# Create server with camera defaults
server = CommandServer(
    host="0.0.0.0",  # Listen on all interfaces
    port=5555,
    camera_index=0,
    width=1280,
    height=720,
    fps=30,
    encoder="h264"
)

# Start server (blocking)
server.start()

# Or run in background
# server.start_background()
```

## Testing

The implementation includes comprehensive tests:

### Protocol Tests (`test_protocol.py`)
- Message creation and validation
- Serialization/deserialization
- Round-trip encoding (serialize → deserialize → serialize)
- Error handling for malformed messages

### Communication Tests (`test_communication.py`)
- Server command execution
- Client connection and communication
- Error handling (server errors, network issues)
- Context manager cleanup

### Running Tests

```bash
# All protocol/communication tests
python -m pytest tests/test_protocol.py tests/test_communication.py -v

# With coverage report
python -m pytest tests/test_protocol.py tests/test_communication.py \
    --cov=nomon --cov-report=html

# Specific test class
python -m pytest tests/test_communication.py::TestCameraClient -v
```

## Test Coverage

- **protocol.py**: 96% - All message types and serialization
- **client.py**: 88% - Connection, commands, error handling
- **server.py**: 44% - Command execution (listener loop mocked)

## Future Enhancements

### Phase 3 Ideas
- Authentication token support
- Compression for large image transfers
- Binary protocol option for performance
- Live frame streaming over protocol
- Command queuing for batch operations
- Server-side notifications (recording finished, etc.)
- Rate limiting and bandwidth control
- Persistent logging of commands executed

### Network Considerations
- Works over WiFi and Ethernet
- Tailscale support for remote connections
- Default localhost binding (change host to enable remote access)
- SSL/TLS encryption (future phase)

## Cross-Platform Support

### Tested On
- Windows 10/11 (Client)
- Python 3.8+ (both client and server)

### Requirements
- No external network libraries (uses stdlib `socket`)
- No platform-specific code
- Compatible with Raspberry Pi OS (tested path)

## Security Notes

Current implementation (Phase 2):
- No authentication
- No encryption
- Localhost binding by default (must explicitly receive remote connections)

Recommendations for production:
- Run on trusted networks only
- Use Tailscale or other VPN for remote access
- Implement token-based authentication in Phase 3
- Add TLS encryption layer

## Troubleshooting

### Connection Refused
```python
# Ensure server is running on the Pi
# Check that port 5555 is not blocked by firewall
# Verify IP address is correct
```

### Timeout Errors
```python
# Increase client timeout if server is slow
client = CameraClient("192.168.1.100", timeout=30.0)
```

### Camera Not Ready
```python
# Check that camera is available on Pi
# Run get_status() to diagnose camera state
status = client.get_status()
print(status)
```

## Deployment Checklist

For Raspberry Pi deployment:
- [ ] Install nomon package with dependencies
- [ ] Create startup script for CommandServer
- [ ] Configure static IP for Pi (for consistent client connections)
- [ ] Test local Windows to Pi communication
- [ ] Set up systemd service to auto-start server (optional)
- [ ] Configure firewall if needed
- [ ] Document the Pi's IP address for client setup
"""
