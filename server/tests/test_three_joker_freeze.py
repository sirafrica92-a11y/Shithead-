"""Regressions for the reported "3/Joker freezes the game" defect.

The engine was never stuck: a refused 3/Joker came back as a generic
"Action rejected" with no reason, and the table offered presses that could not
succeed, so the player had nothing to act on and the game looked frozen.

These tests drive a real uvicorn over real WebSockets, because the defect lived
in what the player is told, not in the reducers.
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

from server.app.gameplay import apply_match_action, private_match_view
from server.app.main import create_app
from server.app.rules.ordinary import Card, IllegalPlay


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    """Real server; the app object is kept so a scenario can be injected."""
    port = _free_port()
    db = tmp_path_factory.mktemp("freeze") / "rooms.sqlite3"
    app = create_app(db_path=db)
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning",
    ))
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


def drain(ws, timeout=0.6):
    out = []
    while True:
        try:
            out.append(json.loads(ws.recv(timeout=timeout)))
        except (TimeoutError, Exception):
            return out


def act(ws, payload, version):
    ws.send(json.dumps({**payload, "expected_version": version,
                        "request_id": str(uuid.uuid4())}))


def errors(msgs):
    return [m for m in msgs if m.get("type") == "error"]


def states(msgs):
    return [m for m in msgs if m.get("type") == "room_state"]


def start_match(base, store, *, pile, locked, joker_in_hand=True):
    """Seat two players, start the match, then inject a deterministic scenario."""
    h = httpx.post(f"http://{base}/api/rooms",
                   json={"capacity": 2, "name": "Africa"}).json()
    g = httpx.post(f"http://{base}/api/rooms/{h['room_id']}/join",
                   json={"name": "Bardia"}).json()
    room_id = h["room_id"]
    a = ws_connect(f"ws://{base}/ws/{room_id}")
    b = ws_connect(f"ws://{base}/ws/{room_id}")
    a.send(json.dumps({"type": "auth", "token": h["token"]}))
    b.send(json.dumps({"type": "auth", "token": g["token"]}))
    drain(a), drain(b)
    room = store.rooms[room_id]
    act(a, {"type": "ready", "ready": True}, room.version)
    drain(a), drain(b)
    act(b, {"type": "ready", "ready": True}, room.version)
    drain(a), drain(b)
    assert room.match is not None

    st = room.match.state
    actor = st.current
    players = list(st.players)
    if joker_in_hand:
        hand = list(players[actor].hand)
        hand[0] = Card(rank=0, suit="J", id="joker-under-test")
        players[actor] = replace(players[actor], hand=tuple(hand))
    room.match = replace(room.match, state=replace(
        st, players=tuple(players), pile=tuple(pile), locked=locked, current=actor))
    room.version += 1
    ws_actor = a if actor == h["seat"] else b
    ws_other = b if actor == h["seat"] else a
    return room, actor, ws_actor, ws_other


def test_refused_joker_explains_what_is_missing(live):
    """The defect: pressing the power with no opponent chosen said nothing useful."""
    base, store = live
    room, actor, ws_actor, ws_other = start_match(
        base, store, pile=[Card(rank=7, suit="H", id="p7")], locked=True)

    act(ws_actor, {"type": "game", "kind": "power", "index": 0,
                   "indices": [0], "target": None}, room.version)
    got = errors(drain(ws_actor))
    assert got, "a refused 3/Joker must tell the player something"
    message = got[0]["message"]
    assert got[0]["reasonCode"] == "illegal_action"
    assert "target" in message.lower(), message
    assert "Action rejected; view refreshed" not in message
    # and the player is still able to act: the game is not stuck
    assert got[0]["stateSnapshot"]["game"]["actor"] == actor
    ws_actor.close(), ws_other.close()


def test_seven_lock_never_blocks_a_joker_over_the_wire(live):
    """D-021 end to end: the lock in the screenshot was never the cause."""
    base, store = live
    room, actor, ws_actor, ws_other = start_match(
        base, store, pile=[Card(rank=7, suit="H", id="p7")], locked=True)
    other = 1 - actor

    act(ws_actor, {"type": "game", "kind": "power", "index": 0,
                   "indices": [0], "target": other}, room.version)
    mine, theirs = drain(ws_actor), drain(ws_other)
    assert not errors(mine), errors(mine)
    assert states(mine) and states(theirs), "both seats must see the attack"
    assert states(theirs)[-1]["game"]["phase"] == "PILE_PASS_DECISION"
    assert states(theirs)[-1]["game"]["actor"] == other

    act(ws_other, {"type": "game", "kind": "accept"}, room.version)
    after = drain(ws_other)
    assert not errors(after), errors(after)
    assert room.match.state.locked is False, "accepting the pile clears the lock"
    assert room.match.pending is None
    ws_actor.close(), ws_other.close()


def test_target_is_still_required_and_named(live):
    """Counter with no card selected is refused with an actionable reason."""
    base, store = live
    room, actor, ws_actor, ws_other = start_match(
        base, store, pile=[Card(rank=9, suit="S", id="p9")], locked=False)
    other = 1 - actor
    act(ws_actor, {"type": "game", "kind": "power", "index": 0,
                   "indices": [0], "target": other}, room.version)
    drain(ws_actor), drain(ws_other)

    act(ws_other, {"type": "game", "kind": "counter", "index": None,
                   "target": actor}, room.version)
    got = errors(drain(ws_other))
    assert got, "a refused counter must explain itself"
    assert "Action rejected; view refreshed" not in got[0]["message"]
    assert got[0]["stateSnapshot"]["game"]["phase"] == "PILE_PASS_DECISION", \
        "a refused counter must leave the decision open, not strand the table"
    ws_actor.close(), ws_other.close()


# --- the blind-power trap, asserted against the rule contract -----------------

def blind_power_match(seed=1):
    from server.app.gameplay import make_match
    m = make_match(2, seed=seed)
    st = m.state
    actor = st.current
    players = list(st.players)
    face_down = list(players[actor].face_down)
    face_down[0] = Card(rank=0, suit="J", id="blind-joker")
    players[actor] = replace(players[actor], hand=(), face_up=(),
                             face_down=tuple(face_down))
    m = replace(m, state=replace(st, players=tuple(players), deck=(),
                                 pile=(Card(rank=9, suit="S", id="x"),),
                                 current=actor))
    return apply_match_action(m, actor, "flip", index=0), actor


def test_blind_power_is_the_committed_card_so_no_selection_is_allowed():
    """client.js used to leave the face-down cards tappable here, and any tap
    made this action impossible. The server contract the UI must respect."""
    match, actor = blind_power_match()
    view = private_match_view(match, actor)
    assert view["your_blind_power"] is not None
    assert view["your_zone"] == "face_down"

    with pytest.raises(IllegalPlay, match="exactly one committed card"):
        apply_match_action(match, actor, "power", index=0, indices=[0],
                           target=1 - actor)

    resolved = apply_match_action(match, actor, "power", index=None,
                                  indices=[], target=1 - actor)
    assert resolved.pending is not None, "the blind 3/Joker must open the attack"


def test_blind_power_without_a_target_names_the_target():
    match, actor = blind_power_match()
    with pytest.raises(IllegalPlay, match="target"):
        apply_match_action(match, actor, "power", index=None, indices=[],
                           target=None)


def test_client_does_not_offer_selection_during_a_blind_power():
    """Guards the client fix itself: the face-down zone must not be live while a
    blind 3/Joker is pending."""
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "app" / "static" / "client.js").read_text(encoding="utf-8")
    assert '&& !g.your_blind_power,\n             "face_down"' in source, \
        "the face-down zone must stop being selectable once a blind power is revealed"
