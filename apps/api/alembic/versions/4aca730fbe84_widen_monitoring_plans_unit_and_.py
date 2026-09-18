"""widen monitoring_plans unit and measurement_frequency to text

Revision ID: 4aca730fbe84
Revises: 666d1a4d61b0
Create Date: 2026-09-18 09:07:14.140083

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4aca730fbe84'
down_revision: Union[str, None] = '666d1a4d61b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table is required for SQLite, which has no native ALTER
    # COLUMN TYPE support (it recreates the table under the hood); it also
    # works unchanged against Postgres, where this becomes a plain
    # ALTER COLUMN ... TYPE TEXT.
    with op.batch_alter_table("monitoring_plans") as batch_op:
        batch_op.alter_column(
            "measurement_frequency", existing_type=sa.VARCHAR(length=80), type_=sa.Text(), existing_nullable=False
        )
        batch_op.alter_column("unit", existing_type=sa.VARCHAR(length=40), type_=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("monitoring_plans") as batch_op:
        batch_op.alter_column("unit", existing_type=sa.Text(), type_=sa.VARCHAR(length=40), existing_nullable=True)
        batch_op.alter_column(
            "measurement_frequency", existing_type=sa.Text(), type_=sa.VARCHAR(length=80), existing_nullable=False
        )
