"""Refresh Game: safe resynchronisation, never a reseat or a replayed move.

The button sends the existing read-only "sync" message when connected, and
reconnects with the saved room id and private seat token when not. These tests
drive a real uvicorn over real WebSockets and assert that match continuity is
preserved in the situations a player is most likely to press it: mid-turn,
while waiting, and in the middle of an unresolved 3/Joker chain.
"""
import json
import socket
import threading
import time
import uuid
from dataclasses import replace

import httpx
import pytest
import uvicorn
from websockets.sync.client import connect as ws_connect

from server.app.main import create_app
from server.app.rules.ordinary import Card


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    port = _free_port()
    db = tmp_path_factory.mktemp("resync") / "rooms.sqlite3"
    app = create_app(db_path=db)
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    while not server.started:
        if time.monotonic() > deadline or not thread.is_alive():
            server.should_exit = True
            raise RuntimeError("uvicorn did not start")
        time.sleep(0.05)
    yield f"127.0.0.1:{port}", app.state.room_store
    server.should_exit = True
    thread.join(timeout=10)


def drain(ws, timeout=0.5):
    out = []
    while True:
        try:
            out.append(json.loads(ws.recv(timeout=timeout)))
        except Exception:
            return out


def act(ws, payload, version, request_id=None):
    ws.send(json.dumps({**payload, "expected_version": version,
                        "request_id": request_id or str(uuid.uuid4())}))


def states(msgs):
    return [m for m in msgs if m.get("type") == "room_state"]


def errors(msgs):
    return [m for m in msgs if m.get("type") == "error"]


def seated_match(base, store, *, joker_for_current=True):
    h = httpx.post(f"http://{base}/api/rooms",
                   json={"capacity": 2, "name": "Africa"}).json()
    g = httpx.post(f"http://{base}/api/rooms/{h['room_id']}/join",
                   json={"name": "Bardia"}).json()
    rid = h["room_id"]
    a = ws_connect(f"ws://{base}/ws/{rid}")
    b = ws_connect(f"ws://{base}/ws/{rid}")
    a.send(json.dumps({"type": "auth", "token": h["token"]}))
    b.send(json.dumps({"type": "auth", "token": g["token"]}))
    drain(a), drain(b)
    room = store.rooms[rid]
    act(a, {"type": "ready", "ready": True}, room.version)
    drain(a), drain(b)
    act(b, {"type": "ready", "ready": True}, room.version)
    drain(a), drain(b)
    st = room.match.state
    actor = st.current
    if joker_for_current:
        players = list(st.players)
        hand = list(players[actor].hand)
        hand[0] = Card(rank=0, suit="J", id="joker-resync")
        players[actor] = replace(players[actor], hand=tuple(hand))
        room.match = replace(room.match, state=replace(
            st, players=tuple(players), pile=(Card(rank=9, suit="S", id="p9"),),
            current=actor))
        room.version += 1
    ws_by_seat = {h["seat"]: a, g["seat"]: b}
    tok_by_seat = {h["seat"]: (rid, h["token"]), g["seat"]: (rid, g["token"])}
    return room, actor, ws_by_seat, tok_by_seat, rid


def sync(ws):
    """What the Refresh button sends while connected."""
    ws.send(json.dumps({"type": "sync"}))
    return states(drain(ws))


def test_sync_returns_private_view_without_changing_anything(live):
    base, store = live
    room, actor, ws, _, _ = seated_match(base, store)
    version_before = room.version
    snap = sync(ws[actor])
    assert snap, "sync must return a snapshot"
    view = snap[-1]
    assert view["game"]["you"] == actor
    assert "hand" in view["game"], "the refreshed view must restore my own hand"
    assert room.version == version_before, "sync must not advance the room version"
    assert room.match is not None


def test_sync_never_exposes_another_seat(live):
    base, store = live
    room, actor, ws, _, _ = seated_match(base, store)
    other = 1 - actor
    view = sync(ws[other])[-1]
    assert view["game"]["you"] == other
    for p in view["game"]["players"]:
        assert "hand" not in p, "a refresh must not leak another seat's cards"


def test_refresh_during_an_unresolved_attack_keeps_the_decision(live):
    """The case the button exists for: a 3/Joker chain is open."""
    base, store = live
    room, actor, ws, _, _ = seated_match(base, store)
    other = 1 - actor
    act(ws[actor], {"type": "game", "kind": "power", "index": 0,
                    "indices": [0], "target": other}, room.version)
    drain(ws[actor]), drain(ws[other])
    assert room.match.pending is not None
    version_before = room.version

    # both seats refresh mid-chain
    target_view = sync(ws[other])[-1]["game"]
    attacker_view = sync(ws[actor])[-1]["game"]
    assert target_view["phase"] == "PILE_PASS_DECISION"
    assert target_view["actor"] == other, "the target must still own the decision"
    assert attacker_view["phase"] == "PILE_PASS_DECISION"
    assert room.version == version_before, "refreshing must not disturb the chain"

    # and the decision can still be taken afterwards
    act(ws[other], {"type": "game", "kind": "accept"}, room.version)
    msgs = drain(ws[other])
    assert not errors(msgs), errors(msgs)
    assert room.match.pending is None


def test_reconnect_with_the_saved_token_keeps_the_same_seat(live):
    """The disconnected path: no new seat, no redeal, no reset."""
    base, store = live
    room, actor, ws, tokens, rid = seated_match(base, store)
    seats_before = len(room.seats)
    hand_before = [c.id for c in room.match.state.players[actor].hand]

    ws[actor].close()
    time.sleep(0.3)
    rid2, token = tokens[actor]
    again = ws_connect(f"ws://{base}/ws/{rid2}")
    again.send(json.dumps({"type": "auth", "token": token}))
    view = states(drain(again))[-1]

    assert view["game"]["you"] == actor, "must land back on the same seat"
    assert len(room.seats) == seats_before, "reconnecting must not add a seat"
    assert [c.id for c in room.match.state.players[actor].hand] == hand_before, \
        "reconnecting must not redeal"
    assert view["room_id"] == rid
    again.close()


def test_a_repeated_request_id_is_not_applied_twice(live):
    """Reconnection or a double tap must never play the same move twice."""
    base, store = live
    room, actor, ws, _, _ = seated_match(base, store)
    other = 1 - actor
    rid = str(uuid.uuid4())
    version = room.version
    act(ws[actor], {"type": "game", "kind": "power", "index": 0,
                    "indices": [0], "target": other}, version, request_id=rid)
    drain(ws[actor]), drain(ws[other])
    after_first = room.version
    removed_first = len(room.match.power_removed)

    # same request id replayed with the same expected_version
    act(ws[actor], {"type": "game", "kind": "power", "index": 0,
                    "indices": [0], "target": other}, version, request_id=rid)
    drain(ws[actor]), drain(ws[other])
    assert room.version == after_first, "a replayed request must not advance state"
    assert len(room.match.power_removed) == removed_first, \
        "a replayed 3/Joker must not be spent twice"


def test_one_players_refresh_does_not_disturb_the_other(live):
    base, store = live
    room, actor, ws, _, _ = seated_match(base, store)
    other = 1 - actor
    before = states(drain(ws[other]))          # clear the pipe
    version_before = room.version
    sync(ws[actor])
    # the other seat receives nothing and the room is untouched
    assert not states(drain(ws[other], 0.3)), \
        "a refresh must not broadcast to the rest of the table"
    assert room.version == version_before
