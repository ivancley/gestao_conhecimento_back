import logging
from typing import Literal, Optional
from uuid import UUID

from decouple import config
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Header,
    Query,
    Request,
    Response,
    status,
)
from openai import OpenAI
from sqlalchemy.orm import Session

from api.utils.db_services import get_db
from api.utils.exceptions import exception_invalid_query, exception_nao_encontrado
from api.utils.security import get_current_user
from api.utils.permissions import require
from api.utils.query_parser import parse_filters
from api.v1._shared.custom_schemas import RagQueryRequest, RagQueryResponse
from api.v1._shared.schemas import (
    WebLinkCreate,
    WebLinkUpdate,
    WebLinkView,
)
from api.v1.web_link.rag.query import query_weblink_knowledge
from api.v1.web_link.use_case import WebLinkUseCase

logger = logging.getLogger(__name__)

OPENAI_API_KEY = config("OPENAI_API_KEY")


router = APIRouter(
    prefix="/web_links",
    tags=["WebLinks"], 
)

use_case = WebLinkUseCase()

@router.get(
    "/",
    # response_model=MedicoResponseList,
    summary="Listar WebLinks",
    description="Recupera uma lista paginada de WebLinks com opções de filtro, ordenação e inclusão de relacionamentos.",
    dependencies=[Depends(require(["LINK"]))]
)
async def list_web_links(
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
    response_model=WebLinkView,
    status_code=status.HTTP_201_CREATED,
    summary="Criar um novo WebLink",
    dependencies=[Depends(require(["LINK"]))]
)
async def create_web_link(
    data: WebLinkCreate, 
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    try:
        created_entity = await use_case.create(db=db, data=data, user_info=user_info)
        return created_entity
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao criar WebLink.")


@router.get(
    "/{id}", 
    response_model=WebLinkView,
    summary="Obter WebLink por ID",
    responses={404: {"description": "WebLink não encontrado"}},
    dependencies=[Depends(require(["LINK"]))]
)
async def get_web_link_by_id(  
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
            select_fields=select_fields
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro inesperado em get_web_link_by_id (ID: {id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno no servidor.")

    if result is None:
        # Lança a exceção 404 se o use_case retornar None
        raise exception_nao_encontrado("WebLink")

    return result

@router.patch(
    "/{id}",
    response_model=WebLinkView,
    summary="Atualizar um WebLink",
    responses={404: {"description": "WebLink não encontrado"}},
    dependencies=[Depends(require(["LINK"]))]
)
async def update_web_link(
    id: UUID,
    data: WebLinkUpdate,
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    try:
        updated_entity = await use_case.update(db=db, id=id, data=data, user_info=user_info)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao atualizar WebLink.")

    if updated_entity is None:
        raise exception_nao_encontrado("WebLink")

    return updated_entity


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Deletar um WebLink",
    responses={
        204: {"description": "WebLink deletado com sucesso"},
        404: {"description": "WebLink não encontrado"}
    },
    dependencies=[Depends(require(["LINK"]))]
)
async def delete_web_link(
    id: UUID,
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    try:
        deleted_entity = await use_case.delete(db=db, id=id)
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao deletar WebLink.")

    if deleted_entity is None:
        raise exception_nao_encontrado("WebLink")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{id}/ask",
    response_model=RagQueryResponse,
    summary="Consultar conhecimento do WebLink via RAG",
    description="Faz uma pergunta sobre o conteúdo ingerido de um WebLink específico usando RAG (Retrieval-Augmented Generation)",
    responses={
        404: {"description": "WebLink não encontrado ou sem conhecimento ingerido"},
        400: {"description": "Erro na requisição"}
    },
    dependencies=[Depends(require(["RAG"]))]
)
async def ask_weblink(
    id: UUID,
    data: RagQueryRequest,
    db: Session = Depends(get_db),
    user_info = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Consulta o conhecimento de um WebLink usando RAG.
    
    - **id**: ID do WebLink a ser consultado
    - **question**: Pergunta a ser respondida com base no conhecimento ingerido
    
    Retorna a resposta gerada pela IA com score de confiança e tokens usados.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        result = query_weblink_knowledge(
            db=db,
            client=client,
            weblink_id=id,
            question=data.question
        )
        
        return result
        
    except ValueError as ve:
        # Erros de validação (WebLink não existe, sem conhecimento, etc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Erro ao processar query RAG para WebLink {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar consulta RAG"
        )