"""
Script simples para testar o envio de email
"""

import sys
from pathlib import Path

# Adicionar o caminho do projeto para permitir imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_single_email():
    """Testa o envio de um único email de notificação"""
    print("📧 TESTE DE ENVIO SIMPLES DE EMAIL")
    print("="*50)
    
    try:
        from api.utils.modules.smtp.email_service import EmailService
        
        # Email de destino
        test_email = "pedroffda@gmail.com"
        
        # Inicializar o serviço de email
        email_service = EmailService()
        print("✅ EmailService inicializado")
        
        # Enviar email de teste
        print(f"📨 Enviando email para: {test_email}")
        
        success = email_service.send_notification_email(
            email=test_email,
            user_name="Pedro",
            message="🎉 Este é um email de teste rápido do sistema FGNIA API! Se você está lendo isso, o sistema está funcionando perfeitamente.",
            notification_subject="Teste Rápido - Sistema de Email Funcionando",
            action_button='<a href="https://github.com/pedroffda" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Ver GitHub</a>',
            additional_info="Enviado em: " + str(Path(__file__).stat().st_mtime)
        )
        
        if success:
            print("✅ EMAIL ENVIADO COM SUCESSO!")
            print(f"📬 Verifique a caixa de entrada de {test_email}")
            print("💡 Dica: Também verifique a pasta de spam")
        else:
            print("❌ FALHA AO ENVIAR EMAIL")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_single_email() 