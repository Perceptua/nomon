"""Command server for Raspberry Pi camera control.

This module provides a TCP server that listens for commands from
remote clients and executes them on the Raspberry Pi camera.

The server handles:
- Command execution (capture, record, etc.)
- Response serialization
- Error handling and status reporting
- Clean client disconnection
- Multiple client handling (one at a time)

Classes
-------
CommandServer
    TCP server for receiving and executing camera commands.
"""

import json
import logging
import socket
import threading
from pathlib import Path
from typing import Optional

from .camera import Camera
from .protocol import (
    CommandMessage,
    MessageHandler,
    NotificationMessage,
    ResponseMessage,
    SUPPORTED_COMMANDS,
)

logger = logging.getLogger(__name__)


class CommandServer:
    """TCP server for remote camera control.

    Listens for camera commands from clients and executes them,
    returning results or errors.

    Parameters
    ----------
    host : str, optional
        Host to bind to (default: '0.0.0.0')
    port : int, optional
        Port to listen on (default: 5555)
    camera_index : int, optional
        Camera index to use (default: 0)
    width : int, optional
        Camera width in pixels (default: 1280)
    height : int, optional
        Camera height in pixels (default: 720)
    fps : int, optional
        Frames per second (default: 30)
    encoder : str, optional
        Video encoder: 'h264' or 'mjpeg' (default: 'h264')
    directory : str or Path, optional
        Directory for saving media files (default: None)
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5555,
        camera_index: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        encoder: str = "h264",
        directory: Optional[str | Path] = None,
    ) -> None:
        """Initialize the command server."""
        self.host = host
        self.port = port
        self.camera = Camera(
            camera_index=camera_index,
            width=width,
            height=height,
            fps=fps,
            encoder=encoder,
            directory=directory,
        )
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.server_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the server (blocking).

        Listens for client connections and processes commands
        until interrupted.
        """
        self._setup_socket()
        try:
            logger.info(f"Starting server on {self.host}:{self.port}")
            self.running = True
            while self.running:
                self._accept_client()
        except KeyboardInterrupt:
            logger.info("Server interrupted")
        finally:
            self.close()

    def start_background(self) -> None:
        """Start the server in a background thread (non-blocking)."""
        self.server_thread = threading.Thread(
            target=self.start,
            daemon=True,
            name="CommandServerThread",
        )
        self.server_thread.start()
        logger.info("Server started in background thread")

    def close(self) -> None:
        """Shut down the server and clean up resources."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        self.camera.close()
        logger.info("Server closed")

    def _setup_socket(self) -> None:
        """Create and bind the server socket."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        logger.debug(f"Socket bound to {self.host}:{self.port}")

    def _accept_client(self) -> None:
        """Accept and handle a client connection."""
        if not self.socket:
            logger.error("Socket not initialized")
            return

        try:
            client_socket, client_address = self.socket.accept()
            logger.info(f"Client connected: {client_address}")
            self._handle_client(client_socket, client_address)
        except OSError as e:
            if self.running:
                logger.error(f"Error accepting client: {e}")

    def _handle_client(
        self, client_socket: socket.socket, client_address: tuple
    ) -> None:
        """Handle a single client connection.

        Reads commands, executes them, and sends responses.

        Parameters
        ----------
        client_socket : socket.socket
            Connected client socket
        client_address : tuple
            Client address (host, port)
        """
        try:
            while self.running:
                data = client_socket.recv(4096).decode("utf-8")
                if not data:
                    break

                for line in data.strip().split("\n"):
                    if not line:
                        continue

                    try:
                        message = MessageHandler.parse_message(line)

                        if isinstance(message, CommandMessage):
                            response = self._execute_command(message)
                            response_json = MessageHandler.serialize(response)
                            client_socket.sendall(
                                (response_json + "\n").encode("utf-8")
                            )
                    except ValueError as e:
                        logger.error(f"Invalid message: {e}")
                        error_response = ResponseMessage(
                            msg_id="unknown",
                            status="error",
                            error=str(e),
                        )
                        response_json = MessageHandler.serialize(error_response)
                        client_socket.sendall(
                            (response_json + "\n").encode("utf-8")
                        )

        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()
            logger.info(f"Client disconnected: {client_address}")

    def _execute_command(self, message: CommandMessage) -> ResponseMessage:
        """Execute a command and return response.

        Parameters
        ----------
        message : CommandMessage
            Command to execute

        Returns
        -------
        ResponseMessage
            Result of command execution
        """
        command = message.command
        params = message.params

        try:
            if command == "capture_image":
                filename = params.get("filename")
                if not filename:
                    return ResponseMessage(
                        msg_id=message.msg_id,
                        status="error",
                        error="Missing 'filename' parameter",
                    )
                self.camera.capture_image(filename)
                return ResponseMessage(
                    msg_id=message.msg_id,
                    status="success",
                    data={"filename": filename, "message": "Image captured"},
                )

            elif command == "start_recording":
                filename = params.get("filename")
                if not filename:
                    return ResponseMessage(
                        msg_id=message.msg_id,
                        status="error",
                        error="Missing 'filename' parameter",
                    )
                self.camera.start_recording(filename)
                return ResponseMessage(
                    msg_id=message.msg_id,
                    status="success",
                    data={"filename": filename, "message": "Recording started"},
                )

            elif command == "stop_recording":
                self.camera.stop_recording()
                return ResponseMessage(
                    msg_id=message.msg_id,
                    status="success",
                    data={"message": "Recording stopped"},
                )

            elif command == "get_status":
                return ResponseMessage(
                    msg_id=message.msg_id,
                    status="success",
                    data={
                        "camera_index": self.camera.camera_index,
                        "width": self.camera.width,
                        "height": self.camera.height,
                        "fps": self.camera.fps,
                        "encoder": self.camera.encoder,
                        "is_recording": self.camera._is_recording,
                    },
                )

            else:
                return ResponseMessage(
                    msg_id=message.msg_id,
                    status="error",
                    error=f"Unknown command: {command}",
                )

        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            return ResponseMessage(
                msg_id=message.msg_id,
                status="error",
                error=str(e),
            )
