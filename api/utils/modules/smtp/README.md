# 📧 Sistema de Email Generalizado

Este módulo fornece um serviço de email versátil e baseado em templates para a aplicação FastAPI.

## 🚀 Características

- **Templates HTML Externos**: Templates organizados em arquivos separados para fácil manutenção
- **Múltiplos Tipos**: Suporte para diferentes tipos de email (reset de senha, boas-vindas, verificação, etc.)
- **Variáveis Dinâmicas**: Sistema flexível de substituição de variáveis
- **Estilos Centralizados**: CSS consistente em todos os emails via template base
- **Validação de Variáveis**: Verificação automática de variáveis obrigatórias
- **Retrocompatibilidade**: Mantém compatibilidade com código existente
- **Extensível**: Fácil adição de novos templates
- **Separação de Responsabilidades**: HTML separado da lógica Python
- **Recarregamento Dinâmico**: Templates podem ser recarregados sem reiniciar a aplicação

## 📁 Estrutura de Arquivos

```
api/utils/modules/smtp/
├── email_service.py           # Serviço principal de email
├── email_examples.py          # Exemplos de uso
├── test_templates.py          # Testes dos templates
├── README.md                  # Documentação principal
└── templates/                 # 📂 Templates HTML
    ├── base.html             # Template base com CSS
    ├── password_reset.html   # Reset de senha
    ├── welcome.html          # Boas-vindas
    ├── verification.html     # Verificação de email
    ├── notification.html     # Notificações gerais
    ├── reminder.html         # Lembretes
    ├── template_config.py    # Configuração dos templates
    └── README.md             # Documentação dos templates
```

## 📋 Templates Disponíveis

### 1. Password Reset (`PASSWORD_RESET`)
Email para redefinição de senha com link seguro.

**Variáveis obrigatórias:**
- `reset_link`: Link para redefinição de senha
- `expiry_time`: Tempo de expiração do link

### 2. Welcome (`WELCOME`)
Email de boas-vindas para novos usuários.

**Variáveis obrigatórias:**
- `user_name`: Nome do usuário
- `dashboard_link`: Link para o dashboard

### 3. Verification (`VERIFICATION`)
Email de verificação de conta com código.

**Variáveis obrigatórias:**
- `verification_link`: Link de verificação
- `verification_code`: Código de verificação
- `expiry_time`: Tempo de expiração

### 4. Notification (`NOTIFICATION`)
Template genérico para notificações personalizadas.

**Variáveis obrigatórias:**
- `user_name`: Nome do usuário
- `message`: Mensagem principal
- `notification_subject`: Assunto da notificação
- `action_button`: HTML do botão de ação (opcional)
- `additional_info`: Informações adicionais (opcional)

### 5. Reminder (`REMINDER`)
Template para lembretes e alertas.

**Variáveis obrigatórias:**
- `user_name`: Nome do usuário
- `reminder_title`: Título do lembrete
- `reminder_message`: Mensagem do lembrete
- `action_link`: Link de ação
- `reminder_datetime`: Data/hora do evento

## 🛠️ Como Usar

### Importação
```python
from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType
```

### Uso Básico
```python
email_service = EmailService()

# Método genérico
success = email_service.send_email(
    template_type=EmailTemplateType.WELCOME,
    to_email="usuario@exemplo.com",
    variables={
        "user_name": "João Silva",
        "dashboard_link": "https://app.exemplo.com/dashboard"
    }
)
```

### Métodos de Conveniência

#### Reset de Senha
```python
success = email_service.send_password_reset_email(
    email="usuario@exemplo.com",
    token="abc123def456",
    expiry_time="30 minutos"
)
```

#### Boas-vindas
```python
success = email_service.send_welcome_email(
    email="novousuario@exemplo.com",
    user_name="João Silva",
    dashboard_link="https://app.exemplo.com/dashboard"
)
```

#### Verificação
```python
success = email_service.send_verification_email(
    email="verificar@exemplo.com",
    verification_link="https://app.exemplo.com/verify?code=xyz789",
    verification_code="XYZ789",
    expiry_time="12 horas"
)
```

#### Notificação Personalizada
```python
success = email_service.send_notification_email(
    email="cliente@exemplo.com",
    user_name="Maria Silva",
    message="Seu pedido foi confirmado!",
    notification_subject="Pedido Confirmado",
    action_button='<a href="/pedidos/123" class="button">Ver Pedido</a>',
    additional_info='<div class="alert alert-success">Status: Confirmado</div>'
)
```

