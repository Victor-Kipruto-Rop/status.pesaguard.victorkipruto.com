import httpx
import pytest

from app.models.component import ComponentStatus
from app.monitoring.checker import HealthChecker
from app.monitoring.mapper import map_health_payload_to_components

SEED_COMPONENTS = [
    ("api", "API"),
    ("dashboard", "Dashboard"),
    ("transactions", "Transactions"),
    ("reconciliation", "Reconciliation"),
    ("fraud", "Fraud Detection"),
    ("webhooks", "Webhooks"),
]


async def _seed(client, slugs=SEED_COMPONENTS):
    for slug, name in slugs:
        resp = await client.post("/api/v1/components", json={"slug": slug, "name": name})
        assert resp.status_code == 201


def test_mapper_all_ok():
    payload = {
        "status": "ok",
        "checks": {
            "database": {"status": "ok"},
            "kafka": {"status": "ok"},
            "redis": {"status": "ok"},
            "daraja": {"status": "ok"},
        },
    }
    statuses = map_health_payload_to_components(payload)
    assert all(s == ComponentStatus.operational for s in statuses.values())


def test_mapper_database_down_is_major_outage_everywhere_it_touches():
    payload = {
        "status": "failed",
        "checks": {
            "database": {"status": "failed"},
            "kafka": {"status": "ok"},
            "redis": {"status": "ok"},
            "daraja": {"status": "ok"},
        },
    }
    statuses = map_health_payload_to_components(payload)
    assert statuses["reconciliation"] == ComponentStatus.major_outage
    assert statuses["transactions"] == ComponentStatus.major_outage
    # api/dashboard mirror the overall status, which is "failed" here
    assert statuses["api"] == ComponentStatus.major_outage


def test_mapper_daraja_degraded_only_affects_transaction_paths():
    payload = {
        "status": "degraded",
        "checks": {
            "database": {"status": "ok"},
            "kafka": {"status": "ok"},
            "redis": {"status": "ok"},
            "daraja": {"status": "degraded"},
        },
    }
    statuses = map_health_payload_to_components(payload)
    assert statuses["transactions"] == ComponentStatus.degraded
    assert statuses["webhooks"] == ComponentStatus.degraded
    assert statuses["reconciliation"] == ComponentStatus.operational


@pytest.mark.asyncio
async def test_checker_updates_components_from_mock_response(client, db_session):
    await _seed(client)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/health"
        return httpx.Response(
            200,
            json={
                "status": "degraded",
                "service": "pesaguard",
                "checks": {
                    "database": {"status": "ok"},
                    "kafka": {"status": "ok"},
                    "redis": {"status": "ok"},
                    "daraja": {"status": "degraded"},
                },
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.pesaguard.victorkipruto.com")
    checker = HealthChecker(db_session, client=mock_client)
    result = await checker.check_once()
    await mock_client.aclose()

    assert result["reachable"] is True
    assert result["statuses"]["webhooks"] == ComponentStatus.degraded

    status_resp = await client.get("/api/v1/status?use_cache=false")
    services_by_id = {s["id"]: s for s in status_resp.json()["services"]}
    assert services_by_id["webhooks"]["status"] == "degraded"
    assert services_by_id["reconciliation"]["status"] == "operational"


@pytest.mark.asyncio
async def test_checker_marks_everything_outage_when_unreachable(client, db_session):
    await _seed(client)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.pesaguard.victorkipruto.com")
    checker = HealthChecker(db_session, client=mock_client)
    result = await checker.check_once()
    await mock_client.aclose()

    assert result["reachable"] is False

    status_resp = await client.get("/api/v1/status?use_cache=false")
    body = status_resp.json()
    assert body["overall"]["status"] == "major-outage"
    assert all(s["status"] == "major-outage" for s in body["services"])
