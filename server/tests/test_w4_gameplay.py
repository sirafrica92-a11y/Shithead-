"""W4 match integration: deck integrity, hidden information, action boundaries."""
import pytest
from fastapi.testclient import TestClient

from server.app.gameplay import (
    apply_match_action, assert_card_conservation, make_match,
    private_match_view, public_match_view,
)
from server.app.rules.ordinary import IllegalPlay
from server.app.main import create_app


@pytest.mark.parametrize("n", range(2, 7))
def test_deal_card_conservation_and_private_views(n):
    match = make_match(n, seed=4)
    assert_card_conservation(match)
    assert len(match.state.players) == n
    assert all(len(p.hand) == len(p.face_up) == len(p.face_down) == 3 for p in match.state.players)
    public = public_match_view(match)
    assert all("hand" not in p for p in public["players"])
    assert "hand" not in public
    for seat in range(n):
        private = private_match_view(match, seat)
        assert len(private["hand"]) == 3
        assert private["you"] == seat


def test_out_of_turn_action_is_rejected_without_state_change():
    match = make_match(2, seed=42)
    with pytest.raises(IllegalPlay):
        apply_match_action(match, 1 - match.state.current, "pickup")
    assert_card_conservation(match)


def test_empty_pile_power_skips_next_player_and_removes_card():
    from dataclasses import replace
    from server.app.rules.ordinary import Card, PlayerState
    match = make_match(2, seed=5)
    players = list(match.state.players)
    original = players[0].hand[0]
    player = players[0]
    # Reconfigure the first player's card while preserving the physical card ID
    players[0] = replace(player, hand=(replace(original, rank=3),) + player.hand[1:])
    # Conservation still checks IDs; this is a test fixture, not a live deck.
    match = replace(match, state=replace(match.state, players=tuple(players)))
    updated = apply_match_action(match, 0, "power", index=0)
    assert updated.state.current == 0
    assert len(updated.power_removed) == 1
    assert updated.pending is None
    assert len(updated.state.players[0].hand) == 3  # refilled from stock


def test_ordinary_action_consumes_owned_card_and_preserves_count():
    match = make_match(2, seed=3)
    st = match.state
    # Use an ordinary card available in the starting hand.
    indices = [i for i, card in enumerate(st.players[0].hand) if card.rank not in (0, 3)]
    if not indices:
        pytest.skip("seed unexpectedly dealt only powers")
    updated = apply_match_action(match, 0, "play", indices=[indices[0]])
    assert_card_conservation(updated)
    assert len(updated.state.pile) in (0, 1)


def test_websocket_match_starts_only_when_both_ready_and_hidden_hands():
    with TestClient(create_app()) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        ta = client.post(f"/api/rooms/{room}/join", json={"name": "A"}).json()["token"]
        tb = client.post(f"/api/rooms/{room}/join", json={"name": "B"}).json()["token"]
        with client.websocket_connect(f"/ws/{room}") as a:
            a.send_json({"type": "auth", "token": ta})
            va = a.receive_json()
            with client.websocket_connect(f"/ws/{room}") as b:
                b.send_json({"type": "auth", "token": tb})
                vb = b.receive_json()
                va = a.receive_json()  # B connected update
                a.send_json({"type": "ready", "ready": True, "expected_version": va["version"], "request_id": "r-a"})
                va = a.receive_json()
                vb = b.receive_json()
                assert va["phase"] == "LOBBY"
                b.send_json({"type": "ready", "ready": True, "expected_version": vb["version"], "request_id": "r-b"})
                va = a.receive_json()
                vb = b.receive_json()
                assert va["phase"] == vb["phase"] == "PLAYING"
                assert va["game"]["you"] == 0 and vb["game"]["you"] == 1
                assert len(va["game"]["hand"]) == len(vb["game"]["hand"]) == 3
                assert "hand" not in client.get(f"/api/rooms/{room}").json()["game"]
                assert all("hand" not in p for p in client.get(f"/api/rooms/{room}").json()["game"]["players"])
