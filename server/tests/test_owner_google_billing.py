"""Only one Google account may access owner analytics; guests remain guests."""
import re
from fastapi.testclient import TestClient
from server.app.main import create_app

ORIGIN = "https://play.shithead.games"
EMAIL = "sirafrica92@gmail.com"


def configure(monkeypatch):
    monkeypatch.setenv("SHITHEAD_GOOGLE_CLIENT_ID", "owner-project.apps.googleusercontent.com")
    monkeypatch.setenv("SHITHEAD_OWNER_EMAIL", EMAIL)
    monkeypatch.setenv("SHITHEAD_ADMIN_SESSION_SECRET", "x" * 48)
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD", "old-legacy-password-should-not-bypass")


def test_google_owner_auth_denial_and_verified_session(monkeypatch, tmp_path):
    configure(monkeypatch)

    async def verify(credential, client_id):
        assert credential == "credible_token" * 4
        assert client_id == "owner-project.apps.googleusercontent.com"
        return dict(sub="google-sub-123", email=EMAIL, email_verified=True,
                    nonce=seen["nonce"])
    seen = {}
    monkeypatch.setattr("server.app.main.verify_google_token", verify)
    with TestClient(create_app(db_path=tmp_path/"game.sqlite3"),
                    base_url=ORIGIN) as client:
        # Everything used by players remains free of sign-in requirements.
        assert client.get("/").status_code == 200
        assert client.post("/api/rooms", json={"name":"Host","game_type":"awale","capacity":2}).status_code == 201
        # Owner endpoints are NOT accessible via legacy HTTP Basic.
        import base64
        legacy = base64.b64encode(b"owner:old-legacy-password-should-not-bypass").decode()
        assert client.get("/owner/api/analytics", headers={"Authorization":"Basic "+legacy}).status_code == 401
        assert client.get("/owner/analytics").status_code == 401
        signin = client.get("/owner/login")
        assert signin.status_code == 200
        assert "owner-project.apps.googleusercontent.com" in signin.text
        assert "sirafrica92@gmail.com" not in signin.text
        nonce = re.search(r'data-nonce="([^"]+)"', signin.text).group(1)
        seen["nonce"] = nonce
        assert client.get("/owner/login.js").status_code == 200
        headers = {"Origin": ORIGIN, "X-Owner-Login-Nonce": nonce}
        assert client.post("/owner/session", json={"credential":"credible_token"*4},
                           headers={"X-Owner-Login-Nonce":nonce,"Origin":"https://evil.example"}).status_code == 403
        assert client.post("/owner/session", json={"credential":"credible_token"*4},
                           headers=headers).status_code == 200
        assert client.get("/owner/analytics").status_code == 200
        assert client.get("/owner/api/analytics").status_code == 200
        assert client.get("/owner/api/analytics.csv").status_code == 200
        assert client.post("/owner/logout", headers={"Origin":"https://evil.example"}).status_code == 403
        assert client.post("/owner/logout", headers={"Origin":ORIGIN}).status_code == 200
        assert client.get("/owner/api/analytics").status_code == 401


def test_google_email_and_nonce_required(monkeypatch, tmp_path):
    configure(monkeypatch)
    current = {"email":"other@example.com", "nonce":None, "verified":True}

    async def verify(credential, client_id):
        return {"sub":"other-sub", "email":current["email"],
                "email_verified":current["verified"],"nonce":current["nonce"]}
    monkeypatch.setattr("server.app.main.verify_google_token", verify)
    with TestClient(create_app(db_path=tmp_path/"rooms.db"),base_url=ORIGIN) as client:
        nonce=re.search(r'data-nonce="([^"]+)"',client.get("/owner/login").text).group(1)
        headers={"Origin":ORIGIN,"X-Owner-Login-Nonce":nonce}
        current["nonce"]=nonce
        assert client.post("/owner/session",headers=headers,json={"credential":"x"*40}).status_code==403
        current["email"]=EMAIL
        current["verified"]=False
        assert client.post("/owner/session",headers=headers,json={"credential":"x"*40}).status_code==403
        current["verified"]=True
        current["nonce"]="wrong-nonce"
        assert client.post("/owner/session",headers=headers,json={"credential":"x"*40}).status_code==403
        assert client.get("/owner/api/analytics").status_code==401


def test_billing_metadata_manual_and_unsupplied(monkeypatch, tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD","a-strong-test-secret")
    for key in ("SHITHEAD_GOOGLE_CLIENT_ID","SHITHEAD_OWNER_EMAIL","SHITHEAD_ADMIN_SESSION_SECRET",
                "SHITHEAD_RAILWAY_NEXT_DUE_DATE","SHITHEAD_RAILWAY_USAGE_USD","SHITHEAD_RAILWAY_BUDGET_USD"):
        monkeypatch.delenv(key, raising=False)
    from server.tests.test_owner_analytics import auth
    with TestClient(create_app(db_path=tmp_path/"absent.db")) as app:
        assert app.get("/owner/api/analytics",headers=auth()).json()["billing"]["next_due_date"] is None
        assert app.get("/owner/api/analytics",headers=auth()).json()["billing"]["estimated_usage_usd"] is None
    monkeypatch.setenv("SHITHEAD_RAILWAY_NEXT_DUE_DATE","2026-11-15")
    monkeypatch.setenv("SHITHEAD_RAILWAY_USAGE_USD","8.75")
    monkeypatch.setenv("SHITHEAD_RAILWAY_BUDGET_USD","41")
    with TestClient(create_app(db_path=tmp_path/"set.db")) as app:
        result=app.get("/owner/api/analytics",headers=auth()).json()
        assert result["billing"]["next_due_date"]=="2026-11-15"
        assert result["billing"]["estimated_usage_usd"]==8.75
        assert result["billing"]["monthly_budget_usd"]==41
        assert result["billing"]["source"]=="manual"
        assert "Railway billing" in app.get("/owner/analytics",headers=auth()).text


def test_google_login_disabled_when_unconfigured(monkeypatch,tmp_path):
    monkeypatch.delenv("SHITHEAD_GOOGLE_CLIENT_ID",raising=False)
    monkeypatch.delenv("SHITHEAD_OWNER_EMAIL",raising=False)
    monkeypatch.delenv("SHITHEAD_ADMIN_SESSION_SECRET",raising=False)
    monkeypatch.delenv("SHITHEAD_ADMIN_PASSWORD",raising=False)
    with TestClient(create_app(db_path=tmp_path/"disabled.db")) as app:
        for url in ("/owner/login","/owner/login.js","/owner/api/analytics"):
            assert app.get(url).status_code==404
        assert app.post("/owner/session").status_code==404
        assert app.get("/").status_code==200
