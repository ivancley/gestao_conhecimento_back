"""
Tarefas assíncronas para envio de emails usando Celery
"""
import time
from typing import Dict, Any, List
from celery import current_task

from api.utils.celery_app import celery_app
from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_email_task(self, template_type: str, to_email: str, variables: Dict[str, Any], 
                   from_name: str = None, custom_subject: str = None):
    """
    Tarefa assíncrona para enviar um email individual
    
    Args:
        template_type: Tipo do template (ex: 'notification', 'welcome')
        to_email: Email do destinatário
        variables: Variáveis para o template
        from_name: Nome do remetente (opcional)
        custom_subject: Assunto customizado (opcional)
    """
    try:
        # Atualizar status da tarefa
        current_task.update_state(
            state='PROGRESS',
            meta={'status': f'Enviando email para {to_email}', 'current': 0, 'total': 1}
        )
        
        # Inicializar serviço de email
        email_service = EmailService()
        
        # Converter string para enum
        email_template_type = EmailTemplateType(template_type)
        
        # Enviar email
        success = email_service.send_email(
            template_type=email_template_type,
            to_email=to_email,
            variables=variables,
            from_name=from_name,
            custom_subject=custom_subject
        )
        
        if success:
            return {
                'status': 'SUCCESS',
                'message': f'Email enviado com sucesso para {to_email}',
                'to_email': to_email,
                'template_type': template_type
            }
        else:
            raise Exception(f"Falha ao enviar email para {to_email}")
            
    except Exception as exc:
        # Log do erro
        error_msg = f"Erro ao enviar email para {to_email}: {str(exc)}"
        
        # Tentar novamente se não excedeu o limite
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        # Se excedeu, retornar erro
        return {
            'status': 'FAILURE',
            'message': error_msg,
            'to_email': to_email,
            'template_type': template_type,
            'retries': self.request.retries
        }


@celery_app.task(bind=True)
def send_bulk_emails_task(self, email_list: List[Dict[str, Any]]):
    """
    Tarefa assíncrona para enviar emails em lote
    
    Args:
        email_list: Lista de dicionários com dados dos emails
                   [{'template_type': str, 'to_email': str, 'variables': dict, ...}, ...]
    """
    try:
        total_emails = len(email_list)
        results = []
        
        # Atualizar status inicial
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Iniciando envio em lote', 'current': 0, 'total': total_emails}
        )
        
        # Inicializar serviço de email
        email_service = EmailService()
        
        for index, email_data in enumerate(email_list):
            try:
                # Atualizar progresso
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Enviando email {index + 1} de {total_emails}',
                        'current': index,
                        'total': total_emails,
                        'to_email': email_data['to_email']
                    }
                )
                
                # Converter string para enum
                email_template_type = EmailTemplateType(email_data['template_type'])
                
                # Enviar email individual
                success = email_service.send_email(
                    template_type=email_template_type,
                    to_email=email_data['to_email'],
                    variables=email_data['variables'],
                    from_name=email_data.get('from_name'),
                    custom_subject=email_data.get('custom_subject')
                )
                
                result = {
                    'to_email': email_data['to_email'],
                    'template_type': email_data['template_type'],
                    'success': success,
                    'index': index
                }
                
                if not success:
                    result['error'] = 'Falha no envio'
                
                results.append(result)
                
                # Pequena pausa entre emails para não sobrecarregar SMTP
                time.sleep(0.5)
                
            except Exception as e:
                results.append({
                    'to_email': email_data.get('to_email', 'unknown'),
                    'template_type': email_data.get('template_type', 'unknown'),
                    'success': False,
                    'error': str(e),
                    'index': index
                })
        
        # Calcular estatísticas
        successful = sum(1 for r in results if r['success'])
        failed = total_emails - successful
        
        return {
            'status': 'COMPLETED',
            'total': total_emails,
            'successful': successful,
            'failed': failed,
            'results': results,
            'message': f'Envio em lote concluído: {successful}/{total_emails} sucessos'
        }
        
    except Exception as exc:
        return {
            'status': 'FAILURE',
            'message': f'Erro no envio em lote: {str(exc)}',
            'total': len(email_list) if email_list else 0,
            'successful': 0,
            'failed': len(email_list) if email_list else 0
        }


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def send_notification_email_task(self, to_email: str, user_name: str, message: str, 
                                notification_subject: str, action_button: str = "", 
                                additional_info: str = ""):
    """
    Tarefa de conveniência para envio de email de notificação
    """
    variables = {
        "user_name": user_name,
        "message": message,
        "notification_subject": notification_subject,
        "action_button": action_button,
        "additional_info": additional_info
    }
    
    return send_email_task.apply_async(
        args=['notification', to_email, variables],
        queue='email'
    )


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def send_welcome_email_task(self, to_email: str, user_name: str, dashboard_link: str = None):
    """
    Tarefa de conveniência para envio de email de boas-vindas
    """
    variables = {
        "user_name": user_name,
        "dashboard_link": dashboard_link or "https://app.exemplo.com/dashboard"
    }
    
    return send_email_task.apply_async(
        args=['welcome', to_email, variables],
        queue='email'
    )


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def send_password_reset_email_task(self, to_email: str, token: str, expiry_time: str = "1 hora"):
    """
    Tarefa de conveniência para envio de email de reset de senha
    """
    from api.utils.settings import settings
    
    variables = {
        "reset_link": f"{settings.SMTP_FRONTEND_URL}/recuperar-senha?token={token}",
        "expiry_time": expiry_time
    }
    
    return send_email_task.apply_async(
        args=['password_reset', to_email, variables],
        queue='email'
    )


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def send_verification_email_task(self, to_email: str, verification_link: str, 
                                verification_code: str, expiry_time: str = "24 horas"):
    """
    Tarefa de conveniência para envio de email de verificação
    """
    variables = {
        "verification_link": verification_link,
        "verification_code": verification_code,
        "expiry_time": expiry_time
    }
    
    return send_email_task.apply_async(
        args=['verification', to_email, variables],
        queue='email'
    ) 