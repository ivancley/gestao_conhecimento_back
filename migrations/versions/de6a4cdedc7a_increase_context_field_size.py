"""increase_context_field_size

Revision ID: de6a4cdedc7a
Revises: c5e8a9b3d1f2
Create Date: 2025-10-21 20:44:18.819132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de6a4cdedc7a'
down_revision: Union[str, Sequence[str], None] = 'c5e8a9b3d1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alterar o campo context de VARCHAR(255) para TEXT
    op.alter_column('conhecimento', 'context',
                    existing_type=sa.String(length=255),
                    type_=sa.TEXT(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Reverter o campo context de TEXT para VARCHAR(255)
    op.alter_column('conhecimento', 'context',
                    existing_type=sa.TEXT(),
                    type_=sa.String(length=255),
                    existing_nullable=False)
