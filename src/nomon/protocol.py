"""Communication protocol for nomon camera control.

This module defines the message types and serialization protocol
for communicating between a remote Raspberry Pi device and a local
client (e.g., Windows PC). Uses JSON over TCP for simplicity and
cross-platform compatibility.

Message Format
--------------
All messages are JSON objects sent as single lines (newline-delimited).
Each message includes a unique transaction ID for matching requests/responses.

Command Message:
{
    "type": "command",
    "id": "<uuid>",
    "command": "capture_image|start_recording|stop_recording|...",
    "params": {...}  // command-specific parameters
}

Response Message:
{
    "type": "response",
    "id": "<uuid>",  // matches request id
    "status": "success|error",
    "data": {...},  // command-specific response data
    "error": "error message if status is error"
}

Notification Message:
{
    "type": "notification",
    "id": "<uuid>",
    "event": "recording_started|recording_stopped|...",
    "data": {...}  // event-specific data
}

Classes
-------
Message
    Base class for all message types.
CommandMessage
    Request to perform an action.
ResponseMessage
    Response to a command with result or error.
NotificationMessage
    Unsolicited notification from server.
MessageHandler
    Serializer/deserializer for protocol messages.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Message:
    """Base message class."""

    type: str
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class CommandMessage(Message):
    """Request message to execute a command."""

    type: str = "command"
    command: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        command: str,
        params: Optional[dict[str, Any]] = None,
        msg_id: Optional[str] = None,
    ) -> None:
        """Initialize command message.

        Parameters
        ----------
        command : str
            Command name (e.g., 'capture_image', 'start_recording')
        params : dict, optional
            Command parameters (default: {})
        msg_id : str, optional
            Message ID (default: generated UUID)
        """
        super().__init__(
            type="command",
            msg_id=msg_id or str(uuid.uuid4()),
        )
        self.command = command
        self.params = params or {}


@dataclass
class ResponseMessage(Message):
    """Response message with result or error."""

    type: str = "response"
    status: str = "success"  # 'success' or 'error'
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __init__(
        self,
        msg_id: str,
        status: str = "success",
        data: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Initialize response message.

        Parameters
        ----------
        msg_id : str
            Message ID matching the request
        status : str, optional
            'success' or 'error' (default: 'success')
        data : dict, optional
            Response data (default: {})
        error : str, optional
            Error message if status is 'error'
        """
        super().__init__(type="response", msg_id=msg_id)
        self.status = status
        self.data = data or {}
        self.error = error


@dataclass
class NotificationMessage(Message):
    """Unsolicited notification from server."""

    type: str = "notification"
    event: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        event: str,
        data: Optional[dict[str, Any]] = None,
        msg_id: Optional[str] = None,
    ) -> None:
        """Initialize notification message.

        Parameters
        ----------
        event : str
            Event name (e.g., 'recording_started')
        data : dict, optional
            Event-specific data (default: {})
        msg_id : str, optional
            Message ID (default: generated UUID)
        """
        super().__init__(
            type="notification",
            msg_id=msg_id or str(uuid.uuid4()),
        )
        self.event = event
        self.data = data or {}


class MessageHandler:
    """Serialize and deserialize protocol messages."""

    @staticmethod
    def parse_message(json_str: str) -> Message:
        """Parse JSON string into appropriate Message type.

        Parameters
        ----------
        json_str : str
            JSON message string

        Returns
        -------
        Message
            CommandMessage, ResponseMessage, or NotificationMessage

        Raises
        ------
        ValueError
            If message format is invalid
        json.JSONDecodeError
            If JSON is malformed
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in message: {e}") from e

        msg_type = data.get("type")
        msg_id = data.get("id")

        if not msg_type or not msg_id:
            raise ValueError("Message must have 'type' and 'id' fields")

        if msg_type == "command":
            command = data.get("command")
            params = data.get("params", {})
            if not isinstance(command, str):
                raise ValueError("Command message must have 'command' field")
            return CommandMessage(
                command=command,
                params=params,
                msg_id=msg_id,
            )

        elif msg_type == "response":
            status = data.get("status", "success")
            response_data = data.get("data", {})
            error = data.get("error")
            if status not in ("success", "error"):
                raise ValueError(f"Invalid status: {status}")
            return ResponseMessage(
                msg_id=msg_id,
                status=status,
                data=response_data,
                error=error,
            )

        elif msg_type == "notification":
            event = data.get("event")
            notif_data = data.get("data", {})
            if not isinstance(event, str):
                raise ValueError("Notification must have 'event' field")
            return NotificationMessage(
                event=event,
                data=notif_data,
                msg_id=msg_id,
            )

        else:
            raise ValueError(f"Unknown message type: {msg_type}")

    @staticmethod
    def serialize(message: Message) -> str:
        """Serialize a message to JSON string.

        Parameters
        ----------
        message : Message
            Message object to serialize

        Returns
        -------
        str
            JSON string (newline-delimited for line-based transmission)
        """
        if isinstance(message, CommandMessage):
            return json.dumps(
                {
                    "type": "command",
                    "id": message.msg_id,
                    "command": message.command,
                    "params": message.params,
                }
            )
        elif isinstance(message, ResponseMessage):
            data = {
                "type": "response",
                "id": message.msg_id,
                "status": message.status,
                "data": message.data,
            }
            if message.error:
                data["error"] = message.error
            return json.dumps(data)
        elif isinstance(message, NotificationMessage):
            return json.dumps(
                {
                    "type": "notification",
                    "id": message.msg_id,
                    "event": message.event,
                    "data": message.data,
                }
            )
        else:
            raise TypeError(f"Unknown message type: {type(message)}")


# Supported commands
SUPPORTED_COMMANDS = {
    "capture_image": {
        "description": "Capture a still image",
        "params": {"filename": str},
    },
    "start_recording": {
        "description": "Start video recording",
        "params": {"filename": str},
    },
    "stop_recording": {
        "description": "Stop video recording",
        "params": {},
    },
    "get_status": {
        "description": "Get camera and server status",
        "params": {},
    },
}
