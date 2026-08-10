"""Tests for serving the built frontend shell from the backend runtime."""

from pathlib import Path

from fastapi.testclient import TestClient

import backend.app.main as main


def test_root_serves_frontend_shell_when_built_assets_exist(tmp_path: Path, monkeypatch) -> None:
    index_file = tmp_path / "index.html"
    index_file.write_text("<html><body>Cognera App</body></html>", encoding="utf-8")

    monkeypatch.setattr(main, "FRONTEND_INDEX_FILE", index_file)
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Cognera App" in response.text
    assert response.headers["content-type"].startswith("text/html")


def test_health_check_route_serves_frontend_shell_when_built_assets_exist(tmp_path: Path, monkeypatch) -> None:
    index_file = tmp_path / "index.html"
    index_file.write_text("<html><body>Cognera Health</body></html>", encoding="utf-8")

    monkeypatch.setattr(main, "FRONTEND_INDEX_FILE", index_file)
    client = TestClient(main.app)

    response = client.get("/health-check")

    assert response.status_code == 200
    assert "Cognera Health" in response.text
    assert response.headers["content-type"].startswith("text/html")