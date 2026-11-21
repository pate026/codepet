from pathlib import Path

from codepet import pet, storage

BASE = 1_700_000_000.0


def test_save_and_load_round_trip(tmp_path):
    state = pet.new_pet(BASE, name="Nib")
    state.hunger = 42
    state.xp = 321
    state.repos = {"/tmp/repo": BASE + 5}
    state.fed_today = 3
    state.fed_date = "2024-05-01"

    path = tmp_path / "nested" / "state.json"
    storage.save_state(state, path)

    assert path.is_file()
    assert storage.load_state(path, BASE + 100) == state


def test_missing_file_returns_a_new_pet(tmp_path):
    state = storage.load_state(tmp_path / "missing.json", BASE)

    assert state == pet.new_pet(BASE)


def test_broken_json_returns_a_new_pet(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")

    assert storage.load_state(path, BASE) == pet.new_pet(BASE)


def test_broken_structure_and_values_are_sanitized(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(
        '{"name": "", "hunger": 999, "xp": -5, "repos": [], "fed_today": -2}',
        encoding="utf-8",
    )

    state = storage.load_state(path, BASE)

    assert state.name == "Bit"
    assert state.hunger == 100
    assert state.xp == 0
    assert state.repos == {}
    assert state.fed_today == 0


def test_save_leaves_no_temporary_file(tmp_path):
    path = tmp_path / "state.json"

    storage.save_state(pet.new_pet(BASE), path)

    assert list(tmp_path.glob("*.tmp")) == []


def test_default_path_respects_xdg_data_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert storage.default_state_path() == tmp_path / "codepet" / "state.json"


def test_default_path_without_xdg_data_home(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    expected = Path.home() / ".local" / "share" / "codepet" / "state.json"
    assert storage.default_state_path() == expected