#### Lembrete
```python
success = email_service.send_reminder_email(
    email="participante@exemplo.com",
    user_name="Carlos Santos",
    reminder_title="Reunião de Equipe",
    reminder_message="Reunião importante amanhã",
    action_link="https://meet.google.com/abc-defg-hij",
    reminder_datetime="25/09/2024 às 14:00"
)
```

## 🎨 Personalização Avançada

### Assunto Customizado
```python
success = email_service.send_email(
    template_type=EmailTemplateType.NOTIFICATION,
    to_email="usuario@exemplo.com",
    variables={...},
    custom_subject="🎉 Assunto Personalizado"
)
```

### Remetente Customizado
```python
success = email_service.send_email(
    template_type=EmailTemplateType.NOTIFICATION,
    to_email="usuario@exemplo.com",
    variables={...},
    from_name="Sistema Automatizado"
)
```

## 🔧 Adicionando Novos Templates

Para adicionar um novo template:

1. **Crie o arquivo HTML:**
```bash
touch api/utils/modules/smtp/templates/invoice.html
```

2. **Edite o arquivo HTML:**
```html
<p>Olá <strong>{user_name}</strong>,</p>
<p>Sua fatura #{invoice_number} no valor de {amount} vence em {due_date}.</p>

<p style="text-align: center;">
    <a href="{invoice_link}" class="button">Ver Fatura</a>
</p>
```

3. **Configure em `templates/template_config.py`:**
```python
"invoice": TemplateConfig(
    subject="Fatura #{invoice_number} - {company_name}",
    template_file="invoice.html",
    variables=["user_name", "invoice_number", "amount", "due_date", "invoice_link"],
    description="Template para faturas e cobranças"
)
```

4. **Adicione o tipo no enum:**
```python
class EmailTemplateType(Enum):
    # ... existentes ...
    INVOICE = "invoice"
```

5. **Crie um método de conveniência (opcional):**
```python
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
```

## 🎨 Classes de Estilo Disponíveis

### Botões
- `.button` - Botão padrão (azul)
- `.button-success` - Botão verde
- `.button-warning` - Botão laranja
- `.button-danger` - Botão vermelho

### Alertas
- `.alert.alert-info` - Alerta informativo (azul)
- `.alert.alert-success` - Alerta de sucesso (verde)
- `.alert.alert-warning` - Alerta de atenção (laranja)

### Outros
- `.code` - Formatação de código
- `.header` - Cabeçalho do email
- `.content` - Conteúdo principal
- `.footer` - Rodapé

## ⚙️ Configuração

Certifique-se de que as seguintes variáveis estão configuradas no seu arquivo de settings:

```python
SMTP_HOST = "smtp.exemplo.com"
SMTP_PORT = 587
SMTP_USER = "seu@email.com"
SMTP_PASSWORD = "suasenha"
FRONTEND_URL = "https://app.exemplo.com"
```

## 🔄 Migração do Código Antigo

O método antigo `send_password_reset_email()` continua funcionando, então não há necessidade de alterações imediatas no código existente. Você pode migrar gradualmente para os novos templates.

**Antes:**
```python
email_service.send_password_reset_email(email, token)
```

**Depois (opcional):**
```python
email_service.send_email(
    template_type=EmailTemplateType.PASSWORD_RESET,
    to_email=email,
    variables={"reset_link": f"https://app.com/reset?token={token}", "expiry_time": "1 hora"}
)
```

## 🐛 Tratamento de Erros

O serviço inclui validação automática de variáveis:

```python
try:
    success = email_service.send_email(...)
except ValueError as e:
    print(f"Erro de validação: {e}")
```

## 🔄 Novos Recursos com Templates Externos

### Recarregamento de Templates
```python
email_service = EmailService()
email_service.reload_templates()  # Recarrega todos os templates
```

### Prévia de Templates
```python
preview_html = email_service.get_template_preview(
    EmailTemplateType.PASSWORD_RESET,
    {
        "reset_link": "https://exemplo.com/reset?token=abc123",
        "expiry_time": "1 hora"
    }
)
```

### Listar Variáveis de um Template
```python
variables = email_service.list_template_variables(EmailTemplateType.WELCOME)
# Retorna: ['user_name', 'dashboard_link']
```

## 📝 Exemplos Completos

Veja os arquivos:
- `email_examples.py` - Exemplos de uso dos templates
- `test_templates.py` - Testes e validação dos templates
- `templates/README.md` - Documentação específica dos templates HTML 