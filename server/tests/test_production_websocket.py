"""Real-server WebSocket checks.

The rest of the suite drives the app through Starlette's TestClient, which
carries WebSocket frames in-process and therefore passes even when the
deployed server cannot speak WebSocket at all. That is exactly how production
reached "No supported WebSocket library detected" with 404s on /ws/{room_id}
while CI was green. These tests boot uvicorn and connect over a real socket.
"""
import importlib
import json
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from websockets.sync.client import connect as ws_connect

from server.app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """A real uvicorn process-in-thread, as Railway runs it."""
    port = _free_port()
    db = tmp_path_factory.mktemp("live") / "rooms.sqlite3"
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


def test_a_websocket_library_is_installed():
    """uvicorn serves /ws/* only when websockets or wsproto is importable."""
    assert any(importlib.util.find_spec(name) for name in ("websockets", "wsproto")), (
        "uvicorn has no WebSocket implementation; install uvicorn[standard]"
    )


def test_requirements_install_websocket_support():
    text = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert ("uvicorn[standard]" in text or "websockets" in text or "wsproto" in text), (
        "requirements.txt installs uvicorn without WebSocket extras"
    )


def test_real_websocket_handshake_and_gameplay_message(live_server):
    base = f"http://{live_server}"
    room = httpx.post(f"{base}/api/rooms", json={"capacity": 2}).json()["room_id"]
    token = httpx.post(f"{base}/api/rooms/{room}/join", json={"name": "A"}).json()["token"]
    httpx.post(f"{base}/api/rooms/{room}/join", json={"name": "B"})

    with ws_connect(f"ws://{live_server}/ws/{room}") as ws:
        ws.send(json.dumps({"type": "auth", "token": token}))
        snapshot = json.loads(ws.recv())
        assert snapshot["type"] == "room_state"
        assert snapshot["you"] == 0
        ws.send(json.dumps({
            "type": "ready", "ready": True,
            "expected_version": snapshot["version"], "request_id": "live-1",
        }))
        updated = json.loads(ws.recv())
        assert updated["players"][0]["ready"] is True


def test_reconnecting_after_an_interruption_restores_the_same_seat(live_server):
    base = f"http://{live_server}"
    room = httpx.post(f"{base}/api/rooms", json={"capacity": 2}).json()["room_id"]
    token = httpx.post(f"{base}/api/rooms/{room}/join", json={"name": "A"}).json()["token"]

    with ws_connect(f"ws://{live_server}/ws/{room}") as ws:
        ws.send(json.dumps({"type": "auth", "token": token}))
        first = json.loads(ws.recv())
        ws.send(json.dumps({
            "type": "ready", "ready": True,
            "expected_version": first["version"], "request_id": "before-drop",
        }))
        json.loads(ws.recv())
    # Socket dropped, as a phone leaving a tunnel would.

    with ws_connect(f"ws://{live_server}/ws/{room}") as ws:
        ws.send(json.dumps({"type": "auth", "token": token}))
        restored = json.loads(ws.recv())
        assert restored["you"] == 0
        assert restored["players"][0]["ready"] is True, "seat state lost on reconnect"

    # Reconnecting must not consume a second seat.
    assert len(httpx.get(f"{base}/api/rooms/{room}").json()["players"]) == 1


def test_unknown_room_code_is_refused_over_a_real_socket(live_server):
    with pytest.raises(Exception):
        with ws_connect(f"ws://{live_server}/ws/ZZZZ") as ws:
            ws.recv()
