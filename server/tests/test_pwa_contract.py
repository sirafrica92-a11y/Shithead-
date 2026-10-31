"""Browser installability contract; no existing game rule engine is modified."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from server.app.main import create_app

STATIC = Path(__file__).resolve().parents[1] / "app" / "static"

def test_install_metadata_served_and_full_game_home_still_available(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "pwa.sqlite3")) as c:
        landing = c.get("/")
        assert landing.status_code == 200
        assert 'rel="manifest" href="/manifest.webmanifest"' in landing.text
        assert '<script defer src="/pwa-registration.js"></script>' in landing.text
        assert "SHITHEAD Games" in landing.text
        manifest = c.get("/manifest.webmanifest")
        assert manifest.status_code == 200
        assert manifest.headers["content-type"].startswith("application/manifest+json")
        assert manifest.headers.get("cache-control") == "no-store"
        data = manifest.json()
        assert data["start_url"].startswith("/")
        assert data["scope"] == "/"
        assert data["display"] == "standalone"
        assert {x["sizes"] for x in data["icons"]} == {"192x192", "512x512"}
        for x in data["icons"]:
            assert x["src"].startswith("/brand/")
            # Installation needs real, accessible images: the FastAPI
            # /brand allowlist is intentionally strict.
            icon = c.get(x["src"])
            assert icon.status_code == 200, x["src"]
            assert icon.headers["content-type"].startswith("image/png")
            assert icon.content.startswith(bytes.fromhex("89504e470d0a1a0a"))
        assert c.get("/brand/not-an-asset.png").status_code == 404
        assert len([x for x in data["icons"] if x.get("purpose")=="maskable"]) == 1

def test_worker_is_network_only_never_caches_seat_or_room_data(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "pwa.sqlite3")) as c:
        r = c.get("/service-worker.js")
        assert r.status_code == 200
        assert r.headers.get("service-worker-allowed") == "/"
        assert r.headers.get("cache-control") == "no-store"
        script = r.text
        assert 'req.method !== "GET"' in script
        assert 'req.mode !== "navigate"' in script
        assert "fetch(req)" in script
        assert "Connection lost" in script
        for disallowed in ["caches.open", "cache.put", "indexedDB", "localStorage", "fetch(event.request.clone())"]:
            assert disallowed not in script
        assert c.get("/pwa-registration.js").status_code == 200
        assert c.get("/health").json() == {"status":"ok"}

def test_approved_logo_files_have_true_png_dimensions():
    # Standard-library PNG header check (no Pillow in production dependencies).
    import struct
    paths = {
        "shithead-logo.png": (512,512),
        "shithead-logo-192.png": (192,192),
        "shithead-maskable-512.png": (512,512),
    }
    for filename, expected in paths.items():
        raw = (STATIC / "brand" / filename).read_bytes()
        assert raw[:8] == bytes.fromhex("89504e470d0a1a0a")
        assert raw[12:16] == b"IHDR"
        assert struct.unpack(">II", raw[16:24]) == expected


def test_no_android_permission_or_assetlinks_credentials_in_source():
    manifest = json.loads((STATIC / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["prefer_related_applications"] is False
    assert not (STATIC / ".well-known" / "assetlinks.json").exists()
