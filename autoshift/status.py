"""Per-run status, written next to the key database so it outlives the log."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from autoshift.common import _L, settings

FILENAME = "status.json"


def _path() -> Path:
    return settings.DATA_DIR / FILENAME


def read() -> dict[str, Any]:
    """The last recorded run, or an empty dict if there is none to read."""
    try:
        with _path().open() as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}

    return data if isinstance(data, dict) else {}


def record(*, source_ok: bool, new_keys: int, redeemed: int, pending: int) -> None:
    """Record this run, carrying the last redemption forward through quiet ones."""
    previous = read()
    now = datetime.now(UTC).isoformat(timespec="seconds")

    payload = {
        "checked_at": now,
        "source_ok": source_ok,
        "new_keys": new_keys,
        "redeemed": redeemed,
        "pending": pending,
        "last_redeemed_at": now if redeemed else previous.get("last_redeemed_at"),
        "last_new_key_at": now if new_keys else previous.get("last_new_key_at"),
        "schedule_minutes": settings.SCHEDULE,
        "tracking_since": previous.get("tracking_since") or now,
    }

    try:
        _write(payload)
    except OSError as e:
        _L.warning(f"Couldn't write {FILENAME} ({e}).")


def _write(payload: dict[str, Any]) -> None:
    """Swap the file in one step, so a reader never gets half of it."""
    path = _path()
    tmp = path.with_suffix(".json.tmp")

    with tmp.open("w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    os.replace(tmp, path)
