"""Owner analytics must never disclose player details or interfere with the six games."""
import base64
import csv
import io

import pytest
from fastapi.testclient import TestClient

from server.app.analytics import AnalyticsStore, traffic_source
from server.app.main import create_app


def auth(password="a-strong-test-secret"):
    raw=base64.b64encode(("owner:"+password).encode("utf-8")).decode("ascii")
    return {"Authorization":"Basic "+raw}


def test_daily_counter_math_all_games_and_domino_modes(tmp_path):
    db=tmp_path/"analytics.sqlite3"
    a=AnalyticsStore(db)
    assert a.available
    assert a.record("page_views",source="instagram")
    assert a.record("page_views",source="instagram")
    assert a.record("page_views",source="direct")
    for game in ("shithead","ludo","awale","dara","yote","dominoes"):
        mode="partner" if game=="dominoes" else ""
        assert a.record("rooms_created",game=game,mode=mode)
        assert a.record("matches_started",game=game,mode=mode)
    assert a.record("matches_started",game="dominoes",mode="cutthroat")
    assert a.record("matches_completed",game="dominoes",mode="cutthroat")
    result=a.report(days=30)
    assert result["overview"]["page_views"]==3
    assert result["overview"]["rooms_created"]==6
    assert result["overview"]["matches_started"]==7
    assert result["overview"]["matches_completed"]==1
    assert "actions_accepted" not in result["overview"]
    assert len(result["games"])==6
    assert result["games"][0]["key"]=="dominoes"
    domino=result["games"][0]
    assert domino["modes"]["partner"]["matches_started"]==1
    assert domino["modes"]["cutthroat"]["matches_started"]==1
    assert next(s["page_views"] for s in result["sources"] if s["source"]=="instagram")==2
    assert len(result["daily"])==30
    assert len(list(csv.reader(io.StringIO(a.export_csv(days=0)))))>=10
    assert AnalyticsStore(db).report(days=0)["overview"]==result["overview"]
    for metric in ("secrets","login","gameover"):
        with pytest.raises(ValueError):
            a.record(metric,game="shithead")
    with pytest.raises(ValueError):
        a.record("matches_started",game="unknown")
    with pytest.raises(ValueError):
        a.record("rooms_created",game="awale",mode="cutthroat")
    with pytest.raises(ValueError):
        a.report(days=100)


def test_referral_mapping_is_coarse_and_does_not_retain_urls():
    assert traffic_source(utm_source="ig")=="instagram"
    assert traffic_source(utm_source="tt")=="tiktok"
    assert traffic_source(utm_source="YouTube")=="youtube"
    assert traffic_source(referrer="https://l.instagram.com/redirect?secret=MYTOKEN")=="instagram"
    assert traffic_source(referrer="https://play.shithead.games/something")=="direct"
    assert traffic_source(referrer="https://notinstagram.com/")=="other"
    assert traffic_source()=="direct"


def test_owner_endpoints_disabled_without_password(monkeypatch,tmp_path):
    monkeypatch.delenv("SHITHEAD_ADMIN_PASSWORD",raising=False)
    with TestClient(create_app(db_path=tmp_path/"rooms.db")) as app:
        for url in ("/owner/analytics", "/owner/analytics.js",
                    "/owner/api/analytics", "/owner/api/analytics.csv"):
            assert app.get(url).status_code==404


