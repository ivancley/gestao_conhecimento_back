import base64
import logging
from pathlib import Path

from api.utils.evolution_api import EvolutionAPIError, get_media_base64
from api.utils.ia.ia_audio import transcribe_mp4_to_text
from api.utils.utils_file import cleanup_temp_file
from api.v1._shared.constants import MESSAGE_TYPE_AUDIO_ERROR
from api.v1._shared.custom_schemas import MensagemZap, TranscriptionResult
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _baixa_audio(instance_name, message_id) -> str:
    try:        
        # Usa o método centralizado da Evolution API com conversão para MP4
        response_data = await get_media_base64(instance_name, message_id, convert_to_mp4=True)
        
        # Assume que o base64 está em response_data["base64"] ou similar
        # Ajuste conforme a estrutura real da resposta da API
        if "base64" in response_data:
            audio_base64 = response_data["base64"]
        elif "data" in response_data and "base64" in response_data["data"]:
            audio_base64 = response_data["data"]["base64"]
        else:
            # Se não encontrar o base64, use a resposta completa
            audio_base64 = response_data.get("media", response_data.get("base64", ""))
        
        if not audio_base64:
            raise ValueError("Base64 não encontrado na resposta da API")
        
        # Remove prefixo data:audio/... se existir
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",")[1]
        
        # Decodifica o base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Cria a pasta temp se não existir
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Define o nome do arquivo
        filename = f"{instance_name}_{message_id}.mp4"
        file_path = temp_dir / filename
        
        # Salva o arquivo MP4
        with open(file_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
        
        logger.info(f"Arquivo salvo com sucesso: {file_path}")
        
        return file_path
        
    except EvolutionAPIError as e:
        logger.error(f"Erro HTTP ao buscar mídia: {e}")
        return "Erro ao baixar áudio da EvolutionAPI"
    except base64.binascii.Error as e:
        logger.error(f"Erro ao decodificar base64: {e}")
        return "Erro ao decodificar áudio"
    except Exception as e:
        logger.error(f"Erro inesperado ao processar áudio: {e}")
        return f"Erro ao processar áudio: {str(e)}"
    

async def text_from_audio(mensagem: MensagemZap) -> str:    

    # Baixa o áudio
    file_path = await _baixa_audio(mensagem.nome_instancia, mensagem.message_id)

    logger.info(f"Áudio salvo em: {file_path}")

    response_texto = ""
    
    # Transcreve o áudio usando OpenAI
    try:
        transcription_result: TranscriptionResult = transcribe_mp4_to_text(str(file_path))
        logger.info(f"Transcrição concluída - Tokens utilizados: {transcription_result.tokens_used}")        
        # Retorna Message com texto transcrito e informações detalhadas
        response_texto = transcription_result.text

    except Exception as e:
        logger.error(f"Erro ao transcrever áudio: {e}")
        mensagem.tipo = MESSAGE_TYPE_AUDIO_ERROR 
    
    # Remove o arquivo temporário após a transcrição
    cleanup_temp_file(file_path)

    return response_texto

