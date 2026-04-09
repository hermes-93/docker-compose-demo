"""Unit tests for the Flask app (no real DB/Redis needed)."""
import json
import pytest
from unittest.mock import patch, MagicMock

# Patch DB and Redis before importing app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture()
def client():
    from src.app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "docker-compose-demo"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_ready_ok(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_redis = MagicMock()

    with patch("src.app.get_db", return_value=mock_conn), \
         patch("src.app.get_redis", return_value=mock_redis):
        resp = client.get("/ready")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ready"
    assert data["checks"]["db"] == "ok"
    assert data["checks"]["redis"] == "ok"


def test_ready_db_fail(client):
    mock_redis = MagicMock()

    with patch("src.app.get_db", side_effect=Exception("connection refused")), \
         patch("src.app.get_redis", return_value=mock_redis):
        resp = client.get("/ready")

    assert resp.status_code == 503
    data = resp.get_json()
    assert data["status"] == "not ready"
    assert "connection refused" in data["checks"]["db"]


def test_list_items(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = [(1, "Buy milk", False), (2, "Write tests", True)]
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_redis = MagicMock()
    mock_redis.get.return_value = None

    with patch("src.app.get_db", return_value=mock_conn), \
         patch("src.app.get_redis", return_value=mock_redis):
        resp = client.get("/api/items")

    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 2
    assert items[0]["name"] == "Buy milk"
    assert items[1]["done"] is True


def test_list_items_cached(client):
    cached = json.dumps([{"id": 1, "name": "Cached item", "done": False}])
    mock_redis = MagicMock()
    mock_redis.get.return_value = cached.encode()

    with patch("src.app.get_redis", return_value=mock_redis):
        resp = client.get("/api/items")

    assert resp.status_code == 200
    items = resp.get_json()
    assert items[0]["name"] == "Cached item"


def test_create_item(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (3, "New task", False)
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_redis = MagicMock()

    with patch("src.app.get_db", return_value=mock_conn), \
         patch("src.app.get_redis", return_value=mock_redis):
        resp = client.post("/api/items", json={"name": "New task"})

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "New task"
    assert data["done"] is False


def test_create_item_missing_name(client):
    resp = client.post("/api/items", json={})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_toggle_item(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (1, "Buy milk", True)
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_redis = MagicMock()

    with patch("src.app.get_db", return_value=mock_conn), \
         patch("src.app.get_redis", return_value=mock_redis):
        resp = client.patch("/api/items/1")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["done"] is True


def test_toggle_item_not_found(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_redis = MagicMock()

    with patch("src.app.get_db", return_value=mock_conn), \
         patch("src.app.get_redis", return_value=mock_redis):
        resp = client.patch("/api/items/999")

    assert resp.status_code == 404
