# PesaGuard Status — Backend API

FastAPI + Postgres + Redis backend for the PesaGuard status page. Designed
as a drop-in data source for the existing static frontend
(`status.pesaguard.victorkipruto.com`) — response shapes mirror
`frontend/data/*.json` exactly, so the frontend's `js/status.js`,
`js/incidents.js`, etc. can eventually point at this API with no changes.

## Run it (local dev, via docker-compose)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

This starts:
- **postgres** — Postgres 16, seeded via Alembic migrations
- **redis** — Redis 7, used to cache the `/api/v1/status` aggregate (15s TTL by default)
- **backend** — runs migrations, seeds the 6 components from the original
  `data/status.json`, then starts the API with hot-reload at
  **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

## Run it without Docker

```bash
cd backend
pip install -r requirements.txt
# point DATABASE_URL / REDIS_URL at your own Postgres/Redis in .env
cp .env.example .env  # then edit DATABASE_URL/REDIS_URL as needed
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

## Run the tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Tests run against an in-memory SQLite database — no Postgres/Redis needed
to run the suite. 9 tests currently cover: health check, the full status
aggregate, component CRUD + status updates, the full incident lifecycle
(create → update → resolve), maintenance window lifecycle, uptime endpoint,
and subscription idempotency.

## What's here vs. what's not yet

**Built and tested:**
- Full REST API: components, incidents (+ timeline), maintenance windows, uptime aggregation, subscriptions, health
- SQLAlchemy async models + Alembic migration (`0001_initial_schema`)
- Redis-backed caching on the status aggregate (fails open — a dead Redis never breaks a request)
- Seed script matching the existing frontend's 6 components

**Not built yet** (see the original project tree for the full scope):
- The monitoring worker that actually probes services and calls
  `PATCH /components/{slug}/status` — right now components sit at
  `unknown` until something external updates them
- The nightly uptime-aggregation job that populates `uptime_daily_records`
  from raw health-check results
- Email/SMS notification dispatch on incident/maintenance updates
- Terraform/AWS infra, Prometheus/Grafana, Alertmanager
- Auth on the write endpoints (POST/PATCH routes are currently open — fine
  for local dev, not for a public deployment)

## API shape reference

`GET /api/v1/status` is the main endpoint — it returns the same shape as
`frontend/data/status.json`:

```json
{
  "overall": {"status": "operational", "label": "All systems operational", "description": "..."},
  "services": [{"id": "api", "name": "API", "status": "operational", "latency": 42.1, "uptime": 99.98, ...}],
  "activeIncidents": [...],
  "activeMaintenance": [...]
}
```
