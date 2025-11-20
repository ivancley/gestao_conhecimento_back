import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def cleanup_temp_file(file_path, context=""):
    """
    Remove arquivo temporário de forma segura com logging apropriado.
    
    Args:
        file_path: Caminho para o arquivo a ser removido
        context: Contexto adicional para o log (ex: "após erro")
    """
    try:
        if file_path and Path(file_path).exists():
            os.remove(file_path)
            context_msg = f" {context}" if context else ""
            logger.info(f"Arquivo temporário removido{context_msg}: {file_path}")
    except Exception as cleanup_error:
        logger.warning(f"Não foi possível remover arquivo temporário {file_path}: {cleanup_error}")