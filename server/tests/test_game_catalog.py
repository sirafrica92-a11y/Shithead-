"""Regression contract for a low-risk, non-gameplay game catalogue."""
import pytest
from fastapi.testclient import TestClient
from server.app.game_catalog import GAMES, game_spec, capacity_options, capacity_after_switch
from server.app.main import create_app


def test_supported_games_and_caps_are_exact():
    assert set(GAMES) == {"shithead", "ludo", "awale", "dara"}
    assert [capacity_options(k) for k in GAMES] == [
        (2, 3, 4, 5, 6), (2, 3, 4), (2,), (2,)
    ]
    for key, spec in GAMES.items():
        assert spec.key == key
        assert spec.valid_capacity(spec.min_players)
        assert spec.valid_capacity(spec.max_players)
        assert not spec.valid_capacity(spec.max_players + 1)
        assert not spec.valid_capacity(True)
    with pytest.raises(ValueError):
        game_spec("unknown")


@pytest.mark.parametrize("game,current,seats,expected", [
    ("shithead", 6, 2, 6), ("shithead", 2, 2, 2),
    ("ludo", 6, 2, 4), ("ludo", 2, 3, 3),
    ("ludo", 4, 2, 4), ("awale", 6, 2, 2),
])
def test_lobby_capacity_remains_compatible(game, current, seats, expected):
    assert capacity_after_switch(game, current, seats) == expected


@pytest.mark.parametrize("game,occupied", [("ludo", 5), ("awale", 3), ("dara", 3)])
def test_overfilled_switch_refused(game, occupied):
    with pytest.raises(ValueError):
        capacity_after_switch(game, 6, occupied)


def test_existing_games_still_accept_and_limit_seats(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"catalog.db")) as app:
        for game, max_seats in [("shithead", 6), ("ludo", 4), ("awale", 2), ("dara", 2)]:
            made = app.post("/api/rooms", json={"name":"Host", "capacity":max_seats, "game_type":game})
            assert made.status_code == 201
            code = made.json()["room_id"]
            for i in range(max_seats-1):
                joined = app.post(f"/api/rooms/{code}/join", json={"name":f"Guest{i}"})
                assert joined.status_code == 201
            refused = app.post(f"/api/rooms/{code}/join", json={"name":"Overflow"})
            assert refused.status_code == 409
