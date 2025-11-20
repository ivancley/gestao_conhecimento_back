import logging
from typing import Any, Dict, Optional

from decouple import config
import httpx

from api.v1._shared.custom_schemas import MensagemZap

# Configurações da Evolution API
EVOLUTIONAPI_URL = config("EVOLUTIONAPI_URL")
EVOLUTIONAPI_KEY = config("EVOLUTIONAPI_KEY")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvolutionAPIError(Exception):
    """Exceção customizada para erros da Evolution API"""
    pass


async def get_media_base64(
    instance_name: str, 
    message_id: str, 
    convert_to_mp4: bool = False
) -> Dict[str, Any]:
    """
    Obtém o conteúdo de mídia em formato Base64 da Evolution API.
    
    Args:
        instance_name: Nome da instância do WhatsApp
        message_id: ID da mensagem que contém a mídia
        convert_to_mp4: Se deve converter áudio para MP4 (opcional, padrão: False)
        
    Returns:
        Dict contendo os dados da resposta da API
        
    Raises:
        EvolutionAPIError: Em caso de erro na requisição
    """
    try:
        url = f"{EVOLUTIONAPI_URL}/chat/getBase64FromMediaMessage/{instance_name}"
        
        headers = {
            "apikey": EVOLUTIONAPI_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": {
                "key": {
                    "id": message_id
                }
            }
        }
        
        # Adiciona parâmetro de conversão para MP4 se necessário
        if convert_to_mp4:
            payload["convertToMp4"] = True
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            
            logger.info(f"Mídia obtida com sucesso para message_id: {message_id}")
            return response_data
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Erro HTTP ao obter mídia (Status {e.response.status_code}): {e.response.text}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)
    except httpx.TimeoutException:
        error_msg = f"Timeout ao obter mídia para message_id: {message_id}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado ao obter mídia: {str(e)}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)


async def send_text_message(
    instance_name: str,
    phone_number: str,
    text: str
) -> Dict[str, Any]:
    """
    Envia uma mensagem de texto via Evolution API.
    
    Args:
        instance_name: Nome da instância do WhatsApp
        phone_number: Número do destinatário
        text: Texto da mensagem
        
    Returns:
        Dict contendo os dados da resposta da API
        
    Raises:
        EvolutionAPIError: Em caso de erro na requisição
    """
    try:
        url = f"{EVOLUTIONAPI_URL}/message/sendText/{instance_name}"
        
        headers = {
            "apikey": EVOLUTIONAPI_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "number": phone_number,
            "text": text
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            
            logger.info(f"Mensagem de texto enviada com sucesso para: {phone_number}")
            return response_data
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Erro HTTP ao enviar texto (Status {e.response.status_code}): {e.response.text}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)
    except httpx.TimeoutException:
        error_msg = f"Timeout ao enviar texto para: {phone_number}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado ao enviar texto: {str(e)}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)


async def send_media_message(
    instance_name: str,
    phone_number: str,
    media_base64: str,
    media_type: str,
    filename: str,
    caption: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envia uma mensagem de mídia (imagem ou PDF) via Evolution API.
    
    Args:
        instance_name: Nome da instância do WhatsApp
        phone_number: Número do destinatário
        media_base64: Conteúdo da mídia em Base64
        media_type: Tipo da mídia ('image' ou 'document')
        filename: Nome do arquivo
        caption: Legenda da mídia (opcional)
        
    Returns:
        Dict contendo os dados da resposta da API
        
    Raises:
        EvolutionAPIError: Em caso de erro na requisição
    """
    try:
        url = f"{EVOLUTIONAPI_URL}/message/sendMedia/{instance_name}"
        
        headers = {
            "apikey": EVOLUTIONAPI_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "number": phone_number,
            "mediaMessage": {
                "mediaType": media_type,
                "fileName": filename,
                "media": media_base64
            }
        }
        
        # Adiciona caption se fornecido
        if caption:
            payload["mediaMessage"]["caption"] = caption
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # Timeout maior para mídia
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            
            logger.info(f"Mensagem de mídia ({media_type}) enviada com sucesso para: {phone_number}")
            return response_data
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Erro HTTP ao enviar mídia (Status {e.response.status_code}): {e.response.text}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)
    except httpx.TimeoutException:
        error_msg = f"Timeout ao enviar mídia para: {phone_number}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado ao enviar mídia: {str(e)}"
        logger.error(error_msg)
        raise EvolutionAPIError(error_msg)


async def send_image_message(
    instance_name: str,
    phone_number: str,
    image_base64: str,
    caption: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envia uma mensagem de imagem via Evolution API.
    
    Args:
        instance_name: Nome da instância do WhatsApp
        phone_number: Número do destinatário
        image_base64: Conteúdo da imagem em Base64
        caption: Legenda da imagem (opcional)
        
    Returns:
        Dict contendo os dados da resposta da API
    """
    return await send_media_message(
        instance_name=instance_name,
        phone_number=phone_number,
        media_base64=image_base64,
        media_type="image",
        filename="image.jpg",
        caption=caption
    )


async def send_pdf_message(
    instance_name: str,
    phone_number: str,
    pdf_base64: str,
    filename: str = "document.pdf",
    caption: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envia uma mensagem de PDF via Evolution API.
    
    Args:
        instance_name: Nome da instância do WhatsApp
        phone_number: Número do destinatário
        pdf_base64: Conteúdo do PDF em Base64
        filename: Nome do arquivo PDF
        caption: Legenda do documento (opcional)
        
    Returns:
        Dict contendo os dados da resposta da API
    """
    return await send_media_message(
        instance_name=instance_name,
        phone_number=phone_number,
        media_base64=pdf_base64,
        media_type="document",
        filename=filename,
        caption=caption
    )


async def enviar_resposta_whatsapp(mensagem: MensagemZap, resposta_texto: str):
    """
    Envia a resposta do agente de volta para o WhatsApp.
    
    Args:
        mensagem: Mensagem original recebida
        resposta_texto: Texto da resposta do agente
    """
    try:
        await send_text_message(
            instance_name=mensagem.nome_instancia,
            phone_number=mensagem.telefone_remetente,
            text=resposta_texto
        )
        logger.info(f"Resposta enviada com sucesso para {mensagem.telefone_remetente}")
    except EvolutionAPIError as e:
        logger.error(f"Erro ao enviar resposta via Evolution API: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar resposta: {e}")