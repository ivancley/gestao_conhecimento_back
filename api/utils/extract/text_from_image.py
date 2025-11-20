"""
Módulo para extração de texto de imagens usando OpenAI Vision.

Este módulo implementa a funcionalidade de extrair texto de imagens recebidas via WhatsApp
através da EvolutionAPI, utilizando o modelo GPT-4 Vision da OpenAI.

Características principais:
- Download de imagens da EvolutionAPI em formato base64
- Processamento com OpenAI Vision (modelo gpt-4o)
- Suporte a captions/legendas como contexto adicional
- Prompt otimizado para extração fiel de texto
- Gerenciamento de arquivos temporários
- Logging detalhado para monitoramento
- Tratamento robusto de erros
- Estimativa de consumo de tokens

O prompt foi especificamente desenhado para preservar formatação, ordem visual,
números, símbolos e marcas d'água, mantendo fidelidade ao texto original.
"""

import base64
import logging
from pathlib import Path

from api.utils.evolution_api import get_media_base64, EvolutionAPIError
from api.utils.ia.ia_imagem import process_image_with_vision
from api.utils.utils_file import cleanup_temp_file
from api.v1._shared.constants import MESSAGE_TYPE_IMAGE_ERROR
from api.v1._shared.custom_schemas import MensagemZap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _baixa_imagem(instance_name, message_id) -> str:
    """
    Baixa imagem da EvolutionAPI e salva localmente.
    
    Args:
        instance_name: Nome da instância
        message_id: ID da mensagem
        
    Returns:
        str: Caminho para o arquivo da imagem baixada
    """
    try:        
        # Usa o método centralizado da Evolution API
        response_data = await get_media_base64(instance_name, message_id)
        
        # Busca o base64 na resposta
        if "base64" in response_data:
            image_base64 = response_data["base64"]
        elif "data" in response_data and "base64" in response_data["data"]:
            image_base64 = response_data["data"]["base64"]
        else:
            # Se não encontrar o base64, use a resposta completa
            image_base64 = response_data.get("media", response_data.get("base64", ""))
        
        if not image_base64:
            raise ValueError("Base64 não encontrado na resposta da API")
        
        # Remove prefixo data:image/... se existir
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        
        # Decodifica o base64
        image_bytes = base64.b64decode(image_base64)
        
        # Cria a pasta temp se não existir
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Define o nome do arquivo (usa jpg como padrão)
        filename = f"{instance_name}_{message_id}.jpg"
        file_path = temp_dir / filename
        
        # Salva o arquivo da imagem
        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)
        
        logger.info(f"Imagem salva com sucesso: {file_path}")
        
        return str(file_path)
        
    except EvolutionAPIError as e:
        logger.error(f"Erro HTTP ao buscar mídia: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        logger.error(f"Detalhes do erro HTTP: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Status HTTP: {e.response.status_code}")
            logger.error(f"Resposta HTTP: {e.response.text}")
        raise Exception(f"Erro HTTP ao baixar imagem da EvolutionAPI: {e}")
    except base64.binascii.Error as e:
        logger.error(f"Erro ao decodificar base64: {e}")
        raise Exception(f"Erro ao decodificar imagem: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao processar imagem: {e}")
        logger.error(f"Tipo do erro: {type(e)}")
        raise Exception(f"Erro ao processar imagem: {str(e)}")

async def extract_text_from_image(mensagem: MensagemZap) -> str:
    """
    Extrai texto de uma imagem usando OpenAI Vision.
    
    Args:
        data: Dados da mensagem contendo a imagem
        
    Returns:
        Message: Objeto com o texto extraído
    """
    response = ""
    try:
        file_path = await _baixa_imagem(mensagem.nome_instancia, mensagem.message_id)
        
    except Exception as e:
        logger.error(f"Erro ao baixar imagem: {e}")
        response = MESSAGE_TYPE_IMAGE_ERROR
        
    
    # Processa a imagem com OpenAI Vision
    try:
        logger.info(f"Processando imagem com OpenAI Vision...")
        response = await process_image_with_vision(file_path, mensagem.label)    
        logger.info(f"FINALIZANDO extract_text_from_image com sucesso")
        
    except Exception as e:
        logger.error(f" Erro ao processar imagem: {e}")
        responseo = MESSAGE_TYPE_IMAGE_ERROR
    
    cleanup_temp_file(file_path)
    return response