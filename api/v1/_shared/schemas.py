from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Any, Dict, ForwardRef, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

class TipoAtividade(str, PyEnum):
    OBJETIVA = "OBJETIVA"
    SUBJETIVA = "SUBJETIVA"

# Forward References
UsuarioViewRef = ForwardRef('UsuarioView')
UsuarioCreateRef = ForwardRef('UsuarioCreate')
UsuarioUpdateRef = ForwardRef('UsuarioUpdate')
WebLinkViewRef = ForwardRef('WebLinkView')
ConhecimentoViewRef = ForwardRef('ConhecimentoView')


class CustomBaseModel(BaseModel):
    flg_ativo: bool = Field(True)
    flg_excluido: bool = Field(False)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True}


class UsuarioBase(CustomBaseModel):
    nome: str
    email: str
    senha: Optional[str] = None
    permissoes: List[str] = Field(default_factory=lambda: ["RAG", "LINK"])

class UsuarioCreate(BaseModel): 
    nome: str 
    email: str 
    senha: str
    permissoes: Optional[List[str]] = Field(default=None, description="Permissões do usuário. Se não informado, usa padrão: ['RAG', 'LINK']")


class UsuarioUpdate(BaseModel): 
    nome: Optional[str] = Field(None) 
    email: Optional[str] = Field(None) 
    senha: Optional[str] = Field(None)
    permissoes: Optional[List[str]] = Field(None)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True}
    
    @model_validator(mode='after')
    def validate_permissoes(self):
        """Valida se as permissões são válidas quando fornecidas"""
        if self.permissoes is not None:
            valid_perms = {"LINK", "RAG", "ADMIN"}
            invalid = set(self.permissoes) - valid_perms
            if invalid:
                raise ValueError(f"Permissões inválidas: {', '.join(invalid)}. Permissões válidas: {', '.join(valid_perms)}")
        return self
    

class UsuarioGeneric(CustomBaseModel):
    nome: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    senha: Optional[str] = Field(None)
    permissoes: Optional[List[str]] = Field(None)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True, "from_attributes": True}


class UsuarioView(BaseModel):
    id: UUID
    nome: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    permissoes: Optional[List[str]] = Field(None)
    flg_ativo: bool
    flg_excluido: bool
    created_at: datetime
    updated_at: datetime
    model_config: Dict[str, Any] = {"from_attributes": True, "arbitrary_types_allowed": True}

# --- Response List Schema ---
class UsuarioResponseList(BaseModel):
    total: int
    data: List["UsuarioViewRef"]


# ============== WebLink Schemas ==============
class WebLinkBase(CustomBaseModel):
    title: Optional[str] = None
    weblink: Optional[str] = None
    resumo: Optional[str] = None
    usuario_id: UUID


class WebLinkCreate(BaseModel):
    weblink: Optional[str] = None
    resumo: Optional[str] = None
    usuario_id: Optional[UUID] = None


class WebLinkUpdate(BaseModel):
    title: Optional[str] = Field(None)
    weblink: Optional[str] = Field(None)
    resumo: Optional[str] = Field(None)
    usuario_id: Optional[UUID] = Field(None)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True}


class WebLinkGeneric(CustomBaseModel):
    weblink: Optional[str] = Field(None)
    resumo: Optional[str] = Field(None)
    usuario_id: Optional[UUID] = Field(None)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True, "from_attributes": True}


class WebLinkView(WebLinkBase):
    id: UUID
    flg_ativo: bool
    flg_excluido: bool
    created_at: datetime
    updated_at: datetime
    model_config: Dict[str, Any] = {"from_attributes": True, "arbitrary_types_allowed": True}


class WebLinkResponseList(BaseModel):
    total: int
    data: List["WebLinkViewRef"]


# ============== Conhecimento Schemas ==============
class ConhecimentoBase(CustomBaseModel):
    title: str
    context: str
    content: str


class ConhecimentoCreate(BaseModel):
    """Schema para criação de conhecimento. O embedding é gerado automaticamente."""
    title: str
    context: str
    content: str


class ConhecimentoUpdate(BaseModel):
    title: Optional[str] = Field(None)
    context: Optional[str] = Field(None)
    content: Optional[str] = Field(None)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True}


class ConhecimentoGeneric(CustomBaseModel):
    title: Optional[str] = Field(None)
    context: Optional[str] = Field(None)
    content: Optional[str] = Field(None)
    model_config: Dict[str, Any] = {"arbitrary_types_allowed": True, "from_attributes": True}


class ConhecimentoView(ConhecimentoBase):
    id: UUID
    flg_ativo: bool
    flg_excluido: bool
    created_at: datetime
    updated_at: datetime
    model_config: Dict[str, Any] = {"from_attributes": True, "arbitrary_types_allowed": True}


