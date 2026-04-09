# docker-compose-demo

A production-style todo API demonstrating multi-stage Docker builds, Docker Compose
service orchestration, health checks, caching, and CI/CD.

[![CI](https://github.com/hermes-93/docker-compose-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/hermes-93/docker-compose-demo/actions/workflows/ci.yml)
[![Security](https://github.com/hermes-93/docker-compose-demo/actions/workflows/security.yml/badge.svg)](https://github.com/hermes-93/docker-compose-demo/actions/workflows/security.yml)

## Stack

| Layer    | Technology         |
|----------|--------------------|
| App      | Python 3.12 / Flask |
| Database | PostgreSQL 16      |
| Cache    | Redis 7            |
| Proxy    | Nginx 1.27         |
| Runtime  | Docker + Compose   |

## Architecture

```
Browser / curl
      │
      ▼
  Nginx :8080          ← reverse proxy, health endpoint
      │
      ▼
  Flask app :5000      ← REST API, non-root user (uid 1001)
      │       │
      ▼       ▼
 PostgreSQL  Redis     ← persistent storage + cache
```

## Quick start

```bash
cp .env.example .env
docker compose up -d
```

Wait for all services to become healthy:

```bash
docker compose ps
```

Then test the API:

```bash
# List items
curl http://localhost:8080/api/items

# Create an item
curl -X POST http://localhost:8080/api/items \
     -H "Content-Type: application/json" \
     -d '{"name": "Buy coffee"}'

# Toggle done
curl -X PATCH http://localhost:8080/api/items/1

# Readiness check (DB + Redis)
curl http://localhost:8080/ready
```

## API reference

| Method | Path                | Description              |
|--------|---------------------|--------------------------|
| GET    | `/`                 | Service info + hostname  |
| GET    | `/health`           | Liveness probe           |
| GET    | `/ready`            | Readiness (DB + Redis)   |
| GET    | `/api/items`        | List all items (cached)  |
| POST   | `/api/items`        | Create item `{name}`     |
| PATCH  | `/api/items/:id`    | Toggle `done` flag       |

## Multi-stage Dockerfile

The `app/Dockerfile` uses two stages to minimise the final image:

| Stage     | Base image         | Purpose                          |
|-----------|--------------------|----------------------------------|
| `builder` | `python:3.12-slim` | Compile C extensions, install deps |
| `runtime` | `python:3.12-slim` | Copy installed packages, no gcc  |

Key security practices:
- Non-root user (`appuser`, uid 1001)
- No build tools in the runtime layer
- `HEALTHCHECK` instruction in the image
- Labels following OCI image spec

## Production deployment

```bash
cp .env.example .env   # fill in real secrets
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d
```

The prod override adds:
- Resource limits (`cpus`, `memory`) on every service
- 2 app replicas
- Published image from GHCR instead of local build

## Running tests locally

```bash
pip install -r app/requirements-dev.txt
pytest app/tests/ -v --cov=app/src
```

## CI/CD

| Workflow   | Trigger               | Jobs                                          |
|------------|-----------------------|-----------------------------------------------|
| `ci.yml`   | push/PR → main        | unit tests, Docker build, compose validate, ruff lint |
| `security.yml` | push/PR + weekly  | Trivy image scan, Trivy config scan (SARIF)   |
| `release.yml`  | tag `v*.*.*`      | build + push to GHCR, GitHub Release          |

## License

MIT
