"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

component_status = sa.Enum(
    "operational", "degraded", "partial-outage", "major-outage", "maintenance", "unknown",
    name="component_status",
)
incident_severity = sa.Enum("low", "medium", "high", "major", name="incident_severity")
incident_update_status = sa.Enum(
    "investigating", "identified", "monitoring", "resolved", name="incident_update_status"
)
maintenance_status = sa.Enum("scheduled", "in-progress", "completed", name="maintenance_status")


def upgrade() -> None:
    bind = op.get_bind()
    component_status.create(bind, checkfirst=True)
    incident_severity.create(bind, checkfirst=True)
    incident_update_status.create(bind, checkfirst=True)
    maintenance_status.create(bind, checkfirst=True)

    op.create_table(
        "components",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", component_status, nullable=False, server_default="unknown"),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float, nullable=True),
        sa.Column("uptime_pct_90d", sa.Float, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_components_slug", "components", ["slug"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("severity", incident_severity, nullable=False),
        sa.Column("affected_service_slugs", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "incident_updates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("incident_id", sa.String(64), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", incident_update_status, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_incident_updates_incident_id", "incident_updates", ["incident_id"])

    op.create_table(
        "maintenance_windows",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", maintenance_status, nullable=False, server_default="scheduled"),
        sa.Column("affected_service_slugs", sa.Text, nullable=True),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "uptime_daily_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("component_id", sa.String(64), sa.ForeignKey("components.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Date, nullable=False),
        sa.Column("uptime_pct", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("downtime_minutes", sa.Float, nullable=False, server_default="0"),
        sa.UniqueConstraint("component_id", "day", name="uq_component_day"),
    )
    op.create_index("ix_uptime_daily_records_component_id", "uptime_daily_records", ["component_id"])
    op.create_index("ix_uptime_daily_records_day", "uptime_daily_records", ["day"])

    op.create_table(
        "subscribers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("confirmed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("unsubscribe_token", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_subscribers_email", "subscribers", ["email"])


def downgrade() -> None:
    op.drop_table("subscribers")
    op.drop_table("uptime_daily_records")
    op.drop_table("maintenance_windows")
    op.drop_table("incident_updates")
    op.drop_table("incidents")
    op.drop_table("components")
    bind = op.get_bind()
    maintenance_status.drop(bind, checkfirst=True)
    incident_update_status.drop(bind, checkfirst=True)
    incident_severity.drop(bind, checkfirst=True)
    component_status.drop(bind, checkfirst=True)
