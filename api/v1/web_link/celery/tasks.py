import json
import logging
from typing import Optional
from uuid import UUID

from decouple import config
from openai import OpenAI
from sqlalchemy.orm import Session

from api.utils.celery_app import celery_app
from api.utils.db_services import get_db
from api.v1._database.models import WebLink
from api.v1._shared.schemas import WebLinkUpdate
from api.v1.web_link.ia.summarize import generate_summary
from api.v1.web_link.rag.ingest import ingest_page_content
from api.v1.web_link.scraping.scraping import url_to_json
from api.v1.web_link.service import WebLinkService


logger = logging.getLogger(__name__)
OPENAI_API_KEY = config("OPENAI_API_KEY")

@celery_app.task(
    name="api.v1.web_link.celery.tasks.scrape_url_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60  
)
def scrape_url_task(self, weblink_id: str, url: str) -> Optional[dict]:
    """
    Task assíncrona para:
    1. Fazer scraping da URL
    2. Atualizar o título do WebLink
    3. Ingerir conteúdo no pgvector para RAG
    
    Args:
        weblink_id: ID do WebLink sendo processado
        url: URL a ser scrapeada
        
    Returns:
        dict: Estatísticas do processamento ou None em caso de erro
    """
    db: Session = next(get_db())
    
    try:
        logger.info(f"[SCRAPING] Iniciando para WebLink ID: {weblink_id}")
        logger.info(f"[SCRAPING] URL: {url}")
        
        # 1) Executa o scraping
        page_content = url_to_json(url)
        
        # Print no terminal (debug)
        content_dict = page_content.model_dump()
        print("\n" + "="*80)
        print(f"[SCRAPING COMPLETO] WebLink ID: {weblink_id}")
        print("="*80)
        print(json.dumps(content_dict, ensure_ascii=False, indent=2))
        print("="*80 + "\n")
        
        # 2) Gera resumo usando OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        logger.info(f"[RESUMO] Gerando resumo para WebLink ID: {weblink_id}")
        summary = generate_summary(
            client=client,
            title=page_content.title,
            text_full=page_content.text_full,
            description=page_content.description
        )
        
        print("\n" + "="*80)
        print(f"[RESUMO GERADO] WebLink ID: {weblink_id}")
        print("="*80)
        print(summary)
        print("="*80 + "\n")
        
        # 3) Atualiza o WebLink no banco com resumo e título usando o service
        # IA Gerou AQUI !!!
        #db.query(WebLink).filter(WebLink.id == UUID(weblink_id)).update({
        #    "title": page_content.title,
        #    "resumo": summary
        #})
        #db.commit()
        #
        
        update_data = WebLinkUpdate(
            title=page_content.title,
            resumo=summary
        )
        
        WebLinkService().update(
            db=db,
            id=UUID(weblink_id),
            data=update_data
        )
        
        # 4) Ingere no pgvector para RAG
        ingest_result = ingest_page_content(
            db=db,
            client=client,
            context=url,
            page_content=page_content
        )
        
        print("\n" + "="*80)
        print(f"[INGESTÃO PGVECTOR] WebLink ID: {weblink_id}")
        print("="*80)
        print(json.dumps(ingest_result, ensure_ascii=False, indent=2))
        print("="*80 + "\n")
        
        logger.info(f"[SCRAPING] Processamento completo para WebLink ID: {weblink_id}")
        
        return {
            "weblink_id": weblink_id,
            "scraping": "success",
            "page_title": page_content.title,
            "summary_length": len(summary),
            "ingest": ingest_result
        }
        
    except Exception as e:
        logger.error(f"[SCRAPING] Erro ao processar WebLink ID {weblink_id}: {str(e)}")
        print(f"\n[SCRAPING ERRO] WebLink ID: {weblink_id} - Erro: {str(e)}\n")
        
        # Retry automático está configurado no decorator
        raise self.retry(exc=e)
        
    finally:
        db.close()

