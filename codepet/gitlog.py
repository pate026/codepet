"""Read the user's commits from git repositories with subprocess."""

from __future__ import annotations

import subprocess
from pathlib import Path

GIT_TIMEOUT = 5


class GitError(Exception):
    """Raised when a git command cannot be completed."""


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
    )


def get_user_email() -> str | None:
    """Return the configured git user.email, or None when it is unavailable."""
    try:
        result = _run_git(["config", "user.email"])
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    email = result.stdout.strip()
    return email or None


def is_git_repo(path: str | Path) -> bool:
    path = Path(path)
    if not path.is_dir():
        return False
    try:
        result = _run_git(["-C", str(path), "rev-parse", "--is-inside-work-tree"])
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def commits_since(path: str | Path, email: str, since: float) -> list[tuple[str, int]]:
    """Return (hash, timestamp) pairs for the user's commits after since."""
    since = float(since)
    args = [
        "-C",
        str(path),
        "log",
        "--all",
        f"--author={email}",
        "--format=%H %ct",
    ]
    # git treats "@0" as "now", so an unset timestamp means "all history".
    if since > 0:
        args.insert(4, f"--since=@{int(since)}")
    try:
        result = _run_git(args)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitError(str(exc)) from exc

    if result.returncode != 0:
        raise GitError(result.stderr.strip() or "git log failed")

    commits: list[tuple[str, int]] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        commit_hash, timestamp_text = parts
        try:
            timestamp = int(timestamp_text)
        except ValueError:
            continue
        if timestamp > since:
            commits.append((commit_hash, timestamp))
    return commits


def check_repo(
    path: str | Path, email: str, since: float
) -> tuple[list[tuple[str, int]], str | None]:
    """Return commits and an optional warning instead of raising errors."""
    repo_path = Path(path)
    if not repo_path.exists():
        return [], f"warning: {path} does not exist, skipping"
    if not repo_path.is_dir():
        return [], f"warning: {path} is not a directory, skipping"

    try:
        commits = commits_since(path, email, since)
    except GitError as exc:
        reason = (
            "not a git repository"
            if "not a git repository" in str(exc).lower()
            else "git failed"
        )
        return [], f"warning: {path}: {reason}, skipping"
    return commits, None
