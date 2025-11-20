import logging
from typing import List, Tuple, Optional
from uuid import UUID

from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1._database.models import Conhecimento, WebLink

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
TOP_K = 5
MAX_TOKENS = 500
TEMPERATURE = 0.3

SYSTEM_PROMPT = """Você é um assistente útil que responde perguntas com base apenas no contexto fornecido.

REGRAS IMPORTANTES:
1. Responda APENAS com base nas informações do contexto fornecido
2. Se a informação não estiver no contexto, diga claramente "Não tenho informações suficientes para responder essa pergunta"
3. Seja claro, objetivo e direto
4. Responda sempre em Português
5. Não invente ou assuma informações que não estão explícitas no contexto
"""


def _calculate_confidence(distances: List[float]) -> float:
    """
    Calcula score de confiança baseado nas distâncias dos chunks.
    Distâncias menores = maior confiança
    
    Fórmula: confidence = 1 / (1 + avg_distance)
    """
    if not distances:
        return 0.0
    
    avg_distance = sum(distances) / len(distances)
    confidence = 1.0 / (1.0 + avg_distance)
    
    # Normaliza entre 0 e 1
    return min(max(confidence, 0.0), 1.0)


def retrieve_relevant_chunks(
    db: Session,
    query_embedding: List[float],
    context: str,
    top_k: int = TOP_K
) -> List[Tuple[str, str, float]]:
    """
    Busca os chunks mais relevantes no pgvector para um contexto específico.
    
    Args:
        db: Sessão do banco
        query_embedding: Embedding da pergunta
        context: URL do WebLink (filtro)
        top_k: Número de chunks a retornar
        
    Returns:
        Lista de tuplas (title, content, distance)
    """
    # Query SQL com busca vetorial filtrada por context
    sql = text("""
        SELECT title, content, embedding <-> :query_embedding AS distance
        FROM conhecimento
        WHERE context = :context
        ORDER BY distance
        LIMIT :top_k
    """)
    
    result = db.execute(
        sql,
        {
            "query_embedding": str(query_embedding),
            "context": context,
            "top_k": top_k
        }
    ).fetchall()
    
    return [(row[0], row[1], row[2]) for row in result]


def generate_rag_answer(
    client: OpenAI,
    question: str,
    chunks: List[Tuple[str, str, float]]
) -> Tuple[str, int, int]:
    """
    Gera resposta usando os chunks recuperados como contexto.
    
    Args:
        client: Cliente OpenAI
        question: Pergunta do usuário
        chunks: Lista de (title, content, distance)
        
    Returns:
        Tupla (answer, input_tokens, output_tokens)
    """
    if not chunks:
        return (
            "Não tenho informações suficientes para responder essa pergunta.",
            0,
            0
        )
    
    # Monta contexto a partir dos chunks
    context_parts = []
    for idx, (title, content, distance) in enumerate(chunks, 1):
        context_parts.append(f"[Fonte {idx}] {title}\n{content}")
    
    context_text = "\n\n".join(context_parts)
    
    # Prompt para o modelo
    user_prompt = f"""Contexto disponível:

{context_text}

---

Pergunta: {question}

Resposta:"""
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        
        answer = response.choices[0].message.content.strip()
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        return answer, input_tokens, output_tokens
        
    except Exception as e:
        logger.error(f"Erro ao gerar resposta RAG: {e}")
        raise


def query_weblink_knowledge(
    db: Session,
    client: OpenAI,
    weblink_id: UUID,
    question: str
) -> dict:
    """
    Executa query RAG completa para um WebLink específico.
    
    Args:
        db: Sessão do banco
        client: Cliente OpenAI
        weblink_id: ID do WebLink
        question: Pergunta do usuário
        
    Returns:
        Dict com answer, confidence, input_tokens, output_tokens
        
    Raises:
        ValueError: Se WebLink não existir ou não tiver conhecimento
    """
    # 1) Verifica se WebLink existe
    weblink = db.query(WebLink).filter(WebLink.id == weblink_id).first()
    if not weblink:
        raise ValueError("WebLink não encontrado")
    
    if not weblink.weblink:
        raise ValueError("WebLink não possui URL associada")
    
    context = weblink.weblink  # URL como context
    
    # 2) Verifica se existe conhecimento para esse context
    conhecimento_count = db.query(Conhecimento).filter(
        Conhecimento.context == context
    ).count()
    
    if conhecimento_count == 0:
        raise ValueError("WebLink não possui conhecimento ingerido")
    
    # 3) Gera embedding da pergunta
    try:
        embedding_response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=question
        )
        query_embedding = embedding_response.data[0].embedding
    except Exception as e:
        logger.error(f"Erro ao gerar embedding da pergunta: {e}")
        raise
    
    # 4) Busca chunks relevantes
    chunks = retrieve_relevant_chunks(
        db=db,
        query_embedding=query_embedding,
        context=context,
        top_k=TOP_K
    )
    
    if not chunks:
        raise ValueError("WebLink não possui conhecimento ingerido")
    
    # 5) Calcula confiança
    distances = [dist for _, _, dist in chunks]
    confidence = _calculate_confidence(distances)
    
    # 6) Gera resposta
    answer, input_tokens, output_tokens = generate_rag_answer(
        client=client,
        question=question,
        chunks=chunks
    )
    
    logger.info(
        f"RAG Query completa - WebLink: {weblink_id}, "
        f"Chunks: {len(chunks)}, Confidence: {confidence:.2f}, "
        f"Tokens: {input_tokens} in / {output_tokens} out"
    )
    
    return {
        "answer": answer,
        "confidence": round(confidence, 2),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "weblink_id": str(weblink_id)
    }