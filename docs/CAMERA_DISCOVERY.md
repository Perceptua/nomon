# Camera Discovery - Raspberry Pi FPC Camera

Run these snippets on your Raspberry Pi to discover camera capabilities and configuration.

## Check Available Cameras

```python
from picamera2 import Picamera2

# List all available cameras
cameras = Picamera2.global_camera_info()
print("Available cameras:")
for camera_info in cameras:
    print(f"  {camera_info}")

# Initialize camera 0
picam2 = Picamera2(0)
print(f"\nCamera properties: {picam2.camera_properties}")
```

## Discover Camera Sensor Info

```python
from picamera2 import Picamera2

picam2 = Picamera2(0)

# Get sensor properties
properties = picam2.camera_properties
print("Camera Properties:")
for key, value in properties.items():
    print(f"  {key}: {value}")

# Get sensor configuration
sensor_modes = picam2.sensor_modes
print(f"\nAvailable sensor modes ({len(sensor_modes)}):")
for i, mode in enumerate(sensor_modes):
    print(f"  Mode {i}: {mode}")
```

## Discover Resolution & FPS Options

```python
from picamera2 import Picamera2

picam2 = Picamera2(0)

# Check available resolutions
print("Available capture modes:")
for mode in picam2.sensor_modes:
    size = mode['size']
    fps = mode['fps']
    print(f"  {size[0]}x{size[1]} @ {fps} fps")

# Get recommended resolution
config = picam2.create_preview_configuration()
print(f"\nDefault preview config: {config}")
```

## Test Image Capture

```python
from picamera2 import Picamera2

picam2 = Picamera2(0)
picam2.configure(picam2.create_still_configuration())
picam2.start()

# Capture a test image
picam2.capture_file("test.jpg")
print("Test image saved as test.jpg")

picam2.stop()
```

## Check Video Codec Support

```python
from picamera2 import Picamera2

picam2 = Picamera2(0)

# Check available encoders (varies by Raspberry Pi OS version)
print("Creating video configuration...")
video_config = picam2.create_video_configuration()
print(f"Video config: {video_config}")
```

## Questions to Answer

Run the above snippets and provide:

1. **Camera Model**: ov5647 ✅
2. **Sensor Modes**: 4 ✅
3. **Maximum Resolution**: 2592x1944 @ 15.63 fps ✅
4. **Video Codec Support**: What codecs are available? (h264, h265, mjpeg)
5. **Default FPS**: What frame rate is used by default?
6. **Any Errors**: If any of the above fails, what's the error message?

---

## Detailed Guidance for Remaining Info

### 4. Video Codec Support

The valid stream configuration keys are: `format`, `size`, `stride`, `preserve_ar`. The encoder is specified separately, not in the config dict.

Run this to discover available encoders:

```python
from picamera2 import Picamera2, encoders

picam2 = Picamera2(0)

# First, see what the default config looks like
print("=== Default Video Configuration ===")
default_config = picam2.create_video_configuration()
print(default_config)
print()

# Check what encoders are available in the module
print("=== Available Encoders in picamera2 ===")
try:
    from picamera2.encoders import H264Encoder, MJPEGEncoder
    print("  H264Encoder: ✓ Available")
    print("  MJPEGEncoder: ✓ Available")
except ImportError as e:
    print(f"  Import error: {e}")

# Try using the start_recording method with different encoders
print("\n=== Test Recording with Different Encoders ===")

# H264
try:
    from picamera2.encoders import H264Encoder
    config = picam2.create_video_configuration()
    print("  H264Encoder: ✓ Available")
except Exception as e:
    print(f"  H264Encoder: ✗ {type(e).__name__}: {e}")

# MJPEG
try:
    from picamera2.encoders import MJPEGEncoder
    config = picam2.create_video_configuration()
    print("  MJPEGEncoder: ✓ Available")
except Exception as e:
    print(f"  MJPEGEncoder: ✗ {type(e).__name__}: {e}")

# Check picamera2 version
import picamera2
print(f"\npicamera2 version: {picamera2.__version__ if hasattr(picamera2, '__version__') else 'Unknown'}")
```

**What to report**: 
- Which encoders imported successfully (H264Encoder, MJPEGEncoder): Both imported successfully
- Your picamera2 version
- Any import errors

### 5. Default FPS

The FPS varies by resolution. Run this to see what the defaults are:

```python
from picamera2 import Picamera2

picam2 = Picamera2(0)

print("Default FPS for each resolution:")
for i, mode in enumerate(picam2.sensor_modes):
    size = mode['size']
    fps = mode['fps']
    print(f"  Mode {i}: {size[0]:4d}x{size[1]:4d} @ {fps:6.2f} fps")

# Also check what gets used by default for preview
config = picam2.create_preview_configuration()
print(f"\nPreview config: {config}")

# And for video
config = picam2.create_video_configuration()
print(f"\nVideo config: {config}")
```

**What to report**: 
- Default FPS at your maximum resolution (2592x1944): 15.63 fps
- What FPS is used for the preview configuration: Not sure about FPS but size is 640x480. Also FrameDurationLimits is (100, 83333).
- What FPS is used for video recording:  'main': {'format': 'XBGR8888', 'size': (1280, 720), 'preserve_ar': True}

### 6. Any Errors

If you get errors running the above, they'll usually be:

**Common errors:**
- `picamera2.runtime = libcamera` - Library not initialized properly
- `Permission denied` - Running without elevated privileges
- `Operation not permitted` - Camera already in use by another process
- Codec not available - Your Raspberry Pi OS or libcamera version doesn't support it

To fix:
1. Make sure you're running with `sudo`
2. Kill any other processes using the camera: `killall libcamera_still`
3. Check your Raspberry Pi OS version: `cat /etc/os-release`
4. Check libcamera version: `dpkg -l | grep libcamera`

---

## Summary

Once you run the above and get the missing numbers, let me know:
- **Video Codec Support**: The tested codecs imported successfully
- **Default FPS**: See above
- **Any Errors**: No errors
