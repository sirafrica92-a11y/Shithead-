"""Four-character room codes: format, collisions, matching and guess limits."""
import re

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server.app import lobby
from server.app.lobby import (
    ROOM_CODE_ALPHABET, ROOM_CODE_LENGTH, Room, RoomStore,
    is_room_code, normalise_room_code,
)
from server.app.main import create_app

CODE = re.compile(r"^[A-Z0-9]{4}$")


def test_a_new_room_gets_a_four_character_uppercase_code():
    with TestClient(create_app()) as client:
        code = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        assert CODE.match(code), code
        assert len(code) == ROOM_CODE_LENGTH == 4
        assert set(code) <= set(ROOM_CODE_ALPHABET)


def test_many_rooms_get_distinct_well_formed_codes():
    with TestClient(create_app()) as client:
        codes = [client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
                 for _ in range(60)]
        assert len(set(codes)) == len(codes)
        assert all(CODE.match(c) for c in codes)


def test_allocate_code_retries_until_it_finds_a_free_one(monkeypatch):
    store = RoomStore()
    store.rooms["AAAA"] = Room(id="AAAA", capacity=2)
    picks = iter("AAAA" "BBBB")
    monkeypatch.setattr(lobby.secrets, "choice", lambda alphabet: next(picks))
    assert store._allocate_code() == "BBBB"


def test_allocate_code_gives_up_rather_than_reusing_a_code(monkeypatch):
    store = RoomStore()
    store.rooms["AAAA"] = Room(id="AAAA", capacity=2)
    monkeypatch.setattr(lobby.secrets, "choice", lambda alphabet: "A")
    with pytest.raises(ValueError):
        store._allocate_code()


def test_codes_are_validated_the_same_way_everywhere():
    assert is_room_code("A1B2")
    assert not is_room_code("a1b2")      # validation happens after normalising
    assert not is_room_code("A1B")       # too short
    assert not is_room_code("A1B2C")     # too long
    assert not is_room_code("A1-2")      # outside the alphabet
    assert normalise_room_code("  a1b2 ") == "A1B2"


def test_a_typed_code_matches_regardless_of_case_or_padding():
    with TestClient(create_app()) as client:
        code = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        for typed in (code.lower(), f"  {code}  ", f" {code.lower()}"):
            joined = client.post(f"/api/rooms/{typed.strip()}/join", json={"name": "A"})
            # Only the first join takes the seat; the rest prove the code resolved.
            assert joined.status_code in (201, 409), (typed, joined.status_code)
        assert client.get(f"/api/rooms/{code.lower()}").status_code == 200


def test_guessing_is_rate_limited_but_real_players_are_not():
    app = create_app(failed_lookup_limit=3, rate_window=60)
    with TestClient(app) as client:
        good = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        for _ in range(3):
            assert client.get("/api/rooms/ZZZZ").status_code == 404
        # The allowance is spent: further wrong codes are refused outright.
        assert client.get("/api/rooms/YYYY").status_code == 429
        assert client.post("/api/rooms/XXXX/join", json={"name": "Eve"}).status_code == 429
        # A player holding a real code is unaffected by someone else's guessing.
        assert client.get(f"/api/rooms/{good}").status_code == 200
        assert client.post(f"/api/rooms/{good}/join", json={"name": "A"}).status_code == 201


def test_oversized_and_empty_codes_are_rejected_without_a_lookup():
    with TestClient(create_app()) as client:
        assert client.get("/api/rooms/" + "A" * 400).status_code == 404
        assert client.get("/api/rooms/%20").status_code == 404


def test_websocket_refuses_an_unknown_code():
    with TestClient(create_app()) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/ZZZZ") as ws:
                ws.receive_json()


def test_guess_limits_are_per_client_not_shared_behind_the_proxy():
    """Railway terminates TLS, so the socket peer is the same for everyone."""
    app = create_app(failed_lookup_limit=2, rate_window=60)
    with TestClient(app) as client:
        guesser = {"X-Forwarded-For": "203.0.113.9"}
        victim = {"X-Forwarded-For": "198.51.100.4"}
        for _ in range(2):
            assert client.get("/api/rooms/ZZZZ", headers=guesser).status_code == 404
        assert client.get("/api/rooms/YYYY", headers=guesser).status_code == 429
        # A different player still gets their normal allowance.
        assert client.get("/api/rooms/QQQQ", headers=victim).status_code == 404


def test_create_room_with_a_name_seats_the_host_in_one_request():
    """Entering a name and pressing Create room must not need a second Join."""
    with TestClient(create_app()) as client:
        created = client.post("/api/rooms", json={"capacity": 2, "name": "Africa"})
        assert created.status_code == 201
        body = created.json()
        assert CODE.match(body["room_id"])
        assert body["seat"] == 0 and body["token"]
        public = client.get(f"/api/rooms/{body['room_id']}").json()
        assert [p["name"] for p in public["players"]] == ["Africa"]
        assert body["token"] not in str(public)


def test_create_room_without_a_name_still_works():
    """An older client that sends no name keeps the previous behaviour."""
    with TestClient(create_app()) as client:
        body = client.post("/api/rooms", json={"capacity": 2}).json()
        assert "token" not in body and "seat" not in body
        assert client.get(f"/api/rooms/{body['room_id']}").json()["players"] == []


def test_create_room_rejects_a_blank_host_name():
    with TestClient(create_app()) as client:
        assert client.post("/api/rooms", json={"capacity": 2, "name": "   "}).status_code == 422


def test_host_and_guest_take_different_seats_and_tokens():
    with TestClient(create_app()) as client:
        host = client.post("/api/rooms", json={"capacity": 2, "name": "Africa"}).json()
        guest = client.post(f"/api/rooms/{host['room_id']}/join",
                            json={"name": "Bardia"}).json()
        assert host["seat"] == 0 and guest["seat"] == 1
        assert host["token"] != guest["token"]
        assert client.post(f"/api/rooms/{host['room_id']}/join",
                           json={"name": "Third"}).status_code == 409
