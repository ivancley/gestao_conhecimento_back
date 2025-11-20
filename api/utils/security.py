from typing import Annotated
import jwt
import pytz

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from api.v1._database.models import Usuario

from api.utils.db_services import get_db
from api.utils.settings import settings

tz = pytz.timezone('America/Sao_Paulo')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/conta/login/oauth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
T_OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]    

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(tz) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    Cria um refresh token com tempo de expiração maior.
    """
    to_encode = data.copy()
    expire = datetime.now(tz) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str):
    """
    Verifica se o refresh token é válido.
    
    Args:
        token: O refresh token a ser verificado
        
    Returns:
        dict: Payload do token se válido
        
    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Verificar se é um refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Token inválido: não é um refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")  # Agora sub é o user_id
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Token inválido: sem subject (user_id)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_user(
    db: Session, 
    email: str, senha: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return False
    if not verify_password(senha, usuario.senha):
        return False
    return usuario

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Verificar se é um access token
        if payload.get("type") != "access":
            raise credentials_exception
            
        user_id: str = payload.get("sub")  # Agora sub é o user_id
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if usuario is None:
        raise credentials_exception
    return usuario
