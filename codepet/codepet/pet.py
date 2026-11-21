"""Pure pet logic: stats, hunger decay, feeding, mood and stage.

This module never reads files, calls git or reads the clock. Time is always
passed in as Unix seconds so every rule can be tested deterministically.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

HOUR = 3600.0
MAX_HUNGER = 100
FEED_HUNGER = 15
FEED_XP = 10
DAILY_COMMIT_LIMIT = 10

DEFAULT_NAME = "Bit"
DEFAULT_HUNGER = 80


@dataclass
class PetState:
    name: str = DEFAULT_NAME
    hunger: int = DEFAULT_HUNGER
    xp: int = 0
    born_at: float = 0.0
    last_update: float = 0.0
    repos: dict[str, float] = field(default_factory=dict)
    fed_today: int = 0
    fed_date: str = ""


@dataclass(frozen=True)
class FeedResult:
    eaten: int
    ignored: int


def day_key(now: float) -> str:
    """Return the local calendar day for a timestamp."""
    return time.strftime("%Y-%m-%d", time.localtime(now))


def new_pet(now: float, name: str = DEFAULT_NAME) -> PetState:
    return PetState(
        name=name,
        hunger=DEFAULT_HUNGER,
        xp=0,
        born_at=now,
        last_update=now,
        repos={},
        fed_today=0,
        fed_date=day_key(now),
    )


def decay(state: PetState, now: float) -> int:
    """Drop hunger by one point per full hour since the last update.

    Only whole hours are consumed, so the remaining fraction is kept for the
    next run. Returns the number of points lost.
    """
    if state.last_update <= 0:
        state.last_update = now
        return 0

    elapsed = now - state.last_update
    if elapsed < HOUR:
        return 0

    hours = int(elapsed // HOUR)
    lost = min(state.hunger, hours)
    state.hunger -= lost
    state.last_update += hours * HOUR
    return lost


def feed(state: PetState, commit_count: int, now: float) -> FeedResult:
    """Feed the pet one portion per new commit, up to the daily limit."""
    if commit_count < 0:
        raise ValueError("commit_count must not be negative")

    today = day_key(now)
    if state.fed_date != today:
        state.fed_date = today
        state.fed_today = 0

    remaining = max(0, DAILY_COMMIT_LIMIT - state.fed_today)
    eaten = min(commit_count, remaining)
    ignored = commit_count - eaten

    if eaten:
        state.fed_today += eaten
        state.hunger = min(MAX_HUNGER, state.hunger + eaten * FEED_HUNGER)
        state.xp += eaten * FEED_XP

    return FeedResult(eaten=eaten, ignored=ignored)


def stage_for_xp(xp: int) -> str:
    if xp >= 500:
        return "adult"
    if xp >= 200:
        return "teen"
    if xp >= 50:
        return "baby"
    return "egg"


def mood_for_hunger(hunger: int) -> str:
    if hunger >= 70:
        return "happy"
    if hunger >= 40:
        return "ok"
    if hunger >= 10:
        return "hungry"
    if hunger >= 1:
        return "starving"
    return "ghost"


def stage(state: PetState) -> str:
    return stage_for_xp(state.xp)


def mood(state: PetState) -> str:
    return mood_for_hunger(state.hunger)
