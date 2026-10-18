"""Private staging access gate regressions."""
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from server.app.main import create_app
from server.app.site_gate import cookie_for, install_test_gate

def test_localhost_unchanged():
    with patch.dict(os.environ, {"SHITHEAD_TEST_PASSWORD": ""}):
        with TestClient(create_app()) as client:
            assert client.get("/").status_code == 200
            assert client.get("/health").json() == {"status": "ok"}

def test_password_required_for_page_api_and_static_js():
    with patch.dict(os.environ, {"SHITHEAD_TEST_PASSWORD": "a-long-private-password"}):
        with TestClient(create_app()) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/", follow_redirects=False).status_code == 303
            assert client.post("/api/rooms", json={"capacity": 2}).status_code == 401
            assert client.get("/client.js").status_code == 401
            assert client.post("/test-login", data={"password": "wrong"}).status_code == 401
            response = client.post("/test-login", data={"password": "a-long-private-password"}, follow_redirects=False)
            assert response.status_code == 303
            assert client.get("/").status_code == 200
            assert client.post("/api/rooms", json={"capacity": 2}).status_code == 201

def test_cloud_requires_secret():
    with patch.dict(os.environ, {"SHITHEAD_TEST_PASSWORD": ""}):
        import pytest
        with pytest.raises(RuntimeError):
            install_test_gate(FastAPI(), cloud=True)

def test_cookie_is_not_password():
    secret = "a-long-private-password"
    assert secret not in cookie_for(secret)
