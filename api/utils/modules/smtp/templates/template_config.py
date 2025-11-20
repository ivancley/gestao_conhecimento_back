"""
Configuração dos templates de email
"""

from typing import Dict, List

class TemplateConfig:
    """Configuração de um template de email"""
    
    def __init__(self, 
                 subject: str, 
                 template_file: str, 
                 variables: List[str] = None,
                 description: str = ""):
        self.subject = subject
        self.template_file = template_file
        self.variables = variables or []
        self.description = description

# Configurações dos templates disponíveis
TEMPLATE_CONFIGS = {
    "password_reset": TemplateConfig(
        subject="Redefinição de senha - {company_name}",
        template_file="password_reset.html",
        variables=["reset_link", "expiry_time"],
        description="Email para redefinição de senha com link seguro"
    ),
    
    "welcome": TemplateConfig(
        subject="Bem-vindo(a) à {company_name}!",
        template_file="welcome.html",
        variables=["user_name", "dashboard_link"],
        description="Email de boas-vindas para novos usuários"
    ),
    
    "verification": TemplateConfig(
        subject="Verificação de e-mail - {company_name}",
        template_file="verification.html",
        variables=["verification_link", "verification_code", "expiry_time"],
        description="Email de verificação de conta com código"
    ),
    
    "notification": TemplateConfig(
        subject="{notification_subject}",
        template_file="notification.html",
        variables=["user_name", "message", "action_button", "additional_info", "notification_subject"],
        description="Template genérico para notificações personalizadas"
    ),
    
    "reminder": TemplateConfig(
        subject="Lembrete: {reminder_title}",
        template_file="reminder.html",
        variables=["user_name", "reminder_title", "reminder_message", "action_link", "reminder_datetime"],
        description="Template para lembretes e alertas"
    )
}

def get_template_config(template_type: str) -> TemplateConfig:
    """Retorna a configuração de um template"""
    if template_type not in TEMPLATE_CONFIGS:
        raise ValueError(f"Template '{template_type}' não encontrado")
    return TEMPLATE_CONFIGS[template_type]

def list_available_templates() -> Dict[str, str]:
    """Lista todos os templates disponíveis com suas descrições"""
    return {name: config.description for name, config in TEMPLATE_CONFIGS.items()} 