"""Package initialization for nomon."""

__version__ = "0.2.0"
__author__ = "Perceptua"

from .camera import Camera
from .client import CameraClient
from .protocol import (
    CommandMessage,
    MessageHandler,
    NotificationMessage,
    ResponseMessage,
)
from .server import CommandServer

try:
    from .streaming import StreamServer
    __all__ = [
        "Camera",
        "StreamServer",
        "CameraClient",
        "CommandServer",
        "CommandMessage",
        "ResponseMessage",
        "NotificationMessage",
        "MessageHandler",
    ]
except ImportError:
    # Flask not installed, streaming not available
    __all__ = [
        "Camera",
        "CameraClient",
        "CommandServer",
        "CommandMessage",
        "ResponseMessage",
        "NotificationMessage",
        "MessageHandler",
    ]


