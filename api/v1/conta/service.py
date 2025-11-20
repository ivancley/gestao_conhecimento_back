from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets

from api.v1._database.models import Usuario, PasswordResetToken
from api.v1._shared.schemas import (
    ContaLogin, 
    ContaChangePassword, 
    UsuarioView,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm
)
from api.utils.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    verify_refresh_token
)
from api.utils.settings import settings
from api.v1.conta.mapper import UsuarioMapper
from api.v1._shared.schemas import ContaCreate, UsuarioCreate
from api.v1.usuario.service import UsuarioService
from api.utils.async_email_service import async_email_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ContaService:
    """
    Service for authentication and account management.
    """

    def __init__(self):
        """Initialize the ContaService with its mapper."""
        self.mapper = UsuarioMapper()
        self.usuario_service = UsuarioService()
        
    def register(self, db: Session, data: ContaCreate) -> Usuario:
        """
        Register a new user account.
        
        Args:
            db: Database session
            data: Registration data
            
        Returns:
            The created user
            
        Raises:
            HTTPException: If email already exists or other validation errors
        """
        # Verifica se o email já está em uso
        existing_user = db.query(Usuario).filter(Usuario.email == data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )

        
        # Criptografa a senha (bcrypt limita a 72 bytes)
        # Trunca em bytes para evitar erro com caracteres especiais
        senha_bytes = data.senha.encode('utf-8')[:72]
        senha_truncada = senha_bytes.decode('utf-8', errors='ignore')
        hashed_password = pwd_context.hash(senha_truncada)
        
        # Cria os dados do usuário
        usuario_data = UsuarioCreate(
            nome=data.nome,
            email=data.email,
            senha=hashed_password,
            permissoes=data.permissoes if hasattr(data, 'permissoes') else None
        )
        
        try:
            return self.usuario_service.create(db=db, data=usuario_data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao criar conta"
            )

    def login(self, db: Session, data: ContaLogin) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens.
        
        Args:
            db: Database session
            data: Login credentials
            
        Returns:
            Dictionary with access token, refresh token, and user info
            
        Raises:
            HTTPException: If credentials are invalid or user is inactive
        """
        # Find user by email
        user = db.query(Usuario).filter(Usuario.email == data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(data.senha, user.senha):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.flg_ativo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta desativada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate access and refresh tokens with user_id as sub
        token_data = {
            "sub": str(user.id),  # user_id como sub
            "email": user.email,
            "nome": user.nome
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        }
    
    def refresh_token(self, db: Session, refresh_token: str) -> Dict[str, Any]:
        """
        Generate new access token using refresh token.
        
        Args:
            db: Database session
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access token
            
        Raises:
            HTTPException: If refresh token is invalid or user not found
        """
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub")  # Agora sub é o user_id
        
        # Get user from database
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        if not user.flg_ativo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta desativada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate new access token with updated user info
        token_data = {
            "sub": str(user.id),  # user_id como sub
            "email": user.email,
            "nome": user.nome,
            "tipo_usuario": user.tipo_usuario
        }
        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        }
    
    def change_password(self, db: Session, user_id: UUID, data: ContaChangePassword) -> Usuario:
        """
        Change user password.
        
        Args:
            db: Database session
            user_id: User ID
            data: Password change data
            
        Returns:
            Updated user
            
        Raises:
            HTTPException: If user not found or current password is incorrect
        """
        # Get user
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verify current password
        if not verify_password(data.senha_atual, user.senha):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta"
            )
        
        # Update password
        user.senha = pwd_context.hash(data.nova_senha)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_profile(self, db: Session, user_id: UUID) -> UsuarioView:
        """
        Get user profile.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User profile view
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return self.mapper.map_to_view(user)

    def update_profile(self, db: Session, user_id: UUID, data: Dict[str, Any]) -> UsuarioView:
        """
        Update user profile.
        
        Args:
            db: Database session
            user_id: User ID
            data: Profile update data
            
        Returns:
            Updated user profile view
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Update fields
        for key, value in data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        return self.mapper.map_to_view(user)

    def request_password_reset(self, db: Session, data: PasswordResetRequest) -> PasswordResetResponse:
        """
        Request password reset token.
        
        Args:
            db: Database session
            data: Password reset request data
            
        Returns:
            PasswordResetResponse with confirmation message
            
        Raises:
            HTTPException: If email not found or other errors
        """
        # Find user by email
        user = db.query(Usuario).filter(Usuario.email == data.email).first()
        if not user:
            # Por segurança, sempre retornamos sucesso mesmo se o email não existir
            return PasswordResetResponse(
                message="Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.",
                email=data.email
            )
        
        if not user.flg_ativo:
            return PasswordResetResponse(
                message="Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.",
                email=data.email
            )
        
        try:
            # Invalidar tokens existentes
            db.query(PasswordResetToken).filter(
                PasswordResetToken.usuario_id == user.id,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.now()
            ).update({"used": True})
            
            # Gerar novo token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)  # Token válido por 1 hora
            
            # Criar registro do token
            reset_token = PasswordResetToken(
                usuario_id=user.id,
                token=token,
                expires_at=expires_at,
                used=False
            )
            
            db.add(reset_token)
            db.commit()
            
            # Enviar email de forma assíncrona
            task_id = async_email_service.send_password_reset_async(
                to_email=user.email,
                token=token,
                expiry_time="1 hora"
            )
            
            return PasswordResetResponse(
                message="Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.",
                email=data.email,
                task_id=task_id
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao processar solicitação"
            )
    
    def confirm_password_reset(self, db: Session, data: PasswordResetConfirm) -> PasswordResetResponse:
        """
        Confirm password reset with token.
        
        Args:
            db: Database session
            data: Password reset confirmation data
            
        Returns:
            PasswordResetResponse with confirmation message
            
        Raises:
            HTTPException: If token is invalid, expired, or other errors
        """
        try:
            # Buscar token válido
            reset_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == data.token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.utcnow(),
                PasswordResetToken.flg_ativo == True
            ).first()
            
            if not reset_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token inválido ou expirado"
                )
            
            # Buscar usuário
            user = db.query(Usuario).filter(Usuario.id == reset_token.usuario_id).first()
            if not user or not user.flg_ativo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token inválido ou expirado"
                )
            
            # Atualizar senha
            user.senha = pwd_context.hash(data.nova_senha)
            
            # Marcar token como usado
            reset_token.used = True
            
            db.commit()
            
            return PasswordResetResponse(
                message="Senha redefinida com sucesso. Você já pode fazer login com a nova senha.",
                email=user.email
            )
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao redefinir senha"
            )
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Clean up expired password reset tokens.
        
        Args:
            db: Database session
            
        Returns:
            Number of tokens cleaned up
        """
        try:
            # Marcar tokens expirados como inativos
            expired_count = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at <= datetime.utcnow(),
                PasswordResetToken.flg_ativo == True
            ).update({"flg_ativo": False})
            
            db.commit()
            return expired_count
            
        except Exception as e:
            db.rollback()
            return 0
