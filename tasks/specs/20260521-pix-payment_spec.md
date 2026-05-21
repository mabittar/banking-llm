# Pix Payment — Pagamento de QR Code via Assistente Conversacional

**Data**: 21/05/2026  
**Última Revisão**: 21/05/2026  
**Versão**: 1.1  
**Solicitante**: feature/pix-payment  
**Prioridade**: 🔴 ALTA

**Changelog v1.1**:

- Validado: campo `status` retorna `ACTIVE`/`PAID`/`EXPIRED` na response do preview.
- Adicionado: fallback de intent — se intenção ambígua, perguntar ao usuário se quer consultar ou pagar.
- Adicionado: resposta de bloqueio informa status atual do QR Code.
- Adicionado: requisito de documentação do checkpointer no README (local + produção).

**Changelog v1.0**:

- Versão inicial — especificação do fluxo de pagamento de QR Code com validação de status e controle de valor (FIXED/CUSTOM).

---

## Technical Context

| Aspecto              | Valor                                                        |
| -------------------- | ------------------------------------------------------------ |
| Language/Version     | Python >= 3.12                                               |
| Primary Dependencies | LangGraph >= 1.1.1, LangChain >= 0.3.0, FastAPI >= 0.115.0  |
| Storage              | PostgreSQL (psycopg >= 3.3.4) — LangGraph checkpointer      |
| Cache                | Redis (redis-py + hiredis >= 5.0.0) — JWT token cache        |
| Testing              | pytest >= 9.0.3, pytest-asyncio, pytest-cov                  |
| Linting              | ruff >= 0.11.0, black >= 26.3.1                              |
| Target Platform      | LangGraph Cloud / Standalone Uvicorn                         |
| Project Type         | HTTP Service (Conversational AI API)                         |
| Performance Goals    | < 3s end-to-end (LLM + banking API call)                     |

---

## 1. Objetivo (Why)

O fluxo atual de QR Code está fragmentado em dois intents separados: `brcode_preview` (consulta) e `pix_withdraw` (pagamento). Quando o usuário solicita "pague o pix copia & cola `000201...6304EEC0`", o comportamento esperado é um **fluxo unificado** que consulta o QR Code, valida se é pagável, e executa o pagamento — sem exigir que o usuário invoque manualmente duas operações distintas.

Além disso, é necessário adicionar **validação de status do QR Code** (`ACTIVE`, `PAID`, `EXPIRED`) antes de permitir o pagamento, e tratar corretamente o **tipo de valor** (`FIXED` vs `CUSTOM`) para decidir se é necessário interagir novamente com o usuário para obter o montante.

---

## 2. Descrição Funcional (What)

### Objetivo

O usuário, através do chat conversacional, pode:
- **Solicitar o pagamento de um QR Code** — informando o payload EMV (copia & cola) diretamente na mensagem.
- O sistema consulta a Banking API (preview), valida o status, apresenta dados do beneficiário, e executa o pagamento automaticamente (se valor fixo) ou pergunta o valor (se customizável).

### Comportamento esperado:

1. **Usuário fornece BRCode com intenção de pagamento**: "Pague o pix copia & cola `000201...6304EEC0`".
2. **Classificação de intent**: O LLM classifica como `pix_payment`.
3. **Extração de entidades**: O LLM extrai `brcode` (payload EMV completo) e opcionalmente `amount` (se informado pelo usuário).
4. **Consulta à Banking API (Preview)**: O nó `pixPayment` chama `GET /brcode/preview` com o payload.
5. **Validação de Status**:
   - `ACTIVE` → prossegue com pagamento.
   - `PAID` → informa ao usuário: _"O QR Code informado possui status **PAGO**. Não é possível realizar o pagamento."_ Exibe dados apenas para consulta.
   - `EXPIRED` → informa ao usuário: _"O QR Code informado possui status **EXPIRADO**. Não é possível realizar o pagamento."_ Exibe dados apenas para consulta.
6. **Controle de Valor (amount_type)**:
   - `FIXED` → o valor não é editável. Prossegue automaticamente com o valor retornado pela API.
   - `CUSTOM` → o valor é editável. Pergunta ao usuário quanto deseja pagar (a menos que o usuário já tenha informado o valor na mensagem original).
