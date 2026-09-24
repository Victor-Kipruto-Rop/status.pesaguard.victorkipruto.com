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
- **worker** — polls the real PesaGuard API's public `/health` endpoint
  (`https://api.pesaguard.victorkipruto.com/health`) every 30s and updates
  this status page's component records from it. See "Monitoring worker"
  below.

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

## Monitoring worker

`worker/main.py` is a standalone loop that polls
`https://api.pesaguard.victorkipruto.com/health` — the real, live PesaGuard
production API's public health endpoint — every `MONITOR_POLL_INTERVAL_SECONDS`
(default 30s), and updates this status page's own component records from it.

**Important:** this worker only ever makes read-only GET requests to that one
public endpoint. It never writes to, deploys to, or otherwise touches the
`api.pesaguard.victorkipruto.com` repository or service in any way.

The real API exposes exactly one aggregate health endpoint — not per-component
health — so `app/monitoring/mapper.py` approximates a mapping from its
`checks.{database,kafka,redis,daraja}` fields onto this page's 6 components
(api, dashboard, transactions, reconciliation, fraud, webhooks). Read the
comments in that file for the reasoning, and adjust the mapping if the real
API's architecture doesn't match what's assumed there — it was written from
reading `api.pesaguard.victorkipruto.com`'s `health.py`/`app.py` source, not
from a spec.

If the real API can't be reached at all (DNS failure, timeout, connection
refused), every component is marked `major-outage` rather than left stale —
a status page that can't tell it's not being updated is worse than one that's
honestly wrong for a few seconds.

Run it standalone:
```bash
cd backend
python -m worker.main
```

## Run the tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Tests run against an in-memory SQLite database and a mocked HTTP transport
for the monitoring worker (`httpx.MockTransport`) — no Postgres, Redis, or
real network access needed to run the suite. 14 tests currently cover:
health check, the full status aggregate, component CRUD + status updates,
the full incident lifecycle (create → update → resolve), maintenance window
lifecycle, uptime endpoint, subscription idempotency, the health-payload
mapping logic, and the worker's behavior on both a mocked real response and
a simulated network failure.

## What's here vs. what's not yet

**Built and tested:**
- Full REST API: components, incidents (+ timeline), maintenance windows, uptime aggregation, subscriptions, health
- SQLAlchemy async models + Alembic migration (`0001_initial_schema`)
- Redis-backed caching on the status aggregate (fails open — a dead Redis never breaks a request)
- Seed script matching the existing frontend's 6 components
- A monitoring worker that polls the real PesaGuard API's `/health` and updates component statuses from it

**Not built yet** (see the original project tree for the full scope):
- The nightly uptime-aggregation job that populates `uptime_daily_records`
  from the health-check history (the worker updates live status; it doesn't
  yet compute rolling daily uptime percentages)
- Email/SMS notification dispatch on incident/maintenance updates
- Automatic incident creation when the monitoring worker detects sustained
  degradation (currently it only updates component status, not incidents —
  deliberately, so a transient blip doesn't spam an incident)
- Terraform/AWS infra, Prometheus/Grafana, Alertmanager for this status page itself
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
