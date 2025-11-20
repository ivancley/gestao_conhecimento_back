import io
import os
import logging
import asyncio
from urllib.parse import unquote, urlparse

import requests
from pdf2image import convert_from_bytes

from api.utils.modules.upload.upload_utils import azure_upload_buffer


# Função de trabalho síncrona (não bloqueia o event loop pois será executada em thread)
def _gerar_thumbnail_pdf_sync(pdf_url: str):
    try:
        parsed_url = urlparse(pdf_url)
        file_extension = os.path.splitext(parsed_url.path)[1].lower()

        if file_extension != ".pdf":
            logging.error("A URL não aponta para um arquivo PDF válido")
            return None

        # 1. Download do PDF
        response = requests.get(pdf_url)
        if response.status_code != 200:
            logging.error("Falha ao fazer download do PDF")
            return None

        pdf_bytes = response.content

        # 2. Conversão para imagem (primeira página)
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)

        # 3. Criação do thumbnail
        thumbnail_size = (256, 256)
        buffer = io.BytesIO()
        images[0].thumbnail(thumbnail_size)
        images[0].save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        # 4. Nome do arquivo
        original_filename = os.path.basename(parsed_url.path)
        base_name = os.path.splitext(original_filename)[0]
        thumbnail_filename = f"{unquote(base_name)}_thumbnail.jpg"

        # 5. Upload
        url_thumbnail = azure_upload_buffer(
            buffer=buffer.getvalue(),
            file_name=thumbnail_filename,
            local_path="thumbnails",
        )

        return url_thumbnail

    except Exception as e:
        logging.error(f"Erro no processamento: {str(e)}")
        return None


# Wrapper assíncrono para ser usado no restante do código
async def gerar_thumbnail_pdf(pdf_url: str):
    """Gera thumbnail de forma assíncrona utilizando thread pool."""
    return await asyncio.to_thread(_gerar_thumbnail_pdf_sync, pdf_url)