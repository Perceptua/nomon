"""Tests for communication protocol and client/server modules."""

import json
import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

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

from nomon.protocol import (
    CommandMessage,
    MessageHandler,
    NotificationMessage,
    ResponseMessage,
)


class TestProtocolMessages:
    """Tests for protocol message creation and serialization."""

    def test_command_message_creation(self):
        """Test creating a command message."""
        msg = CommandMessage("capture_image", {"filename": "test.jpg"})
        assert msg.type == "command"
        assert msg.command == "capture_image"
        assert msg.params == {"filename": "test.jpg"}
        assert msg.msg_id != ""

    def test_command_message_custom_id(self):
        """Test command message with custom ID."""
        msg = CommandMessage(
            "capture_image",
            {"filename": "test.jpg"},
            msg_id="custom-id-123",
        )
        assert msg.msg_id == "custom-id-123"

    def test_response_message_success(self):
        """Test creating a successful response message."""
        msg = ResponseMessage(
            msg_id="req-123",
            status="success",
            data={"filename": "test.jpg"},
        )
        assert msg.type == "response"
        assert msg.msg_id == "req-123"
        assert msg.status == "success"
        assert msg.data == {"filename": "test.jpg"}
        assert msg.error is None

    def test_response_message_error(self):
        """Test creating an error response message."""
        msg = ResponseMessage(
            msg_id="req-123",
            status="error",
            error="Invalid filename",
        )
        assert msg.status == "error"
        assert msg.error == "Invalid filename"
        assert msg.data == {}

    def test_notification_message_creation(self):
        """Test creating a notification message."""
        msg = NotificationMessage(
            "recording_started",
            {"filename": "video.h264"},
        )
        assert msg.type == "notification"
        assert msg.event == "recording_started"
        assert msg.data == {"filename": "video.h264"}