7. **Execução do pagamento**: Após ter todos os dados validados, chama `POST /transfer` via `PixWithdrawService`.
8. **Apresentação de resultado**: O nó `chatResponse` formata a resposta com sucesso ou erro.

### Regras de negócio:

| Regra | Descrição |
|-------|-----------|
| Status ACTIVE obrigatório | Somente QR Codes com `status == "ACTIVE"` podem ser pagos. |
| PAID/EXPIRED = apenas consulta | QR Codes com status `PAID` ou `EXPIRED` retornam dados ao usuário, **informam o status atual**, e **não** permitem pagamento. |
| FIXED = sem interação extra | Se `amount_type == "FIXED"`, o valor vem da API e não pode ser alterado. Pagamento prossegue automaticamente. |
| CUSTOM = interação necessária | Se `amount_type == "CUSTOM"`, o sistema deve perguntar o valor ao usuário (exceto se já informado na mensagem). |
| Valor > 0 | O valor de pagamento deve ser maior que zero e ter no máximo 2 casas decimais. |
| BRCode obrigatório | Sem o payload EMV, o fluxo não pode iniciar. |
| Dados de preview populam state | Os dados retornados pelo preview (beneficiário, e2e, qr_code, reconciliation_id) devem ser armazenados no `GraphState` para uso no `pix_transfer`. |

### Diferença entre `brcode_preview` e `pix_payment`:

| Aspecto | `brcode_preview` | `pix_payment` |
|---------|-------------------|---------------|
| Intent | Consultar dados do QR Code | Pagar um QR Code |
| Resultado | Exibe dados, não executa pagamento | Exibe dados E executa pagamento |
| Status validation | Não bloqueia | Bloqueia se não ACTIVE (informa status atual) |
| Interação amount | Não pergunta valor | Pergunta se CUSTOM |

### Desambiguação de intent (fallback conversacional):

Quando o usuário fornece um BRCode mas **não deixa claro** se quer apenas consultar ou pagar, o sistema deve:
1. Classificar como `brcode_ambiguous` (ou fallback interno).
2. Perguntar ao usuário: _"Você gostaria de consultar os dados deste QR Code ou realizar o pagamento diretamente?"_
3. Com base na resposta, rotear para `brcode_preview` ou `pix_payment`.

Exemplos de ambiguidade:
- "QR Code: 000201...6304EEC0" (sem verbo de ação)
- "Olha esse pix copia e cola 000201...6304EEC0" (intenção não clara)

Exemplos **não** ambíguos:
- "Pague o pix 000201..." → `pix_payment`
- "Consulte o qr code 000201..." → `brcode_preview`

---

## 3. Fluxo Técnico

### 3.1 Novo Intent: `pix_payment`

```
Gatilho: Usuário solicita PAGAMENTO de QR Code (explicitamente "pague", "pagar")
→ Classificação de intent: "pix_payment"
→ Extração de entidades: brcode, amount (opcional)
→ Chamada ao endpoint de preview (GET /brcode/preview)
→ Validação de status (ACTIVE/PAID/EXPIRED)
→ Verificação de amount_type (FIXED/CUSTOM)
  → FIXED: prossegue direto
  → CUSTOM sem amount: retorna pedindo valor ao usuário (awaiting_amount)
  → CUSTOM com amount: prossegue com valor informado
→ Execução do pagamento (POST /transfer)
→ Resposta contextualizada ao usuário
```

### 3.2 Fluxo no StateGraph (atualizado)

```
START → identifyIntent ─(conditional)─→ listKeys ─────────→ chatResponse → END
                              │
                              ├──→ readKey ──────────→ chatResponse → END
                              │
                              ├──→ brcodePreview ────→ chatResponse → END
                              │
                              ├──→ pixPayment ───────→ chatResponse → END
                              │
                              ├──→ pixWithdraw ──────→ chatResponse → END
                              │
                              └──→ fallback ─────────→ chatResponse → END
```

### 3.3 Sub-fluxo do nó `pixPayment`

```
pixPayment:
  1. Validar brcode (format check)
  2. Chamar BRCodePreviewService.execute() → obter dados do QR Code
  3. Validar status:
     - PAID → retornar dados + mensagem "QR Code já pago"
     - EXPIRED → retornar dados + mensagem "QR Code expirado"
     - ACTIVE → prosseguir
  4. Determinar valor:
     - FIXED → usar amount da response
     - CUSTOM + amount no state → usar amount do state
     - CUSTOM + sem amount → retornar dados + pedir valor (action_success=True, awaiting_amount=True)
  5. Chamar PixWithdrawService.execute() com state enriquecido
  6. Retornar resultado
```