def test_authenticated_owner_dashboard_and_csv(monkeypatch,tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD","a-strong-test-secret")
    db=tmp_path/"rooms.db"
    with TestClient(create_app(db_path=db)) as app:
        assert app.get("/health").status_code==200
        assert app.get("/").status_code==200
        assert app.get("/?utm_source=ig").status_code==200
        assert app.get("/?utm_source=ig").status_code==200
        for url in ("/owner/analytics","/owner/analytics.js",
                    "/owner/api/analytics","/owner/api/analytics.csv"):
            assert app.get(url).status_code==401
            assert app.get(url,headers=auth("wrong")).status_code==401
        page=app.get("/owner/analytics",headers=auth())
        assert page.status_code==200
        assert "Most played games" in page.text
        assert page.headers["cache-control"]=="no-store, private"
        assert "Content-Security-Policy" in page.headers
        assert app.get("/owner/analytics.js",headers=auth()).status_code==200
        metrics=app.get("/owner/api/analytics?days=30",headers=auth())
        assert metrics.status_code==200
        data=metrics.json()
        assert data["overview"]["page_views"]==3
        assert data["overview"]["rooms_created"]==0
        assert data["sources"][0]=={"source":"instagram","page_views":2}
        assert data["live"]["connected_seats"]==0
        assert app.get("/owner/api/analytics?days=12",headers=auth()).status_code==422
        csv_response=app.get("/owner/api/analytics.csv?days=0",headers=auth())
        assert csv_response.status_code==200
        assert "date_utc,game,mode,metric,source,count" in csv_response.text
        assert "instagram" in csv_response.text
        # No raw source URL, room IDs, names, or per-visitor records.
        assert "utm_source" not in csv_response.text

    with TestClient(create_app(db_path=db)) as restarted:
        restored=restarted.get("/owner/api/analytics?days=30",headers=auth()).json()
        assert restored["overview"]["page_views"]==3


def test_seat_and_match_start_events_are_server_confirmed(monkeypatch,tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD","a-strong-test-secret")
    with TestClient(create_app(db_path=tmp_path/"rooms.db")) as app:
        created=app.post("/api/rooms",json={"game_type":"awale","capacity":2,"name":"Host"})
        assert created.status_code==201
        room=created.json()["room_id"]
        guest=app.post(f"/api/rooms/{room}/join",json={"name":"Guest"})
        assert guest.status_code==201
        assert app.post(f"/api/rooms/{room}/join",json={"name":"Overflow"}).status_code==409
        before=app.get("/owner/api/analytics",headers=auth()).json()
        assert before["overview"]["rooms_created"]==1
        assert before["overview"]["players_joined"]==2
        assert before["overview"]["matches_started"]==0
        with app.websocket_connect(f"/ws/{room}") as one:
            one.send_json({"type":"auth","token":created.json()["token"]})
            a=one.receive_json()
            with app.websocket_connect(f"/ws/{room}") as two:
                two.send_json({"type":"auth","token":guest.json()["token"]})
                b=two.receive_json()
                a=one.receive_json()
                one.send_json({"type":"ready","ready":True,"expected_version":a["version"],"request_id":"host-ready"})
                a=one.receive_json()
                b=two.receive_json()
                assert a["phase"]=="LOBBY"
                two.send_json({"type":"ready","ready":True,"expected_version":b["version"],"request_id":"guest-ready"})
                a=one.receive_json()
                b=two.receive_json()
                assert a["phase"]==b["phase"]=="PLAYING"
                # Duplicate request ID cannot double-count a start.
                two.send_json({"type":"ready","ready":True,"expected_version":b["version"],"request_id":"guest-ready"})
                repeated=two.receive_json()
                assert repeated["phase"]=="PLAYING"
        after=app.get("/owner/api/analytics",headers=auth()).json()
        assert after["overview"]["matches_started"]==1
        assert after["overview"]["matches_completed"]==0
        assert next(g for g in after["games"] if g["key"]=="awale")["matches_started"]==1
        assert after["overview"]["rooms_created"]==1
        assert after["overview"]["players_joined"]==2


def test_analytics_storage_failure_does_not_break_gameplay(monkeypatch,tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD","a-strong-test-secret")
    # A directory cannot be opened as SQLite database.
    bad=tmp_path/"not_a_database"
    bad.mkdir()
    with TestClient(create_app(db_path=tmp_path/"rooms.db",analytics_path=bad)) as app:
        assert app.get("/health").status_code==200
        assert app.get("/").status_code==200
        r=app.post("/api/rooms",json={"name":"Owner","game_type":"ludo","capacity":2})
        assert r.status_code==201
        assert app.get("/owner/api/analytics",headers=auth()).status_code==503
