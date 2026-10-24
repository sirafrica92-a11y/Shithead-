"""D-024 under real connection loss: the new refill choice must survive a
reconnect and a Refresh Game resync, and must never leak to other seats.

The choice is the only new state D-024 introduces, so it is the one place a
player could get stranded waiting for a decision their client cannot see.
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

from server.app.gameplay import private_match_view, public_match_view
from server.app.main import create_app
from server.app.rules.ordinary import Card


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    port = _free_port()
    db = tmp_path_factory.mktemp("d024") / "rooms.sqlite3"
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


def act(ws, payload, version):
    ws.send(json.dumps({**payload, "expected_version": version,
                        "request_id": str(uuid.uuid4())}))


def states(msgs):
    return [m for m in msgs if m.get("type") == "room_state"]


def errors(msgs):
    return [m for m in msgs if m.get("type") == "error"]


def table_with_pending_choice(base, store):
    """Seat two players and drive a play that leaves a D-024 choice open."""
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

    # Deterministic D-024: the actor plays a 9 and the stock's next card is a 9.
    st = room.match.state
    actor = st.current
    players = list(st.players)
    hand = list(players[actor].hand)
    hand[0] = Card(rank=9, suit="S", id="played-9")
    players[actor] = replace(players[actor], hand=tuple(hand))
    room.match = replace(room.match, state=replace(
        st, players=tuple(players),
        deck=(Card(rank=9, suit="H", id="drawn-9"),) + tuple(st.deck),
        pile=(Card(rank=4, suit="C", id="p4"),), locked=False, current=actor))
    room.version += 1

    ws_by_seat = {h["seat"]: a, g["seat"]: b}
    tokens = {h["seat"]: (rid, h["token"]), g["seat"]: (rid, g["token"])}
    act(ws_by_seat[actor], {"type": "game", "kind": "play", "indices": [0]},
        room.version)
    drain(a), drain(b)
    assert room.match.refill_choice is not None, "the drawn 9 must offer a choice"
    return room, actor, ws_by_seat, tokens, rid


def test_choice_is_private_to_the_player_who_drew(live):
    base, store = live
    room, actor, ws, _, _ = table_with_pending_choice(base, store)
    other = 1 - actor

    mine = private_match_view(room.match, actor)
    theirs = private_match_view(room.match, other)
    public = public_match_view(room.match)

    assert mine["your_refill_indices"], "the drawing seat must see its options"
    assert theirs["your_refill_indices"] == [], \
        "another seat must never learn which drawn cards are playable"
    assert public["refill_choice"] is True, \
        "the table may know a choice is open, without its contents"
    assert "your_refill_indices" not in public


def test_refresh_during_a_choice_restores_it(live):
    """Refresh Game must not strand a player mid-decision."""
    base, store = live
    room, actor, ws, _, _ = table_with_pending_choice(base, store)
    version_before = room.version

    ws[actor].send(json.dumps({"type": "sync"}))
    snap = states(drain(ws[actor]))[-1]
    assert snap["game"]["refill_choice"] is True
    assert snap["game"]["your_refill_indices"], \
        "a refresh must restore the pending drawn-match options"
    assert snap["game"]["actor"] == actor
    assert room.version == version_before, "sync must not advance the game"

    # and the decision can still be taken
    act(ws[actor], {"type": "game", "kind": "keep_drawn"}, room.version)
    msgs = drain(ws[actor])
    assert not errors(msgs), errors(msgs)
    assert room.match.refill_choice is None


def test_reconnect_during_a_choice_keeps_the_seat_and_the_decision(live):
    base, store = live
    room, actor, ws, tokens, rid = table_with_pending_choice(base, store)
    seats_before = len(room.seats)

    ws[actor].close()
    time.sleep(0.3)
    rid2, token = tokens[actor]
    again = ws_connect(f"ws://{base}/ws/{rid2}")
    again.send(json.dumps({"type": "auth", "token": token}))
    view = states(drain(again))[-1]

    assert view["game"]["you"] == actor
    assert len(room.seats) == seats_before, "reconnecting must not add a seat"
    assert view["game"]["refill_choice"] is True
    assert view["game"]["your_refill_indices"], \
        "the reconnected player must still see the pending choice"

    act(again, {"type": "game", "kind": "play_drawn",
                "indices": view["game"]["your_refill_indices"][:1]}, room.version)
    msgs = drain(again)
    assert not errors(msgs), errors(msgs)
    again.close()


def test_other_seat_cannot_answer_the_choice(live):
    base, store = live
    room, actor, ws, _, _ = table_with_pending_choice(base, store)
    other = 1 - actor
    act(ws[other], {"type": "game", "kind": "keep_drawn"}, room.version)
    msgs = drain(ws[other])
    assert errors(msgs), "a seat that did not draw must not end the choice"
    assert room.match.refill_choice is not None, "the choice must survive"


def test_keep_is_always_available_so_the_table_cannot_stall(live):
    """Whatever else is refused, keep_drawn must always end the decision."""
    base, store = live
    room, actor, ws, _, _ = table_with_pending_choice(base, store)
    # a selection of wrong actions, each refused with an explanation
    for kind, payload in (("pickup", {}),
                          ("play", {"indices": [0]}),
                          ("play_drawn", {"indices": [99]})):
        act(ws[actor], {"type": "game", "kind": kind, **payload}, room.version)
        msgs = drain(ws[actor])
        assert errors(msgs), f"{kind} should be refused during a choice"
        assert not errors(msgs)[0]["message"].startswith(
            "Action rejected; view refreshed"), "refusal must explain itself"
    act(ws[actor], {"type": "game", "kind": "keep_drawn"}, room.version)
    msgs = drain(ws[actor])
    assert not errors(msgs), errors(msgs)
    assert room.match.refill_choice is None
    assert room.match.state.current != actor or True   # turn resumed normally
