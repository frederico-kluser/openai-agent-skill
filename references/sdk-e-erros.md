# SDKs oficiais, erros e retentativas

Fontes: documentação oficial da OpenAI e READMEs dos SDKs (ver
`pesquisas/2026-11-06-estado-da-api-openai.md`, Q7). Estado a 2026-11.

## SDKs oficiais

| | Python | Node.js |
| --- | --- | --- |
| Pacote | `pip install openai` (PyPI, linha **3.x**, ex.: 3.46.0) | `npm i openai` (linha **7.x**) |
| Requisitos | Python ≥ 3.10 | Node ≥ 22 (LTS 22/24) |
| Cliente HTTP | HTTPX2 por omissão | fetch nativo |
| Timeout por omissão | 10 min (configurável por cliente/pedido) | 10 min |
| Retries por omissão | 2, backoff exponencial curto | 2, idem |

Autenticação (igual nos dois): a key vem da variável de ambiente
**`OPENAI_API_KEY`** (os SDKs leem-na sozinhos); organização/projeto via
`OPENAI_ORG_ID` / `OPENAI_PROJECT_ID` (headers `OpenAI-Organization` /
`OpenAI-Project`).

```python
from openai import OpenAI
client = OpenAI()            # lê OPENAI_API_KEY do ambiente
r = client.responses.create(model="gpt-5.2", input="Olá")
print(r.output_text)
```

```js
import OpenAI from "openai";
const client = new OpenAI();  // lê process.env.OPENAI_API_KEY
const r = await client.responses.create({ model: "gpt-5.2", input: "Olá" });
console.log(r.output_text);
```

Os exemplos desta skill (`examples/`) são **stdlib/fetch puros, sem SDK** —
funcionam em qualquer lado; use o SDK oficial em produção quando puder.

## Responses API vs Chat Completions

- **Responses API** (`POST /v1/responses`) é a primitiva **recomendada para
  projetos novos**: reasoning tipado, `instructions`, `previous_response_id`,
  eventos de streaming tipados (`response.output_text.delta`,
  `response.completed`).
- **Chat Completions** (`POST /v1/chat/completions`) continua **suportada** e
  é a escolha certa para compatibilidade e para o ecossistema de ferramentas
  que já fala `messages[]`.

## Streaming

SSE (`stream=True` / `stream: true`):
- Chat Completions → chunks incrementais com `choices[].delta.content`.
- Responses → eventos tipados; use `response.output_text.delta` para o texto
  e `response.completed` para o fim (contém usage).

Dica: em gerações longas use sempre streaming — proxies e hosts cortam
ligações paradas (~60 s) antes do timeout de 10 min do SDK.

## Tool calling e Structured Outputs

- **Function calling** liga o modelo a ferramentas suas; **Structured
  Outputs** garante JSON válido (`response_format: {type: "json_schema", …,
  strict: true}` na Chat Completions, `text.format` na Responses).
- Recomendação oficial: ativar sempre `strict: true` em tool calling — exige
  `additionalProperties: false` e todos os campos em `required` (opcionais
  tipados como `["string", "null"]`).

## Mapa de erros

| HTTP | SDK Python | SDK Node | O que fazer |
| --- | --- | --- | --- |
| 400 | `BadRequestError` | `BadRequestError` | corrigir parâmetros/pedido |
| 401 | `AuthenticationError` | `AuthenticationError` | key inválida/revogada → nova key no ambiente |
| 403 | `PermissionDeniedError` | `PermissionDeniedError` | política/escopo; ajustar pedido |
| 404 | `NotFoundError` | `NotFoundError` | modelo/endpoint errado |
| 409 | (—) | `ConflictError` | conflito de estado; não repetir às cegas |
| 422 | `UnprocessableEntityError` | `UnprocessableEntityError` | payload inválido |
| 429 | `RateLimitError` | `RateLimitError` | ver abaixo |
| ≥500 | `InternalServerError` | `InternalServerError` | repetir com backoff |
| — | `APIConnectionError` | `APIConnectionError` | rede; repetir |

Semântica de sobrecarga: **503** (`service_unavailable_error` /
`server_is_overloaded`) é o código atual para modelo sem capacidade — já foi
429 no passado. No SDK Python, 503 levanta `InternalServerError` (não
`RateLimitError`): **apanhe ambas as classes e inspecione `error.code`**.

## Retentativas (política oficial)

1. **`Retry-After` é um mínimo**: espere pelo menos esse valor **+ jitter
   aleatório** (evita a manada).
2. Sem o header: **backoff exponencial com jitter**, com limite de tentativas
   (os SDKs já repetem 2× por omissão: ligação, 408, 409, 429, ≥500).
3. **429 nem sempre é retentável**: `credit_balance_exhausted` (créditos
   gastos) não se resolve com espera — não repita.
4. Pedidos falhados **contam para os limites** por minuto; retentativa cega
   prolonga o problema.
5. Cuidado com `Retry-After` muito longos: o SDK Python pode abortar o retry
   automático — faça a espera na aplicação e conte as tentativas do SDK.
6. **Idempotência**: só alguns endpoints de criação aceitam `Idempotency-Key`
   (Agents API environments/sessions, Ads, Workspace Agents). Em
   `/v1/responses` e `/v1/chat/completions` uma retentativa duplica tokens e
   custo — desenhe para idempotência ao nível da aplicação.

## Armadilhas comuns

- **Listagens paginadas**: `models`, `files`, `batches` etc. são paginados;
  os SDKs têm auto-pagination.
- **Uploads**: `files.create` exige o **objeto ficheiro** (não o nome) e um
  `purpose` do enum (`assistants`, `batch`, `fine-tune`, `vision`,
  `user_data`, `evals`).
- **Timeout**: 10 min por omissão; corte intencional em proxies a ~60 s →
  streaming para gerações longas.
- **Mudanças de versão do SDK**: o `openai-python` já teve uma reescrita
  total (v1.0.0); fixe versões em produção e siga os guides de migração.
