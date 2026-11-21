"""Command line commands, tying the pure logic to files, git and the clock."""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

from . import art, gitlog, pet, storage


def _resolve_repo(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _load(state_path: Path) -> pet.PetState:
    return storage.load_state(state_path, time.time())


def _show(state: pet.PetState, mood: str, message: str, result: pet.FeedResult) -> None:
    stage = pet.stage(state)
    header = f"  {state.name} the {stage} penguin"
    print(f"{header:<34}xp: {state.xp}")
    for line in art.render(stage, mood, message).splitlines():
        print(f"  {line}")
    print(f"  Hunger {art.hunger_bar(state.hunger)}    mood: {mood}")
    if result.eaten:
        noun = "commit" if result.eaten == 1 else "commits"
        print(f"  Ate {result.eaten} new {noun}!")
    if result.ignored:
        print("  I'm full, save some for tomorrow!")


def _cmd_default(state_path: Path) -> int:
    now = time.time()
    state = storage.load_state(state_path, now)
    pet.decay(state, now)

    warnings: list[str] = []
    total = 0
    email = gitlog.get_user_email()
    if email is None:
        warnings.append("warning: git user.email is not set, no commits can be eaten")
    else:
        for repo_path in list(state.repos):
            commits, warning = gitlog.check_repo(repo_path, email, state.repos[repo_path])
            if warning is not None:
                warnings.append(warning)
                continue
            total += len(commits)
            # Git timestamps have one-second resolution. Keep a one-second grace
            # so a commit made right after this scan is not skipped, while the
            # newest commit we saw prevents counting it twice.
            newest = max((timestamp for _, timestamp in commits), default=0.0)
            state.repos[repo_path] = max(now - 1.0, newest)

    result = pet.feed(state, total, now)
    mood = pet.mood(state)
    message = art.speech(mood, random.Random())

    try:
        storage.save_state(state, state_path)
    except OSError as exc:
        warnings.append(f"warning: could not save state: {exc}")

    _show(state, mood, message, result)
    for warning in warnings:
        print(warning, file=sys.stderr)
    return 0


def _cmd_add_repo(state_path: Path, path: str) -> int:
    repo = _resolve_repo(path)
    if not repo.is_dir():
        print(f"codepet: {repo} is not a directory", file=sys.stderr)
        return 1
    if not gitlog.is_git_repo(repo):
        print(f"codepet: {repo} is not a git repository", file=sys.stderr)
        return 1

    now = time.time()
    state = storage.load_state(state_path, now)
    # One-second grace for commits made in the same second as this command.
    state.repos[str(repo)] = now - 1.0
    storage.save_state(state, state_path)
    print(f"Now watching {repo}")
    return 0


def _cmd_remove_repo(state_path: Path, path: str) -> int:
    repo = _resolve_repo(path)
    state = _load(state_path)
    if str(repo) not in state.repos:
        print(f"Not watching {repo}")
        return 0

    del state.repos[str(repo)]
    storage.save_state(state, state_path)
    print(f"Stopped watching {repo}")
    return 0


def _cmd_repos(state_path: Path) -> int:
    state = _load(state_path)
    if not state.repos:
        print("No repos watched yet. Add one with: python main.py add-repo PATH")
        return 0
    for path in state.repos:
        print(path)
    return 0


def _cmd_rename(state_path: Path, name: str) -> int:
    name = name.strip()
    if not name:
        print("codepet: the name must not be empty", file=sys.stderr)
        return 1

    state = _load(state_path)
    state.name = name
    storage.save_state(state, state_path)
    print(f"The pet is now called {name}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codepet",
        description="A terminal penguin that eats your git commits.",
    )
    subparsers = parser.add_subparsers(dest="command")

    add_repo = subparsers.add_parser("add-repo", help="watch a git repository")
    add_repo.add_argument("path")

    remove_repo = subparsers.add_parser("remove-repo", help="stop watching a repository")
    remove_repo.add_argument("path")

    subparsers.add_parser("repos", help="list watched repositories")

    rename = subparsers.add_parser("rename", help="rename the pet")
    rename.add_argument("name")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        state_path = storage.default_state_path()
        if args.command is None:
            return _cmd_default(state_path)
        if args.command == "add-repo":
            return _cmd_add_repo(state_path, args.path)
        if args.command == "remove-repo":
            return _cmd_remove_repo(state_path, args.path)
        if args.command == "repos":
            return _cmd_repos(state_path)
        if args.command == "rename":
            return _cmd_rename(state_path, args.name)
        return 0
    except Exception as exc:  # the shell must never see a traceback
        message = str(exc).strip() or "something went wrong"
        print(f"codepet: {message}", file=sys.stderr)
        return 0 if args.command is None else 1
