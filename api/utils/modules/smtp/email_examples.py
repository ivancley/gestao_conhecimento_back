"""
Exemplos de uso do EmailService generalizado

Este arquivo demonstra como usar os diferentes templates de email
disponíveis no serviço de email refatorado.
"""


def example_conceptual_usage():
    """
    Exemplos conceituais de como usar o novo EmailService
    (sem executar o código, apenas mostrando a interface)
    """
    
    print("=== Exemplos de Uso do EmailService Generalizado ===\n")
    
    # Exemplo 1: Email de redefinição de senha
    print("1. Email de redefinição de senha:")
    print("""
    email_service = EmailService()
    success = email_service.send_password_reset_email(
        email="usuario@exemplo.com",
        token="abc123def456",
        expiry_time="30 minutos"
    )
    """)
    
    # Exemplo 2: Email de boas-vindas
    print("2. Email de boas-vindas:")
    print("""
    success = email_service.send_welcome_email(
        email="novousuario@exemplo.com",
        user_name="João Silva",
        dashboard_link="https://app.exemplo.com/dashboard"
    )
    """)
    
    # Exemplo 3: Email de verificação
    print("3. Email de verificação:")
    print("""
    success = email_service.send_verification_email(
        email="verificar@exemplo.com",
        verification_link="https://app.exemplo.com/verify?code=xyz789",
        verification_code="XYZ789",
        expiry_time="12 horas"
    )
    """)
    
    # Exemplo 4: Notificação personalizada
    print("4. Notificação personalizada:")
    print("""
    success = email_service.send_email(
        template_type=EmailTemplateType.NOTIFICATION,
        to_email="cliente@exemplo.com",
        variables={
            "user_name": "Maria Silva",
            "message": "Seu pedido #123 foi confirmado com sucesso!",
            "notification_subject": "Pedido Confirmado - #123",
            "action_button": '<p style="text-align: center;"><a href="/pedidos/123" class="button">Ver Pedido</a></p>',
            "additional_info": '<div class="alert alert-success">Status: Confirmado</div>'
        }
    )
    """)
    
    # Exemplo 5: Lembrete
    print("5. Lembrete de evento:")
    print("""
    success = email_service.send_reminder_email(
        email="participante@exemplo.com",
        user_name="Carlos Santos",
        reminder_title="Reunião de Equipe",
        reminder_message="Não se esqueça da nossa reunião de equipe amanhã.",
        action_link="https://meet.google.com/abc-defg-hij",
        reminder_datetime="24/09/2024 às 14:00"
    )
    """)
    
    # Exemplo 6: Email personalizado avançado
    print("6. Email totalmente personalizado:")
    print("""
    success = email_service.send_email(
        template_type=EmailTemplateType.NOTIFICATION,
        to_email="personalizado@exemplo.com",
        variables={
            "user_name": "Admin",
            "message": "Mensagem personalizada com HTML.",
            "notification_subject": "Email Personalizado",
            "action_button": '<a href="#" class="button button-danger">Ação Importante</a>',
            "additional_info": '''
                <div class="alert alert-warning">
                    <p><strong>Atenção:</strong> Esta é uma mensagem de teste.</p>
                </div>
            '''
        },
        from_name="Sistema Automatizado",
        custom_subject="🔔 Assunto Customizado com Emoji"
    )
    """)

def show_template_structure():
    """Mostra a estrutura dos templates disponíveis"""
    
    print("\n=== Estrutura dos Templates ===\n")
    
    templates = {
        "PASSWORD_RESET": {
            "description": "Email para redefinição de senha",
            "variables": ["reset_link", "expiry_time"],
            "example": {
                "reset_link": "https://app.com/reset?token=abc123",
                "expiry_time": "1 hora"
            }
        },
        "WELCOME": {
            "description": "Email de boas-vindas para novos usuários",
            "variables": ["user_name", "dashboard_link"],
            "example": {
                "user_name": "João Silva",
                "dashboard_link": "https://app.com/dashboard"
            }
        },
        "VERIFICATION": {
            "description": "Email de verificação de conta",
            "variables": ["verification_link", "verification_code", "expiry_time"],
            "example": {
                "verification_link": "https://app.com/verify?code=xyz789",
                "verification_code": "XYZ789",
                "expiry_time": "24 horas"
            }
        },
        "NOTIFICATION": {
            "description": "Template genérico para notificações",
            "variables": ["user_name", "message", "notification_subject", "action_button", "additional_info"],
            "example": {
                "user_name": "Maria Silva",
                "message": "Sua mensagem aqui",
                "notification_subject": "Título da Notificação",
                "action_button": '<a href="#" class="button">Ação</a>',
                "additional_info": '<div class="alert alert-info">Info adicional</div>'
            }
        },
        "REMINDER": {
            "description": "Template para lembretes e alertas",
            "variables": ["user_name", "reminder_title", "reminder_message", "action_link", "reminder_datetime"],
            "example": {
                "user_name": "Carlos Santos",
                "reminder_title": "Reunião Importante",
                "reminder_message": "Lembrete da nossa reunião",
                "action_link": "https://meet.google.com/abc-defg",
                "reminder_datetime": "25/09/2024 às 14:00"
            }
        }
    }
    
    for template_name, template_info in templates.items():
        print(f"📧 {template_name}")
        print(f"   Descrição: {template_info['description']}")
        print(f"   Variáveis obrigatórias: {', '.join(template_info['variables'])}")
        print(f"   Exemplo de variáveis:")
        for var, value in template_info['example'].items():
            print(f"     - {var}: {value}")
        print()

