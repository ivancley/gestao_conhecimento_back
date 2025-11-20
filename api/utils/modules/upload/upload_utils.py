import logging
from typing import Optional

from pydantic import BaseModel, FilePath
from azure.storage.blob import BlobServiceClient, BlobClient
from api.utils.exceptions import ExceptionInternalServerError
from api.utils.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UPLOAD_UTIL")

# Para validação de parametros
class AzureUploadFileParams(BaseModel):
    output_file: FilePath
    file_name: str
    local_path: str

class AzureUploadBuffer(BaseModel):
    buffer: bytes
    file_name: str
    local_path: str

def azure_upload_file(output_file: str, file_name: str, local_path: str) -> str:
    """
    Uploads a file to Azure Blob Storage.
    :param output_file: Caminho do arquivo a ser enviado.
    :param file_name: Nome do arquivo no Azure Blob Storage.
    :param local_path: Local onde o arquivo está armazenado.
    :return: Caminho do arquivo enviado.
    """
    settings = Settings()
    params = AzureUploadFileParams(
        output_file=output_file,
        file_name=file_name, 
        local_path=local_path
    )
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        
        with open(output_file, "rb") as data:
            blob_client = container_client.get_blob_client(f"{params.local_path}/{params.file_name}")
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Arquivo {params.file_name} enviado com sucesso para o Azure Blob Storage como {params.file_name}.")
            
        response = f"{settings.AZURE_STORAGE_LINK}/{settings.AZURE_STORAGE_CONTAINER}/{params.local_path}/{params.file_name}"
        
    except Exception as e:
        logger.error(f"Erro ao enviar o arquivo para o Azure: {e}")
        raise ExceptionInternalServerError(detail=f"Erro ao enviar o arquivo para o Azure: {e}")
    
    return response


def azure_upload_buffer(buffer: bytes, file_name: str, local_path: str) -> str:
    """
    Uploads a file to Azure Blob Storage.
    :param buffer: Buffer do arquivo a ser enviado.
    :param file_name: Nome do arquivo no Azure Blob Storage.
    :param local_path: Local onde o arquivo está armazenado.
    :return: Caminho do arquivo enviado.
    """
    params = AzureUploadBuffer(
        buffer=buffer,
        file_name=file_name, 
        local_path=local_path
    )
    try:
        settings = Settings()
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        
        blob_client = container_client.get_blob_client(f"{params.local_path}/{params.file_name}")
        blob_client.upload_blob(params.buffer, overwrite=True)
        logger.info(f"Arquivo {params.file_name} enviado com sucesso para o Azure Blob Storage como {params.file_name}.")
        
        response = f"{settings.AZURE_STORAGE_LINK}/{settings.AZURE_STORAGE_CONTAINER}/{params.local_path}/{params.file_name}"
        
    except Exception as e:
        logger.error(f"Erro ao enviar o arquivo para o Azure: {e}")
        raise ExceptionInternalServerError(detail=f"Erro ao enviar o arquivo para o Azure: {e}")
    
    return response

def azure_get_file_exists(file_name: str, local_path: str) -> Optional[BlobClient]:
    
    try:
        settings = Settings()
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        blob_path = f"{local_path}/{file_name}"
        
        blob_client = container_client.get_blob_client(blob_path)
        
        return blob_client 
    except Exception:
        logger.warning(f"Arquivo {file_name} não encontrado em {local_path}")
        return None

def azure_get_file_bytes(file_name: str, local_path: str) -> bytes | None:
    """
    Obtém um arquivo do Azure Blob Storage.
    
    :param file_name: Nome do arquivo com extensão.
    :param local_path: Pasta onde o arquivo está armazenado.
    :return: Conteúdo do arquivo em bytes ou None se não existir.
    """
    try:        
        blob_path = f"{local_path}/{file_name}"
        blob_client = azure_get_file_exists(file_name, local_path)
        
        if blob_client is None:
            logger.warning(f"Arquivo {file_name} não encontrado em {local_path}")
            return None
        
        # Verifica se o blob existe
        blob_client.get_blob_properties()
        
        # Faz o download do conteúdo
        downloaded_blob = blob_client.download_blob()
        content = downloaded_blob.readall()
        
        logger.info(f"Arquivo {file_name} recuperado com sucesso de {blob_path}")
        return content
        
    except Exception:
        logger.warning(f"Arquivo {file_name} não encontrado em {local_path}")
        return None