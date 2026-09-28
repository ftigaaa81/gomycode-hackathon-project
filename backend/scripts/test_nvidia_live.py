#!/usr/bin/env python3
"""
Live NVIDIA vision smoke test (real API call).

Usage (from repository root or backend/):
    python backend/scripts/test_nvidia_live.py /path/to/image.jpg

Requires GEMINI_API_KEY in .env (repo root or backend/.env).
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.schemas.analysis import AnalysisSource  # noqa: E402
from app.services.nvidia_service import (  # noqa: E402
    NvidiaServiceError,
    get_nvidia_service,
)

LATENCY_WARNING_SECONDS = 3.0


async def _run(image_path: Path) -> int:
    """Load image, call NVIDIA, print JSON and timing."""
    frame_bytes = image_path.read_bytes()
    if len(frame_bytes) < 512:
        print("Error: image file is too small to be a valid frame.", file=sys.stderr)
        return 1

    service = get_nvidia_service()
    started = time.perf_counter()
    try:
        result = await service.analyze_frame(
            frame_bytes,
            source=AnalysisSource.CAPTOR,
            captor_id="live-test-script",
        )
    except NvidiaServiceError as exc:
        elapsed = time.perf_counter() - started
        print(f"NVIDIA call failed after {elapsed:.2f}s: {exc}", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - started
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
    print(f"\nResponse time: {elapsed:.2f}s")
    if elapsed > LATENCY_WARNING_SECONDS:
        print(
            f"WARNING: response exceeded {LATENCY_WARNING_SECONDS:.0f}s "
            "(EyE C real-time budget).",
            file=sys.stderr,
        )
    return 0


def main() -> None:
    """CLI entrypoint."""
    if len(sys.argv) != 2:
        print(
            "Usage: python backend/scripts/test_nvidia_live.py <path-to-image>",
            file=sys.stderr,
        )
        sys.exit(2)

    image_path = Path(sys.argv[1]).expanduser().resolve()
    if not image_path.is_file():
        print(f"Error: file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    exit_code = asyncio.run(_run(image_path))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
