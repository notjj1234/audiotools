"""Rate-limit key prefers JWT subject over IP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("fastapi")

from tests.backend_test_utils import configure_backend, login_headers


def test_rate_key_uses_access_token_sub(tmp_path, monkeypatch) -> None:
    main_mod = configure_backend(
        tmp_path,
        monkeypatch,
        ATT_REQUIRE_AUTH="false",
        ATT_DEMO_MODE="true",
    )
    with TestClient(main_mod.app) as client:
        headers = login_headers(client)
        token = headers["Authorization"].removeprefix("Bearer ")
        sub = main_mod.decode_token(token, "access")["sub"]

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
            "client": ("203.0.113.9", 12345),
            "server": ("test", 80),
        }
        request = main_mod.Request(scope)
        assert main_mod._rate_key(request) == f"user:{sub}"


def test_rate_key_falls_back_to_ip_without_bearer(tmp_path, monkeypatch) -> None:
    main_mod = configure_backend(
        tmp_path,
        monkeypatch,
        ATT_REQUIRE_AUTH="false",
        ATT_DEMO_MODE="true",
    )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("203.0.113.9", 12345),
        "server": ("test", 80),
    }
    request = main_mod.Request(scope)
    assert main_mod._rate_key(request) == "203.0.113.9"
