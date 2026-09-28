"""Pure logic for deciding when the assistant should speak."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.schemas.analysis import UrgenceLevel

# Minimum interval between spoken messages per urgency tier.
_COOLDOWN = {
    UrgenceLevel.DANGER: timedelta(seconds=0),
    UrgenceLevel.ATTENTION: timedelta(seconds=8),
    UrgenceLevel.NORMAL: timedelta(seconds=20),
}


def should_speak(urgence: UrgenceLevel, last_spoken_at: datetime | None) -> bool:
    """
    Return True if a message with the given urgency should be spoken now.

    Danger always passes; attention and normal respect cooldowns after the last speech.
    The first frame (no prior speech) always triggers output.
    """
    if last_spoken_at is None:
        return True
    if urgence == UrgenceLevel.DANGER:
        return True

    elapsed = datetime.now() - last_spoken_at
    return elapsed >= _COOLDOWN[urgence]
