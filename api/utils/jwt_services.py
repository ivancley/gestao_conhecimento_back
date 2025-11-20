import jwt
from datetime import datetime, timedelta, timezone
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from api.utils.settings import settings
from api.utils.exceptions import ExceptionUnauthorized
from api.utils.db_services import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        # A claim "sub" representa o identificador do usuário
        user_id = payload.get("user_id") or payload.get("sub")

        # Se mesmo após a tentativa acima o user_id estiver ausente, o token é inválido
        if user_id is None:
            raise ExceptionUnauthorized(detail="Token não contém 'sub' (user_id)")

        return user_id, token  

    except ExpiredSignatureError:
        raise ExceptionUnauthorized(detail="Token expirado")

    except InvalidTokenError:
        raise ExceptionUnauthorized(detail="Token inválido")

def decode_refresh_token_unsafe(token: str) -> dict:
    """
    Decodifica um refresh token sem verificar a assinatura.
    Útil para extrair informações do token durante o processo de renovação.
    
    Args:
        token: O refresh token JWT
        
    Returns:
        dict: Claims do token
        
    Raises:
        ExceptionUnauthorized: Se não conseguir decodificar o token
    """
    try:
        # Decodifica sem verificar assinatura
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return decoded_token
    except jwt.PyJWTError:
        raise ExceptionUnauthorized(detail="Token malformado")

def is_token_nearing_expiration(token: str, margin_seconds: int = 30) -> bool:
    """
    Verifica se um token JWT está prestes a expirar, sem validar a assinatura.

    Args:
        token: O token JWT.
        margin_seconds: A margem de segurança em segundos.

    Returns:
        True se o token está dentro da margem de expiração, False caso contrário.
    """
    try:
        # Decodifica o token apenas para ler os claims, sem verificar a assinatura
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        
        exp_timestamp = decoded_token.get("exp")
        if not exp_timestamp:
            # Se não houver claim de expiração, não podemos verificar
            return False

        # Converte o timestamp de expiração para um objeto datetime
        exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        # Pega o tempo atual em UTC
        now_time = datetime.now(timezone.utc)
        
        # Calcula o tempo restante
        time_remaining = exp_time - now_time
        
        # Verifica se o tempo restante é menor que a margem de segurança
        return time_remaining < timedelta(seconds=margin_seconds)

    except jwt.PyJWTError:
        # Se o token for inválido e não puder ser decodificado, trata como expirado
        return True
