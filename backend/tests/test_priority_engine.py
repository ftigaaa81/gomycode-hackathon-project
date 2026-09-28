"""Unit tests for priority_engine.should_speak."""

from datetime import datetime, timedelta

from app.schemas.analysis import UrgenceLevel
from app.services.priority_engine import should_speak


def test_first_frame_always_speaks() -> None:
    """No prior speech should always allow output."""
    assert should_speak(UrgenceLevel.NORMAL, None) is True
    assert should_speak(UrgenceLevel.ATTENTION, None) is True
    assert should_speak(UrgenceLevel.DANGER, None) is True


def test_danger_always_speaks_even_after_recent_message() -> None:
    """Danger bypasses cooldown."""
    last = datetime.now() - timedelta(seconds=1)
    assert should_speak(UrgenceLevel.DANGER, last) is True


def test_attention_respects_cooldown() -> None:
    """Attention waits at least 8 seconds between messages."""
    recent = datetime.now() - timedelta(seconds=2)
    assert should_speak(UrgenceLevel.ATTENTION, recent) is False

    older = datetime.now() - timedelta(seconds=10)
    assert should_speak(UrgenceLevel.ATTENTION, older) is True


def test_normal_respects_longer_cooldown() -> None:
    """Normal tier uses a 20 second cooldown."""
    mid = datetime.now() - timedelta(seconds=12)
    assert should_speak(UrgenceLevel.NORMAL, mid) is False

    older = datetime.now() - timedelta(seconds=25)
    assert should_speak(UrgenceLevel.NORMAL, older) is True
