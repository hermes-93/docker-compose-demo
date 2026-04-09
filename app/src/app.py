import os
import socket
import logging

import psycopg2
import redis
from flask import Flask, jsonify, request

from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)


def get_db():
    return psycopg2.connect(app.config["DATABASE_URL"])


def get_redis():
    return redis.from_url(app.config["REDIS_URL"])


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id   SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT false
                )
            """)
        conn.commit()


@app.route("/")
def index():
    return jsonify({
        "service": "docker-compose-demo",
        "host": socket.gethostname(),
        "version": os.environ.get("APP_VERSION", "dev"),
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/ready")
def ready():
    checks = {}
    ok = True

    # DB check
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = str(exc)
        ok = False

    # Redis check
    try:
        r = get_redis()
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = str(exc)
        ok = False

    status = 200 if ok else 503
    return jsonify({"status": "ready" if ok else "not ready", "checks": checks}), status


@app.route("/api/items", methods=["GET"])
def list_items():
    cache_key = "items:all"
    try:
        r = get_redis()
        cached = r.get(cache_key)
        if cached:
            import json
            return jsonify(json.loads(cached))
    except Exception:
        pass

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, done FROM items ORDER BY id")
            rows = [{"id": r[0], "name": r[1], "done": r[2]} for r in cur.fetchall()]

    try:
        import json
        r = get_redis()
        r.setex(cache_key, 30, json.dumps(rows))
    except Exception:
        pass

    return jsonify(rows)


@app.route("/api/items", methods=["POST"])
def create_item():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (name) VALUES (%s) RETURNING id, name, done",
                (name,),
            )
            row = cur.fetchone()
        conn.commit()

    # invalidate cache
    try:
        get_redis().delete("items:all")
    except Exception:
        pass

    return jsonify({"id": row[0], "name": row[1], "done": row[2]}), 201


@app.route("/api/items/<int:item_id>", methods=["PATCH"])
def toggle_item(item_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE items SET done = NOT done WHERE id = %s RETURNING id, name, done",
                (item_id,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        return jsonify({"error": "not found"}), 404

    try:
        get_redis().delete("items:all")
    except Exception:
        pass

    return jsonify({"id": row[0], "name": row[1], "done": row[2]})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
