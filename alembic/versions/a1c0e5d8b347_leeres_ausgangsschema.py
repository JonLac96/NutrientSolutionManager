"""Leeres Ausgangsschema ohne Fachtabellen.

Revision ID: a1c0e5d8b347
Revises:
Create Date: 2026-10-07

"""

from collections.abc import Sequence

revision: str = "a1c0e5d8b347"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
