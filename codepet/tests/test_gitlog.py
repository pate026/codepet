import os
import subprocess

import pytest

from codepet import gitlog

EMAIL = "pet@example.com"


def _git(repo, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def _init_repo(path):
    path.mkdir()
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True, text=True)
    _git(path, "config", "user.email", EMAIL)
    _git(path, "config", "user.name", "Pet Tester")
    return path


def _commit(repo, message, timestamp, email=EMAIL):
    date = f"@{int(timestamp)} +0000"
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
            "GIT_AUTHOR_NAME": "Pet Tester",
            "GIT_COMMITTER_NAME": "Pet Tester",
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_EMAIL": email,
        }
    )
    _git(repo, "commit", "--allow-empty", "-m", message, env=env)


def test_commits_since_finds_the_users_commits(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, "one", 1_700_000_000)
    _commit(repo, "two", 1_700_000_100)

    found = gitlog.commits_since(repo, EMAIL, 0)

    assert len(found) == 2
    assert {timestamp for _, timestamp in found} == {1_700_000_000, 1_700_000_100}
    assert all(len(commit_hash) == 40 for commit_hash, _ in found)


def test_only_commits_strictly_newer_than_since_count(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, "one", 1_700_000_000)
    _commit(repo, "two", 1_700_000_100)

    found = gitlog.commits_since(repo, EMAIL, 1_700_000_000)

    assert [timestamp for _, timestamp in found] == [1_700_000_100]


def test_other_authors_are_ignored(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _commit(repo, "mine", 1_700_000_000)
    _commit(repo, "theirs", 1_700_000_100, email="other@example.com")

    found = gitlog.commits_since(repo, EMAIL, 0)

    assert [timestamp for _, timestamp in found] == [1_700_000_000]


def test_non_repo_directory_gives_a_warning(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()

    commits, warning = gitlog.check_repo(plain, EMAIL, 0)

    assert commits == []
    assert warning is not None
    assert "skipping" in warning


def test_missing_path_gives_a_warning(tmp_path):
    commits, warning = gitlog.check_repo(tmp_path / "gone", EMAIL, 0)

    assert commits == []
    assert warning is not None
    assert "does not exist" in warning


def test_commits_since_raises_for_non_repo(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()

    with pytest.raises(gitlog.GitError):
        gitlog.commits_since(plain, EMAIL, 0)


def test_is_git_repo(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    plain = tmp_path / "plain"
    plain.mkdir()

    assert gitlog.is_git_repo(repo)
    assert not gitlog.is_git_repo(plain)
    assert not gitlog.is_git_repo(tmp_path / "gone")
