"""
Exemplo prático: Como criar um novo template

Este arquivo demonstra o processo completo de criação de um novo template
do zero, usando como exemplo um template de "Confirmação de Pedido".
"""

def step_1_create_html_file():
    """
    PASSO 1: Criar o arquivo HTML do template
    
    Arquivo: api/utils/modules/smtp/templates/order_confirmation.html
    """
    
    html_content = """<p>Olá <strong>{customer_name}</strong>,</p>

<p>Seu pedido <strong>#{order_number}</strong> foi confirmado com sucesso!</p>

<div class="alert alert-success">
    <p><strong>Detalhes do Pedido:</strong></p>
    <ul>
        <li>Número: #{order_number}</li>
        <li>Total: {order_total}</li>
        <li>Data: {order_date}</li>
        <li>Entrega prevista: {delivery_date}</li>
    </ul>
</div>

<p style="text-align: center;">
    <a href="{order_tracking_link}" class="button button-success">Acompanhar Pedido</a>
</p>

<p>Obrigado por escolher nossa loja!</p>

{additional_info}"""
    
    print("📄 Conteúdo do arquivo order_confirmation.html:")
    print(html_content)
    print("\n" + "="*50)

def step_2_configure_template():
    """
    PASSO 2: Configurar o template em template_config.py
    """
    
    config_code = '''
# Adicionar em TEMPLATE_CONFIGS:
"order_confirmation": TemplateConfig(
    subject="Pedido #{order_number} confirmado - {company_name}",
    template_file="order_confirmation.html",
    variables=[
        "customer_name", 
        "order_number", 
        "order_total", 
        "order_date", 
        "delivery_date", 
        "order_tracking_link",
        "additional_info"
    ],
    description="Template para confirmação de pedidos"
)'''
    
    print("⚙️ Configuração a ser adicionada em template_config.py:")
    print(config_code)
    print("\n" + "="*50)

def step_3_add_enum():
    """
    PASSO 3: Adicionar ao enum EmailTemplateType
    """
    
    enum_code = '''
class EmailTemplateType(Enum):
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    REMINDER = "reminder"
    ORDER_CONFIRMATION = "order_confirmation"  # NOVA LINHA
'''
    
    print("📝 Adicionar ao enum em email_service.py:")
    print(enum_code)
    print("\n" + "="*50)

def step_4_convenience_method():
    """
    PASSO 4: Criar método de conveniência (opcional)
    """
    
    method_code = '''
def send_order_confirmation_email(self, 
                                email: str, 
                                customer_name: str,
                                order_number: str,
                                order_total: str,
                                order_date: str,
                                delivery_date: str,
                                order_tracking_link: str,
                                additional_info: str = "") -> bool:
    """Método de conveniência para confirmação de pedidos"""
    return self.send_email(
        template_type=EmailTemplateType.ORDER_CONFIRMATION,
        to_email=email,
        variables={
            "customer_name": customer_name,
            "order_number": order_number,
            "order_total": order_total,
            "order_date": order_date,
            "delivery_date": delivery_date,
            "order_tracking_link": order_tracking_link,
            "additional_info": additional_info
        }
    )
'''
    
    print("🔧 Método de conveniência a ser adicionado ao EmailService:")
    print(method_code)
    print("\n" + "="*50)

def step_5_usage_example():
    """
    PASSO 5: Como usar o novo template
    """
    
    usage_code = '''
# Exemplo de uso:
from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType

email_service = EmailService()

# Método 1: Usando o método de conveniência
success = email_service.send_order_confirmation_email(
    email="cliente@exemplo.com",
    customer_name="João Silva",
    order_number="2024001",
    order_total="R$ 299,90",
    order_date="23/09/2024",
    delivery_date="25/09/2024",
    order_tracking_link="https://loja.com/tracking/2024001",
    additional_info=\'\'\'
        <div class="alert alert-info">
            <p><strong>Dica:</strong> Você receberá um email quando o pedido for enviado.</p>
        </div>
    \'\'\'
)

# Método 2: Usando o método genérico
success = email_service.send_email(
    template_type=EmailTemplateType.ORDER_CONFIRMATION,
    to_email="cliente@exemplo.com",
    variables={
        "customer_name": "João Silva",
        "order_number": "2024001",
        "order_total": "R$ 299,90",
        "order_date": "23/09/2024",
        "delivery_date": "25/09/2024",
        "order_tracking_link": "https://loja.com/tracking/2024001",
        "additional_info": ""
    },
    custom_subject="🛒 Seu pedido foi confirmado!",
    from_name="Equipe de Vendas"
)
'''
    
    print("💻 Exemplos de uso do novo template:")
    print(usage_code)
    print("\n" + "="*50)

