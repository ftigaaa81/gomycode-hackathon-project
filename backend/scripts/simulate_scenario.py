#!/usr/bin/env python3
"""
Simulate a 10-frame EyE C session (captor + mobile) against the live API.

Validates timing and anti-spam ``doit_parler`` behaviour using the same priority
cooldowns as the backend priority engine.

Usage:
    python backend/scripts/simulate_scenario.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import base64
import io
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services.priority_engine import should_speak  # noqa: E402
from app.schemas.analysis import UrgenceLevel  # noqa: E402

FRAME_INTERVAL_SECONDS = 3.5
FRAME_COUNT = 10
SECONDS_PER_WORD = 0.35


def _minimal_jpeg_base64() -> str:
    """Build a tiny valid JPEG for API validation."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Install Pillow to generate test JPEG bytes.") from exc

    buffer = io.BytesIO()
    Image.new("RGB", (640, 480), color=(40, 40, 40)).save(
        buffer,
        format="JPEG",
        quality=80,
    )
    return base64.standard_b64encode(buffer.getvalue()).decode("ascii")


def _estimate_speech_seconds(message: str) -> float:
    words = max(1, len(message.split()))
    return words * SECONDS_PER_WORD


def _post_analyze(
    client: httpx.Client,
    base_url: str,
    *,
    source: str,
    image_b64: str,
    captor_id: str | None,
) -> tuple[dict, float]:
    started = time.perf_counter()
    payload: dict = {
        "image_base64": image_b64,
        "source": source,
    }
    if source == "captor":
        payload["captor_id"] = captor_id or "pi-sim-01"

    response = client.post(f"{base_url.rstrip('/')}/api/analyze", json=payload)
    source_label = source
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    body = response.json()
    body["_source_label"] = source_label
    return body, elapsed


def run_simulation(base_url: str) -> int:
    """Run 10 spaced frames alternating captor/mobile sources."""
    image_b64 = _minimal_jpeg_base64()
    last_spoken_at: datetime | None = None
    speaking_until = 0.0

    print(f"Simulating {FRAME_COUNT} frames every {FRAME_INTERVAL_SECONDS}s → {base_url}\n")

    with httpx.Client(timeout=30.0) as client:
        for index in range(1, FRAME_COUNT + 1):
            cycle_start = time.perf_counter()
            now = time.time()

            if now < speaking_until:
                print(
                    f"[frame {index:02d}] SKIP capture — still speaking "
                    f"({speaking_until - now:.1f}s left)"
                )
            else:
                source = "captor" if index % 2 == 1 else "mobile"
                try:
                    body, api_seconds = _post_analyze(
                        client,
                        base_url,
                        source=source,
                        image_b64=image_b64,
                        captor_id="pi-sim-01",
                    )
                except httpx.HTTPError as exc:
                    print(f"[frame {index:02d}] HTTP error: {exc}")
                    body = None
                    api_seconds = 0.0

                if body is not None:
                    urgence = UrgenceLevel(body["urgence"])
                    message = body.get("message_court", "")
                    wire_doit_parler = bool(str(message).strip())
                    priority_ok = should_speak(urgence, last_spoken_at)
                    doit_parler = wire_doit_parler and priority_ok

                    print(
                        f"[frame {index:02d}] source={source} "
                        f"api={api_seconds:.2f}s urgence={urgence.value} "
                        f"wire_doit_parler={wire_doit_parler} "
                        f"priority_ok={priority_ok} "
                        f"doit_parler={doit_parler} "
                        f"msg={message!r}"
                    )

                    if doit_parler:
                        last_spoken_at = datetime.now()
                        speaking_until = time.time() + _estimate_speech_seconds(message)

            elapsed = time.perf_counter() - cycle_start
            sleep_for = max(0.0, FRAME_INTERVAL_SECONDS - elapsed)
            if index < FRAME_COUNT and sleep_for > 0:
                time.sleep(sleep_for)

    print("\nSimulation complete.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate EyE C frame session.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL",
    )
    args = parser.parse_args()
    raise SystemExit(run_simulation(args.base_url))


if __name__ == "__main__":
    main()
