import uuid
import pytz
import logging
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import (
    Table, Column, String, Text, Date, DateTime, Boolean, ForeignKey, Index,
    Enum as SqlAlchemyEnum, Integer, ARRAY # Adicionar Integer e ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TEXT
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List
from pgvector.sqlalchemy import Vector


Base = declarative_base()
tz = pytz.timezone('America/Sao_Paulo') # Defina seu timezone
logger = logging.getLogger(__name__)


class PermissaoTipo(str, PyEnum):
    """Tipos de permissões do sistema"""
    LINK = "LINK"      # CRUD de Links (WebLinks)
    RAG = "RAG"        # Permitir fazer perguntas ao RAG
    ADMIN = "ADMIN"    # CRUD de Usuários (desativar usuários e gerenciar permissões)


class BaseModel(Base):
    __abstract__ = True
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz), onupdate=lambda: datetime.now(tz), nullable=False)
    flg_ativo = Column(Boolean, default=True, nullable=False, server_default='true') 
    flg_excluido = Column(Boolean, default=False, nullable=False, server_default='false')


class Usuario(BaseModel):
    __tablename__ = 'usuario'
       
    nome = Column(String(255), nullable=False)   
    email = Column(String(255), nullable=False, unique=True, index=True)   
    senha = Column(String(255), nullable=True)
    permissoes = Column(ARRAY(String), nullable=False, default=list, server_default='{}')

    # Relacionamento
    web_links: Mapped[List["WebLink"]] = relationship("WebLink", back_populates="usuario", lazy="selectin")

    def __repr__(self):
        return f"<Usuario(id={self.id}), nome={self.nome}>"


class PasswordResetToken(BaseModel):
    __tablename__ = 'password_reset_token'

    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey('usuario.id'), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    
    # Relacionamento
    usuario = relationship("Usuario", lazy="selectin")

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, usuario_id={self.usuario_id})>"
        

class WebLink(BaseModel):
    __tablename__ = 'weblink'
       
    weblink = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)
    resumo = Column(Text, nullable=True)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey('usuario.id'), nullable=False, index=True) 

    # Relacionamento
    usuario = relationship("Usuario", lazy="selectin")

    def __repr__(self):
        return f"<WebLink(id={self.id}), weblink={self.weblink}>"

# Tabela de Rag 
EMBED_DIM = 1536

class Conhecimento(Base): 
    __tablename__ = "conhecimento"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(TEXT, nullable=False)
    context = Column(TEXT, nullable=False, index=True)  # Alterado de String(255) para TEXT
    content = Column(TEXT, nullable=False)
    embedding = Column(Vector(EMBED_DIM), nullable=False)

# Índice vetorial (IVFFLAT com L2).
Index(
    "ix_faq_embedding_ivfflat",
    Conhecimento.embedding,
    postgresql_using="ivfflat",
    postgresql_with={"lists": 100},
    postgresql_ops={"embedding": "vector_l2_ops"},
)

    