### 3.4 Fluxo de Continuação (CUSTOM amount)

Quando o QR Code é CUSTOM e o usuário não informou o valor:
1. O nó `pixPayment` retorna com `awaiting_amount: True` e `action_data` contendo dados do beneficiário.
2. O `chatResponse` formata uma mensagem perguntando o valor ao usuário.
3. Na próxima mensagem do usuário (com o valor), o intent classifier detecta `pix_payment` novamente.
4. Desta vez, o state já possui os dados do preview (via checkpointer/memory), e o `amount` é extraído.
5. O nó `pixPayment` identifica que já possui preview data e amount, e executa diretamente o pagamento.

### 3.5 Endpoints Banking API

**Preview (leitura):**
```
GET /api/v1/pix/{fin_account_id}/brcode/preview

Body: { "brcode": "<payload EMV>" }

Response: BRCodePreviewResponseDTO (inclui status, amount, amount_type, beneficiary, etc.)
```

**Transfer (pagamento):**
```
POST /api/v1/pix/{fin_account_id}/transfer

Headers:
  - Transaction-Hash-Key: HMAC-SHA256(payload, secret)

Body: {
  "beneficiary": { ... },
  "amount": float,
  "initType": "STATIC_QR_CODE" | "DYNAMIC_QR_CODE",
  "endToEndId": "string",
  "qrCode": "string",
  "reconciliationId": "string",
  "keyId": "string",
  "amountType": "FIXED" | "CUSTOM",
  "nominalAmount": float | null
}
```

---

## 4. Critérios de Aceitação (Gherkin)

```
Feature: Pix Payment (QR Code) | Esforço: Alto | Risco: Médio

Scenario: Sucesso - QR Code ACTIVE com valor FIXED
  Given um usuário autenticado com financial account válido
  And o usuário envia "Pague o pix copia & cola 000201...6304EEC0"
  When o intent é classificado como "pix_payment"
  And o brcode é extraído da mensagem
  Then o sistema consulta GET /brcode/preview
  And o status retornado é "ACTIVE"
  And o amount_type é "FIXED" com amount = 150.00
  Then o sistema executa POST /transfer com amount = 150.00
  And retorna mensagem de sucesso com dados da transação

Scenario: Sucesso - QR Code ACTIVE com valor CUSTOM e amount informado
  Given um usuário autenticado com financial account válido
  And o usuário envia "Pague R$50 no qr code 000201...6304EEC0"
  When o intent é classificado como "pix_payment"
  And brcode e amount (50.00) são extraídos
  Then o sistema consulta GET /brcode/preview
  And o status retornado é "ACTIVE"
  And o amount_type é "CUSTOM"
  Then o sistema executa POST /transfer com amount = 50.00
  And retorna mensagem de sucesso

Scenario: Interação - QR Code ACTIVE com valor CUSTOM sem amount
  Given um usuário autenticado com financial account válido
  And o usuário envia "Pague o qr code 000201...6304EEC0"
  When o intent é classificado como "pix_payment"
  And brcode é extraído mas amount está ausente
  Then o sistema consulta GET /brcode/preview
  And o status retornado é "ACTIVE"
  And o amount_type é "CUSTOM"
  Then o sistema retorna dados do beneficiário
  And pergunta "Qual valor deseja pagar?"
  And o estado fica com awaiting_amount = True

Scenario: Continuação - Usuário informa valor após pergunta
  Given o estado anterior tem awaiting_amount = True e dados do preview
  And o usuário envia "R$75,00"
  When o intent é classificado como "pix_payment"
  And amount (75.00) é extraído
  Then o sistema detecta que já possui dados de preview no state
  And executa POST /transfer com amount = 75.00
  And retorna mensagem de sucesso

Scenario: Bloqueio - QR Code com status PAID
  Given um usuário autenticado com financial account válido
  And o usuário envia "Pague o qr code 000201...6304EEC0"
  When o intent é classificado como "pix_payment"
  Then o sistema consulta GET /brcode/preview
  And o status retornado é "PAID"
  Then o sistema NÃO executa o pagamento
  And retorna mensagem: "O QR Code informado possui status PAGO. Não é possível realizar o pagamento."
  And exibe dados do beneficiário apenas para consulta

Scenario: Bloqueio - QR Code com status EXPIRED
  Given um usuário autenticado com financial account válido
  And o usuário envia "Pague o qr code 000201...6304EEC0"
  When o intent é classificado como "pix_payment"
  Then o sistema consulta GET /brcode/preview
  And o status retornado é "EXPIRED"
  Then o sistema NÃO executa o pagamento
  And retorna mensagem: "O QR Code informado possui status EXPIRADO. Não é possível realizar o pagamento."

Scenario: Desambiguação - Intent não claro
  Given um usuário envia "Segue o qr code 000201...6304EEC0" sem verbo claro de ação
  When o intent classifier não consegue distinguir entre preview e payment
  Then o sistema pergunta: "Você gostaria de consultar os dados deste QR Code ou realizar o pagamento diretamente?"
  And aguarda resposta do usuário para rotear

Scenario: Erro - BRCode não fornecido
  Given um usuário envia "Pague o qr code" sem payload EMV
  When o intent é classificado como "pix_payment"
  And brcode está ausente no state
  Then o sistema solicita ao usuário que forneça o código copia & cola

Scenario: Erro - BRCode inválido (formato)
  Given um usuário fornece um payload que não inicia com "000201"
  When o nó pixPayment valida o formato
  Then o sistema retorna erro de formato inválido

Scenario: Erro - Valor inválido (zero ou negativo)
  Given QR Code CUSTOM e usuário informa valor "0" ou "-10"
  When o nó tenta executar o pagamento
  Then retorna erro "Invalid amount: must be greater than zero"

Scenario: Erro - Banking API indisponível
  Given a Banking API retorna 5xx no preview ou no transfer
  When o nó tenta consultar/executar
  Then retorna mensagem de erro amigável ao usuário
```

