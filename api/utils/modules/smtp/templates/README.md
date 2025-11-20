# 📧 Templates de Email HTML

Esta pasta contém todos os templates HTML para o sistema de email da aplicação.

## 📁 Estrutura dos Arquivos

### `base.html`
Template base que contém a estrutura HTML comum a todos os emails:
- CSS styles centralizados
- Layout responsivo
- Header, content area e footer
- Variáveis: `{header_title}`, `{content}`, `{footer}`, `{year}`, `{company_name}`

### Templates Específicos

#### `password_reset.html`
Template para emails de redefinição de senha.
- **Variáveis obrigatórias:**
  - `{reset_link}`: URL para redefinição de senha
  - `{expiry_time}`: Tempo de expiração do link

#### `welcome.html`
Template para emails de boas-vindas.
- **Variáveis obrigatórias:**
  - `{user_name}`: Nome do usuário
  - `{dashboard_link}`: URL do dashboard
  - `{company_name}`: Nome da empresa (automática)

#### `verification.html`
Template para verificação de email.
- **Variáveis obrigatórias:**
  - `{verification_link}`: URL de verificação
  - `{verification_code}`: Código de verificação
  - `{expiry_time}`: Tempo de expiração

#### `notification.html`
Template genérico para notificações.
- **Variáveis obrigatórias:**
  - `{user_name}`: Nome do usuário
  - `{message}`: Mensagem principal
  - `{action_button}`: HTML do botão de ação (opcional)
  - `{additional_info}`: Informações extras (opcional)
  - `{notification_subject}`: Usado apenas no assunto

#### `reminder.html`
Template para lembretes e alertas.
- **Variáveis obrigatórias:**
  - `{user_name}`: Nome do usuário
  - `{reminder_title}`: Título do lembrete
  - `{reminder_message}`: Mensagem do lembrete
  - `{action_link}`: URL de ação
  - `{reminder_datetime}`: Data e hora do evento

### `template_config.py`
Arquivo de configuração que mapeia os templates e define metadados.

## 🎨 Classes CSS Disponíveis

### Botões
```html
<a href="#" class="button">Botão Padrão</a>
<a href="#" class="button button-success">Botão Verde</a>
<a href="#" class="button button-warning">Botão Laranja</a>
<a href="#" class="button button-danger">Botão Vermelho</a>
```

### Alertas
```html
<div class="alert alert-info">
    <p>Informação importante</p>
</div>

<div class="alert alert-success">
    <p>Mensagem de sucesso</p>
</div>

<div class="alert alert-warning">
    <p>Mensagem de atenção</p>
</div>
```

### Outros Elementos
```html
<span class="code">código</span>
```

## ✏️ Como Editar Templates

### 1. Editando Templates Existentes
Simplesmente abra o arquivo `.html` desejado e edite o conteúdo:

```html
<p>Olá <strong>{user_name}</strong>,</p>
<p>Sua nova mensagem personalizada aqui...</p>
```

### 2. Adicionando Novos Templates

**Passo 1:** Crie um novo arquivo `.html`
```bash
touch api/utils/modules/smtp/templates/meu_template.html
```

**Passo 2:** Adicione o conteúdo HTML
```html
<p>Olá <strong>{user_name}</strong>,</p>
<p>Conteúdo do seu novo template com {variavel_personalizada}.</p>

<p style="text-align: center;">
    <a href="{action_link}" class="button">Ação</a>
</p>
```

**Passo 3:** Configure em `template_config.py`
```python
"meu_template": TemplateConfig(
    subject="Assunto do Email - {company_name}",
    template_file="meu_template.html",
    variables=["user_name", "variavel_personalizada", "action_link"],
    description="Descrição do novo template"
)
```

**Passo 4:** Adicione ao enum em `email_service.py`
```python
class EmailTemplateType(Enum):
    # ... existentes ...
    MEU_TEMPLATE = "meu_template"
```

## 🔄 Recarregamento de Templates

Durante o desenvolvimento, você pode recarregar os templates sem reiniciar a aplicação:

```python
email_service = EmailService()
email_service.reload_templates()  # Recarrega todos os templates
```

## 🧪 Testando Templates

Para gerar uma prévia de um template:

```python
preview_html = email_service.get_template_preview(
    EmailTemplateType.PASSWORD_RESET,
    {
        "reset_link": "https://exemplo.com/reset?token=abc123",
        "expiry_time": "1 hora"
    }
)
```

## 📋 Boas Práticas

### 1. Variáveis
- Use nomes descritivos para variáveis: `{user_full_name}` em vez de `{name}`
- Sempre documente variáveis obrigatórias
- Use variáveis opcionais para conteúdo dinâmico

### 2. HTML
- Mantenha HTML simples e compatível com clientes de email
- Use estilos inline quando necessário para compatibilidade
- Teste em diferentes clientes de email

### 3. Conteúdo
- Escreva textos claros e diretos
- Use calls-to-action evidentes
- Mantenha consistência visual entre templates

### 4. Responsividade
- Use o sistema de CSS do template base
- Teste em dispositivos móveis
- Mantenha largura máxima de 600px

## 🚀 Exemplo Prático

Criando um template de cobrança:

**1. Arquivo:** `invoice.html`
```html
<p>Olá <strong>{customer_name}</strong>,</p>

<p>Sua fatura #{invoice_number} no valor de <strong>{amount}</strong> vence em {due_date}.</p>

<p style="text-align: center;">
    <a href="{payment_link}" class="button">Pagar Agora</a>
</p>

<div class="alert alert-warning">
    <p><strong>Importante:</strong> O pagamento deve ser efetuado até a data de vencimento para evitar juros.</p>
</div>

<p>Caso tenha dúvidas, entre em contato conosco.</p>
```

**2. Configuração:** `template_config.py`
```python
"invoice": TemplateConfig(
    subject="Fatura #{invoice_number} - Vencimento {due_date}",
    template_file="invoice.html",
    variables=["customer_name", "invoice_number", "amount", "due_date", "payment_link"],
    description="Template para faturas e cobranças"
)
```

**3. Uso:**
```python
email_service.send_email(
    template_type=EmailTemplateType.INVOICE,
    to_email="cliente@exemplo.com",
    variables={
        "customer_name": "João Silva",
        "invoice_number": "2024001",
        "amount": "R$ 150,00",
        "due_date": "15/10/2024",
        "payment_link": "https://app.exemplo.com/pay/2024001"
    }
)
```

## 📞 Suporte

Se você encontrar problemas com templates:
1. Verifique se todas as variáveis obrigatórias estão presentes
2. Valide a sintaxe HTML
3. Teste o template com dados de exemplo
4. Consulte os logs de erro do EmailService 