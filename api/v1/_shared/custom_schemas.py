from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class HeadingsData(BaseModel):
    """Estrutura para cabeçalhos extraídos da página"""
    h1: List[str] = Field(default_factory=list)
    h2: List[str] = Field(default_factory=list)
    h3: List[str] = Field(default_factory=list)


class OpenGraphData(BaseModel):
    """Metadados Open Graph"""
    type: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None


class PageContent(BaseModel):
    """Schema para conteúdo extraído de uma página web"""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    canonical: Optional[str] = None
    headings: HeadingsData = Field(default_factory=HeadingsData)
    text_full: Optional[str] = Field(None, description="Texto completo da página (limitado a 20KB)")
    og: OpenGraphData = Field(default_factory=OpenGraphData)
    model_config: Dict[str, Any] = {"from_attributes": True}


class RagQueryRequest(BaseModel):
    """Schema para requisição de query RAG"""
    question: str = Field(..., min_length=3, description="Pergunta a ser respondida com base no conhecimento")


class RagChunkSource(BaseModel):
    """Chunk de conhecimento usado como fonte"""
    title: str
    content: str
    distance: float


class RagQueryResponse(BaseModel):
    """Schema para resposta de query RAG"""
    answer: str = Field(..., description="Resposta gerada pela IA")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança da resposta (0-1)")
    input_tokens: int = Field(..., description="Tokens de entrada usados")
    output_tokens: int = Field(..., description="Tokens de saída gerados")
    weblink_id: str = Field(..., description="ID do WebLink consultado")