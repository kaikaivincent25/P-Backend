"""Add Instagram and Facebook to social platforms."""

from typing import Sequence, Union

from alembic import op


revision: str = "20261109_social_platforms"
down_revision: Union[str, None] = "f1921ef75ec8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE socialplatform ADD VALUE IF NOT EXISTS 'instagram'")
    op.execute("ALTER TYPE socialplatform ADD VALUE IF NOT EXISTS 'facebook'")


def downgrade() -> None:
    pass
