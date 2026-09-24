"""
Maps the real PesaGuard API's /health payload onto the status page's own
component slugs.

The real API (api.pesaguard.victorkipruto.com) exposes exactly ONE aggregate
health endpoint — it does not report per-component health for "the API",
"transactions", "fraud detection", etc. separately. So this mapping is an
approximation, not a precise 1:1 reflection of reality:

  - database  -> backs transaction storage and reconciliation reads/writes
  - daraja    -> the M-Pesa OAuth/callback integration; most directly tied
                 to transaction ingestion and webhook delivery
  - redis     -> used for webhook idempotency caching and the transaction
                 outbox drain queue
  - kafka     -> event bus; not required for "ok" by default
                 (PESAGUARD_HEALTH_REQUIRE_KAFKA), so a kafka failure alone
                 does not necessarily mean something is actually broken

"dashboard" and "fraud" have no dedicated check in the real payload at all,
so they fall back to the overall status — a reasonable default since they
run in the same process and share the same database/Redis.

If/when the real API grows per-component health reporting, replace this
mapping with a direct read instead of guessing from the aggregate checks.
"""
from app.models.component import ComponentStatus

# Real API status string -> our ComponentStatus
_CHECK_STATUS_MAP = {
    "ok": ComponentStatus.operational,
    "degraded": ComponentStatus.degraded,
    "failed": ComponentStatus.major_outage,
}

_OVERALL_STATUS_MAP = {
    "ok": ComponentStatus.operational,
    "degraded": ComponentStatus.degraded,
    "failed": ComponentStatus.major_outage,
}


def _check_status(checks: dict, name: str, overall_fallback: ComponentStatus) -> ComponentStatus:
    check = checks.get(name) or {}
    raw_status = check.get("status")
    return _CHECK_STATUS_MAP.get(raw_status, overall_fallback)


def map_health_payload_to_components(payload: dict) -> dict[str, ComponentStatus]:
    """
    payload: the parsed JSON body of GET /health from api.pesaguard.victorkipruto.com
    Returns: {component_slug: ComponentStatus} for every component this
    worker knows how to derive an opinion about.
    """
    overall = _OVERALL_STATUS_MAP.get(payload.get("status"), ComponentStatus.unknown)
    checks = payload.get("checks") or {}

    database_status = _check_status(checks, "database", overall)
    daraja_status = _check_status(checks, "daraja", overall)
    redis_status = _check_status(checks, "redis", overall)

    def worse(*statuses: ComponentStatus) -> ComponentStatus:
        rank = {
            ComponentStatus.unknown: 0,
            ComponentStatus.operational: 1,
            ComponentStatus.maintenance: 2,
            ComponentStatus.degraded: 3,
            ComponentStatus.partial_outage: 4,
            ComponentStatus.major_outage: 5,
        }
        return max(statuses, key=lambda s: rank.get(s, 0))

    return {
        "api": overall,
        "dashboard": overall,
        "transactions": worse(database_status, daraja_status),
        "reconciliation": database_status,
        "fraud": worse(database_status, redis_status),
        "webhooks": worse(daraja_status, redis_status),
    }


def all_components_unreachable() -> dict[str, ComponentStatus]:
    """
    Used when the real API can't be reached at all (network error, timeout,
    DNS failure) — as opposed to responding with a non-ok status, which
    all_components_unreachable is NOT for. A true network-level failure to
    reach the host at all means the whole service is presumed down.
    """
    outage = ComponentStatus.major_outage
    return {
        "api": outage,
        "dashboard": outage,
        "transactions": outage,
        "reconciliation": outage,
        "fraud": outage,
        "webhooks": outage,
    }
