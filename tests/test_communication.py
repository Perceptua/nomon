"""Tests for server and client communication modules."""

import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock picamera2 before importing nomon modules
mock_picamera2_module = MagicMock()
mock_picamera2_module.Picamera2 = MagicMock()
mock_picamera2_module.H264Encoder = MagicMock()
mock_picamera2_module.MJPEGEncoder = MagicMock()
mock_encoders = MagicMock()
mock_encoders.H264Encoder = MagicMock()
mock_encoders.MJPEGEncoder = MagicMock()
mock_picamera2_module.encoders = mock_encoders
sys.modules["picamera2"] = mock_picamera2_module
sys.modules["picamera2.encoders"] = mock_encoders

from nomon.client import CameraClient
from nomon.protocol import CommandMessage, MessageHandler, ResponseMessage
from nomon.server import CommandServer


class TestCommandServer:
    """Tests for the command server."""

    @patch("nomon.server.Camera")
    def test_server_initialization(self, mock_camera_class):
        """Test server initialization with default parameters."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera

        server = CommandServer()

        assert server.host == "0.0.0.0"
        assert server.port == 5555
        assert server.running is False
        assert server.socket is None
        mock_camera_class.assert_called_once_with(
            camera_index=0,
            width=1280,
            height=720,
            fps=30,
            encoder="h264",
            directory=None,
        )

    @patch("nomon.server.Camera")
    def test_server_initialization_custom_params(self, mock_camera_class):
        """Test server initialization with custom parameters."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera

        with tempfile.TemporaryDirectory() as tmpdir:
            server = CommandServer(
                host="192.168.1.100",
                port=6000,
                camera_index=1,
                width=1920,
                height=1080,
                fps=24,
                encoder="mjpeg",
                directory=tmpdir,
            )

            assert server.host == "192.168.1.100"
            assert server.port == 6000
            mock_camera_class.assert_called_once_with(
                camera_index=1,
                width=1920,
                height=1080,
                fps=24,
                encoder="mjpeg",
                directory=tmpdir,
            )

    @patch("nomon.server.Camera")
    def test_execute_capture_image_command(self, mock_camera_class):
        """Test executing capture_image command."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera
        server = CommandServer()

        command = CommandMessage("capture_image", {"filename": "test.jpg"})
        response = server._execute_command(command)

        assert response.status == "success"
        assert response.data["filename"] == "test.jpg"
        assert "captured" in response.data["message"].lower()
        mock_camera.capture_image.assert_called_once_with("test.jpg")

    @patch("nomon.server.Camera")
    def test_execute_capture_image_missing_filename(self, mock_camera_class):
        """Test capture_image command with missing filename."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera
        server = CommandServer()

        command = CommandMessage("capture_image", {})
        response = server._execute_command(command)

        assert response.status == "error"
        assert "filename" in response.error.lower()

    @patch("nomon.server.Camera")
    def test_execute_start_recording_command(self, mock_camera_class):
        """Test executing start_recording command."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera
        server = CommandServer()

        command = CommandMessage("start_recording", {"filename": "video.h264"})
        response = server._execute_command(command)

        assert response.status == "success"
        assert response.data["filename"] == "video.h264"
        assert "started" in response.data["message"].lower()
        mock_camera.start_recording.assert_called_once_with("video.h264")

    @patch("nomon.server.Camera")
    def test_execute_stop_recording_command(self, mock_camera_class):
        """Test executing stop_recording command."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera
        server = CommandServer()

        command = CommandMessage("stop_recording", {})
        response = server._execute_command(command)

        assert response.status == "success"
        assert "stopped" in response.data["message"].lower()
        mock_camera.stop_recording.assert_called_once()

    @patch("nomon.server.Camera")
    def test_execute_get_status_command(self, mock_camera_class):
        """Test executing get_status command."""
        mock_camera = MagicMock()
        mock_camera.camera_index = 0
        mock_camera.width = 1280
        mock_camera.height = 720
        mock_camera.fps = 30
        mock_camera.encoder = "h264"
        mock_camera._is_recording = False
        mock_camera_class.return_value = mock_camera

        server = CommandServer()
        command = CommandMessage("get_status", {})
        response = server._execute_command(command)

        assert response.status == "success"
        assert response.data["camera_index"] == 0
        assert response.data["width"] == 1280
        assert response.data["height"] == 720
        assert response.data["fps"] == 30
        assert response.data["encoder"] == "h264"
        assert response.data["is_recording"] is False

    @patch("nomon.server.Camera")
    def test_execute_unknown_command(self, mock_camera_class):
        """Test executing unknown command."""
        mock_camera = MagicMock()
        mock_camera_class.return_value = mock_camera
        server = CommandServer()

        command = CommandMessage("unknown_command", {})
        response = server._execute_command(command)

        assert response.status == "error"
        assert "unknown" in response.error.lower()

    @patch("nomon.server.Camera")
    def test_execute_command_with_exception(self, mock_camera_class):
        """Test command execution when camera raises exception."""
        mock_camera = MagicMock()
        mock_camera.capture_image.side_effect = RuntimeError("Camera error")
        mock_camera_class.return_value = mock_camera

        server = CommandServer()
        command = CommandMessage("capture_image", {"filename": "test.jpg"})
        response = server._execute_command(command)

        assert response.status == "error"
        assert "camera error" in response.error.lower()