---

## 5. Considerações Técnicas

### 5.1 Novos Artefatos

| Artefato | Caminho | Propósito |
|----------|---------|-----------|
| Service | `src/services/pix_payment_service.py` | Orquestra preview → validação → pagamento |
| Graph Node | `src/graph/nodes/pix_payment_node.py` | Nó do StateGraph |
| Intent prompt update | `src/graph/prompts/identify_intent.py` | Novo intent `pix_payment` |
| GraphState update | `src/graph/state.py` | Novo campo `awaiting_amount` |
| Graph routing | `src/graph/graph.py` | Novo nó + conditional edge |
| Tests | `tests/test_pix_payment_service.py` | Unit tests do service |
| README | `readme.md` | Documentação do checkpointer (local/produção) |

### 5.2 GraphState — Novos/Atualizados Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `command` | `Literal[...]` | Adicionar `"pix_payment"` e `"brcode_ambiguous"` ao union type |
| `awaiting_amount` | `bool \| None` | Indica que o fluxo está aguardando valor do usuário |
| `brcode_status` | `str \| None` | Status do QR Code retornado pela API (`ACTIVE`, `PAID`, `EXPIRED`) |

> Os campos `withdraw_*` existentes continuam sendo reutilizados para dados do beneficiário e transação.

### 5.3 PixPaymentService — Lógica Central

```python
class PixPaymentService:
    def __init__(self, brcode_preview_service: BRCodePreviewService, pix_withdraw_service: PixWithdrawService):
        self._preview_service = brcode_preview_service
        self._withdraw_service = pix_withdraw_service

    async def execute(self, state: dict) -> dict:
        # Se já tem dados de preview no state (continuação), pular preview
        if state.get("withdraw_end_to_end_id") and state.get("withdraw_amount"):
            return await self._withdraw_service.execute(state)

        # 1. Executar preview
        preview_result = await self._preview_service.execute(state)
        if not preview_result.get("action_success"):
            return preview_result

        # 2. Validar status
        status = preview_result["action_data"].get("status", "UNKNOWN")
        if status == "PAID":
            return {**preview_result, "action_error": "O QR Code informado possui status PAGO. Não é possível realizar o pagamento.", "brcode_status": "PAID"}
        if status == "EXPIRED":
            return {**preview_result, "action_error": "O QR Code informado possui status EXPIRADO. Não é possível realizar o pagamento.", "brcode_status": "EXPIRED"}

        # 3. Controle de valor
        amount_type = preview_result.get("withdraw_amount_type")
        amount = preview_result.get("withdraw_amount") or state.get("withdraw_amount")

        if amount_type == "FIXED":
            # Valor fixo, prosseguir direto
            return await self._withdraw_service.execute({**state, **preview_result})

        if amount_type == "CUSTOM":
            if amount and amount > 0:
                # Usuário informou valor, prosseguir
                enriched = {**state, **preview_result, "withdraw_amount": amount}
                return await self._withdraw_service.execute(enriched)
            else:
                # Precisa perguntar valor ao usuário
                return {**preview_result, "awaiting_amount": True}

        return {**preview_result, "action_error": f"Tipo de valor desconhecido: {amount_type}"}
```

