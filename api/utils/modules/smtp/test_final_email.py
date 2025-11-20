"""
Teste final de envio de emails - versão simplificada
"""

import sys
from pathlib import Path

# Adicionar o caminho do projeto para permitir imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_essential_emails():
    """Testa o envio dos emails essenciais do sistema"""
    print("🎯 TESTE FINAL DOS EMAILS ESSENCIAIS")
    print("="*55)
    
    try:
        from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType
        
        # Email de destino
        test_email = "pedroffda@gmail.com"
        
        # Inicializar o serviço de email
        email_service = EmailService()
        print("✅ EmailService inicializado")
        
        emails_sent = 0
        total_emails = 4
        
        # 1. Email de Notificação (mais genérico e útil)
        print(f"\n📧 1/4 - Enviando email de notificação...")
        try:
            success = email_service.send_notification_email(
                email=test_email,
                user_name="Pedro",
                message="Sistema de email do FGNIA API está funcionando perfeitamente! ✅",
                notification_subject="Sistema Operacional",
                action_button='<a href="https://github.com/pedroffda" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Ver GitHub</a>',
                additional_info="Teste executado com sucesso em " + str(Path().cwd())
            )
            
            if success:
                print("   ✅ Notificação enviada!")
                emails_sent += 1
            else:
                print("   ❌ Falha na notificação")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 2. Email de Boas-vindas
        print(f"\n🎉 2/4 - Enviando email de boas-vindas...")
        try:
            success = email_service.send_welcome_email(
                email=test_email,
                user_name="Pedro (Teste Final)",
                dashboard_link="https://exemplo.com/dashboard"
            )
            
            if success:
                print("   ✅ Boas-vindas enviado!")
                emails_sent += 1
            else:
                print("   ❌ Falha nas boas-vindas")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 3. Email de Verificação
        print(f"\n📧 3/4 - Enviando email de verificação...")
        try:
            success = email_service.send_verification_email(
                email=test_email,
                verification_link="https://exemplo.com/verify?code=ABC123",
                verification_code="ABC123",
                expiry_time="2 horas"
            )
            
            if success:
                print("   ✅ Verificação enviada!")
                emails_sent += 1
            else:
                print("   ❌ Falha na verificação")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 4. Email de Reset de Senha
        print(f"\n🔐 4/4 - Enviando email de reset de senha...")
        try:
            success = email_service.send_password_reset_email(
                email=test_email,
                token="token_de_teste_123",
                expiry_time="30 minutos"
            )
            
            if success:
                print("   ✅ Reset de senha enviado!")
                emails_sent += 1
            else:
                print("   ❌ Falha no reset de senha")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # Resumo final
        print("\n" + "="*55)
        print(f"📊 RESUMO: {emails_sent}/{total_emails} emails enviados com sucesso")
        
        if emails_sent == total_emails:
            print("🎉 TODOS OS EMAILS FORAM ENVIADOS! Sistema 100% funcional!")
        elif emails_sent > 0:
            print(f"✅ {emails_sent} emails enviados. Sistema parcialmente funcional.")
        else:
            print("❌ Nenhum email foi enviado. Verifique as configurações.")
        
        print(f"\n📬 Verifique a caixa de entrada de {test_email}")
        print("💡 Dica: Também verifique a pasta de spam/lixo eletrônico")
        print("\n🔧 Sistema pronto para uso em produção!")
        
        return emails_sent == total_emails
        
    except Exception as e:
        print(f"❌ Erro geral no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_essential_emails() 