class ConhecimentoResponseList(BaseModel):
    total: int
    data: List["ConhecimentoViewRef"]


class ConhecimentoBuscaRequest(BaseModel):
    """Schema para busca de conhecimentos similares"""
    query: str = Field(..., description="Texto da consulta para busca semântica")
    limit: int = Field(5, ge=1, le=50, description="Número máximo de resultados (entre 1 e 50)")
    context: Optional[str] = Field(None, description="Filtrar por contexto específico")


class ConhecimentoBuscaResult(BaseModel):
    """Schema para resultado de busca com score de similaridade"""
    conhecimento: ConhecimentoView
    distance: float = Field(..., description="Distância L2 (menor = mais similar)")
    model_config: Dict[str, Any] = {"from_attributes": True}


class PasswordResetRequest(BaseModel):
    """Schema para requisição de redefinição de senha"""
    email: EmailStr = Field(..., description="Email do usuário que deseja redefinir a senha")

class PasswordResetConfirm(BaseModel):
    """Schema para confirmação de redefinição de senha"""
    token: str = Field(..., description="Token de redefinição de senha")
    nova_senha: str = Field(..., min_length=6, description="Nova senha deve ter pelo menos 6 caracteres")

class PasswordResetResponse(BaseModel):
    """Schema para resposta de solicitação de redefinição de senha"""
    message: str = Field(..., description="Mensagem de confirmação")
    email: EmailStr = Field(..., description="Email para onde foi enviado o token")
    task_id: Optional[str] = Field(None, description="ID da tarefa de envio de email (para acompanhamento)")


class ContaCreate(BaseModel):
    """Schema para criação de conta (registro)"""
    nome: str
    email: str
    senha: str = Field(..., min_length=6, description="Senha deve ter pelo menos 6 caracteres")
    permissoes: Optional[List[str]] = Field(default=None, description="Permissões do usuário. Se não informado, usa padrão: ['RAG', 'LINK']")

class ContaLogin(BaseModel):
    """Schema para login"""
    email: str
    senha: str

class ContaChangePassword(BaseModel):
    """Schema para trocar senha"""
    senha_atual: str
    nova_senha: str = Field(..., min_length=6, description="Nova senha deve ter pelo menos 6 caracteres")

class TokenResponse(BaseModel):
    """Schema para resposta de token"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int

class RefreshTokenRequest(BaseModel):
    """Schema para requisição de refresh token"""
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    """Schema para resposta de refresh token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str

class ContaView(CustomBaseModel):
    """Schema para visualização de conta (sem dados sensíveis)"""
    id: UUID
    nome: str
    email: str
    created_at: datetime
    updated_at: datetime
    model_config: Dict[str, Any] = {"from_attributes": True}


class UsuarioPermissoesUpdate(BaseModel):
    """Schema para atualizar permissões de um usuário (apenas admin)"""
    permissoes: List[str] = Field(..., description="Lista de permissões: LINK, RAG, ADMIN")
    
    @model_validator(mode='after')
    def validate_permissoes(self):
        """Valida se as permissões são válidas"""
        valid_perms = {"LINK", "RAG", "ADMIN"}
        invalid = set(self.permissoes) - valid_perms
        if invalid:
            raise ValueError(f"Permissões inválidas: {', '.join(invalid)}. Permissões válidas: {', '.join(valid_perms)}")
        return self

# --- Atualizar Forward References ---
# Usuario schemas
UsuarioBase.model_rebuild()
UsuarioCreate.model_rebuild()
UsuarioUpdate.model_rebuild()
UsuarioGeneric.model_rebuild()
UsuarioView.model_rebuild()
UsuarioResponseList.model_rebuild()
UsuarioPermissoesUpdate.model_rebuild()

# WebLink schemas
WebLinkBase.model_rebuild()
WebLinkCreate.model_rebuild()
WebLinkUpdate.model_rebuild()
WebLinkGeneric.model_rebuild()
WebLinkView.model_rebuild()
WebLinkResponseList.model_rebuild()

# Conhecimento schemas
ConhecimentoBase.model_rebuild()
ConhecimentoCreate.model_rebuild()
ConhecimentoUpdate.model_rebuild()
ConhecimentoGeneric.model_rebuild()
ConhecimentoView.model_rebuild()
ConhecimentoResponseList.model_rebuild()
ConhecimentoBuscaRequest.model_rebuild()
ConhecimentoBuscaResult.model_rebuild()

# Auth schemas
ContaCreate.model_rebuild()
ContaLogin.model_rebuild()
ContaView.model_rebuild()
ContaChangePassword.model_rebuild()
PasswordResetRequest.model_rebuild()
PasswordResetConfirm.model_rebuild()
PasswordResetResponse.model_rebuild()
TokenResponse.model_rebuild()
RefreshTokenRequest.model_rebuild()
RefreshTokenResponse.model_rebuild()