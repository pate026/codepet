"""Penguin ASCII art, mood eyes and speech-bubble messages."""

from __future__ import annotations

import random

STAGES = ("egg", "baby", "teen", "adult")
MOODS = ("happy", "ok", "hungry", "starving", "ghost")

EYES = {
    "happy": "^ ^",
    "ok": "o o",
    "hungry": "- -",
    "starving": "; ;",
}
GHOST_EYES = "x x"

STAGE_ART = {
    "egg": r"""   .--.
  /    \
 |  /\/ |
  \____/""",
    "baby": r"""   .-.
  ({eyes})
  (\v/)
   ^ ^""",
    "teen": r"""   .---.
  ( {eyes} )
  /( v )\
   |   |
    ^ ^""",
    "adult": r"""   .---.
  ( {eyes} )
  >=====<
 /|     |\
  |     |
  '-----'
   ^   ^""",
}

GHOST_ART = r"""   .---.
  ( x x )
  /( v )\
  |     |
  |/\/\/|"""

MESSAGES = {
    "happy": [
        "Mmm, tasty commits!",
        "Another commit? Delicious!",
        "My code belly is happy!",
    ],
    "ok": [
        "Not bad. Keep coding.",
        "I could eat a few more commits.",
        "A steady diet of commits. Nice.",
    ],
    "hungry": [
        "Psst... git commit -m 'feed me'",
        "My tummy is rumbling.",
        "Got any fresh commits?",
    ],
    "starving": [
        "So... hungry...",
        "One commit. Please.",
        "I can see the code... fading...",
    ],
    "ghost": [
        "Boooo... I starved waiting for your code.",
        "Feed me and I shall return!",
        "Even ghosts need commits.",
    ],
}


def render(stage: str, mood: str, message: str | None = None) -> str:
    """Return the art for a stage and mood, optionally with a speech bubble."""
    if stage not in STAGE_ART:
        raise ValueError(f"unknown stage: {stage}")
    if mood not in MOODS:
        raise ValueError(f"unknown mood: {mood}")

    if mood == "ghost":
        template = GHOST_ART
        eyes = GHOST_EYES
    else:
        template = STAGE_ART[stage]
        eyes = EYES[mood]

    lines = template.replace("{eyes}", eyes).splitlines()
    if message:
        index = min(1, len(lines) - 1)
        lines[index] = f"{lines[index]}   < {message}"
    return "\n".join(lines)


def speech(mood: str, rng: random.Random) -> str:
    """Pick a random message for the mood using the given random source."""
    if mood not in MESSAGES:
        raise ValueError(f"unknown mood: {mood}")
    return rng.choice(MESSAGES[mood])


def hunger_bar(hunger: int) -> str:
    """Render a ten-slot hunger bar followed by the percentage."""
    hunger = max(0, min(100, hunger))
    filled = hunger // 10
    return f"[{'#' * filled}{'-' * (10 - filled)}] {hunger}%"
