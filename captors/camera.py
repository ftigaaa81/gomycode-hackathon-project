"""Camera abstraction for Raspberry Pi capture (hardware isolated for testing)."""

from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import CaptorSettings

logger = logging.getLogger(__name__)


class Camera(ABC):
    """Interface for JPEG frame capture."""

    @abstractmethod
    def start(self) -> None:
        """Initialize camera hardware or mock resources."""

    @abstractmethod
    def stop(self) -> None:
        """Release camera resources."""

    @abstractmethod
    def capture_jpeg(self) -> bytes:
        """Return one JPEG-encoded frame."""


class MockCamera(Camera):
    """Synthetic camera for development without a Raspberry Pi attached."""

    def __init__(self, width: int, height: int, jpeg_quality: int) -> None:
        self._width = width
        self._height = height
        self._jpeg_quality = jpeg_quality
        self._frame_index = 0

    def start(self) -> None:
        logger.info(
            "mock_camera_started",
            extra={"width": self._width, "height": self._height},
        )

    def stop(self) -> None:
        logger.info("mock_camera_stopped")

    def capture_jpeg(self) -> bytes:
        """Return a valid JPEG buffer generated in software."""
        from PIL import Image

        self._frame_index += 1
        color = (self._frame_index % 256, 64, 128)
        image = Image.new("RGB", (self._width, self._height), color=color)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self._jpeg_quality)
        return buffer.getvalue()


class Picamera2Camera(Camera):
    """Raspberry Pi camera using picamera2."""

    def __init__(self, width: int, height: int, jpeg_quality: int) -> None:
        self._width = width
        self._height = height
        self._jpeg_quality = jpeg_quality
        self._picam2 = None

    def start(self) -> None:
        try:
            from picamera2 import Picamera2
        except ImportError as exc:
            raise RuntimeError(
                "picamera2 is not installed. Install Raspberry Pi OS camera stack "
                "or set USE_MOCK_CAMERA=true."
            ) from exc

        self._picam2 = Picamera2()
        config = self._picam2.create_still_configuration(
            main={"size": (self._width, self._height), "format": "RGB888"},
        )
        self._picam2.configure(config)
        self._picam2.start()
        logger.info(
            "picamera2_started",
            extra={"width": self._width, "height": self._height},
        )

    def stop(self) -> None:
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2.close()
            self._picam2 = None
        logger.info("picamera2_stopped")

    def capture_jpeg(self) -> bytes:
        """Capture one still and encode as JPEG."""
        if self._picam2 is None:
            raise RuntimeError("Camera not started")

        from PIL import Image

        array = self._picam2.capture_array("main")
        image = Image.fromarray(array)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self._jpeg_quality)
        frame = buffer.getvalue()
        if len(frame) < 512:
            raise RuntimeError("Captured JPEG frame too small")
        return frame


def create_camera(settings: CaptorSettings) -> Camera:
    """Factory: picamera2 on Pi, mock when requested or import fails."""
    if settings.use_mock_camera:
        return MockCamera(
            settings.camera_width,
            settings.camera_height,
            settings.jpeg_quality,
        )

    try:
        import picamera2  # noqa: F401
    except ImportError:
        logger.warning("picamera2_unavailable_using_mock")
        return MockCamera(
            settings.camera_width,
            settings.camera_height,
            settings.jpeg_quality,
        )

    return Picamera2Camera(
        settings.camera_width,
        settings.camera_height,
        settings.jpeg_quality,
    )
