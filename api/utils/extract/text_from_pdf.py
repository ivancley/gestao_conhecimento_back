import base64
import logging
from pathlib import Path

import PyPDF2

from api.utils.evolution_api import EvolutionAPIError, get_media_base64
from api.utils.utils_file import cleanup_temp_file
from api.v1._shared.constants import (
    MESSAGE_TYPE_ARQUIVO_MUITO_LONGO,
    MESSAGE_TYPE_PDF_ERROR,
)
from api.v1._shared.custom_schemas import MensagemZap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _baixa_pdf(instance_name, message_id) -> str:
    try:        
        # Usa o método centralizado da Evolution API
        response_data = await get_media_base64(instance_name, message_id)
            
        # Assume que o base64 está em response_data["base64"] ou similar
        # Ajuste conforme a estrutura real da resposta da API
        if "base64" in response_data:
            pdf_base64 = response_data["base64"]
        elif "data" in response_data and "base64" in response_data["data"]:
            pdf_base64 = response_data["data"]["base64"]
        else:
            # Se não encontrar o base64, use a resposta completa
            pdf_base64 = response_data.get("media", response_data.get("base64", ""))
        
        if not pdf_base64:
            raise ValueError("Base64 não encontrado na resposta da API")
        
        # Remove prefixo data:application/pdf;... se existir
        if "," in pdf_base64:
            pdf_base64 = pdf_base64.split(",")[1]
        
        # Decodifica o base64
        pdf_bytes = base64.b64decode(pdf_base64)
        
        # Cria a pasta temp se não existir
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Define o nome do arquivo
        filename = f"{instance_name}_{message_id}.pdf"
        file_path = temp_dir / filename
        
        # Salva o arquivo PDF
        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_bytes)
        
        logger.info(f"Arquivo PDF salvo com sucesso: {file_path}")
        
        return str(file_path)
            
    except EvolutionAPIError as e:
        logger.error(f"Erro HTTP ao buscar mídia: {e}")
        raise Exception(f"Erro ao baixar PDF da EvolutionAPI: {e}")
    except base64.binascii.Error as e:
        logger.error(f"Erro ao decodificar base64: {e}")
        raise Exception(f"Erro ao decodificar PDF: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao processar PDF: {e}")
        raise Exception(f"Erro ao processar PDF: {str(e)}")

def _extract_text_from_pdf_file(file_path: str) -> tuple[str, int]:
    """
    Extrai texto de um arquivo PDF e retorna o texto e número de páginas.
    
    Args:
        file_path: Caminho para o arquivo PDF
        
    Returns:
        tuple: (texto_extraido, numero_de_paginas)
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Se tem mais que 2 páginas, retorna mensagem especial
            if num_pages > 2:
                return MESSAGE_TYPE_ARQUIVO_MUITO_LONGO, num_pages
            
            # Extrai texto de todas as páginas (máximo 2)
            text = ""
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text.strip(), num_pages
            
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {e}")
        raise Exception(f"Erro ao processar conteúdo do PDF: {str(e)}")

async def extract_text_from_pdf(mensagem: MensagemZap) -> str:    

    response = ""

    try:
        file_path = await _baixa_pdf(mensagem.nome_instancia, mensagem.message_id)
        logger.info(f"PDF salvo em: {file_path}")
        
        # Extrai o texto do PDF
        extracted_text = _extract_text_from_pdf_file(file_path)
        
        logger.info(f"Extração de texto concluída ")
        response = extracted_text
        
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}")
        response = MESSAGE_TYPE_PDF_ERROR
        
    cleanup_temp_file(file_path)
    return response