"""_rate_key must identify users from the Bearer token (SlowAPI runs before body)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from tests.backend_test_utils import configure_backend, login_headers


def test_rate_key_uses_jwt_sub_not_request_state(tmp_path: Path, monkeypatch):
    main_mod = configure_backend(
        tmp_path,
        monkeypatch,
        ATT_REQUIRE_AUTH="false",
        ATT_DEMO_MODE="true",
    )
    from fastapi.testclient import TestClient

    with TestClient(main_mod.app) as client:
        headers = login_headers(client)
        token = headers["Authorization"].removeprefix("Bearer ")
        payload = main_mod.decode_token(token, "access")
        request = SimpleNamespace(
            state=SimpleNamespace(),  # no user_id yet — matches SlowAPI timing
            headers={"Authorization": f"Bearer {token}"},
        )
        assert main_mod._rate_key(request) == f"user:{payload['sub']}"


def test_rate_key_falls_back_to_ip_without_token(tmp_path: Path, monkeypatch):
    main_mod = configure_backend(tmp_path, monkeypatch, ATT_REQUIRE_AUTH="false")
    request = SimpleNamespace(
        state=SimpleNamespace(),
        headers={},
        client=SimpleNamespace(host="203.0.113.9"),
    )
    # SlowAPI's get_remote_address reads request.client.host
    key = main_mod._rate_key(request)
    assert key == "203.0.113.9" or key.startswith("203.0.113.9")
