"""add user permissions

Revision ID: c5e8a9b3d1f2
Revises: b4733ca56408
Create Date: 2025-10-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5e8a9b3d1f2'
down_revision: Union[str, Sequence[str], None] = 'b4733ca56408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona campo de permissoes ao modelo Usuario.
    
    O campo permissoes é um ARRAY de strings que pode conter:
    - 'LINK': CRUD de Links (WebLinks)
    - 'RAG': Permitir fazer perguntas ao RAG
    - 'ADMIN': CRUD de Usuários (desativar usuários e gerenciar permissões)
    
    Por padrão, novos usuários recebem as permissões: ["RAG", "LINK"]
    Admin automaticamente tem todas as permissões.
    """
    # Adicionar coluna permissoes como ARRAY de strings com default ["RAG", "LINK"]
    op.add_column('usuario', 
        sa.Column('permissoes', 
                  postgresql.ARRAY(sa.String()), 
                  nullable=False,
                  server_default=sa.text("ARRAY['RAG', 'LINK']"))  # Default para novos usuários
    )


def downgrade() -> None:
    """Remove o campo de permissoes do modelo Usuario."""
    op.drop_column('usuario', 'permissoes')

