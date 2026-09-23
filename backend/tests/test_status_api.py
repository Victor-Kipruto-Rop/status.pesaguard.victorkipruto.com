import pytest


@pytest.mark.asyncio
async def test_status_with_no_components(client):
    response = await client.get("/api/v1/status?use_cache=false")
    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["status"] == "unknown"
    assert body["services"] == []
    assert body["activeIncidents"] == []
    assert body["activeMaintenance"] == []


@pytest.mark.asyncio
async def test_create_component_and_see_it_in_status(client):
    create_resp = await client.post(
        "/api/v1/components", json={"slug": "api", "name": "API", "description": "REST API"}
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["id"] == "api"
    assert create_resp.json()["status"] == "unknown"

    status_resp = await client.get("/api/v1/status?use_cache=false")
    body = status_resp.json()
    assert len(body["services"]) == 1
    assert body["services"][0]["id"] == "api"


@pytest.mark.asyncio
async def test_component_status_update_flips_overall_status(client):
    await client.post("/api/v1/components", json={"slug": "api", "name": "API"})

    resp = await client.patch("/api/v1/components/api/status", json={"status": "major-outage"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "major-outage"

    status_resp = await client.get("/api/v1/status?use_cache=false")
    assert status_resp.json()["overall"]["status"] == "major-outage"


@pytest.mark.asyncio
async def test_update_unknown_component_404s(client):
    resp = await client.patch("/api/v1/components/does-not-exist/status", json={"status": "degraded"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_incident_lifecycle(client):
    create_resp = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Elevated API latency",
            "severity": "medium",
            "affected_service_slugs": ["api"],
            "initial_status": "investigating",
            "initial_description": "We are investigating reports of elevated latency.",
        },
    )
    assert create_resp.status_code == 201
    incident = create_resp.json()
    assert incident["status"] == "investigating"
    assert len(incident["timeline"]) == 1

    active_resp = await client.get("/api/v1/incidents/active")
    assert len(active_resp.json()) == 1

    update_resp = await client.post(
        f"/api/v1/incidents/{incident['id']}/updates",
        json={"status": "resolved", "description": "The issue has been resolved."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "resolved"
    assert update_resp.json()["duration"] is not None

    active_resp_after = await client.get("/api/v1/incidents/active")
    assert active_resp_after.json() == []


@pytest.mark.asyncio
async def test_subscription_is_idempotent(client):
    first = await client.post("/api/v1/subscriptions", json={"email": "person@example.com"})
    assert first.status_code == 201
    second = await client.post("/api/v1/subscriptions", json={"email": "person@example.com"})
    assert second.status_code == 201
    assert first.json()["email"] == second.json()["email"]


@pytest.mark.asyncio
async def test_maintenance_lifecycle(client):
    create_resp = await client.post(
        "/api/v1/maintenance",
        json={
            "title": "Database upgrade",
            "description": "Upgrading Postgres to v16.",
            "affected_service_slugs": ["api", "transactions"],
            "scheduled_start": "2026-10-01T02:00:00+00:00",
            "scheduled_end": "2026-10-01T04:00:00+00:00",
        },
    )
    assert create_resp.status_code == 201
    maintenance = create_resp.json()
    assert maintenance["status"] == "scheduled"
    assert maintenance["services"] == ["api", "transactions"]

    active_resp = await client.get("/api/v1/maintenance/active")
    assert len(active_resp.json()) == 1

    status_resp = await client.get("/api/v1/status?use_cache=false")
    assert len(status_resp.json()["activeMaintenance"]) == 1

    complete_resp = await client.patch(
        f"/api/v1/maintenance/{maintenance['id']}/status", params={"status": "completed"}
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"

    active_resp_after = await client.get("/api/v1/maintenance/active")
    assert active_resp_after.json() == []


@pytest.mark.asyncio
async def test_uptime_endpoint_with_no_data(client):
    resp = await client.get("/api/v1/uptime")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall"] is None
    assert body["services"] == []
    assert body["history"] == []
    assert body["recentDowntime"] == []
