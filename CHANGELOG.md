# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-04-15

### Added
- Flask application with SQLAlchemy, Redis caching, health endpoints
- Docker Compose stack: app + PostgreSQL + Redis + Nginx reverse proxy
- Production compose file with resource limits and restart policies
- Multi-stage Dockerfile: builder + runtime, non-root user, HEALTHCHECK
- Nginx config: rate limiting, security headers, proxy caching
- pytest test suite with ≥80% coverage gate
- GitHub Actions CI: tests, ruff lint, coverage report
- GitHub Actions Security: Trivy image scan + config scan (scheduled weekly)
- GitHub Actions Release: GHCR push with semver tags + GitHub Release on tag push
- `.env.example` with documented configuration

### Security
- Non-root container user (UID 1001)
- Security headers: X-Frame-Options, X-Content-Type-Options, CSP, HSTS
- Nginx rate limiting: 10 req/s per IP
- Trivy scans run on every push and weekly schedule

[Unreleased]: https://github.com/hermes-93/docker-compose-demo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/hermes-93/docker-compose-demo/releases/tag/v1.0.0
