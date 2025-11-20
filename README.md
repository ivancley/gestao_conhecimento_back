# Gestão de Conhecimento Backend API

Sistema de gestão de conhecimento que permite extrair, processar e consultar conteúdo de páginas web através de IA. O usuário envia um link, o sistema extrai o conteúdo, gera um resumo e disponibiliza um chat inteligente baseado em RAG para consultas sobre o material extraído.

---

## Funcionalidade Principal

### Como Funciona

O sistema oferece uma solução completa para transformar conteúdo web em conhecimento consultável:

1. **Envio de Link**: O usuário envia um link de uma página da internet
2. **Acesso e Extração**: O sistema acessa automaticamente a página e extrai todas as informações relevantes
3. **Geração de Resumo**: Utilizando IA (GPT-4o-mini), o sistema cria um resumo inteligente do conteúdo extraído
4. **Alimentação do RAG**: O conteúdo é processado, dividido em chunks e seus embeddings são gerados e armazenados em um banco vetorial (PostgreSQL com pgvector)
5. **Chat Inteligente**: O RAG dá origem a um sistema de chat onde o usuário pode fazer perguntas sobre o conteúdo extraído e receber respostas precisas baseadas no contexto original

### Fluxo Completo

```
┌─────────────┐
│  Usuário    │
│  envia link │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Sistema acessa     │
│  a página web       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Extração de        │
│  informações        │
│  (texto, metadados) │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Geração de resumo  │
│  com IA (GPT-4o)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Processamento e    │
│  criação de chunks  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Geração de         │
│  embeddings e       │
│  armazenamento no   │
│  banco vetorial     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Chat RAG           │
│  Usuário faz        │
│  perguntas sobre    │
│  o conteúdo         │
└─────────────────────┘
```

---

## 📋 Índice