class TestMessageHandler:
    """Tests for message serialization and deserialization."""

    def test_serialize_command_message(self):
        """Test serializing a command message."""
        msg = CommandMessage(
            "capture_image",
            {"filename": "test.jpg"},
            msg_id="test-123",
        )
        json_str = MessageHandler.serialize(msg)
        data = json.loads(json_str)

        assert data["type"] == "command"
        assert data["id"] == "test-123"
        assert data["command"] == "capture_image"
        assert data["params"] == {"filename": "test.jpg"}

    def test_serialize_response_message(self):
        """Test serializing a response message."""
        msg = ResponseMessage(
            msg_id="test-123",
            status="success",
            data={"result": "ok"},
        )
        json_str = MessageHandler.serialize(msg)
        data = json.loads(json_str)

        assert data["type"] == "response"
        assert data["id"] == "test-123"
        assert data["status"] == "success"
        assert data["data"] == {"result": "ok"}
        assert "error" not in data

    def test_serialize_response_message_with_error(self):
        """Test serializing error response message."""
        msg = ResponseMessage(
            msg_id="test-123",
            status="error",
            error="Camera not ready",
        )
        json_str = MessageHandler.serialize(msg)
        data = json.loads(json_str)

        assert data["type"] == "response"
        assert data["status"] == "error"
        assert data["error"] == "Camera not ready"

    def test_serialize_notification_message(self):
        """Test serializing a notification message."""
        msg = NotificationMessage(
            "recording_started",
            {"filename": "video.h264"},
            msg_id="notif-123",
        )
        json_str = MessageHandler.serialize(msg)
        data = json.loads(json_str)

        assert data["type"] == "notification"
        assert data["id"] == "notif-123"
        assert data["event"] == "recording_started"
        assert data["data"] == {"filename": "video.h264"}

    def test_parse_command_message(self):
        """Test parsing a command message."""
        json_str = json.dumps(
            {
                "type": "command",
                "id": "test-123",
                "command": "capture_image",
                "params": {"filename": "test.jpg"},
            }
        )
        msg = MessageHandler.parse_message(json_str)

        assert isinstance(msg, CommandMessage)
        assert msg.command == "capture_image"
        assert msg.params == {"filename": "test.jpg"}
        assert msg.msg_id == "test-123"

    def test_parse_response_message(self):
        """Test parsing a response message."""
        json_str = json.dumps(
            {
                "type": "response",
                "id": "test-123",
                "status": "success",
                "data": {"result": "ok"},
            }
        )
        msg = MessageHandler.parse_message(json_str)

        assert isinstance(msg, ResponseMessage)
        assert msg.status == "success"
        assert msg.data == {"result": "ok"}
        assert msg.error is None

    def test_parse_response_message_with_error(self):
        """Test parsing error response message."""
        json_str = json.dumps(
            {
                "type": "response",
                "id": "test-123",
                "status": "error",
                "error": "Camera not found",
            }
        )
        msg = MessageHandler.parse_message(json_str)

        assert isinstance(msg, ResponseMessage)
        assert msg.status == "error"
        assert msg.error == "Camera not found"

    def test_parse_notification_message(self):
        """Test parsing a notification message."""
        json_str = json.dumps(
            {
                "type": "notification",
                "id": "test-123",
                "event": "recording_started",
                "data": {"filename": "video.h264"},
            }
        )
        msg = MessageHandler.parse_message(json_str)

        assert isinstance(msg, NotificationMessage)
        assert msg.event == "recording_started"
        assert msg.data == {"filename": "video.h264"}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON string."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            MessageHandler.parse_message("{invalid json")

    def test_parse_missing_type(self):
        """Test parsing message without type field."""
        with pytest.raises(ValueError, match="must have 'type' and 'id'"):
            MessageHandler.parse_message(json.dumps({"id": "test"}))

    def test_parse_missing_id(self):
        """Test parsing message without id field."""
        with pytest.raises(ValueError, match="must have 'type' and 'id'"):
            MessageHandler.parse_message(json.dumps({"type": "command"}))

    def test_parse_command_missing_command_field(self):
        """Test parsing command message without command field."""
        with pytest.raises(ValueError, match="must have 'command'"):
            MessageHandler.parse_message(
                json.dumps({"type": "command", "id": "test"})
            )

    def test_parse_notification_missing_event_field(self):
        """Test parsing notification without event field."""
        with pytest.raises(ValueError, match="must have 'event'"):
            MessageHandler.parse_message(
                json.dumps({"type": "notification", "id": "test"})
            )

    def test_parse_invalid_response_status(self):
        """Test parsing response with invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            MessageHandler.parse_message(
                json.dumps(
                    {
                        "type": "response",
                        "id": "test",
                        "status": "invalid",
                    }
                )
            )

    def test_parse_unknown_message_type(self):
        """Test parsing unknown message type."""
        with pytest.raises(ValueError, match="Unknown message type"):
            MessageHandler.parse_message(
                json.dumps({"type": "unknown", "id": "test"})
            )

    def test_roundtrip_command_message(self):
        """Test serializing and deserializing command message."""
        original = CommandMessage(
            "start_recording",
            {"filename": "video.h264"},
            msg_id="roundtrip-123",
        )
        json_str = MessageHandler.serialize(original)
        restored = MessageHandler.parse_message(json_str)

        assert isinstance(restored, CommandMessage)
        assert restored.command == original.command
        assert restored.params == original.params
        assert restored.msg_id == original.msg_id

    def test_roundtrip_response_message(self):
        """Test serializing and deserializing response message."""
        original = ResponseMessage(
            msg_id="roundtrip-123",
            status="success",
            data={"result": "ok", "duration": 42},
        )
        json_str = MessageHandler.serialize(original)
        restored = MessageHandler.parse_message(json_str)

        assert isinstance(restored, ResponseMessage)
        assert restored.status == original.status
        assert restored.data == original.data
        assert restored.msg_id == original.msg_id

    def test_roundtrip_notification_message(self):
        """Test serializing and deserializing notification message."""
        original = NotificationMessage(
            "recording_stopped",
            {"filename": "video.h264", "duration": 123},
            msg_id="notif-roundtrip-123",
        )
        json_str = MessageHandler.serialize(original)
        restored = MessageHandler.parse_message(json_str)

        assert isinstance(restored, NotificationMessage)
        assert restored.event == original.event
        assert restored.data == original.data
        assert restored.msg_id == original.msg_id
