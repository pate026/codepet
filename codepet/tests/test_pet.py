import random
import time

from codepet import art, pet

HOUR = 3600.0
DAY = 86400.0
BASE = time.mktime((2024, 5, 1, 12, 0, 0, 0, 0, -1))


def test_new_pet_defaults():
    state = pet.new_pet(BASE)

    assert state.name == "Bit"
    assert state.hunger == 80
    assert state.xp == 0
    assert state.born_at == BASE
    assert state.last_update == BASE
    assert state.repos == {}
    assert state.fed_today == 0
    assert state.fed_date == "2024-05-01"
    assert pet.stage(state) == "egg"
    assert pet.mood(state) == "happy"


def test_hunger_decays_one_point_per_hour():
    state = pet.new_pet(BASE)

    lost = pet.decay(state, BASE + 5 * HOUR)

    assert lost == 5
    assert state.hunger == 75


def test_decay_keeps_partial_hours():
    state = pet.new_pet(BASE)

    lost = pet.decay(state, BASE + 2.5 * HOUR)

    assert lost == 2
    assert state.hunger == 78
    assert state.last_update == BASE + 2 * HOUR
    assert pet.decay(state, BASE + 2.5 * HOUR) == 0


def test_hunger_never_drops_below_zero():
    state = pet.new_pet(BASE)
    state.hunger = 10

    assert pet.decay(state, BASE + 100 * HOUR) == 10
    assert state.hunger == 0
    assert pet.decay(state, BASE + 200 * HOUR) == 0
    assert state.hunger == 0


def test_feeding_adds_hunger_and_caps_it():
    state = pet.new_pet(BASE)
    state.hunger = 90

    result = pet.feed(state, 1, BASE)

    assert result.eaten == 1
    assert result.ignored == 0
    assert state.hunger == 100
    assert state.xp == 10


def test_feeding_adds_xp_for_every_commit():
    state = pet.new_pet(BASE)

    result = pet.feed(state, 3, BASE)

    assert result.eaten == 3
    assert state.hunger == 100
    assert state.xp == 30
    assert state.fed_today == 3


def test_only_ten_commits_per_day_count():
    state = pet.new_pet(BASE)

    first = pet.feed(state, 8, BASE)
    second = pet.feed(state, 5, BASE)
    third = pet.feed(state, 1, BASE)

    assert (first.eaten, first.ignored) == (8, 0)
    assert (second.eaten, second.ignored) == (2, 3)
    assert (third.eaten, third.ignored) == (0, 1)
    assert state.fed_today == 10
    assert state.xp == 100


def test_daily_counter_resets_on_a_new_day():
    state = pet.new_pet(BASE)
    pet.feed(state, 10, BASE)

    result = pet.feed(state, 1, BASE + DAY)

    assert result.eaten == 1
    assert state.fed_today == 1
    assert state.xp == 110


def test_stage_boundaries():
    cases = {
        0: "egg",
        49: "egg",
        50: "baby",
        199: "baby",
        200: "teen",
        499: "teen",
        500: "adult",
        1000: "adult",
    }
    for xp, expected in cases.items():
        assert pet.stage_for_xp(xp) == expected


def test_mood_boundaries():
    cases = {
        100: "happy",
        70: "happy",
        69: "ok",
        40: "ok",
        39: "hungry",
        10: "hungry",
        9: "starving",
        1: "starving",
        0: "ghost",
    }
    for hunger, expected in cases.items():
        assert pet.mood_for_hunger(hunger) == expected


def test_ghost_returns_after_feeding():
    state = pet.new_pet(BASE)
    state.hunger = 0
    assert pet.mood(state) == "ghost"

    pet.feed(state, 1, BASE)

    assert state.hunger == 15
    assert pet.mood(state) != "ghost"


def test_every_stage_and_mood_renders_art():
    for stage in art.STAGES:
        for mood in art.MOODS:
            text = art.render(stage, mood)
            assert text.strip()
            assert "{eyes}" not in text


def test_egg_art_is_exact():
    expected = r"""   .--.
  /    \
 |  /\/ |
  \____/"""

    assert art.render("egg", "happy") == expected


def test_eyes_follow_the_mood():
    assert "( ^ ^ )" in art.render("teen", "happy")
    assert "( o o )" in art.render("teen", "ok")
    assert "( - - )" in art.render("teen", "hungry")
    assert "( ; ; )" in art.render("teen", "starving")


def test_ghost_always_has_ghost_eyes():
    for stage in art.STAGES:
        text = art.render(stage, "ghost")
        assert "( x x )" in text
        for eyes in ("^ ^", "o o", "- -", "; ;"):
            assert eyes not in text


def test_every_mood_has_messages_and_is_deterministic():
    for mood in art.MOODS:
        assert len(art.MESSAGES[mood]) >= 3
        first = art.speech(mood, random.Random(7))
        second = art.speech(mood, random.Random(7))
        assert first == second
        assert first in art.MESSAGES[mood]


def test_hunger_bar():
    assert art.hunger_bar(70) == "[#######---] 70%"
    assert art.hunger_bar(100) == "[##########] 100%"
    assert art.hunger_bar(0) == "[----------] 0%"
