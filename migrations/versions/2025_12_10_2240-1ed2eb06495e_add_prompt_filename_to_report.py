"""add_prompt_filename_to_report

Revision ID: 1ed2eb06495e
Revises: d8bb40b07ff3
Create Date: 2025-12-10 22:40:05.363259

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1ed2eb06495e'
down_revision: str | Sequence[str] | None = 'd8bb40b07ff3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('report', sa.Column('prompt_name', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('report', 'prompt_name')
