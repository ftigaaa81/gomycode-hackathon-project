"""EyE C captor main loop: capture a frame every 3.5s and upload to the backend."""

from __future__ import annotations

import logging
import signal
import sys
import time

from camera import create_camera
from config import get_settings
from uploader import FrameUploader

CAPTURE_INTERVAL_SECONDS = 3.5

logger = logging.getLogger(__name__)
_running = True


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _handle_shutdown(signum: int, _frame: object) -> None:
    global _running
    logger.info("shutdown_signal_received", extra={"signal": signum})
    _running = False


def run_loop() -> int:
    """Run capture/upload loop until interrupted."""
    settings = get_settings()
    camera = create_camera(settings)
    uploader = FrameUploader(settings)

    camera.start()
    logger.info(
        "captor_loop_started",
        extra={
            "captor_id": settings.captor_id,
            "interval_s": CAPTURE_INTERVAL_SECONDS,
            "backend": str(settings.backend_url),
        },
    )

    try:
        while _running:
            cycle_start = time.monotonic()
            try:
                frame = camera.capture_jpeg()
                uploader.upload_frame(frame)
            except Exception:
                logger.exception("capture_or_upload_cycle_failed")

            elapsed = time.monotonic() - cycle_start
            sleep_for = max(0.0, CAPTURE_INTERVAL_SECONDS - elapsed)
            if _running and sleep_for > 0:
                time.sleep(sleep_for)
    finally:
        camera.stop()
        logger.info("captor_loop_stopped")

    return 0


def main() -> None:
    """Entry point for the Raspberry Pi captor process."""
    _configure_logging()
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)
    sys.exit(run_loop())


if __name__ == "__main__":
    main()
