"""Owner service-management records are private, persistent and game-independent."""
from fastapi.testclient import TestClient
from server.app.main import create_app
from server.tests.test_owner_analytics import auth

ORIGIN = "https://play.shithead.games"


def test_incident_problem_change_lifecycle_and_persistence(monkeypatch, tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD", "a-strong-test-secret")
    for key in ("SHITHEAD_GOOGLE_CLIENT_ID", "SHITHEAD_OWNER_EMAIL",
                "SHITHEAD_ADMIN_SESSION_SECRET"):
        monkeypatch.delenv(key, raising=False)
    db = tmp_path / "rooms.sqlite3"
    with TestClient(create_app(db_path=db), base_url=ORIGIN) as client:
        # No guest-facing tools, no unauthenticated writes or reads.
        assert client.get("/owner/api/operations").status_code == 401
        assert client.post("/owner/api/operations", json={
            "kind": "incident", "title": "Denied"}).status_code == 401
        assert client.post("/owner/api/operations", headers=auth(), json={
            "kind": "incident", "title": "Wrong origin"}).status_code == 403
        assert client.get("/").status_code == 200
        created = {}
        for kind, title in (("incident", "Room unavailable"),
                            ("problem", "Repeat slot saturation"),
                            ("change", "Deploy capacity notice")):
            result = client.post("/owner/api/operations", headers={
                **auth(), "Origin": ORIGIN}, json={
                    "kind": kind, "title": title, "description": "Owner note"})
            assert result.status_code == 201
            created[kind] = result.json()
            assert result.json()["reference"].startswith({
                "incident": "INC-", "problem": "PRB-", "change": "CHG-"}[kind])
        records = client.get("/owner/api/operations", headers=auth()).json()["records"]
        assert len(records) == 3
        assert {r["kind"] for r in records} == {"incident", "problem", "change"}
        assert "Incidents" in client.get("/owner/analytics", headers=auth()).text
        assert "Problems" in client.get("/owner/analytics", headers=auth()).text
        assert "Changes" in client.get("/owner/analytics", headers=auth()).text
        for kind, status in (("incident", "resolved"),
                             ("problem", "known_error"),
                             ("change", "completed")):
            result = client.post(
                f"/owner/api/operations/{created[kind]['id']}/status",
                headers={**auth(), "Origin": ORIGIN}, json={"status": status})
            assert result.status_code == 200
            assert result.json()["status"] == status
        assert client.post(
            f"/owner/api/operations/{created['incident']['id']}/status",
            headers={**auth(), "Origin": ORIGIN},
            json={"status": "completed"}).status_code == 422
        assert client.post("/owner/api/operations", headers={
            **auth(), "Origin": ORIGIN}, json={
                "kind": "change", "title": " "}).status_code == 422
        assert client.post("/owner/api/operations", headers={
            **auth(), "Origin": ORIGIN}, json={
                "kind": "change", "title": "x" * 130}).status_code == 422
        assert client.get("/owner/api/analytics", headers=auth()).status_code == 200
    with TestClient(create_app(db_path=db), base_url=ORIGIN) as restored:
        records = restored.get("/owner/api/operations", headers=auth()).json()["records"]
        assert len(records) == 3
        assert {r["status"] for r in records} == {
            "resolved", "known_error", "completed"}


def test_ops_records_do_not_require_players_to_sign_in(monkeypatch, tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD", "a-strong-test-secret")
    with TestClient(create_app(db_path=tmp_path / "games.db"),
                    base_url=ORIGIN) as client:
        assert client.post("/api/rooms", json={
            "name": "Guest", "capacity": 2, "game_type": "ludo"}).status_code == 201
        assert client.get("/owner/api/operations").status_code == 401
