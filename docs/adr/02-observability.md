# ADR 02 — Observabilidade (OpenTelemetry)

**Data**: 25/06/2026
**Status**: Aceita
**Prioridade**: ALTA
**Contexto macro**: [01-langchain-pix-environment_macro.md](01-langchain-pix-environment_macro.md)
**Spec**: `tasks/specs/20260625-observability_spec.md`
**Plano**: `tasks/plans/20260625-observability_plan.md`

---

## Contexto

O serviço executa operações PIX reais orquestradas por um grafo LangGraph com múltiplas
chamadas a LLM e à API bancária. Sem observabilidade, diagnosticar incidentes
(latência, falhas de dependência, bloqueios de guardrail, comportamento do LLM) exige
inferência a partir de logs não correlacionados. O roadmap previa uma camada de
observabilidade; esta ADR registra a decisão de implementá-la com OpenTelemetry.

## Decisão

Adotar **OpenTelemetry (OTel) nativo** para os três sinais — traces, métricas e logs —
exportados via **OTLP** para um **OpenTelemetry Collector**, que distribui para backends
open-source (Tempo, Jaeger, Prometheus, Loki) visualizados no **Grafana**. O acesso de
agentes às telemetrias é feito por um **Grafana MCP read-only** (opt-in).

A instrumentação é **desligada por padrão** (`OTEL_ENABLED=false`): sem o flag, nenhum
provider/exporter é criado e o código de telemetria opera em modo no-op, com overhead
zero e sem dependência de rede.

### Componentes

- **Bootstrap** (`src/core/observability/telemetry.py`): `setup()` idempotente que constrói
  `TracerProvider`/`MeterProvider`/`LoggerProvider` e registra instrumentations apenas
  quando habilitado. Chamado como primeira instrução em `src/main.py`.
- **Traces**: span raiz HTTP enriquecido (rota legível, `http.route`, `app.handler`),
  spans de domínio por nó do grafo via utilitário `domain_span` (`graph.*`, `pix.*`,
  `llm.*`), spans de IO automáticos (requests/Redis/psycopg) e spans de LLM com tokens
  (OpenInference para LangChain).
- **Métricas**: RED de HTTP via instrumentação FastAPI, métricas de domínio
  (`pix_operations_total`, `graph_node_duration_seconds`, `guardrail_block_total`) e de
  LLM, exportadas via push OTLP (sem endpoint `/metrics` na app).
- **Logs**: `structlog` com `JSONRenderer` fora de dev e processor de correlação que
  injeta `trace_id`/`span_id` quando há span ativo.
- **Privacidade**: mascaramento compartilhado (`masking.py`) aplicado a atributos de span,
  labels de métrica e logs — chaves PIX, `government_id`, tokens e secrets nunca aparecem
  em texto claro.

## Alternativas consideradas

| Abordagem | Por que foi preterida |
| --- | --- |
| **OTel zero-code** (`opentelemetry-instrument` CLI) | Não produz spans/métricas de domínio (nó do grafo, tokens PIX); toggle e testes mais difíceis. |
| **LangSmith / vendor proprietário** | Vendor lock-in; cobre apenas o sinal de LLM, não IO/HTTP/métricas/logs; contraria a decisão de ser OTel-nativo. |
| **Pull `/metrics` na app** | Adiciona endpoint extra e acopla o formato Prometheus; o padrão OTel é push OTLP para o Collector. |
| **MCP por backend** (um por Tempo/Loki/Prometheus) | Multiplica servidores e permissões; o Grafana MCP centraliza com menor superfície. |
| **Não fazer nada** | Diagnóstico de incidentes inviável; viola o roadmap. |

## Consequências

### Positivas

- Correlação trace ↔ log ↔ métrica ponta a ponta no Grafana.
- Kill-switch de runtime (`OTEL_ENABLED=false`) sem deploy de código.
- Aditividade: nenhuma mudança de schema de banco ou de contratos públicos (apenas o
  header `traceparent`, aditivo).
- Backends open-source, sem lock-in; o app só conhece o endpoint do Collector.

### Negativas / Trade-offs

- Mais código de bootstrap e ordem de inicialização sensível (telemetria antes dos
  módulos instrumentados).
- A stack local adiciona seis serviços ao docker-compose (somente quando iniciada).
- Exporters em modo best-effort: falha de conexão é logada como warning e não propaga.

## Segurança (OWASP)

- **A01 Broken Access Control**: Grafana MCP com service account **Viewer** (read-only),
  em profile opcional que não sobe por padrão.
- **A02 Cryptographic Failures**: `GRAFANA_SERVICE_ACCOUNT_TOKEN` via env (secret), nunca
  commitado.
- **A05 Security Misconfiguration**: backends não expostos em produção (out-of-scope);
  flags desligados por padrão.
- **Privacidade de dados**: invariante de mascaramento testado em spans, métricas e logs.

## Como operar

```sh
make install-observability   # instala o extra [observability]
make observability-up        # sobe Collector + Tempo + Jaeger + Prometheus + Loki + Grafana
make server-otel             # sobe a app com OTEL_ENABLED=true
make observability-mcp-up    # (opcional) sobe o grafana-mcp read-only
```

| UI         | URL                    |
| ---------- | ---------------------- |
| Grafana    | http://localhost:3000  |
| Jaeger     | http://localhost:16686 |
| Prometheus | http://localhost:9090  |
