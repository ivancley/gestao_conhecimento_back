from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.v1.conta.use_case import ContaUseCase
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
from api.utils.db_services import get_db
from api.utils.security import get_current_user
from api.utils.exceptions import exception_nao_encontrado

router = APIRouter(
    prefix="/conta",
    tags=["Conta"], 
)

use_case = ContaUseCase()

@router.post(
    "/registro",
    response_model=ContaView,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nova conta",
    description="Cria uma nova conta de usuário no sistema."
)
async def registrar_conta(
    data: ContaCreate, 
    db: Session = Depends(get_db)
):
    """
    Registra uma nova conta de usuário.
    
    - **nome**: Nome completo do usuário
    - **email**: Email único do usuário
    - **senha**: Senha para acesso
    """
    try:
        conta = await use_case.register(db=db, data=data)
        return conta
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erro interno ao registrar conta."
        )

@router.post(
    "/login",
    # response_model=TokenResponse,
    summary="Fazer login",
    description="Autentica o usuário e retorna tokens de acesso e refresh."
)
async def fazer_login(
    data: ContaLogin,
    db: Session = Depends(get_db)
):
    """
    Autentica o usuário e retorna tokens de acesso e refresh.
    
    - **email**: Email do usuário
    - **senha**: Senha do usuário
    """
    try:
        token_response = await use_case.login(db=db, data=data)
        return token_response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao fazer login."
        )

@router.post(
    "/login/oauth",
    response_model=TokenResponse,
    summary="Fazer login (OAuth2)",
    description="Autentica o usuário usando OAuth2 form e retorna tokens de acesso e refresh."
)
async def fazer_login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autentica o usuário usando OAuth2 form.
    Compatible com ferramentas que usam OAuth2 form.
    """
    try:
        data = ContaLogin(email=form_data.username, senha=form_data.password)
        token_response = await use_case.login(db=db, data=data)
        return token_response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao fazer login."
        )

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Renovar token de acesso",
    description="Gera um novo token de acesso usando o refresh token."
)
async def renovar_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Gera um novo token de acesso usando o refresh token.
    
    - **refresh_token**: Refresh token válido obtido no login
    """
    try:
        refresh_response = await use_case.refresh_token(db=db, data=data)
        return refresh_response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao renovar token."
        )

@router.post(
    "/trocar-senha",
    response_model=ContaView,
    summary="Trocar senha",
    description="Altera a senha do usuário autenticado.",
    dependencies=[Depends(get_current_user)]
)
async def trocar_senha(
    data: ContaChangePassword,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Altera a senha do usuário autenticado.
    
    - **senha_atual**: Senha atual do usuário
    - **nova_senha**: Nova senha desejada
    """
    try:
        conta = await use_case.change_password(db=db, user_id=current_user.id, data=data)
        return conta
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao trocar senha."
        )

@router.get(
    "/perfil",
    response_model=ContaView,
    summary="Obter perfil do usuário",
    description="Retorna os dados do perfil do usuário autenticado.",
    dependencies=[Depends(get_current_user)]
)
async def obter_perfil(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Retorna os dados do perfil do usuário autenticado.
    """
    try:
        from api.v1.conta.mapper import conta_mapper
        conta = conta_mapper.map_to_conta_view(current_user)
        
        if conta is None:
            raise exception_nao_encontrado("Usuário")
            
        return conta
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter perfil."
        )

@router.post(
    "/esqueci-senha",
    response_model=PasswordResetResponse,
    summary="Solicitar redefinição de senha",
    description="Envia um email com instruções para redefinir a senha."
)
async def esqueci_senha(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita redefinição de senha via email.
    
    - **email**: Email da conta que deseja redefinir a senha
    
    Por motivos de segurança, sempre retorna sucesso, mesmo se o email não existir.
    """
    try:
        response = await use_case.request_password_reset(db=db, data=data)
        return response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar solicitação."
        )

@router.post(
    "/redefinir-senha",
    response_model=PasswordResetResponse,
    summary="Redefinir senha com token",
    description="Redefine a senha usando o token recebido por email."
)
async def redefinir_senha(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Redefine a senha usando o token recebido por email.
    
    - **token**: Token de redefinição recebido por email
    - **nova_senha**: Nova senha desejada (mínimo 6 caracteres)
    """
    try:
        response = await use_case.confirm_password_reset(db=db, data=data)
        return response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao redefinir senha."
        )

@router.post(
    "/admin/limpar-tokens-expirados",
    summary="Limpar tokens de senha expirados",
    description="Remove tokens de redefinição de senha expirados (endpoint administrativo).",
    dependencies=[Depends(get_current_user)]
)
async def limpar_tokens_expirados(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Limpa tokens de redefinição de senha expirados.
    
    Endpoint administrativo para manutenção do sistema.
    """
    try:
        # Verificar se é administrador
        if current_user.tipo_usuario != TipoUsuario.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Apenas administradores podem executar esta ação."
            )
        
        from api.v1.conta.service import ContaService
        service = ContaService()
        tokens_removidos = service.cleanup_expired_tokens(db)
        
        return {
            "message": f"Limpeza concluída. {tokens_removidos} tokens expirados foram marcados como inativos.",
            "tokens_removidos": tokens_removidos
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao limpar tokens."
        )

@router.get(
    "/email-status/{task_id}",
    summary="Verificar status do envio de email",
    description="Verifica o status de uma tarefa de envio de email."
)
async def verificar_status_email(task_id: str):
    """
    Verifica o status de uma tarefa de envio de email.
    
    - **task_id**: ID da tarefa retornado no endpoint de solicitação de senha
    """
    try:
        from api.utils.async_email_service import async_email_service
        
        status_info = async_email_service.get_task_status(task_id)
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status da tarefa: {str(e)}"
        )