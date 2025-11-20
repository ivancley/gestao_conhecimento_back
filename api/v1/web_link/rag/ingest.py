from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
from api.v1._database.models import Conhecimento
from api.v1._shared.custom_schemas import PageContent
from decouple import config
from textwrap import wrap

MAX_CHARS = 2500  # Aumentado para preservar mais contexto
MIN_CHARS_TO_PROCESS = 100  # Aumentado para evitar chunks muito pequenos
# Otimização - N textos enviados por vez para o OpenAI
BATCH_SIZE = 64 

EMBED_MODEL = config("EMBED_MODEL")


def embed_batch(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """Gera embeddings em batch para múltiplos textos."""
    if not texts:
        return []
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def replace_context(db: Session, context: str):
    """Apaga todos os conhecimentos de um contexto específico."""
    db.execute(text("DELETE FROM conhecimento WHERE context = :c"), {"c": context})
    db.commit()


def analyze_table(db: Session):
    """Otimiza a tabela conhecimento após inserções."""
    db.execute(text("ANALYZE conhecimento;"))
    db.commit()


def _chunk_text(text: str, max_chars: int = MAX_CHARS) -> List[str]:
    """
    Divide texto em chunks respeitando o limite de caracteres.
    Mantém palavras inteiras (não quebra no meio) e preserva contexto.
    """
    if len(text) <= max_chars:
        return [text.strip()]
    
    # Primeiro tenta dividir por parágrafos duplos
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Se o parágrafo sozinho já é muito grande, divide ele
        if len(para) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Divide o parágrafo grande usando wrap
            para_chunks = wrap(para, max_chars, break_long_words=False, replace_whitespace=False)
            chunks.extend([c.strip() for c in para_chunks if c.strip()])
        else:
            # Se adicionar este parágrafo exceder o limite, finaliza o chunk atual
            if current_chunk and len(current_chunk) + len(para) + 2 > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
    
    # Adiciona o último chunk se houver
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return [c for c in chunks if len(c) >= MIN_CHARS_TO_PROCESS]


def _filter_navigation_content(text: str) -> str:
    """
    Remove conteúdo de navegação e menus do texto, mantendo conteúdo técnico do produto.
    """
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Mantém linhas com conteúdo substancial (mais de 50 caracteres)
        if len(line) > 50:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def _extract_paragraphs_with_headings(page_content: PageContent) -> List[Tuple[str, str]]:
    """
    Extrai parágrafos do text_full e associa com headings quando possível.
    Filtra conteúdo de navegação para focar no conteúdo real do produto.
    
    Retorna lista de (heading, paragraph).
    Se não houver heading correspondente, usa o primeiro h1 ou título da página.
    """
    items: List[Tuple[str, str]] = []
    
    # Pega o texto completo e filtra navegação
    text_full = page_content.text_full or ""
    text_full = _filter_navigation_content(text_full)
    
    if len(text_full) < MIN_CHARS_TO_PROCESS:
        return []
    
    # Determina heading padrão
    default_heading = ""
    if page_content.headings.h1:
        default_heading = page_content.headings.h1[0]
    elif page_content.title:
        default_heading = page_content.title
    else:
        default_heading = "Conteúdo"
    
    # Divide por parágrafos (linhas duplas ou simples)
    paragraphs = [p.strip() for p in text_full.split("\n\n") if p.strip()]
    
    # Se não tiver parágrafos bem definidos, divide por \n
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in text_full.split("\n") if p.strip()]
    
    # Associa cada parágrafo ao heading mais próximo ou ao padrão
    current_heading = default_heading
    h2_list = page_content.headings.h2 if page_content.headings.h2 else []
    h3_list = page_content.headings.h3 if page_content.headings.h3 else []
    all_headings = page_content.headings.h1 + h2_list + h3_list
    
    for para in paragraphs:
        # Verifica se o parágrafo começa com algum heading conhecido
        heading_found = False
        for heading in all_headings:
            if para.startswith(heading):
                current_heading = heading
                # Remove o heading do parágrafo
                para = para[len(heading):].strip()
                heading_found = True
                break
        
        if para and len(para) >= MIN_CHARS_TO_PROCESS:  # Só adiciona se tiver conteúdo suficiente
            items.append((current_heading, para))
    
    return items


def chunk_page_content(page_content: PageContent) -> List[Tuple[str, str]]:
    """
    Converte PageContent em chunks (title, content) para embedding.
    
    Estratégia:
    1. Extrai parágrafos do text_full
    2. Associa com headings (h1, h2, h3)
    3. Divide parágrafos longos em chunks de MAX_CHARS
    4. Title = "{page_title} - {heading}"
    
    Returns:
        Lista de tuplas (title, chunk_content)
    """
    items: List[Tuple[str, str]] = []
    
    # Extrai parágrafos com headings
    paragraphs_with_headings = _extract_paragraphs_with_headings(page_content)
    
    if not paragraphs_with_headings:
        return []
    
    # Processa cada parágrafo
    page_title = page_content.title or "Sem título"
    
    for heading, paragraph in paragraphs_with_headings:
        # Cria título combinado
        if heading and heading != page_title:
            combined_title = f"{page_title} - {heading}"
        else:
            combined_title = page_title
        
        # Divide parágrafo em chunks se necessário
        chunks = _chunk_text(paragraph, MAX_CHARS)
        
        for chunk in chunks:
            if len(chunk) >= MIN_CHARS_TO_PROCESS:
                items.append((combined_title, chunk))
    
    return items


def ingest_page_content(
    db: Session,
    client: OpenAI,
    *,
    context: str,
    page_content: PageContent
) -> Dict:
    """
    Ingere um PageContent no pgvector.
    
    Args:
        db: Sessão do banco de dados
        client: Cliente OpenAI para embeddings
        context: URL do weblink (identificador único)
        page_content: Objeto PageContent extraído do scraping
        
    Returns:
        Dict com estatísticas: processed, chunks_total, inserted, failed
    """
    # 1) Apaga conhecimentos antigos do mesmo contexto
    replace_context(db, context)
    
    # 2) Cria chunks do PageContent
    items = chunk_page_content(page_content)
    
    if not items:
        return {
            "processed": False,
            "reason": "sem chunks válidos (texto muito curto ou vazio)"
        }
    
    # 3) Gera embeddings e insere em batches
    total = len(items)
    inserted = 0
    failed = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        
        try:
            # Tenta embeddar o batch inteiro
            texts = [content for (_, content) in batch]
            embeddings = embed_batch(client, texts)
            
            # Insere todos do batch
            for (title, content), embedding in zip(batch, embeddings):
                row = Conhecimento(
                    title=title,
                    context=context,
                    content=content,
                    embedding=embedding
                )
                db.add(row)
                inserted += 1
            
            db.commit()
            
        except Exception as e:
            # Se batch falhar, tenta item a item
            print(f"[AVISO] Falha no batch {i}-{i+BATCH_SIZE}: {e}")
            
            for title, content in batch:
                try:
                    embedding = embed_batch(client, [content])[0]
                    row = Conhecimento(
                        title=title,
                        context=context,
                        content=content,
                        embedding=embedding
                    )
                    db.add(row)
                    inserted += 1
                except Exception as item_error:
                    print(f"[ERRO] Falha ao inserir chunk: {item_error}")
                    failed += 1
            
            db.commit()
    
    # 4) Otimiza a tabela
    analyze_table(db)
    
    return {
        "processed": True,
        "chunks_total": total,
        "inserted": inserted,
        "failed": failed
    }