### 5.4 Intent Classifier — Atualização

Adicionar ao prompt de classificação:

```python
"pix_payment": {
    "description": "User explicitly wants to PAY/execute a QR Code (not just preview/consult)",
    "keywords": [
        "pague o pix",
        "pagar qr code",
        "pagar copia e cola",
        "pagar pix copia e cola",
        "pague o qr code",
        "efetuar pagamento qr",
        "pagar o brcode",
        "pay qr code",
        "pay pix",
    ],
    "required_fields": ["brcode"],
    "optional_fields": ["amount"],
},
```

**Distinção de intent:**
- Usuário diz "consultar qr code" / "ver dados do qr code" → `brcode_preview`
- Usuário diz "pagar qr code" / "pague o pix copia e cola" → `pix_payment`
- Usuário fornece BRCode **sem verbo claro** de ação → `brcode_ambiguous`

**Regra de desambiguação:**
Quando o classifier identifica `brcode_ambiguous`, o nó deve retornar uma pergunta ao usuário:
> "Você gostaria de consultar os dados deste QR Code ou realizar o pagamento diretamente?"

Após a resposta do usuário, o classifier reclassifica como `brcode_preview` ou `pix_payment`.

### 5.5 Segurança

- **Transaction-Hash-Key**: HMAC-SHA256 gerado a partir do payload + `TRANSACTION_HASH_SECRET` (já implementado no `BankingClient`).
- **Validação de amount**: Max 2 casas decimais, > 0, tipo Decimal (já implementado no `PixWithdrawService`).
- **Mascaramento de CPF/CNPJ**: Dados do beneficiário mascarados antes de exibir ao usuário (já implementado no `BRCodePreviewService`).
- **Não permitir pagamento duplicado**: Status `PAID` bloqueia re-execução.

### 5.7 Checkpointer — Configuração (documentar no README)

O checkpointer utiliza o **mesmo banco PostgreSQL** já existente na aplicação (`AsyncPostgresSaver` do `langgraph.checkpoint.postgres.aio`). A conexão é derivada da `DATABASE_URL` configurada em `src/core/config.py`.

**Variáveis de ambiente necessárias:**
```bash
DBNAME=banking-llm          # Nome do banco PostgreSQL
DB_USER=postgres            # Usuário do banco
DB_PASSWORD=mysecretpassword # Senha do banco
DB_HOST=localhost           # Host (local) ou host do cluster (produção)
DB_PORT=5432                # Porta do PostgreSQL
```

**Local (desenvolvimento com Docker):**
```bash
# Subir o PostgreSQL via docker-compose:
docker-compose up -d postgres

# A connection string gerada será:
# postgresql://postgres:mysecretpassword@localhost:5432/banking-llm?sslmode=disable
```

**Produção (LangGraph Cloud):**
```bash
# Em produção, configurar as variáveis de ambiente com os dados do cluster PostgreSQL.
# O LangGraph Cloud gerencia automaticamente o checkpointer quando deployado via langgraph.json.
# As tabelas de checkpoint são criadas automaticamente via `checkpointer.setup()` no lifespan da aplicação.
```

**Inicialização (já implementada em `src/main.py`):**
```python
async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
    await checkpointer.setup()  # Cria tabelas de checkpoint no banco existente
    app.state.checkpointer = checkpointer
```

> O checkpointer é **obrigatório** para o fluxo multi-turn (CUSTOM amount). Sem ele, o state não persiste entre mensagens e o usuário precisaria re-enviar o BRCode a cada interação. Como já está integrado ao banco existente, nenhuma infraestrutura adicional é necessária.

### 5.6 Observabilidade

