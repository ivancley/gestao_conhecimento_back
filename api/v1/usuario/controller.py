from typing import Optional, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Request, Response
from sqlalchemy.orm import Session
from api.v1.usuario.use_case import UsuarioUseCase
from api.v1._shared.schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioView,
    UsuarioPermissoesUpdate
)
from api.utils.db_services import get_db
from api.utils.security import get_current_user
from api.utils.permissions import require
from api.utils.exceptions import exception_nao_encontrado, exception_invalid_query
from api.utils.query_parser import parse_filters

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"], 
)

use_case = UsuarioUseCase()

@router.get(
    "/me",
    response_model=UsuarioView,
    summary="Obter informações do usuário logado",
    description="Retorna as informações e permissões do usuário autenticado atualmente.",
)
async def get_me(
    current_user = Depends(get_current_user)
):
    """
    Endpoint público (apenas requer autenticação) para o usuário verificar suas próprias informações.
    
    Retorna:
    - Dados completos do usuário
    - Lista de permissões que o usuário possui
    """
    # current_user já é o objeto Usuario completo do banco (vem de security.get_current_user)
    # Converter para UsuarioView usando Pydantic
    return UsuarioView.model_validate(current_user)


@router.get(
    "/",
    # response_model=UsuarioResponseList,
    summary="Listar Usuarios",
    description="Recupera uma lista paginada de Usuarios com opções de filtro, ordenação e inclusão de relacionamentos.",
    dependencies=[Depends(require(["ADMIN"]))]
)
async def list_usuarios(
    request: Request, 
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None), 
    skip: int = Query(0, ge=0, description="Número de registros a pular (paginação)."),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar."),
    include: Optional[str] = Query(None, description="Relacionamentos a serem incluídos na resposta (separados por vírgula). Ex: 'usuario,projeto'"),
    sort_by: Optional[str] = Query(None, description="Campo pelo qual ordenar. Ex: 'nome' ou 'endereco.cidade'"),
    sort_dir: Optional[Literal["asc", "desc"]] = Query("asc", description="Direção da ordenação ('asc' ou 'desc')."),
    select_fields: Optional[str] = Query(None, alias="select"),
    search: Optional[str] = Query(None, description="Termo de busca para filtrar resultados.")
):
    
    try:
        include_list = include.split(',') if include else None
        filter_params_dict = parse_filters(request.query_params)
    except ValueError as e:
        raise exception_invalid_query(str(e))

    try:
        result = await use_case.get_all(
            db=db,
            skip=skip,
            limit=limit,
            include=include_list,
            filter_params=filter_params_dict,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
            select_fields=select_fields,
            user_info=user_info
        )
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")

    return result


@router.post(
    "/",
    response_model=UsuarioView,
    status_code=status.HTTP_201_CREATED,
    summary="Criar um novo Usuario",
    dependencies=[Depends(require(["LINK"]))]
)
async def create_usuario(
    data: UsuarioCreate, 
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    try:
        created_entity = await use_case.create(db=db, data=data)
        return created_entity
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao criar Usuario.")


@router.get(
    "/{id}", 
    # response_model=UsuarioView,
    summary="Obter Usuario por ID",
    responses={404: {"description": "Usuario não encontrado"}},
    dependencies=[Depends(require(["ADMIN"]))]
)
async def get_usuario_by_id(  
    id: UUID,  
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None),
    select_fields: Optional[str] = Query(None, alias="select"),
    include: Optional[str] = Query(None, description="Relacionamentos a serem incluídos.")
    
):
    try:
        include_list = include.split(',') if include else None
        result = await use_case.get_by_id(
            db=db, 
            id=id, 
            include=include_list, 
            select_fields=select_fields,
            user_info=user_info
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro inesperado em get_usuario_by_id (ID: {id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")

    if result is None:
        # Lança a exceção 404 se o use_case retornar None
        raise exception_nao_encontrado("Usuario")

    return result

@router.patch(
    "/{id}",
    response_model=UsuarioView,
    summary="Atualizar um Usuario",
    responses={404: {"description": "Usuario não encontrado"}},
    dependencies=[Depends(require(["ADMIN"]))]
)
async def update_usuario(
    id: UUID,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    try:
        updated_entity = await use_case.update(db=db, id=id, data=data)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao atualizar Usuario.")

    if updated_entity is None:
        raise exception_nao_encontrado("Usuario")

    return updated_entity


@router.patch(
    "/{id}/permissoes",
    response_model=UsuarioView,
    summary="Atualizar permissões de um usuário",
    description="Permite que administradores atualizem as permissões de um usuário. As permissões são substituídas completamente.",
    responses={404: {"description": "Usuario não encontrado"}},
    dependencies=[Depends(require(["ADMIN"]))]
)
async def update_usuario_permissoes(
    id: UUID,
    data: UsuarioPermissoesUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Atualiza as permissões de um usuário (apenas ADMIN).
    
    As permissões válidas são:
    - **LINK**: CRUD de Links (WebLinks)
    - **RAG**: Permitir fazer perguntas ao RAG
    - **ADMIN**: Gerenciar usuários e permissões
    
    **Atenção**: Este endpoint substitui completamente as permissões anteriores.
    """
    try:
        # Usar o update normal do use_case com as novas permissões
        update_data = UsuarioUpdate(permissoes=data.permissoes)
        updated_entity = await use_case.update(db=db, id=id, data=update_data)
        
        if updated_entity is None:
            raise exception_nao_encontrado("Usuario")
        
        return updated_entity
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro inesperado ao atualizar permissões do usuário {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar permissões do usuário"
        )


@router.patch(
    "/{id}/desativar",
    response_model=UsuarioView,
    summary="Desativar um usuário",
    description="Desativa um usuário, impedindo seu acesso ao sistema. O usuário não é deletado, apenas inativado.",
    responses={404: {"description": "Usuario não encontrado"}},
    dependencies=[Depends(require(["ADMIN"]))]
)
async def desativar_usuario(
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Desativa um usuário (apenas ADMIN).
    
    O usuário desativado:
    - Não consegue fazer login
    - Perde acesso a todos os endpoints
    - Seus dados são mantidos no sistema
    - Pode ser reativado posteriormente via PATCH /usuarios/{id} com flg_ativo=true
    """
    try:
        # Atualizar o flag de ativo para False
        update_data = UsuarioUpdate(flg_ativo=False)
        updated_entity = await use_case.update(db=db, id=id, data=update_data)
        
        if updated_entity is None:
            raise exception_nao_encontrado("Usuario")
        
        return updated_entity
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro inesperado ao desativar usuário {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao desativar usuário"
        )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Deletar um Usuario",
    responses={
        204: {"description": "Usuario deletado com sucesso"},
        404: {"description": "Usuario não encontrado"}
    },
    dependencies=[Depends(require(["ADMIN"]))]
)
async def delete_usuario(
    id: UUID,
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    try:
        deleted_entity = await use_case.delete(db=db, id=id, user_info=user_info)
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao deletar Usuario.")

    if deleted_entity is None:
        raise exception_nao_encontrado("Usuario")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
