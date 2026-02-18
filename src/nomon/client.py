"""Client for remote camera control via TCP.

This module provides a client for sending camera commands to a
remote CommandServer (typically on a Raspberry Pi) and receiving
responses.

Designed to be run on client machines (Windows, macOS, Linux)
to control a Raspberry Pi camera remotely.

Classes
-------
CameraClient
    TCP client for remote camera control.
"""

import logging
import socket
import time
from typing import Optional

from .protocol import CommandMessage, MessageHandler, ResponseMessage

logger = logging.getLogger(__name__)


class CameraClient:
    """TCP client for remote camera control.

    Sends camera commands to a remote CommandServer and waits
    for responses.

    Parameters
    ----------
    host : str
        Server host address
    port : int, optional
        Server port (default: 5555)
    timeout : float, optional
        Connection timeout in seconds (default: 10.0)
    """

    def __init__(
        self,
        host: str,
        port: int = 5555,
        timeout: float = 10.0,
    ) -> None:
        """Initialize the camera client."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self._connected = False

    def connect(self) -> None:
        """Connect to the server.

        Raises
        ------
        ConnectionError
            If unable to connect to server
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self._connected = True
            logger.info(f"Connected to {self.host}:{self.port}")
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._connected = False
            raise ConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {e}"
            ) from e

    def close(self) -> None:
        """Disconnect from the server."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        self._connected = False
        logger.info("Disconnected from server")

    def is_connected(self) -> bool:
        """Check if client is connected to server.

        Returns
        -------
        bool
            True if connected, False otherwise
        """
        return self._connected

    def capture_image(self, filename: str) -> dict:
        """Capture an image on the remote camera.

        Parameters
        ----------
        filename : str
            Filename to save the image as (e.g., 'photo.jpg')

        Returns
        -------
        dict
            Response data from server

        Raises
        ------
        ConnectionError
            If not connected to server
        RuntimeError
            If server returns error response
        """
        response = self._send_command(
            "capture_image",
            {"filename": filename},
        )
        return response

    def start_recording(self, filename: str) -> dict:
        """Start recording video on the remote camera.

        Parameters
        ----------
        filename : str
            Filename to save the video as (e.g., 'video.h264')

        Returns
        -------
        dict
            Response data from server

        Raises
        ------
        ConnectionError
            If not connected to server
        RuntimeError
            If server returns error response
        """
        response = self._send_command(
            "start_recording",
            {"filename": filename},
        )
        return response

    def stop_recording(self) -> dict:
        """Stop recording video on the remote camera.

        Returns
        -------
        dict
            Response data from server

        Raises
        ------
        ConnectionError
            If not connected to server
        RuntimeError
            If server returns error response
        """
        response = self._send_command("stop_recording")
        return response

    def get_status(self) -> dict:
        """Get status of the remote camera.

        Returns
        -------
        dict
            Status data from server with keys:
            - camera_index: int
            - width: int
            - height: int
            - fps: int
            - encoder: str
            - is_recording: bool

        Raises
        ------
        ConnectionError
            If not connected to server
        RuntimeError
            If server returns error response
        """
        response = self._send_command("get_status")
        return response

    def _send_command(
        self,
        command: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Send a command to the server and wait for response.

        Parameters
        ----------
        command : str
            Command name
        params : dict, optional
            Command parameters

        Returns
        -------
        dict
            Response data

        Raises
        ------
        ConnectionError
            If not connected to server
        RuntimeError
            If server returns error response
        """
        if not self._connected:
            raise ConnectionError("Not connected to server")

        if not self.socket:
            raise ConnectionError("Socket not initialized")

        try:
            # Create and send command
            command_msg = CommandMessage(command, params or {})
            command_json = MessageHandler.serialize(command_msg)
            self.socket.sendall((command_json + "\n").encode("utf-8"))

            # Wait for response
            response_data = self.socket.recv(4096).decode("utf-8").strip()
            if not response_data:
                raise RuntimeError("Server closed connection")

            response_msg = MessageHandler.parse_message(response_data)

            if not isinstance(response_msg, ResponseMessage):
                raise RuntimeError(
                    f"Expected ResponseMessage, got {type(response_msg)}"
                )

            # Check for errors
            if response_msg.status == "error":
                raise RuntimeError(f"Server error: {response_msg.error}")

            return response_msg.data

        except socket.timeout:
            self._connected = False
            raise ConnectionError("Server response timeout") from None
        except Exception as e:
            self._connected = False
            raise

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
