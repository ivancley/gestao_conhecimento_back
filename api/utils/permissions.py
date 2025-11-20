"""
Sistema de permissões baseado em roles.

Este módulo fornece funções e classes para verificar permissões de usuários.

Permissões disponíveis:
    - LINK: CRUD de Links (WebLinks)
    - RAG: Permitir fazer perguntas ao RAG
    - ADMIN: Gerenciar usuários e permissões (tem acesso a tudo automaticamente)

Permissões padrão:
    - Novos usuários: ["RAG", "LINK"]
    - Administrador: ["ADMIN"] (herda automaticamente todas as outras permissões)

Uso:
    - require(["RAG"]) - requer apenas a permissão RAG
    - require(["RAG", "LINK"]) - requer RAG OU LINK (qualquer uma das duas)
    - require(["ADMIN"]) - requer permissão de administrador
"""
from typing import List
from fastapi import HTTPException, Depends, status

from api.v1._database.models import Usuario, PermissaoTipo
from api.utils.security import get_current_user


# Permissões padrão para novos usuários
DEFAULT_USER_PERMISSIONS = ["RAG", "LINK"]


class PermissionChecker:
    """
    Classe que verifica se o usuário tem as permissões necessárias.
    
    Admin sempre tem todas as permissões automaticamente.
    Para outros usuários, verifica se tem pelo menos uma das permissões requeridas.
    """
    
    def __init__(self, required_permissions: List[str]):
        """
        Inicializa o checker com as permissões necessárias.
        
        Args:
            required_permissions: Lista de strings com as permissões necessárias.
                                 Ex: ["RAG"], ["RAG", "LINK"]
        """
        self.required_permissions = required_permissions
        
        # Validar se as permissões são válidas
        valid_perms = {p.value for p in PermissaoTipo}
        for perm in required_permissions:
            if perm not in valid_perms:
                raise ValueError(f"Permissão inválida: {perm}. Permissões válidas: {valid_perms}")
    
    def __call__(self, current_user: Usuario = Depends(get_current_user)) -> Usuario:
        """
        Verifica se o usuário atual tem as permissões necessárias.
        
        Args:
            current_user: Usuário autenticado (injetado via dependency)
            
        Returns:
            Usuario: O usuário atual se tiver permissão
            
        Raises:
            HTTPException: Se o usuário não tiver permissão (403 Forbidden)
        """
        # Verificar se o usuário está ativo
        if not current_user.flg_ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sua conta está desativada. Entre em contato com o administrador."
            )
        
        # Admin tem todas as permissões automaticamente
        if PermissaoTipo.ADMIN.value in current_user.permissoes:
            return current_user
        
        # Verificar se o usuário tem pelo menos uma das permissões necessárias
        user_permissions = set(current_user.permissoes or [])
        required = set(self.required_permissions)
        
        if user_permissions.intersection(required):
            # Usuário tem pelo menos uma das permissões necessárias
            return current_user
        
        # Usuário não tem nenhuma das permissões necessárias
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Você não tem permissão para acessar este recurso. Permissões necessárias: {', '.join(self.required_permissions)}"
        )


def require(permissions: List[str]) -> PermissionChecker:
    """
    Helper function para criar um PermissionChecker.
    
    Uso nos endpoints:
        @router.post("/", dependencies=[Depends(require(["LINK"]))])
        async def create_link(...):
            ...
        
        @router.post("/{id}/ask", dependencies=[Depends(require(["RAG"]))])
        async def ask_rag(...):
            ...
        
        @router.patch("/{id}/permissions", dependencies=[Depends(require(["ADMIN"]))])
        async def update_permissions(...):
            ...
    
    Args:
        permissions: Lista de permissões necessárias. O usuário precisa ter pelo menos uma delas.
                    Ex: ["RAG"], ["RAG", "LINK"], ["ADMIN"]
    
    Returns:
        PermissionChecker: Instância do checker que pode ser usada como dependency
    """
    return PermissionChecker(permissions)


def has_permission(user: Usuario, permission: str) -> bool:
    """
    Verifica se um usuário tem uma permissão específica.
    
    Esta é uma função auxiliar para verificações programáticas (não para usar em dependencies).
    
    Args:
        user: Instância do usuário
        permission: String com a permissão a ser verificada
        
    Returns:
        bool: True se o usuário tem a permissão, False caso contrário
        
    Example:
        if has_permission(current_user, "LINK"):
            # usuário pode criar links
            ...
    """
    if not user.flg_ativo:
        return False
    
    # Admin tem todas as permissões
    if PermissaoTipo.ADMIN.value in (user.permissoes or []):
        return True
    
    return permission in (user.permissoes or [])


def has_any_permission(user: Usuario, permissions: List[str]) -> bool:
    """
    Verifica se um usuário tem pelo menos uma das permissões da lista.
    
    Args:
        user: Instância do usuário
        permissions: Lista de permissões
        
    Returns:
        bool: True se o usuário tem pelo menos uma permissão, False caso contrário
    """
    if not user.flg_ativo:
        return False
    
    # Admin tem todas as permissões
    if PermissaoTipo.ADMIN.value in (user.permissoes or []):
        return True
    
    user_perms = set(user.permissoes or [])
    return bool(user_perms.intersection(set(permissions)))


def has_all_permissions(user: Usuario, permissions: List[str]) -> bool:
    """
    Verifica se um usuário tem todas as permissões da lista.
    
    Args:
        user: Instância do usuário
        permissions: Lista de permissões
        
    Returns:
        bool: True se o usuário tem todas as permissões, False caso contrário
    """
    if not user.flg_ativo:
        return False
    
    # Admin tem todas as permissões
    if PermissaoTipo.ADMIN.value in (user.permissoes or []):
        return True
    
    user_perms = set(user.permissoes or [])
    return set(permissions).issubset(user_perms)

