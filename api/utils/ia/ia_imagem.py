import base64
import logging
import os

from decouple import config
from openai import OpenAI

OPENAI_API_KEY = config("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_image_with_vision(image_path: str, caption: str = "") -> str:
    """
    Processa imagem usando OpenAI Vision para extrair texto.
    
    Args:
        image_path: Caminho para o arquivo da imagem
        caption: Caption/legenda da imagem se existir
        
    Returns:
        str: Texto extraído da imagem
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        # Lê a imagem e converte para base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Constrói o prompt otimizado para extração de texto
        system_prompt = """#Instruções 
TODO o texto visível.

Regras:
- Transcreva exatamente como está: não corrija, não traduza, não interprete.
- Preserve quebras de linha, listas, títulos e a ordem visual sempre que possível.
- Inclua números, datas, símbolos, selos/carimbos, assinaturas e marcas d'água.
- Se uma parte estiver ilegível, escreva [ilegível] no lugar.
- Se não houver texto, responda apenas: "Nenhum texto encontrado".

IMPORTANTE:
- A mensagem pode ter um caption (<legenda>). SE existir, utilize a mensagem anexa como contexto extra, tente capturar o sentido da mensagem e objetivo pelo qual o usuário esteja enviando esta imagem na conversa
- Não invente conteúdo; se tiver dúvida, use [ilegível]."""

        # Adiciona contexto da legenda se existir
        user_prompt = f"""#Dados
<legenda>
{caption if caption else "Nenhuma legenda fornecida"}
</legenda>

Analise a imagem e extraia TODO o texto visível seguindo as instruções."""

        # Monta a mensagem para a API
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                            "detail": "high"  # Usar alta resolução para melhor extração de texto
                        }
                    }
                ]
            }
        ]
        
        logger.info("Iniciando extração de texto com OpenAI Vision...")
        
        # Faz a chamada para a API
        response = client.chat.completions.create(
            model="gpt-4o",  # Modelo otimizado para visão e texto
            messages=messages,
            max_tokens=4000,  # Permite respostas longas para textos extensos
            temperature=0.0   # Determinístico para maior precisão
        )
        
        extracted_text = response.choices[0].message.content.strip()
        
        # Estima tokens utilizados (aproximação baseada no tamanho da imagem e resposta)
        image_size = os.path.getsize(image_path)
        estimated_tokens = int((image_size / 1024) * 0.75) + len(extracted_text.split()) * 1.3
        
        logger.info(f"Extração concluída:")
        logger.info(f"  - Texto extraído: {len(extracted_text)} caracteres")
        logger.info(f"  - Palavras: {len(extracted_text.split())} palavras")
        logger.info(f"  - Tokens estimados: {int(estimated_tokens)}")
        logger.info(f"  - Tamanho da imagem: {image_size / 1024:.1f} KB")
        
        if caption:
            logger.info(f"  - Caption utilizada como contexto: {caption[:100]}...")
        
        return extracted_text
        
    except Exception as e:
        logger.error(f"Erro na API OpenAI Vision: {e}")
        raise Exception(f"Erro ao processar imagem com OpenAI Vision: {str(e)}") 