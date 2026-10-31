"""Playtest presentation regression tests; game engine logic is not changed."""
from fastapi.testclient import TestClient
from server.app.main import create_app

def test_all_six_games_and_labels(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        page=c.get("/").text
        assert "Shithead Games — Shithead &amp; Ludo" not in page
        assert 'id="domino-hand-total"' in page
        assert 'id="domino-home-mode"' in page
        js=c.get("/client.js").text
        assert "namedGameEvent" in js
        assert 'snap?.players?.[Number(seat)-1]?.name' in js
        assert "Waiting for partner" in js
        assert "cutthroat" in js
        domino=c.get("/dominoes.js").text
        assert "count===1" in domino
        assert "myHand.length" in domino
        assert "uninterrupted run" in domino
        assert "g.scores" in domino
        assert "namedGameEvent" in domino
        awale=c.get("/awale.js").text
        assert "g.captured[winner]" in awale
        assert "namedGameEvent" in awale
        yote=c.get("/yote.js").text
        assert "last enemy piece on the board" in yote
        assert "in reserve" in yote
        assert "namedGameEvent" in yote
        dara=c.get("/dara.js").text
        assert "(gold):" in dara and "(crimson):" in dara
        assert "namedGameEvent" in dara
        for game,capacity in (("shithead",2),("ludo",2),("awale",2),("dara",2),("yote",2),("dominoes",4)):
            res=c.post("/api/rooms",json={"name":"Host","capacity":capacity,"game_type":game})
            assert res.status_code==201
            assert c.post("/api/rooms/"+res.json()["room_id"]+"/join",json={"name":"Friend"}).status_code==201


def test_actual_piece_color_labels_match_css(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as client:
        css=client.get("/").text
        for name in ("dara","yote"):
            assert f".{name}-p1 .{name}-piece" in css
            assert f".{name}-p2 .{name}-piece" in css
            script=client.get(f"/{name}.js").text
            assert "(gold):" in script
            assert "(crimson):" in script
            assert "(red):" not in script
            assert "(cream):" not in script
