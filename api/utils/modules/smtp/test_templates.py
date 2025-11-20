"""
Teste dos templates HTML externos
"""

import sys
from pathlib import Path

# Adicionar o caminho do projeto para permitir imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from api.utils.settings import Settings

def test_template_loading():
    """Testa o carregamento dos templates HTML"""
    print("🧪 Testando carregamento dos templates HTML externos...\n")
    
    try:
        # Importar as configurações dos templates
        from api.utils.modules.smtp.templates.template_config import (
            TEMPLATE_CONFIGS, 
            get_template_config, 
            list_available_templates
        )
        
        print("✅ Configurações dos templates carregadas com sucesso")
        print(f"📋 Templates disponíveis: {len(TEMPLATE_CONFIGS)}")
        
        # Listar templates disponíveis
        templates = list_available_templates()
        for name, description in templates.items():
            print(f"   📧 {name}: {description}")
        
        print("\n" + "="*60)
        
        # Testar cada template individualmente
        templates_dir = Path(__file__).parent / "templates"
        
        for template_name, config in TEMPLATE_CONFIGS.items():
            print(f"\n🔍 Testando template: {template_name}")
            
            # Verificar se o arquivo existe
            template_path = templates_dir / config.template_file
            if template_path.exists():
                print(f"   ✅ Arquivo encontrado: {config.template_file}")
                
                # Ler o conteúdo
                with open(template_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    print(f"   📄 Tamanho: {len(content)} caracteres")
                    print(f"   🔧 Variáveis: {', '.join(config.variables)}")
                    
                    # Verificar se as variáveis estão no template
                    missing_vars = []
                    for var in config.variables:
                        if f"{{{var}}}" not in content:
                            missing_vars.append(var)
                    
                    if missing_vars:
                        print(f"   ⚠️  Variáveis ausentes no template: {', '.join(missing_vars)}")
                    else:
                        print(f"   ✅ Todas as variáveis encontradas no template")
            else:
                print(f"   ❌ Arquivo não encontrado: {config.template_file}")
        
        print("\n" + "="*60)
        
        # Testar template base
        print("\n🏗️  Testando template base...")
        base_template_path = templates_dir / "base.html"
        if base_template_path.exists():
            print("   ✅ Template base encontrado")
            with open(base_template_path, 'r', encoding='utf-8') as file:
                base_content = file.read()
                print(f"   📄 Tamanho: {len(base_content)} caracteres")
                
                # Verificar variáveis obrigatórias do template base
                required_base_vars = ["{header_title}", "{content}", "{footer}", "{year}", "{company_name}"]
                missing_base_vars = []
                for var in required_base_vars:
                    if var not in base_content:
                        missing_base_vars.append(var)
                
                if missing_base_vars:
                    print(f"   ⚠️  Variáveis ausentes no template base: {', '.join(missing_base_vars)}")
                else:
                    print("   ✅ Todas as variáveis base encontradas")
        else:
            print("   ❌ Template base não encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_email_service_with_files():
    """Testa o EmailService com templates de arquivos"""
    print("\n" + "="*60)
    print("🧪 Testando EmailService com templates externos...\n")
    
    try:
        # Simular um settings mock para o teste
        class MockSettings:
            SMTP_HOST = Settings.SMTP_HOST
            SMTP_PORT = Settings.SMTP_PORT
            SMTP_USER = Settings.SMTP_USER
            SMTP_PASSWORD = Settings.SMTP_PASSWORD
            SMTP_FRONTEND_URL = Settings.SMTP_FRONTEND_URL
            EMAIL_TO = "pedroffda@gmail.com"
        
        # Patchear temporariamente as configurações
        import api.utils.modules.smtp.email_service as email_module
        original_settings = email_module.Settings
        email_module.Settings = MockSettings
        
        from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType
        
        # Inicializar o serviço de email
        email_service = EmailService()
        print("✅ EmailService inicializado com sucesso")
        
        # Testar carregamento de templates
        print(f"📋 Templates carregados: {len(email_service._templates)}")
        
        # Testar métodos auxiliares
        print("\n🔧 Testando métodos auxiliares...")
        
        # Listar variáveis de um template
        variables = email_service.list_template_variables(EmailTemplateType.PASSWORD_RESET)
        print(f"   📝 Variáveis do PASSWORD_RESET: {variables}")
        
        # Testar geração de prévia
        print("\n👁️  Testando geração de prévia...")
        preview_vars = {
            "reset_link": "https://app.exemplo.com/reset?token=abc123",
            "expiry_time": "1 hora"
        }
        
        preview_html = email_service.get_template_preview(
            EmailTemplateType.PASSWORD_RESET, 
            preview_vars
        )
        print(f"   ✅ Prévia gerada: {len(preview_html)} caracteres")
        
        # Verificar se o HTML contém os valores esperados
        if "https://app.exemplo.com/reset?token=abc123" in preview_html:
            print("   ✅ Link de reset encontrado na prévia")
        else:
            print("   ⚠️  Link de reset não encontrado na prévia")
        
        if "1 hora" in preview_html:
            print("   ✅ Tempo de expiração encontrado na prévia")
        else:
            print("   ⚠️  Tempo de expiração não encontrado na prévia")
        
        # Restaurar configurações originais
        email_module.Settings = original_settings
        
        print("\n✅ Todos os testes de EmailService passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do EmailService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_email_sending():
    """Testa o envio real de emails usando o EmailService"""
    print("\n" + "="*60)
    print("📧 TESTE DE ENVIO REAL DE EMAIL")
    print("="*60)
    
    try:
        from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType
        
        # Email de destino configurado
        test_email = "pedroffda@gmail.com"
        
        # Inicializar o serviço de email
        email_service = EmailService()
        print("✅ EmailService inicializado com sucesso")
        
        # Teste 1: Email de teste simples (Notification)
        print(f"\n📨 Enviando email de teste para: {test_email}")
        
        success = email_service.send_notification_email(
            email=test_email,
            user_name="Pedro",
            message="Este é um email de teste do sistema FGNIA API. Se você recebeu este email, significa que o sistema de envio está funcionando corretamente!",
            notification_subject="Teste do Sistema de Email",
            action_button='<a href="https://github.com" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Acessar GitHub</a>',
            additional_info="Este teste foi executado automaticamente pelo sistema."
        )
        
        if success:
            print("✅ Email de notificação enviado com sucesso!")
        else:
            print("❌ Falha ao enviar email de notificação")
            return False
        
        # Teste 2: Email de boas-vindas
        print(f"\n🎉 Enviando email de boas-vindas para: {test_email}")
        
        success = email_service.send_welcome_email(
            email=test_email,
            user_name="Pedro (Teste)",
            dashboard_link="https://app.exemplo.com/dashboard"
        )
        
        if success:
            print("✅ Email de boas-vindas enviado com sucesso!")
        else:
            print("❌ Falha ao enviar email de boas-vindas")
            return False
        
        # Teste 3: Email de redefinição de senha
        print(f"\n🔐 Enviando email de redefinição de senha para: {test_email}")
        
        success = email_service.send_password_reset_email(
            email=test_email,
            token="teste123abc456def",
            expiry_time="30 minutos"
        )
        
        if success:
            print("✅ Email de redefinição de senha enviado com sucesso!")
        else:
            print("❌ Falha ao enviar email de redefinição de senha")
            return False
        
        # Teste 4: Email de verificação
        print(f"\n✉️ Enviando email de verificação para: {test_email}")
        
        success = email_service.send_verification_email(
            email=test_email,
            verification_link="https://app.exemplo.com/verify?code=TESTE123",
            verification_code="TESTE123",
            expiry_time="2 horas"
        )
        
        if success:
            print("✅ Email de verificação enviado com sucesso!")
        else:
            print("❌ Falha ao enviar email de verificação")
            return False
        
        # Teste 5: Email de lembrete
        print(f"\n⏰ Enviando email de lembrete para: {test_email}")
        
        success = email_service.send_reminder_email(
            email=test_email,
            user_name="Pedro (Teste)",
            reminder_title="Lembrete de Teste",
            reminder_message="Este é um lembrete automático gerado pelo sistema para teste.",
            action_link="https://app.exemplo.com/action",
            reminder_datetime="29 de Setembro de 2025 às 15:30"
        )
        
        if success:
            print("✅ Email de lembrete enviado com sucesso!")
        else:
            print("❌ Falha ao enviar email de lembrete")
            return False
        
        print("\n🎉 TODOS OS EMAILS FORAM ENVIADOS COM SUCESSO!")
        print(f"📬 Verifique a caixa de entrada de {test_email}")
        print("💡 Dica: Verifique também a pasta de spam/lixo eletrônico")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste de envio: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_template_structure():
    """Mostra a estrutura dos arquivos de template"""
    print("\n" + "="*60)
    print("📁 Estrutura dos templates criados:\n")
    
    templates_dir = Path(__file__).parent / "templates"
    
    if templates_dir.exists():
        print(f"📂 {templates_dir.name}/")
        
        for file_path in sorted(templates_dir.iterdir()):
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"   📄 {file_path.name} ({size} bytes)")
    else:
        print("❌ Diretório de templates não encontrado")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DOS TEMPLATES HTML EXTERNOS")
    print("=" * 60)
    
    # Executar todos os testes
    success = True
    
    success &= test_template_loading()
    success &= test_email_service_with_files()
    success &= test_real_email_sending() # Adicionado o novo teste
    show_template_structure()
    
    print("\n" + "="*60)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("\n📋 Benefícios dos templates externos:")
        print("   ✅ Fácil manutenção dos templates HTML")
        print("   ✅ Separação clara entre lógica e apresentação")
        print("   ✅ Possibilidade de editar templates sem alterar código Python")
        print("   ✅ Estrutura organizada e escalável")
        print("   ✅ Reutilização do template base")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("   Verifique os erros acima e corrija os problemas.")
    
    print("\n📝 Próximos passos:")
    print("   1. Edite os templates HTML conforme necessário")
    print("   2. Adicione novos templates criando arquivos .html")
    print("   3. Configure os novos templates em template_config.py")
    print("   4. Use o EmailService normalmente") 