| Evento | Log Level | Campos |
|--------|-----------|--------|
| Payment flow started | INFO | brcode (primeiros 30 chars), has_amount |
| Preview completed | INFO | status, amount_type, e2e_id |
| Status blocked | WARN | status (PAID/EXPIRED), e2e_id |
| Awaiting amount | INFO | beneficiary_name, amount_type |
| Payment executed | INFO | e2e_id, amount, init_type |
| Payment failed | ERROR | error, e2e_id |

---

## 6. Diagrama (Mermaid)

```mermaid
flowchart TD
    A[Usuário: 'Pague o QR Code ...'] --> B[identifyIntent]
    B -->|pix_payment| C[pixPayment Node]
    C --> D{Tem preview data + amount no state?}
    D -->|Sim - continuação| K[PixWithdrawService.execute]
    D -->|Não| E[BRCodePreviewService.execute]
    E --> F{Preview OK?}
    F -->|Erro| G[Retorna erro ao usuário]
    F -->|Sucesso| H{Status do QR Code}
    H -->|PAID| I[Informa: QR Code já pago]
    H -->|EXPIRED| J[Informa: QR Code expirado]
    H -->|ACTIVE| L{amount_type}
    L -->|FIXED| K
    L -->|CUSTOM| M{Usuário informou amount?}
    M -->|Sim| K
    M -->|Não| N[Retorna dados + pergunta valor]
    N --> O[awaiting_amount = True]
    K --> P{Transfer OK?}
    P -->|Sucesso| Q[chatResponse: Pagamento realizado]
    P -->|Erro| R[chatResponse: Erro no pagamento]
    I --> S[chatResponse: Dados consulta]
    J --> S
```

---

## 7. DoD (Definition of Done)

- [ ] Código lintado (ruff + black)
- [ ] `PixPaymentService` implementado com orquestração preview → validação → pagamento
- [ ] Nó `pixPayment` adicionado ao StateGraph
- [ ] Intent `pix_payment` adicionado ao classifier
- [ ] `GraphState` atualizado com `awaiting_amount` e `brcode_status`
- [ ] Validação de status (`ACTIVE`/`PAID`/`EXPIRED`) implementada
- [ ] Controle de `amount_type` (`FIXED`/`CUSTOM`) implementado
- [ ] Fluxo de continuação (CUSTOM → pergunta valor → recebe valor → executa) funcional
- [ ] Testes unitários: cenários de sucesso (FIXED, CUSTOM com/sem amount), bloqueios (PAID, EXPIRED), desambiguação, erros (brcode inválido, API error)
- [ ] Logs estruturados em pontos-chave do fluxo
- [ ] README atualizado com configuração do checkpointer (local + produção)
- [ ] Fluxo de desambiguação (`brcode_ambiguous`) implementado
- [ ] Code review aprovado

---

## 8. Estimativa & Riscos

| Aspecto | Avaliação |
|---------|-----------|
| Esforço | **Alto** — novo service, novo nó, atualização de intent, fluxo de continuação multi-turn |
| Risco técnico | **Médio** — depende da correta distinção entre intents `brcode_preview` vs `pix_payment` pelo LLM |
| Risco de negócio | **Baixo** — reutiliza serviços existentes (`BRCodePreviewService`, `PixWithdrawService`) |
| Dependência externa | Banking API (preview + transfer) — já integrada |
| Ponto de atenção | Fluxo multi-turn (CUSTOM amount) depende do checkpointer/memory para manter estado entre mensagens |

---

## Verificação

- [x] Requisito validado com stakeholder (fluxo de pagamento com validação de status e controle de valor)
- [x] Impacto em contratos existentes mapeado (reutiliza `withdraw_*` fields, adiciona `awaiting_amount` e `brcode_status`)
- [x] Estimativa consensuada (Alto esforço, Médio risco)
- [x] Sem [Consulta Necessária] ou [Suposição] não validada

### Suposições validadas:
1. ✅ O campo `status` retorna `ACTIVE`/`PAID`/`EXPIRED` na response de `/brcode/preview` — confirmado.
2. ✅ O fluxo de continuação (multi-turn) depende do LangGraph checkpointer — **documentar no README** como configurar local (SQLite/in-memory) e produção (PostgreSQL). Ver seção 5.7.
3. ✅ Quando a intenção não é clara, o sistema pergunta ao usuário se quer consultar ou pagar — implementado via `brcode_ambiguous` intent.