def show_css_classes():
    """Mostra as classes CSS disponíveis"""
    
    print("=== Classes CSS Disponíveis ===\n")
    
    css_classes = {
        "Botões": {
            ".button": "Botão padrão (azul)",
            ".button-success": "Botão verde para ações positivas",
            ".button-warning": "Botão laranja para atenção",
            ".button-danger": "Botão vermelho para ações críticas"
        },
        "Alertas": {
            ".alert.alert-info": "Alerta informativo (azul)",
            ".alert.alert-success": "Alerta de sucesso (verde)",
            ".alert.alert-warning": "Alerta de atenção (laranja)"
        },
        "Elementos": {
            ".code": "Formatação para códigos",
            ".header": "Cabeçalho do email",
            ".content": "Área de conteúdo principal",
            ".footer": "Rodapé do email"
        }
    }
    
    for category, classes in css_classes.items():
        print(f"🎨 {category}:")
        for class_name, description in classes.items():
            print(f"   {class_name} - {description}")
        print()

def show_extension_guide():
    """Mostra como estender o sistema com novos templates"""
    
    print("=== Como Adicionar Novos Templates ===\n")
    
    print("1. Adicione o novo tipo no enum EmailTemplateType:")
    print("""
    class EmailTemplateType(Enum):
        PASSWORD_RESET = "password_reset"
        WELCOME = "welcome"
        VERIFICATION = "verification"
        NOTIFICATION = "notification"
        REMINDER = "reminder"
        INVOICE = "invoice"  # Novo template
    """)
    
    print("2. Implemente o template no método _initialize_templates():")
    print("""
    # Template de fatura
    invoice_content = '''
        <p>Olá <strong>{user_name}</strong>,</p>
        <p>Sua fatura #{invoice_number} no valor de <strong>{amount}</strong> vence em {due_date}.</p>
        
        <p style="text-align: center;">
            <a href="{invoice_link}" class="button">Ver Fatura</a>
        </p>
        
        <div class="alert alert-warning">
            <p><strong>Importante:</strong> O pagamento deve ser efetuado até a data de vencimento.</p>
        </div>
    '''
    
    templates[EmailTemplateType.INVOICE] = EmailTemplate(
        subject="Fatura #{invoice_number} - {company_name}",
        html_content=invoice_content,
        variables=["user_name", "invoice_number", "amount", "due_date", "invoice_link"]
    )
    """)
    
    print("3. (Opcional) Crie um método de conveniência:")
    print("""
    def send_invoice_email(self, email: str, user_name: str, invoice_number: str,
                          amount: str, due_date: str, invoice_link: str) -> bool:
        return self.send_email(
            template_type=EmailTemplateType.INVOICE,
            to_email=email,
            variables={
                "user_name": user_name,
                "invoice_number": invoice_number,
                "amount": amount,
                "due_date": due_date,
                "invoice_link": invoice_link
            }
        )
    """)

if __name__ == "__main__":
    example_conceptual_usage()
    show_template_structure()
    show_css_classes()
    show_extension_guide()
    
    print("\n=== Vantagens do Novo Sistema ===")
    print("✅ Templates reutilizáveis e consistentes")
    print("✅ Fácil adição de novos tipos de email")
    print("✅ Variáveis dinâmicas para personalização")
    print("✅ Métodos de conveniência para casos comuns")
    print("✅ Sistema de estilos CSS centralizado")
    print("✅ Validação de variáveis obrigatórias")
    print("✅ Retrocompatibilidade com código existente")
    print("✅ Interface intuitiva e bem documentada")
    
    print("\n=== Próximos Passos ===")
    print("1. Configure as variáveis SMTP no arquivo de settings")
    print("2. Importe EmailService nos seus módulos")
    print("3. Use os métodos de conveniência ou o método genérico send_email()")
    print("4. Adicione novos templates conforme necessário")
    print("5. Consulte a documentação no README.md para mais detalhes") 