- [Funcionalidade Principal](#-funcionalidade-principal)
- [Visão Geral](#-visão-geral)
- [Arquitetura e Padrões de Projeto](#-arquitetura-e-padrões-de-projeto)
- [Stack Tecnológico](#-stack-tecnológico)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Funcionalidades Detalhadas](#-funcionalidades-detalhadas)
- [API Endpoints](#-api-endpoints)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Desenvolvimento](#-desenvolvimento)

---

## 📖 Visão Geral

Este projeto é uma API backend robusta e escalável desenvolvida em Python com FastAPI que implementa:

- **Extração Inteligente de Conteúdo Web**: Web scraping automatizado com Selenium para páginas dinâmicas
- **Processamento com IA**: Geração de resumos e análise de conteúdo usando GPT-4o-mini
- **RAG (Retrieval Augmented Generation)**: Sistema de busca semântica usando embeddings vetoriais (pgvector) e OpenAI
- **Chat Inteligente**: Interface de conversação que permite consultar o conteúdo extraído de forma natural
- **Processamento Assíncrono**: Tarefas em background com Celery e Redis
- **Arquitetura em Camadas**: Separação clara de responsabilidades para facilitar manutenção e testes

---

## Arquitetura e Padrões de Projeto

### Arquitetura em Camadas (Layered Architecture)

O projeto segue uma arquitetura em camadas bem definida, garantindo separação de responsabilidades e facilitando manutenção e testes:

```
┌─────────────────────────────────────┐
│     Controller (API Layer)          │  ← Recebe requisições HTTP
│     - Validação de entrada          │     Valida parâmetros
│     - Tratamento de erros HTTP      │     Retorna respostas JSON
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     UseCase (Business Logic)        │  ← Lógica de negócio
│     - Orquestração de operações     │     Regras de negócio
│     - Validações complexas          │     Coordenação entre serviços
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Service (Data Access)           │  ← Acesso a dados
│     - Operações CRUD genéricas      │     Queries otimizadas
│     - Filtros, ordenação, busca     │     Soft delete
└──────────────┬──────────────────────┘
               │
┌──────────────▼───────────────────────┐
│     Model (Database)                 │  ← Modelos SQLAlchemy
│     - Definição de entidades         │     Relacionamentos
│     - Migrations com Alembic         │
└──────────────────────────────────────┘
```

### Padrões de Projeto Implementados

#### 1. **Generic Base Classes (DRY Principle)**

- `BaseService`: Classe genérica que implementa todas as operações CRUD, eliminando duplicação de código
- `BaseUseCase`: Camada de orquestração genérica com tratamento de erros consistente
- `BaseMapper`: Sistema de mapeamento genérico entre modelos de banco e schemas Pydantic

**Benefícios:**

- Redução de ~70% de código duplicado
- Consistência em todas as operações CRUD
- Facilita manutenção e adição de novas entidades

#### 2. **Repository Pattern**

- Abstração da camada de acesso a dados através do `BaseService`
- Isolamento da lógica de negócio das operações de banco de dados

#### 3. **Dependency Injection**

- FastAPI nativo para injeção de dependências (sessões de banco, autenticação)
- Facilita testes unitários e mock de dependências

#### 4. **Strategy Pattern**

- Sistema de permissões baseado em estratégias (`PermissionChecker`)
- Templates de email configuráveis por tipo

#### 5. **Factory Pattern**

- Criação dinâmica de queries com filtros, ordenação e includes
- Sistema de templates de email

#### 6. **Soft Delete Pattern**

- Exclusão lógica de registros mantendo histórico
- Suporte a restore de entidades deletadas

---

## Stack Tecnológico

### Backend Framework

- **FastAPI 0.119.1**: Framework moderno, assíncrono e de alta performance
  - Documentação automática (Swagger/OpenAPI)
  - Validação de dados com Pydantic
  - Type hints nativos

### Banco de Dados

- **PostgreSQL 16**: Banco de dados relacional robusto
- **pgvector 0.4.1**: Extensão para busca vetorial semântica
  - Índices IVFFlat para busca por similaridade
  - Embeddings de 1536 dimensões (OpenAI)

### ORM e Migrations

- **SQLAlchemy 2.0.44**: ORM moderno com suporte a async
- **Alembic 1.17.0**: Sistema de migrations versionado

### Cache e Message Broker

- **Redis 7**: Cache e message broker para Celery
- **Celery 5.5.3**: Processamento assíncrono de tarefas

### Autenticação e Segurança

- **PyJWT 2.10.1**: Tokens JWT para autenticação
- **passlib 1.7.4**: Hash de senhas com bcrypt
- **python-jose 3.5.0**: Suporte adicional para JWT

### IA e Processamento de Texto

- **OpenAI 2.6.0**:
  - GPT-4o-mini para resumos e análise de conteúdo
  - Embeddings (text-embedding-ada-002) para busca semântica
  - Vision API para processamento de imagens
  - Whisper para transcrição de áudio

### Web Scraping

- **Selenium 4.27.1**: Automação de navegador para scraping dinâmico
- **BeautifulSoup4 4.14.2**: Parsing de HTML
- **lxml 6.0.2**: Parser XML/HTML rápido

### Email

- **SMTP**: Sistema de templates HTML reutilizáveis
- **Jinja2 3.1.6**: Engine de templates

### Monitoramento e Logging

- **Sentry SDK 2.42.1**: Monitoramento de erros em produção
- **Logging nativo Python**: Sistema de logs estruturado

### Outras Ferramentas

- **Pydantic 2.12.3**: Validação de dados e schemas
- **python-decouple 3.8**: Gerenciamento de variáveis de ambiente
- **Uvicorn 0.38.0**: ASGI server de alta performance

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.11+**
- **PostgreSQL 16+** com extensão `pgvector`
- **Redis 7+**
- **Docker e Docker Compose** (opcional, para ambiente containerizado)
- **Chrome/Chromium** (para web scraping com Selenium)

---

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone <repository-url>
cd gestao_conhecimento_back
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure as variáveis:

```bash
cp .env_example .env
```

Edite o arquivo `.env` com suas configurações (veja seção [Variáveis de Ambiente](#-variáveis-de-ambiente)).

### 5. Inicialize o usuário administrador (opcional)

```bash
python scripts/init_admin.py
```

### 6. Execute a aplicação

#### Desenvolvimento:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Com Docker Compose:

```bash
docker-compose up -d
```

### 7. Inicie o worker Celery (para tarefas assíncronas)

```bash
celery -A api.utils.celery_app worker --loglevel=info -Q scraping --concurrency=1
```

### 8. Acesse a documentação da API

Após iniciar a aplicação, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Funcionalidades Detalhadas

### 1. Sistema de Extração e Processamento de Links

#### Web Scraping Inteligente

- **Scraping Assíncrono**: Processamento em background com Celery para não bloquear a API
- **Selenium Headless**: Navegação automática de páginas dinâmicas (JavaScript)
- **Anti-detecção**: User agents rotativos para evitar bloqueios
- **Extração de Metadados**: Open Graph, títulos, descrições e outras informações estruturadas
- **Resumo com IA**: Geração automática de resumos inteligentes com GPT-4o-mini

#### Processo de Extração

1. O usuário envia um link através da API
2. O sistema valida o link e cria um registro no banco
3. Uma tarefa assíncrona é disparada para processar o link
4. O Selenium acessa a página e extrai o conteúdo
5. O texto é limpo e processado
6. Um resumo é gerado usando IA
7. O conteúdo é preparado para ingestão no RAG

### 2. Sistema RAG (Retrieval Augmented Generation)

#### Ingestão de Conteúdo

- **Chunking Inteligente**: Divisão do texto em pedaços otimizados para preservar contexto
- **Embeddings Vetoriais**: Geração de embeddings com OpenAI (text-embedding-ada-002)
- **Armazenamento Vetorial**: Armazenamento no PostgreSQL com extensão pgvector
- **Índices Otimizados**: Índices IVFFlat para busca por similaridade rápida

#### Consultas ao RAG

- **Busca Semântica**: Consultas por similaridade usando embeddings
- **Contexto Preservado**: Manutenção do contexto original nas respostas
- **Respostas Contextuais**: O chat utiliza o conteúdo extraído para responder perguntas
- **Precisão**: Respostas baseadas no conteúdo real da página, não em conhecimento genérico

### 3. Chat Inteligente

O sistema de chat permite que o usuário:

- Faça perguntas sobre o conteúdo extraído de qualquer link processado
- Receba respostas precisas baseadas no contexto original
- Consulte múltiplos links processados anteriormente
- Obtenha informações específicas sem precisar reler o conteúdo completo

**Exemplo de uso:**

```
Usuário: "Qual é o resumo deste artigo?"
Sistema: [Responde com o resumo gerado pela IA]

Usuário: "Quais são os principais pontos mencionados?"
Sistema: [Responde baseado no conteúdo extraído e indexado no RAG]
```

### 4. Sistema de Autenticação JWT

- **Login com OAuth2**: Autenticação padrão OAuth2 Password Flow
- **Access Tokens**: Tokens de curta duração (configurável)
- **Refresh Tokens**: Tokens de longa duração para renovação
- **Recuperação de Senha**: Sistema completo com tokens temporários e emails
- **Hash de Senhas**: Bcrypt para segurança

### 5. Sistema de Permissões

- **Permissões baseadas em roles**: `LINK`, `RAG`, `ADMIN`
- **Middleware de permissões**: Decorator `@require()` para proteção de endpoints
- **Validação automática**: Verificação de permissões em cada requisição

### 6. CRUD Genérico Avançado

- **Operações Padrão**: Create, Read, Update, Delete
- **Soft Delete**: Exclusão lógica com possibilidade de restore
- **Filtros Dinâmicos**: Sistema flexível de filtragem
- **Ordenação**: Ordenação por qualquer campo
- **Busca Textual**: Busca full-text em campos configuráveis
- **Paginação**: Sistema completo de paginação
- **Includes Relacionais**: Carregamento otimizado de relacionamentos
- **Select Fields**: Seleção de campos específicos na resposta

### 7. Sistema de Email

- **Templates HTML**: Sistema de templates reutilizáveis
- **Múltiplos Tipos**: Password reset, welcome, verification, notification, reminder
- **Variáveis Dinâmicas**: Sistema flexível de substituição
- **Envio Assíncrono**: Integração com Celery para envio em background

---

## API Endpoints

### Autenticação (`/api/v1/conta`)

- `POST /login/oauth` - Login com OAuth2
- `POST /refresh` - Renovar access token
- `POST /register` - Registrar novo usuário
- `POST /forgot-password` - Solicitar recuperação de senha
- `POST /reset-password` - Redefinir senha com token

### Usuários (`/api/v1/usuarios`)

- `GET /` - Listar usuários (com filtros, ordenação, paginação)
- `GET /{id}` - Obter usuário por ID
- `POST /` - Criar usuário
- `PUT /{id}` - Atualizar usuário
- `DELETE /{id}` - Soft delete de usuário
- `POST /{id}/restore` - Restaurar usuário deletado

### WebLinks (`/api/v1/web_links`)

- `GET /` - Listar WebLinks processados
- `GET /{id}` - Obter WebLink por ID (inclui resumo e conteúdo)
- `POST /` - Criar WebLink e iniciar processamento (envia link para scraping)
- `PUT /{id}` - Atualizar WebLink
- `DELETE /{id}` - Deletar WebLink
- `POST /{id}/ask` - **Fazer pergunta ao RAG sobre o conteúdo extraído** (Chat)

### Health Check

- `GET /health` - Verificar status da aplicação

**Documentação Completa**: Acesse `/docs` para ver todos os endpoints com exemplos interativos.

---

## Variáveis de Ambiente

Configure as seguintes variáveis no arquivo `.env`:

```env
# OpenAI (Obrigatório para IA e RAG)
OPENAI_API_KEY=sua_chave_openai
EMBED_MODEL=text-embedding-ada-002

# Database
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_banco

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_SECRET_KEY=sua_chave_secreta_jwt
JWT_ALGORITHM=HS256

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
SMTP_FRONTEND_URL=http://localhost:3000

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Migrações de Banco de Dados

### Criar uma nova migration:

```bash
alembic revision --autogenerate -m "descricao_da_mudanca"
```

### Aplicar migrations:

```bash
alembic upgrade head
```

### Reverter migration:

```bash
alembic downgrade -1
```

### Ver histórico de migrations:

```bash
alembic history
```

---

## Desenvolvimento

### Executar em modo desenvolvimento:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O `--reload` habilita auto-reload quando arquivos são modificados.

---

## Notas Adicionais

### Performance do RAG

- O sistema usa **chunking inteligente** para dividir textos longos preservando contexto
- **Batch processing** de embeddings para otimizar chamadas à API OpenAI
- **Índices IVFFlat** no PostgreSQL para busca vetorial rápida
- **Cache de embeddings** para evitar reprocessamento

### Web Scraping

- **Timeout configurável** para evitar travamentos
- **Limpeza automática** de processos Chrome órfãos
- **Retry logic** para lidar com falhas temporárias
- **Suporte a páginas dinâmicas** com JavaScript através do Selenium

### Segurança

- **Rate limiting** recomendado para produção (não implementado neste projeto base)
- **HTTPS obrigatório** em produção
- **Validação de tokens** em cada requisição autenticada
- **Validação de URLs** antes do scraping para evitar SSRF

### Fluxo Completo de Uso

1. **Autenticação**: Usuário faz login e obtém token JWT
2. **Envio de Link**: Usuário envia POST para `/api/v1/web_links` com a URL
3. **Processamento**: Sistema processa o link em background (scraping → resumo → RAG)
4. **Consulta**: Usuário pode consultar o status do processamento
5. **Chat**: Após processamento, usuário pode fazer perguntas via `POST /api/v1/web_links/{id}/ask`

---
