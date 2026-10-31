"""Social-first navigation and server-authoritative visible CPU turns.

These tests extend (never replace) the complete six-game regression suite.
"""
from dataclasses import replace

from fastapi.testclient import TestClient

from server.app import solo_ludo, solo_awale
from server.app.ludo import make_ludo_match
from server.app.awale import make_awale_match
from server.app.main import create_app


def test_choice_and_setup_are_separate_views(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        response = c.get("/")
        assert response.status_code == 200
        html = response.text
        home_start = html.index('<section id="screen-home"')
        setup_start = html.index('<section id="screen-setup"')
        lobby_start = html.index('<section id="screen-lobby"')
        assert home_start < setup_start < lobby_start
        home = html[home_start:setup_start]
        setup = html[setup_start:lobby_start]
        for game in ("shithead", "ludo", "awale", "dara", "yote", "dominoes"):
            assert f'data-game="{game}"' in home
        assert 'id="name"' not in home
        assert 'id="go-create"' not in home
        assert 'id="go-join"' not in home
        for element in ("setup-game-name", "setup-back", "name", "go-create", "go-join",
                        "create-panel", "join-panel", "capacity", "domino-home-mode"):
            assert f'id="{element}"' in setup
        js = c.get("/client.js").text
        assert 'show("screen-setup")' in js
        assert 'el("setup-game-name").textContent' in js
        assert 'el("setup-back").onclick' in js
        assert 'game_type: chosenGame' in js
        assert 'return_lobby' in js


def test_ludo_cpu_trace_records_real_ordered_engine_states_and_no_resume_replay(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        first = c.post("/api/solo/ludo").json()
        key = first["id"]
        sess = solo_ludo._sessions[key]
        sess.match = replace(make_ludo_match(2, seed=9), actor=1)
        before = sess.version
        response = c.post(f"/api/solo/ludo/{key}/reset", json={
            "token": first["token"], "version": before,
        })
        assert response.status_code == 200
        # Force a computer turn after reset to test its sequence without relying on random starter.
        sess.match = replace(make_ludo_match(2, seed=9), actor=1)
        solo_ludo._bot_play(sess)
        steps = sess.action_trace
        assert steps
        assert all(step["message"].startswith("Computer ") for step in steps)
        assert any("rolled" in step["message"] for step in steps)
        assert steps[-1]["game"] == solo_ludo.private_ludo_view(sess.match, 0)
        resumed = c.get(f"/api/solo/ludo/{key}",
                        headers={"X-Solo-Token": first["token"]})
        assert resumed.status_code == 200
        assert resumed.json()["computer_actions"] == []


def test_awale_cpu_trace_discloses_legal_sowing_and_no_resume_replay(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        first = c.post("/api/solo/awale").json()
        key = first["id"]
        sess = solo_awale._sessions[key]
        sess.match = replace(make_awale_match(seed=9), actor=1)
        before = sess.match
        legal = solo_awale.legal_awale_pits(before, 1)
        solo_awale._computer_reply(sess)
        steps = sess.action_trace
        assert len(steps) == 1
        assert any(f"house {pit+1}" in steps[0]["message"] for pit in legal)
        assert "sowed" in steps[0]["message"]
        assert steps[-1]["game"] == solo_awale.private_awale_view(sess.match, 0)
        assert sum(sess.match.pits) + sum(sess.match.captured) == 48
        response = c.get(f"/api/solo/awale/{key}",
                         headers={"X-Solo-Token": first["token"]})
        assert response.status_code == 200
        assert response.json()["computer_actions"] == []
        assert not c.app.state.room_store.rooms


def test_all_six_multiplayer_games_still_create_and_join(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        for name, capacity in (("shithead", 2), ("ludo", 2), ("awale", 2),
                               ("dara", 2), ("yote", 2), ("dominoes", 4)):
            created = c.post("/api/rooms", json={
                "name": "Host", "capacity": capacity, "game_type": name,
            })
            assert created.status_code == 201, (name, created.text)
            room = created.json()["room_id"]
            joined = c.post(f"/api/rooms/{room}/join", json={"name": "Friend"})
            assert joined.status_code == 201
            assert c.get(f"/api/rooms/{room}").json()["game_type"] == name
        assert len(c.app.state.room_store.rooms) == 6

def test_cpu_playback_is_accessible_and_cannot_play_cpu_from_browser(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        for name in ("ludo", "awale"):
            html = c.get(f"/solo/{name}").text
            js = c.get(f"/solo/{name}.js").text
            assert 'id="cpu-log"' in html
            assert 'id="skip-cpu"' in html
            assert 'aria-live="polite"' in html
            assert "await showComputerTurns" in js
            assert "computer_actions" in js
            assert "displayFrame=step.game" in js
            assert "session={...session" in js
            assert 'if(!session||busy)return' in js
            # Human API actions remain authorised; CPU steps are display-only.
            assert 'showComputerTurns' in js
            assert "skip.classList.add" in js


def test_new_home_keeps_multiplayer_primary_and_original_brand(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        html=c.get("/").text
        assert 'src="/brand/shithead-logo.png"' in html
        assert 'id="go-create"' in html
        assert 'id="go-join"' in html
        assert html.count('id="screen-setup"') == 1
        assert html.count('id="screen-home"') == 1
        start=html.index('<section id="screen-home"')
        end=html.index('<section id="screen-setup"')
        assert 'Solo Play · Ludo' not in html[start:end]
        assert 'Solo Play · Awalé' not in html[start:end]
