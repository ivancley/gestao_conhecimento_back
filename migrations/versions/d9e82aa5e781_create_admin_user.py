"""create admin user

Revision ID: d9e82aa5e781
Revises: de6a4cdedc7a
Create Date: 2025-11-20 16:00:24.090868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# revision identifiers, used by Alembic.
revision: str = 'd9e82aa5e781'
down_revision: Union[str, Sequence[str], None] = 'de6a4cdedc7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    admin_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    admin_email = "admin@gmail.com"
    admin_nome = "Administrador"
    admin_senha = pwd_context.hash("Senha@123")

    conn.execute(
        sa.text(
            """
            INSERT INTO "usuario" 
                (id, nome, email, senha, permissoes, created_at, updated_at, flg_ativo, flg_excluido)
            VALUES 
                (:id, :nome, :email, :senha, :permissoes, :created_at, :updated_at, :flg_ativo, :flg_excluido)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "id": str(admin_id),
            "nome": admin_nome,
            "email": admin_email,
            "senha": admin_senha,
            "permissoes": ["admin"],
            "created_at": now,
            "updated_at": now,
            "flg_ativo": True,
            "flg_excluido": False,
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM "usuario"
            WHERE email = :email
            """
        ),
        {"email": "admin@gmail.com"},
    )