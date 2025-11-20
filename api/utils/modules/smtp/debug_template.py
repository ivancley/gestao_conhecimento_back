"""
Script de debug para identificar problemas nos templates
"""

import sys
from pathlib import Path

# Adicionar o caminho do projeto para permitir imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def debug_template():
    """Debug do template para identificar problemas"""
    print("🐛 DEBUG DOS TEMPLATES")
    print("="*50)
    
    try:
        from api.utils.modules.smtp.email_service import EmailService, EmailTemplateType
        
        # Inicializar o serviço de email
        email_service = EmailService()
        print("✅ EmailService inicializado")
        
        # Tentar gerar apenas uma prévia
        print("\n🔍 Gerando prévia do template...")
        
        variables = {
            "user_name": "Pedro",
            "message": "Teste de mensagem",
            "notification_subject": "Teste",
            "action_button": '<a href="#">Botão</a>',
            "additional_info": "Info adicional"
        }
        
        preview_html = email_service.get_template_preview(
            EmailTemplateType.NOTIFICATION, 
            variables
        )
        
        print(f"✅ Prévia gerada com sucesso: {len(preview_html)} caracteres")
        
        # Salvar prévia em arquivo para inspecionar
        with open("/tmp/debug_preview.html", "w", encoding="utf-8") as f:
            f.write(preview_html)
        
        print("📄 Prévia salva em /tmp/debug_preview.html")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_template() 