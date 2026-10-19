"""End-to-end two-player match over real WebSockets against a real uvicorn.

This is the playtest Africa and Bardia will run, driven in code: host creates
and is seated in one press, friend joins with the code, both ready up, the
match starts, each sees only their own cards, a turn is played, and a dropped
player reconnects onto the same seat without losing it.
"""
import contextlib
import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn
from websockets.sync.client import connect as ws_connect

from server.app.main import create_app


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    port = _free_port()
    db = tmp_path_factory.mktemp("play") / "rooms.sqlite3"
    server = uvicorn.Server(uvicorn.Config(
        create_app(db_path=db), host="127.0.0.1", port=port, log_level="warning",
    ))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    while not server.started:
        if time.monotonic() > deadline or not thread.is_alive():
            server.should_exit = True
            raise RuntimeError("uvicorn did not start")
        time.sleep(0.05)
    yield f"127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


def drain(ws, timeout=0.4):
    """Swallow queued broadcasts so the next read is the one we asked for."""
    last = None
    while True:
        try:
            last = json.loads(ws.recv(timeout=timeout))
        except TimeoutError:
            return last


def fresh(ws):
    """The authoritative current view for this seat, with its live version."""
    drain(ws)
    ws.send(json.dumps({"type": "sync"}))
    return json.loads(ws.recv(timeout=5))


def act(ws, payload, version):
    ws.send(json.dumps({**payload, "expected_version": version,
                        "request_id": f"t-{time.monotonic_ns()}"}))
    return json.loads(ws.recv(timeout=5))


def open_seat(stack, live, room, token):
    ws = stack.enter_context(ws_connect(f"ws://{live}/ws/{room}"))
    ws.send(json.dumps({"type": "auth", "token": token}))
    return ws, json.loads(ws.recv(timeout=5))


def test_two_players_create_join_ready_play_and_reconnect(live):
    base = f"http://{live}"
    stack = contextlib.ExitStack()

    # 1. Host enters a name and presses Create room: one request, already seated.
    created = httpx.post(f"{base}/api/rooms",
                         json={"capacity": 2, "name": "Africa"}).json()
    room, host_token = created["room_id"], created["token"]
    assert created["seat"] == 0
    assert len(room) == 4 and room.isupper()

    # 2. Friend enters a name and the code and presses Join once.
    guest = httpx.post(f"{base}/api/rooms/{room}/join", json={"name": "Bardia"}).json()
    assert guest["seat"] == 1
    assert guest["token"] != host_token

    ws0, view0 = open_seat(stack, live, room, host_token)
    ws1, view1 = open_seat(stack, live, room, guest["token"])
    assert view0["you"] == 0 and view1["you"] == 1
    names = [p["name"] for p in fresh(ws0)["players"]]
    assert names == ["Africa", "Bardia"]

    # 3. Both ready up until a match starts (a D-019 start tie resets readiness).
    for _ in range(8):
        state0 = fresh(ws0)
        if state0.get("game"):
            break
        if not state0["players"][0]["ready"]:
            act(ws0, {"type": "ready", "ready": True}, state0["version"])
        state1 = fresh(ws1)
        if state1.get("game"):
            break
        if not state1["players"][1]["ready"]:
            act(ws1, {"type": "ready", "ready": True}, state1["version"])
    started = fresh(ws0)
    assert started.get("game"), "two ready players did not start a match"

    # 4. Each player sees their own cards and never the opponent's hand.
    a, b = fresh(ws0)["game"], fresh(ws1)["game"]
    assert a["hand"] and b["hand"], "a seated player cannot see their own cards"
    assert a["hand"] != b["hand"]
    assert "hand" not in a["players"][1] and "hand" not in b["players"][0]
    assert all("hand" not in p for p in a["players"])  # only counts are public

    # 5. The player to act takes a real turn.
    state = fresh(ws0)
    actor = state["game"]["actor"]
    ws = ws0 if actor == 0 else ws1
    view = fresh(ws)
    before = view["version"]
    for indices in ([i] for i in range(len(view["game"]["hand"]))):
        reply = act(ws, {"type": "game", "kind": "play", "indices": indices}, before)
        if reply.get("type") != "error":
            break
        before = reply["stateSnapshot"]["version"]
    else:
        reply = act(ws, {"type": "game", "kind": "pickup"}, before)
    assert reply.get("type") != "error", f"no legal action available: {reply}"
    assert fresh(ws)["version"] > state["version"], "a played turn did not advance state"

    # 6. A dropped player reconnects onto the same seat, mid-match.
    ws1.close()
    time.sleep(0.2)
    ws1b, restored = open_seat(stack, live, room, guest["token"])
    assert restored["you"] == 1, "reconnect landed on a different seat"
    assert restored.get("game"), "match state lost on reconnect"
    assert restored["game"]["hand"], "own cards lost on reconnect"
    assert len(httpx.get(f"{base}/api/rooms/{room}").json()["players"]) == 2

    stack.close()
