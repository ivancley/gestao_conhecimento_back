# Gestão de Conhecimento Backend API

API RESTful moderna desenvolvida em Python com FastAPI, implementando arquitetura em camadas, RAG (Retrieval Augmented Generation), processamento assíncrono com Celery e integração com IA para análise e resumo de conteúdo web.

---

##  Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura e Padrões de Projeto](#-arquitetura-e-padrões-de-projeto)
- [Stack Tecnológico](#-stack-tecnológico)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Destaques Técnicos](#-destaques-técnicos)
- [API Endpoints](#-api-endpoints)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Desenvolvimento](#-desenvolvimento)

---

#  Visão Geral

Este projeto é uma API backend robusta e escalável que oferece:

- **Gerenciamento de Usuários**: Sistema completo de autenticação JWT com refresh tokens, recuperação de senha e controle de permissões baseado em roles
- **Web Scraping Inteligente**: Extração automatizada de conteúdo web com Selenium, processamento assíncrono e geração de resumos com IA
- **RAG (Retrieval Augmented Generation)**: Sistema de busca semântica usando embeddings vetoriais (pgvector) e OpenAI para consultas inteligentes sobre conteúdo indexado
- **Processamento Assíncrono**: Tarefas em background com Celery e Redis para scraping e processamento de dados

---

##  Arquitetura e Padrões de Projeto

### Arquitetura em Camadas (Layered Architecture)

O projeto segue uma arquitetura em camadas bem definida, garantindo separação de responsabilidades e facilitando manutenção e testes:

```
┌─────────────────────────────────────┐
│     Controller (API Layer) n        │  ← Recebe requisições HTTP
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

##  Stack Tecnológico

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

##  Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.11+**
- **PostgreSQL 16+** com extensão `pgvector`
- **Redis 7+**
- **Docker e Docker Compose** (opcional, para ambiente containerizado)
- **Chrome/Chromium** (para web scraping com Selenium)

---

##  Instalação e Configuração

### 1. Clone o repositório

```bash
git clone <repository-url>
cd back
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

### 8. Inicie o worker Celery (para tarefas assíncronas)

```bash
celery -A api.utils.celery_app worker --loglevel=info -Q scraping --concurrency=1
```

### 9. Acesse a documentação da API

Após iniciar a aplicação, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

##  Funcionalidades Principais

### 1. Sistema de Autenticação JWT

- **Login com OAuth2**: Autenticação padrão OAuth2 Password Flow
- **Access Tokens**: Tokens de curta duração (configurável)
- **Refresh Tokens**: Tokens de longa duração para renovação
- **Recuperação de Senha**: Sistema completo com tokens temporários e emails
- **Hash de Senhas**: Bcrypt para segurança

### 2. Sistema de Permissões

- **Permissões baseadas em roles**: `LINK`, `RAG`, `ADMIN`
- **Middleware de permissões**: Decorator `@require()` para proteção de endpoints
- **Validação automática**: Verificação de permissões em cada requisição

### 3. Web Scraping Inteligente

- **Scraping Assíncrono**: Processamento em background com Celery
- **Selenium Headless**: Navegação automática de páginas dinâmicas
- **Anti-detecção**: User agents rotativos
- **Extração de Metadados**: Open Graph, títulos, descrições
- **Resumo com IA**: Geração automática de resumos com GPT-4o-mini

### 4. RAG (Retrieval Augmented Generation)

- **Ingestão de Conteúdo**: Chunking inteligente de textos
- **Embeddings Vetoriais**: Geração de embeddings com OpenAI
- **Busca Semântica**: Consultas por similaridade usando pgvector
- **Índices Otimizados**: IVFFlat para performance
- **Contexto Preservado**: Manutenção de contexto original nas respostas

### 5. CRUD Genérico Avançado

- **Operações Padrão**: Create, Read, Update, Delete
- **Soft Delete**: Exclusão lógica com possibilidade de restore
- **Filtros Dinâmicos**: Sistema flexível de filtragem
- **Ordenação**: Ordenação por qualquer campo
- **Busca Textual**: Busca full-text em campos configuráveis
- **Paginação**: Sistema completo de paginação
- **Includes Relacionais**: Carregamento otimizado de relacionamentos
- **Select Fields**: Seleção de campos específicos na resposta

### 6. Sistema de Email

- **Templates HTML**: Sistema de templates reutilizáveis
- **Múltiplos Tipos**: Password reset, welcome, verification, notification, reminder
- **Variáveis Dinâmicas**: Sistema flexível de substituição
- **Envio Assíncrono**: Integração com Celery para envio em background

---

##  Destaques Técnicos

### 1. Arquitetura Escalável

- **Separação de Responsabilidades**: Cada camada tem uma responsabilidade única
- **Baixo Acoplamento**: Módulos independentes e testáveis
- **Alta Coesão**: Funcionalidades relacionadas agrupadas

### 2. Performance

- **Queries Otimizadas**: Uso de índices, eager loading seletivo
- **Processamento Assíncrono**: Celery para tarefas pesadas
- **Cache com Redis**: Redução de carga no banco de dados
- **Busca Vetorial Otimizada**: Índices IVFFlat para RAG

### 3. Segurança

- **JWT com Refresh Tokens**: Autenticação segura e renovável
- **Hash de Senhas**: Bcrypt com salt automático
- **Validação de Entrada**: Pydantic para validação de dados
- **SQL Injection Prevention**: SQLAlchemy ORM previne injeções
- **CORS Configurado**: Controle de origens permitidas

### 4. Manutenibilidade

- **Código DRY**: Base classes genéricas eliminam duplicação
- **Type Hints**: Tipagem completa para melhor IDE support
- **Documentação Automática**: Swagger/OpenAPI gerado automaticamente
- **Migrations Versionadas**: Controle de versão do schema do banco

### 5. Testabilidade

- **Dependency Injection**: Facilita criação de mocks
- **Separação de Camadas**: Cada camada pode ser testada isoladamente
- **Base Classes**: Testes genéricos para operações CRUD

### 6. Extensibilidade

- **Fácil Adição de Entidades**: Herdar de base classes é suficiente
- **Sistema de Permissões Extensível**: Fácil adicionar novas permissões
- **Templates de Email Extensíveis**: Adicionar novos templates é simples

---

## 🔌API Endpoints

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

- `GET /` - Listar WebLinks
- `GET /{id}` - Obter WebLink por ID
- `POST /` - Criar WebLink (dispara scraping assíncrono)
- `PUT /{id}` - Atualizar WebLink
- `DELETE /{id}` - Deletar WebLink
- `POST /{id}/ask` - Fazer pergunta ao RAG sobre o conteúdo

### Health Check

- `GET /health` - Verificar status da aplicação

**Documentação Completa**: Acesse `/docs` para ver todos os endpoints com exemplos interativos.

---

##  Variáveis de Ambiente

Configure as seguintes variáveis no arquivo `.env`:

```env
# OpenAI
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

##  Migrações de Banco de Dados

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

- O sistema usa **chunking inteligente** para dividir textos longos
- **Batch processing** de embeddings para otimizar chamadas à API OpenAI
- **Índices IVFFlat** no PostgreSQL para busca vetorial rápida

### Web Scraping

- **Timeout configurável** para evitar travamentos
- **Limpeza automática** de processos Chrome órfãos
- **Retry logic** para lidar com falhas temporárias

### Segurança

- **Rate limiting** recomendado para produção (não implementado neste projeto base)
- **HTTPS obrigatório** em produção
- **Validação de tokens** em cada requisição autenticada

---

