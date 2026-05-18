# Project Specification

<p align="center">
  <h3 align="center">LangChain Pix Environment</h3>
  <p align="center">
    Assistente conversacional inteligente para via integração bancária, utilizando LangGraph para orquestração de fluxos com LLM.
    <br />
  </p>
</p>

---

## Objetivo

Desenvolver um assistente conversacional baseado em LLM para operações Pix, integrando-se a APIs bancárias de forma segura e performática. O sistema interpreta intenções do usuário em linguagem natural, roteia para o nó adequado do grafo de processamento e retorna respostas contextualizadas — abstraindo a complexidade da API bancária para o usuário final.

## Technical Context

| Aspecto              | Valor                                                                |
| -------------------- | -------------------------------------------------------------------- |
| Language/Version     | Python 3.12+                                                         |
| Primary Dependencies | LangChain, LangGraph, FastAPI, Pydantic v2                           |
| LLM Providers        | OpenRouter (Gemini 2.5 Flash) / Ollama (local dev)                   |
| Storage              | PostgreSQL (LangGraph checkpointer persistence)                      |
| Cache                | Redis 5+ (redis-py async com hiredis)                                |
| Broker               | —                                                                    |
| Testing              | pytest + pytest-asyncio + pytest-cov                                 |
| Linting              | Ruff (lint + isort) + Black (formatting)                             |
| Target Platform      | LangGraph Cloud / Uvicorn standalone                                 |
| Project Type         | HTTP Service (conversational AI API)                                 |
| Performance Goals    | Async I/O, connection pooling via httpx, Redis caching de tokens JWT |

## Architecture

```
┌─────────────┐       ┌──────────────┐        ┌──────────────────────────┐
│   Client    │──────▶│  FastAPI     │───────▶│  LangGraph Agent         │
│ (POST /chat)│       │  (Uvicorn)   │        │                          │
└─────────────┘       └──────────────┘        │  ┌────────────────────┐  │
                                              │  │ Identify Intent    │  │
                                              │  └────────┬───────────┘  │
                                              │           │              │
                                              │  ┌────────▼───────────┐  │
                                              │  │ Route (conditional)│  │
                                              │  └──┬──────┬──────┬──┘   │
                                              │     │      │      │      │
                                              │  ┌──▼─┐ ┌──▼──┐ ┌▼──┐    │
                                              │  │List│ │Read │ │Fall│   │
                                              │  │Keys│ │Key  │ │back│   │
                                              │  └──┬─┘ └──┬──┘ └─┬─┘    │
                                              │     │      │      │      │
                                              │  ┌──▼──────▼──────▼──┐   │
                                              │  │  Chat Response    │   │
                                              │  └───────────────────┘   │
                                              └──────────────────────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  Banking API (Pix)  │
                                              └─────────────────────┘
```

### Graph Nodes

| Node             | Responsabilidade                                             |
| ---------------- | ------------------------------------------------------------ |
| `identifyIntent` | Classifica a intenção do usuário via LLM (structured output) | 
| `listKeys`       | Consulta chaves Pix ativas de uma conta financeira           |
| `readKey`        | Consulta detalhes de uma chave Pix específica                |
| `fallback`       | Trata comandos não reconhecidos                              |
| `chatResponse`   | Gera resposta humanizada com base nos dados coletados        |

## Built With

- [LangChain](https://www.langchain.com/) — Framework para aplicações LLM
- [LangGraph](https://langchain-ai.github.io/langgraph/) — Orquestração de agentes como grafos de estado
- [FastAPI](https://fastapi.tiangolo.com/) — Framework web async de alta performance
- [Redis](https://redis.io/) — Cache de tokens e dados intermediários
- [PostgreSQL](https://www.postgresql.org/) — Banco de dados para persistência do LangGraph (checkpointer)
- [Pydantic v2](https://docs.pydantic.dev/) — Validação e serialização de dados

## Getting Started

### Prerequisites

- Python 3.12+
- Redis server (local ou remoto)
- PostgreSQL server (local ou remoto)
- Ollama (para desenvolvimento local) ou API key OpenRouter

### Installation

1. Clone o repositório

   ```sh
   git clone <repo-url>
   cd lang
   ```

2. Crie e ative o virtualenv

   ```sh
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências

   ```sh
   make install-deps
   ```

4. Configure as variáveis de ambiente
   ```sh
   cp .env.example .env
   # Edite .env com suas credenciais
   ```

### Environment Variables

| Variável             | Descrição                         | Default                        |
| -------------------- | --------------------------------- | ------------------------------ |
| `OPENROUTER_API_KEY` | API key do OpenRouter             | —                              |
| `OPENROUTER_MODEL`   | Modelo LLM (produção)             | `google/gemini-2.5-flash`      |
| `OLLAMA_BASE_URL`    | URL do Ollama (dev local)         | `http://localhost:11434`       |
| `OLLAMA_MODEL`       | Modelo Ollama                     | `qwen3.5:latest`               |
| `REDIS_HOST`         | Host do Redis                     | `localhost`                    |
| `REDIS_PORT`         | Porta do Redis                    | `6379`                         |
| `POSTGRES_DB`        | Nome do banco de dados PostgreSQL | `banking-llm`                  |
| `POSTGRES_USER`      | Usuário do banco PostgreSQL       | `postgres`                     |
| `POSTGRES_PASSWORD`  | Senha do banco PostgreSQL         | `postgres`                     |
| `POSTGRES_HOST`      | Host do banco PostgreSQL          | `localhost`                    |
| `POSTGRES_PORT`      | Porta do banco PostgreSQL         | `5432`                         |
| `CLIENT_ID`          | Client ID para API bancária       | —                              |
| `JWT_SECRET`         | Secret para autenticação bancária | —                              |
| `BANKING_BASE_URL`   | URL base da API bancária          | `https://banking.kanastra.dev` |

## Usage

### Iniciar o servidor de desenvolvimento

```sh
make server
```

### Executar via LangGraph Studio (debug/monitoring)

```sh
make langgraph
```

### Exemplo de request

```sh
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Quais são as chaves pix ativas da conta 550e8400?"}'
```

### Executar testes

```sh
make tests
```

### Lint

```sh
make lint
```

## Project Structure

```
src/
├── main.py                    # Application entrypoint (FastAPI)
├── chat/
│   └── router.py              # HTTP routes (/chat)
├── core/
│   ├── cache.py               # Cache protocol (interface)
│   ├── config.py              # Settings (pydantic-settings)
│   ├── health_check.py        # Health endpoint
│   ├── logger.py              # Structured logging
│   └── middleware.py          # Request logging middleware
├── graph/
│   ├── factory.py             # Graph builder/processor
│   ├── graph.py               # LangGraph workflow definition
│   ├── state.py               # Graph state (TypedDict)
│   ├── nodes/                 # Processing nodes
│   └── prompts/               # System/user prompts
└── infrastructure/
    ├── llm_service.py         # LLM abstraction (Ollama/OpenRouter)
    ├── banking/               # Banking API integration
    ├── cache/                 # Redis cache implementation
    └── dto/                   # Data transfer objects
```

## Roadmap

- [ ] Adicionar mais operações Pix (criação, exclusão de chaves)
- [ ] Implementar histórico de conversas persistente
- [ ] Adicionar autenticação no endpoint /chat
- [ ] Dockerfile para deploy containerizado
- [ ] CI/CD pipeline com GitHub Actions
- [ ] Observabilidade (OpenTelemetry / LangSmith)

## Contact

Marcel Bittar — marcel.bittar@gmail.com
