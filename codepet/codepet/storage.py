"""Load and save pet state as JSON."""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from .pet import MAX_HUNGER, PetState, new_pet


def default_state_path() -> Path:
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return base / "codepet" / "state.json"


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return default


def _as_timestamp(value: object, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return default
    return result if result >= 0 else default


def _state_from_dict(data: object, now: float) -> PetState:
    default = new_pet(now)
    if not isinstance(data, dict):
        return default

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        name = default.name

    hunger = max(0, min(MAX_HUNGER, _as_int(data.get("hunger"), default.hunger)))
    xp = max(0, _as_int(data.get("xp"), 0))

    repos: dict[str, float] = {}
    raw_repos = data.get("repos")
    if isinstance(raw_repos, dict):
        for path, checked in raw_repos.items():
            if isinstance(path, str) and path:
                repos[path] = _as_timestamp(checked, 0.0)

    fed_date = data.get("fed_date")
    if not isinstance(fed_date, str):
        fed_date = default.fed_date

    return PetState(
        name=name,
        hunger=hunger,
        xp=xp,
        born_at=_as_timestamp(data.get("born_at"), now),
        last_update=_as_timestamp(data.get("last_update"), now),
        repos=repos,
        fed_today=max(0, _as_int(data.get("fed_today"), 0)),
        fed_date=fed_date,
    )


def load_state(path: str | Path, now: float | None = None) -> PetState:
    """Load state, falling back to a fresh pet when the file is unusable."""
    now = time.time() if now is None else now
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return new_pet(now)
    return _state_from_dict(data, now)


def save_state(state: PetState, path: str | Path) -> None:
    """Write state atomically: a temporary file is renamed into place."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(asdict(state), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