def step_6_testing():
    """
    PASSO 6: Como testar o novo template
    """
    
    test_code = '''
# Testar carregamento do template
email_service = EmailService()
email_service.reload_templates()

# Gerar prévia do template
preview_html = email_service.get_template_preview(
    EmailTemplateType.ORDER_CONFIRMATION,
    {
        "customer_name": "João Silva",
        "order_number": "2024001",
        "order_total": "R$ 299,90",
        "order_date": "23/09/2024",
        "delivery_date": "25/09/2024",
        "order_tracking_link": "https://loja.com/tracking/2024001",
        "additional_info": ""
    }
)

# Salvar prévia para visualização
with open("preview_order_confirmation.html", "w", encoding="utf-8") as f:
    f.write(preview_html)

print("Prévia salva em preview_order_confirmation.html")

# Verificar variáveis obrigatórias
variables = email_service.list_template_variables(EmailTemplateType.ORDER_CONFIRMATION)
print(f"Variáveis obrigatórias: {variables}")
'''
    
    print("🧪 Como testar o novo template:")
    print(test_code)
    print("\n" + "="*50)

def show_file_structure():
    """
    Mostra a estrutura de arquivos após adicionar o novo template
    """
    
    structure = """
📁 Estrutura final após adicionar o novo template:

api/utils/modules/smtp/
├── email_service.py                    # ← MODIFICADO (enum + método)
├── templates/
│   ├── base.html
│   ├── password_reset.html
│   ├── welcome.html
│   ├── verification.html
│   ├── notification.html
│   ├── reminder.html
│   ├── order_confirmation.html         # ← NOVO ARQUIVO
│   └── template_config.py              # ← MODIFICADO (nova config)
└── README.md

🔄 Arquivos que precisam ser modificados:
1. ✅ Criar: templates/order_confirmation.html
2. ✅ Modificar: templates/template_config.py
3. ✅ Modificar: email_service.py (enum + método opcional)

📋 Resumo das modificações:
- 1 arquivo criado
- 2 arquivos modificados
- 0 arquivos removidos
"""
    
    print(structure)

def main():
    """Executa o tutorial completo"""
    
    print("🎓 TUTORIAL: Como Criar um Novo Template de Email")
    print("=" * 60)
    print("\nEste tutorial mostra como criar um template de 'Confirmação de Pedido'")
    print("do zero, seguindo as melhores práticas do sistema.\n")
    
    step_1_create_html_file()
    step_2_configure_template()
    step_3_add_enum()
    step_4_convenience_method()
    step_5_usage_example()
    step_6_testing()
    show_file_structure()
    
    print("🎉 TUTORIAL CONCLUÍDO!")
    print("\n✨ Benefícios do sistema de templates externos:")
    print("   • 📝 HTML separado da lógica Python")
    print("   • 🔧 Fácil manutenção e edição")
    print("   • 🎨 Reutilização do design base")
    print("   • 🧪 Testes e prévias simples")
    print("   • 📚 Documentação automática")
    print("   • 🔄 Recarregamento sem restart")
    
    print("\n📋 Próximos passos:")
    print("   1. Implemente os passos mostrados acima")
    print("   2. Teste o template com dados reais")
    print("   3. Ajuste o design conforme necessário")
    print("   4. Documente o novo template")
    print("   5. Compartilhe com a equipe!")

if __name__ == "__main__":
    main() 