from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.v1._shared.schemas import (
    ContaCreate, 
    ContaLogin, 
    ContaChangePassword,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ContaView,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)
from api.v1.conta.service import ContaService
from api.v1.conta.mapper import conta_mapper
from api.utils.permissions import DEFAULT_USER_PERMISSIONS

class ContaUseCase:
    """
    Use case for Conta (Account) operations.
    
    This class handles the business logic for account operations like
    registration, authentication, and password management.
    """
    
    def __init__(self):
        self.service = ContaService()
    
    async def register(self, db: Session, data: ContaCreate) -> ContaView:
        """
        Register a new user account with default permissions.
        
        Business rule: New users receive default permissions ["RAG", "LINK"]
        unless explicitly specified.
        
        Args:
            db: Database session
            data: Registration data
            
        Returns:
            ContaView with user data (without sensitive fields)
        """
        try:
            # Aplicar permissões padrão se não foram fornecidas (REGRA DE NEGÓCIO)
            if data.permissoes is None or data.permissoes == []:
                # Criar nova instância com permissões padrão
                data = ContaCreate(
                    nome=data.nome,
                    email=data.email,
                    senha=data.senha,
                    permissoes=DEFAULT_USER_PERMISSIONS  # ["RAG", "LINK"]
                )
            
            user = self.service.register(db, data)
            return conta_mapper.map_to_conta_view(user)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao registrar conta: {str(e)}"
            )
    
    async def login(self, db: Session, data: ContaLogin) -> str:
        """
        Authenticate user and return access and refresh tokens.
        
        Args:
            db: Database session
            data: Login credentials
            
        Returns:
            TokenResponse with access token, refresh token and user data
        """
        try:
            login_result = self.service.login(db, data)
            
            # Map user to ContaView for response
            # user_view = conta_mapper.map_to_conta_view(login_result["user"])
            
            data = TokenResponse(
                access_token=login_result["access_token"],
                refresh_token=login_result["refresh_token"],
                token_type=login_result["token_type"],
                expires_in=login_result["expires_in"],
                # user=user_view
            )
            
            return {"data": data}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao fazer login: {str(e)}"
            )
    
    async def refresh_token(self, db: Session, data: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Generate new access token using refresh token.
        
        Args:
            db: Database session
            data: Refresh token request data
            
        Returns:
            RefreshTokenResponse with new access token
        """
        try:
            refresh_result = self.service.refresh_token(db, data.refresh_token)
            
            return RefreshTokenResponse(
                access_token=refresh_result["access_token"],
                refresh_token=refresh_result["refresh_token"],
                token_type=refresh_result["token_type"],
                expires_in=refresh_result["expires_in"]
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao renovar token: {str(e)}"
            )
    
    async def change_password(self, db: Session, user_id: UUID, data: ContaChangePassword) -> ContaView:
        """
        Change user password.
        
        Args:
            db: Database session
            user_id: User ID
            data: Password change data
            
        Returns:
            ContaView with updated user data
        """
        try:
            user = self.service.change_password(db, user_id, data)
            return conta_mapper.map_to_conta_view(user)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao alterar senha: {str(e)}"
            )
    
    async def request_password_reset(self, db: Session, data: PasswordResetRequest) -> PasswordResetResponse:
        """
        Request password reset token.
        
        Args:
            db: Database session
            data: Password reset request data
            
        Returns:
            PasswordResetResponse with confirmation message
        """
        try:
            return self.service.request_password_reset(db, data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao solicitar redefinição de senha: {str(e)}"
            )
    
    async def confirm_password_reset(self, db: Session, data: PasswordResetConfirm) -> PasswordResetResponse:
        """
        Confirm password reset with token.
        
        Args:
            db: Database session
            data: Password reset confirmation data
            
        Returns:
            PasswordResetResponse with confirmation message
        """
        try:
            return self.service.confirm_password_reset(db, data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao confirmar redefinição de senha: {str(e)}"
            ) 