class TestCameraClient:
    """Tests for the camera client."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = CameraClient("192.168.1.100", port=6000, timeout=5.0)

        assert client.host == "192.168.1.100"
        assert client.port == 6000
        assert client.timeout == 5.0
        assert client.is_connected() is False

    def test_client_default_port(self):
        """Test client initialization with default port."""
        client = CameraClient("localhost")

        assert client.port == 5555

    def test_client_default_timeout(self):
        """Test client initialization with default timeout."""
        client = CameraClient("localhost")

        assert client.timeout == 10.0

    @patch("nomon.client.socket.socket")
    def test_client_connect_success(self, mock_socket_class):
        """Test successful client connection."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()

        assert client.is_connected() is True
        mock_socket.connect.assert_called_once_with(("localhost", 5555))

    @patch("nomon.client.socket.socket")
    def test_client_connect_failure(self, mock_socket_class):
        """Test failed client connection."""
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            client.connect()

        assert client.is_connected() is False

    @patch("nomon.client.socket.socket")
    def test_client_close(self, mock_socket_class):
        """Test closing client connection."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()
        assert client.is_connected() is True

        client.close()
        assert client.is_connected() is False
        mock_socket.close.assert_called_once()

    @patch("nomon.client.socket.socket")
    def test_send_command_not_connected(self, mock_socket_class):
        """Test sending command when not connected."""
        client = CameraClient("localhost")

        with pytest.raises(ConnectionError, match="Not connected"):
            client._send_command("capture_image", {"filename": "test.jpg"})

    @patch("nomon.client.socket.socket")
    def test_send_command_with_success_response(self, mock_socket_class):
        """Test sending command and receiving success response."""
        import json

        mock_socket = MagicMock()
        response_data = {
            "type": "response",
            "id": "msg-123",
            "status": "success",
            "data": {"filename": "test.jpg"},
        }
        mock_socket.recv.return_value = (
            (json.dumps(response_data) + "\n").encode("utf-8")
        )
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()

        result = client._send_command("capture_image", {"filename": "test.jpg"})

        assert result == {"filename": "test.jpg"}
        mock_socket.sendall.assert_called_once()

    @patch("nomon.client.socket.socket")
    def test_send_command_with_error_response(self, mock_socket_class):
        """Test sending command and receiving error response."""
        import json

        mock_socket = MagicMock()
        response_data = {
            "type": "response",
            "id": "msg-123",
            "status": "error",
            "error": "Camera not found",
        }
        mock_socket.recv.return_value = (
            (json.dumps(response_data) + "\n").encode("utf-8")
        )
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()

        with pytest.raises(RuntimeError, match="Server error"):
            client._send_command("capture_image", {"filename": "test.jpg"})

    @patch("nomon.client.socket.socket")
    def test_capture_image_method(self, mock_socket_class):
        """Test capture_image client method."""
        import json

        mock_socket = MagicMock()
        response_data = {
            "type": "response",
            "id": "msg-123",
            "status": "success",
            "data": {"filename": "photo.jpg"},
        }
        mock_socket.recv.return_value = (
            (json.dumps(response_data) + "\n").encode("utf-8")
        )
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()

        result = client.capture_image("photo.jpg")

        assert result == {"filename": "photo.jpg"}

    @patch("nomon.client.socket.socket")
    def test_start_recording_method(self, mock_socket_class):
        """Test start_recording client method."""
        import json

        mock_socket = MagicMock()
        response_data = {
            "type": "response",
            "id": "msg-123",
            "status": "success",
            "data": {"filename": "video.h264"},
        }
        mock_socket.recv.return_value = (
            (json.dumps(response_data) + "\n").encode("utf-8")
        )
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()

        result = client.start_recording("video.h264")

        assert result == {"filename": "video.h264"}

    @patch("nomon.client.socket.socket")
    def test_get_status_method(self, mock_socket_class):
        """Test get_status client method."""
        import json

        mock_socket = MagicMock()
        response_data = {
            "type": "response",
            "id": "msg-123",
            "status": "success",
            "data": {
                "camera_index": 0,
                "width": 1280,
                "height": 720,
                "fps": 30,
                "encoder": "h264",
                "is_recording": False,
            },
        }
        mock_socket.recv.return_value = (
            (json.dumps(response_data) + "\n").encode("utf-8")
        )
        mock_socket_class.return_value = mock_socket

        client = CameraClient("localhost")
        client.connect()

        result = client.get_status()

        assert result["width"] == 1280
        assert result["fps"] == 30
        assert result["is_recording"] is False

    @patch("nomon.client.socket.socket")
    def test_client_context_manager(self, mock_socket_class):
        """Test client as context manager."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        with CameraClient("localhost") as client:
            assert client.is_connected() is True

        assert client.is_connected() is False
        mock_socket.close.assert_called_once()
