"""
Serviço assíncrono para envio de emails via Celery
"""
from typing import Optional
from api.utils.tasks.email_tasks import (
    send_password_reset_email_task,
    send_welcome_email_task,
    send_verification_email_task,
    send_notification_email_task
)


class AsyncEmailService:
    """
    Serviço para envio assíncrono de emails via Celery.
    
    Este serviço oferece uma interface simples para enviar emails
    através das filas do Celery, garantindo que o envio não bloqueie
    a resposta da API.
    """
    
    @staticmethod
    def send_password_reset_async(to_email: str, token: str, expiry_time: str = "1 hora") -> str:
        """
        Envia email de recuperação de senha de forma assíncrona.
        
        Args:
            to_email: Email do destinatário
            token: Token de recuperação
            expiry_time: Tempo de expiração do token
            
        Returns:
            Task ID para acompanhamento do status
        """
        task = send_password_reset_email_task.delay(
            to_email=to_email,
            token=token,
            expiry_time=expiry_time
        )
        return task.id
    
    @staticmethod
    def send_welcome_async(to_email: str, user_name: str, dashboard_link: Optional[str] = None) -> str:
        """
        Envia email de boas-vindas de forma assíncrona.
        
        Args:
            to_email: Email do destinatário
            user_name: Nome do usuário
            dashboard_link: Link para o dashboard (opcional)
            
        Returns:
            Task ID para acompanhamento do status
        """
        task = send_welcome_email_task.delay(
            to_email=to_email,
            user_name=user_name,
            dashboard_link=dashboard_link
        )
        return task.id
    
    @staticmethod
    def send_verification_async(to_email: str, verification_link: str, 
                               verification_code: str, expiry_time: str = "24 horas") -> str:
        """
        Envia email de verificação de forma assíncrona.
        
        Args:
            to_email: Email do destinatário
            verification_link: Link de verificação
            verification_code: Código de verificação
            expiry_time: Tempo de expiração
            
        Returns:
            Task ID para acompanhamento do status
        """
        task = send_verification_email_task.delay(
            to_email=to_email,
            verification_link=verification_link,
            verification_code=verification_code,
            expiry_time=expiry_time
        )
        return task.id
    
    @staticmethod
    def send_notification_async(to_email: str, user_name: str, message: str, 
                               notification_subject: str, action_button: str = "", 
                               additional_info: str = "") -> str:
        """
        Envia email de notificação de forma assíncrona.
        
        Args:
            to_email: Email do destinatário
            user_name: Nome do usuário
            message: Mensagem principal
            notification_subject: Assunto da notificação
            action_button: HTML do botão de ação (opcional)
            additional_info: Informações adicionais (opcional)
            
        Returns:
            Task ID para acompanhamento do status
        """
        task = send_notification_email_task.delay(
            to_email=to_email,
            user_name=user_name,
            message=message,
            notification_subject=notification_subject,
            action_button=action_button,
            additional_info=additional_info
        )
        return task.id
    
    @staticmethod
    def get_task_status(task_id: str) -> dict:
        """
        Obtém o status de uma tarefa de email.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Dicionário com informações do status da tarefa
        """
        from api.utils.celery_app import celery_app
        
        try:
            result = celery_app.AsyncResult(task_id)
            
            if result.state == 'PENDING':
                return {
                    'state': result.state,
                    'status': 'Tarefa pendente...',
                    'progress': 0
                }
            elif result.state == 'PROGRESS':
                return {
                    'state': result.state,
                    'status': result.info.get('status', ''),
                    'progress': result.info.get('current', 0),
                    'total': result.info.get('total', 1)
                }
            elif result.state == 'SUCCESS':
                return {
                    'state': result.state,
                    'status': 'Email enviado com sucesso',
                    'result': result.result
                }
            else:  # FAILURE
                return {
                    'state': result.state,
                    'status': f'Erro: {str(result.info)}',
                    'error': str(result.info)
                }
        except Exception as e:
            return {
                'state': 'ERROR',
                'status': f'Erro ao consultar tarefa: {str(e)}',
                'error': str(e)
            }


# Instância global para uso em toda a aplicação
async_email_service = AsyncEmailService() 