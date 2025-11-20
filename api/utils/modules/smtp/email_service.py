from datetime import datetime
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from enum import Enum
from api.utils.settings import Settings
from .templates.template_config import get_template_config

class EmailTemplateType(Enum):
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    REMINDER = "reminder"

class EmailTemplate:
    def __init__(self, subject: str, html_content: str, variables: list = None):
        self.subject = subject
        self.html_content = html_content
        self.variables = variables or []

class EmailService:
    def __init__(self):
        self.settings = Settings()
        self.templates_dir = Path(__file__).parent / "templates"
        self._templates = self._load_templates()
    
    def _get_header_title(self, template_type: EmailTemplateType) -> str:
        """Retorna o título em português para o cabeçalho do email"""
        header_titles = {
            "password_reset": "Redefinição de Senha",
            "welcome": "Boas-vindas",
            "verification": "Verificação de E-mail",
            "notification": "Notificação",
            "reminder": "Lembrete"
        }
        return header_titles.get(template_type.value, template_type.value.replace("_", " ").title())
    
    def _load_template_file(self, filename: str) -> str:
        """Carrega um arquivo de template HTML"""
        template_path = self.templates_dir / filename
        if not template_path.exists():
            raise FileNotFoundError(f"Template não encontrado: {filename}")
        
        with open(template_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _load_base_template(self) -> str:
        """Carrega o template base HTML"""
        return self._load_template_file("base.html")
    
    def _load_templates(self) -> Dict[EmailTemplateType, EmailTemplate]:
        """Carrega todos os templates de arquivos HTML"""
        templates = {}
        
        for template_type in EmailTemplateType:
            config = get_template_config(template_type.value)
            html_content = self._load_template_file(config.template_file)
            
            templates[template_type] = EmailTemplate(
                subject=config.subject,
                html_content=html_content,
                variables=config.variables
            )
        
        return templates
    
    def send_email(self, 
                   template_type: EmailTemplateType, 
                   to_email: str, 
                   variables: Dict[str, Any],
                   from_name: Optional[str] = None,
                   custom_subject: Optional[str] = None) -> bool:
        """
        Método genérico para envio de emails usando templates
        
        Args:
            template_type: Tipo do template a ser usado
            to_email: Email do destinatário
            variables: Dicionário com as variáveis do template
            from_name: Nome do remetente (opcional)
            custom_subject: Assunto customizado (opcional)
        """
        
        if template_type not in self._templates:
            raise ValueError(f"Template {template_type} não encontrado")
        
        template = self._templates[template_type]
        
        # Preparar variáveis padrão
        default_variables = {
            "company_name": self.settings.SMTP_USER,
            "year": datetime.now().year,
            "header_title": self._get_header_title(template_type),
            "footer": ""
        }
        
        # Mesclar variáveis
        all_variables = {**default_variables, **variables}
        
        # Renderizar template
        try:
            subject = custom_subject or template.subject.format(**all_variables)
            content = template.html_content.format(**all_variables)
            
            # Carregar template base e inserir conteúdo
            base_template = self._load_base_template()
            html_content = base_template.format(
                content=content,
                **all_variables
            )
            
        except KeyError as e:
            raise ValueError(f"Variável obrigatória não fornecida: {e}")
        
        # Preparar mensagem
        msg = MIMEMultipart()
        msg["From"] = self.settings.SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        
        msg.attach(MIMEText(html_content, "html"))
        
        # Enviar email
        return self._send_message(msg)
    
    def _send_message(self, msg: MIMEMultipart) -> bool:
        """Método privado para envio da mensagem"""
        try:
            with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as server:
                server.starttls()
                server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            return False
    
    def get_template_preview(self, template_type: EmailTemplateType, variables: Dict[str, Any]) -> str:
        """
        Gera uma prévia do template com as variáveis fornecidas
        Útil para debugging e visualização
        """
        if template_type not in self._templates:
            raise ValueError(f"Template {template_type} não encontrado")
        
        template = self._templates[template_type]
        
        # Preparar variáveis padrão
        default_variables = {
            "company_name": self.settings.SMTP_USER,
            "year": datetime.now().year,
            "header_title": self._get_header_title(template_type),
            "footer": ""
        }
        
        # Mesclar variáveis
        all_variables = {**default_variables, **variables}
        
        try:
            content = template.html_content.format(**all_variables)
            base_template = self._load_base_template()
            return base_template.format(content=content, **all_variables)
        except KeyError as e:
            raise ValueError(f"Variável obrigatória não fornecida: {e}")
    
    def list_template_variables(self, template_type: EmailTemplateType) -> list:
        """Retorna as variáveis obrigatórias de um template"""
        config = get_template_config(template_type.value)
        return config.variables
    
    def reload_templates(self):
        """Recarrega todos os templates (útil em desenvolvimento)"""
        self._templates = self._load_templates()
    
    # Métodos de conveniência para manter compatibilidade
    def send_password_reset_email(self, email: str, token: str, expiry_time: str = "1 hora") -> bool:
        """Método de conveniência para redefinição de senha"""
        reset_link = f"{self.settings.SMTP_FRONTEND_URL}/recuperar-senha?token={token}"
        
        return self.send_email(
            template_type=EmailTemplateType.PASSWORD_RESET,
            to_email=email,
            variables={
                "reset_link": reset_link,
                "expiry_time": expiry_time
            }
        )
    
    def send_welcome_email(self, email: str, user_name: str, dashboard_link: str = None) -> bool:
        """Método de conveniência para email de boas-vindas"""
        dashboard_link = dashboard_link or f"{self.settings.SMTP_FRONTEND_URL}/dashboard"
        
        return self.send_email(
            template_type=EmailTemplateType.WELCOME,
            to_email=email,
            variables={
                "user_name": user_name,
                "dashboard_link": dashboard_link
            }
        )
    
    def send_verification_email(self, email: str, verification_link: str, verification_code: str, expiry_time: str = "24 horas") -> bool:
        """Método de conveniência para verificação de email"""
        return self.send_email(
            template_type=EmailTemplateType.VERIFICATION,
            to_email=email,
            variables={
                "verification_link": verification_link,
                "verification_code": verification_code,
                "expiry_time": expiry_time
            }
        )
    
    def send_notification_email(self, email: str, user_name: str, message: str, 
                               notification_subject: str, action_button: str = "", 
                               additional_info: str = "") -> bool:
        """Método de conveniência para notificações"""
        return self.send_email(
            template_type=EmailTemplateType.NOTIFICATION,
            to_email=email,
            variables={
                "user_name": user_name,
                "message": message,
                "notification_subject": notification_subject,
                "action_button": action_button,
                "additional_info": additional_info
            }
        )
    
    def send_reminder_email(self, email: str, user_name: str, reminder_title: str,
                           reminder_message: str, action_link: str, 
                           reminder_datetime: str) -> bool:
        """Método de conveniência para lembretes"""
        return self.send_email(
            template_type=EmailTemplateType.REMINDER,
            to_email=email,
            variables={
                "user_name": user_name,
                "reminder_title": reminder_title,
                "reminder_message": reminder_message,
                "action_link": action_link,
                "reminder_datetime": reminder_datetime
            }
        )
