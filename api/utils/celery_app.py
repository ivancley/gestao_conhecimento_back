"""
Configuração do Celery para processamento assíncrono de tarefas
"""
from celery import Celery
from api.utils.settings import settings

# Configuração do Celery
celery_app = Celery(
    "celery_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'api.utils.tasks.email_tasks',
        'api.v1.web_link.celery.tasks',
    ]
)

# Configurações do Celery
celery_app.conf.update(
    # Configurações gerais
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    
    # Configurações de retry
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Configurações de resultado
    result_expires=3600,  # 1 hora
    
    # Configurações de roteamento
    task_routes={
        'api.utils.tasks.email_tasks.*': {'queue': 'email'},
        'api.utils.tasks.ia_tasks.*': {'queue': 'ia'},
        'api.v1.web_link.celery.tasks.*': {'queue': 'scraping'},
        'api.v1.web_link.celery.tasks.scrape_url_task': {'queue': 'scraping'}, 
    },
    
    # Rate limiting
    task_annotations={
        'api.utils.tasks.email_tasks.send_email_task': {'rate_limit': '10/m'},  # 10 emails por minuto
        'api.utils.tasks.email_tasks.send_bulk_emails_task': {'rate_limit': '2/m'},  # 2 bulk por minuto
    },
) 