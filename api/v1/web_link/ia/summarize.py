from typing import Optional
from openai import OpenAI
import logging
from decouple import config
logger = logging.getLogger(__name__)

# Configurações
MODEL = "gpt-4o-mini"
MAX_INPUT_CHARS = 12000  # ~3000 tokens (limite seguro para contexto)
MAX_OUTPUT_TOKENS = 400  # ~150 palavras em português
TEMPERATURE = 0.3
CHUNK_SIZE = 10000 
OPENAI_API_KEY = config("OPENAI_API_KEY")

SYSTEM_PROMPT1 = """
Você é um assistente que resume textos de forma fiel, concisa e objetiva. 
Use o idioma Português, seja claro e não invente informações.
Crie um resumo executivo em um parágrafo de aproximadamente 100-150 palavras, destacando os pontos principais.
"""

SYSTEM_PROMPT = """
Você é um assistente especializado em resumir textos de forma fiel, concisa e direta. 
Resuma o conteúdo em **tópicos claros e objetivos**, com frases curtas e linguagem executiva.
Use o idioma Português e **não invente informações**.  
Estrutura de saída:
- Título geral (1 linha)
- 5 a 8 tópicos principais destacando ideias-chave, decisões, dados e conclusões.
- Se aplicável, um tópico final chamado "Síntese" com uma frase que resume o todo.
"""

def _truncate_text(text: str, max_chars: int) -> str:
    """Trunca texto mantendo palavras inteiras."""
    if len(text) <= max_chars:
        return text
    
    # Trunca e encontra o último espaço
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated + "..."


def _summarize_chunk(client: OpenAI, text: str) -> str:
    """
    Resume um chunk de texto usando GPT-4o-mini.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Resuma o seguinte texto:\n\n{text}"}
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=TEMPERATURE,
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo do chunk: {e}")
        raise


def generate_summary(
    client: OpenAI,
    title: Optional[str],
    text_full: Optional[str],
    description: Optional[str] = None
) -> str:
    """
    Gera um resumo executivo do conteúdo usando GPT-4o-mini.
    
    Estratégia:
    - Se text_full for pequeno (<12K chars): resume direto
    - Se text_full for grande (>12K chars): divide em chunks, resume cada um, depois resume os resumos
    - Se text_full estiver vazio: usa title + description
    
    Args:
        client: Cliente OpenAI
        title: Título da página
        text_full: Texto completo da página
        description: Descrição da página (meta tag)
        
    Returns:
        str: Resumo em português (~100-150 palavras)
    """
    # Caso 1: Sem conteúdo suficiente
    if not text_full or len(text_full.strip()) < 50:
        # Fallback: title + description
        fallback_text = ""
        if title:
            fallback_text += title
        if description:
            fallback_text += f". {description}" if fallback_text else description
        
        if fallback_text:
            return _summarize_chunk(client, fallback_text)
        else:
            return "Sem conteúdo disponível para resumir."
    
    # Caso 2: Texto pequeno - resume direto
    if len(text_full) <= MAX_INPUT_CHARS:
        context = f"Título: {title}\n\n" if title else ""
        context += text_full
        return _summarize_chunk(client, context)
    
    # Caso 3: Texto grande - estratégia de resumo em etapas
    logger.info(f"Texto grande ({len(text_full)} chars), usando estratégia de chunks")
    
    # Divide em chunks
    chunks = []
    for i in range(0, len(text_full), CHUNK_SIZE):
        chunk = text_full[i:i + CHUNK_SIZE]
        chunks.append(chunk)
    
    # Resume cada chunk
    chunk_summaries = []
    for idx, chunk in enumerate(chunks[:3]):
        try:
            logger.info(f"Resumindo chunk {idx+1}/{min(len(chunks), 3)}")
            summary = _summarize_chunk(client, chunk)
            chunk_summaries.append(summary)
        except Exception as e:
            logger.warning(f"Falha ao resumir chunk {idx+1}: {e}")
            continue
    
    # Se não conseguiu resumir nenhum chunk, usa fallback
    if not chunk_summaries:
        logger.warning("Falha em todos os chunks, usando fallback")
        fallback = _truncate_text(text_full, 500)
        return fallback
    
    combined_summaries = "\n\n".join(chunk_summaries)
    
    # Gerado pela IA
    # if len(combined_summaries) <= MAX_INPUT_CHARS:
    #
    if len(combined_summaries) > 1:
        try:
            final_context = f"Título: {title}\n\n" if title else ""
            final_context += f"Resumos parciais do conteúdo:\n\n{combined_summaries}"
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Crie um resumo executivo único e coeso a partir destes resumos parciais:\n\n{final_context}"}
                ],
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.3,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo final: {e}")
            return chunk_summaries[0]
    
    # Se ainda for muito grande, retorna o primeiro resumo
    return chunk_summaries[0] 