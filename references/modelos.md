# Modelos de texto/código — catálogo (2026)

Fontes: documentação oficial da OpenAI (ver
`pesquisas/2026-11-06-estado-da-api-openai.md`, Q1) + `GET /v1/models` ao vivo.
Estado a 2026-11. Preços por 1M tokens (input/output) — tabela completa em
`precos-e-limites.md`.

## Endpoints de inferência

| Endpoint | Quando usar |
| --- | --- |
| **`POST /v1/responses`** (recomendado) | projetos novos: melhor reasoning, tool calling (obrigatório para GPT-6 Astra/6.1 Sol e modelos Pro), `instructions`, `previous_response_id`/Conversations, `store`, `text.verbosity`, `text.format` |
| `POST /v1/chat/completions` | compatibilidade/ecossistema `messages[]`; **sem tool calling com `reasoning_effort != "none"` desde o GPT-5.4** |

Modelos **Pro só existem na Responses API** (`o3-pro`, `gpt-5.2-pro`,
`gpt-5.5-pro`). `store` é `true` por omissão (desligar com `store: false`;
com `previous_response_id` todos os tokens da cadeia são faturados como
input). Parâmetros de reasoning: `reasoning.effort` (none→max conforme o
modelo), `reasoning.mode` (standard/pro) e `reasoning.context`
(all_turns/current_turn).

## Famílias ativas

| Família | Modelos | Contexto / output | Preços in/out | Notas |
| --- | --- | --- | --- | --- |
| **GPT-6** | `gpt-6-astra` | 1,05M / 128K | $10/$50 | topo; reasoning low→max (**não** aceita `none`); tools: Functions, Web/File search, Computer use |
| | `gpt-6.1-sol` | 1,05M / 128K | $2/$10 | ≈ Astra a 1/5 do preço; sem `none`/`minimal`; default medium |
| | `gpt-6.1-terra` | 1,05M / 128K | $1/$5 | cutoff jun/2026 |
| | `gpt-6-luna` | 1,05M / 128K | $0.10/$0.50 | barato; 30k RPM/180M TPM no tier Grow |
| **GPT-5.6** | `gpt-5.6-sol` (alias `gpt-5.6`→Sol) | 1,05M / 128K | $5/$30 (promo $4/$20?) | cutoff 16/fev/2026; efforts none→max |
| | `gpt-5.6-terra`, `gpt-5.6-luna` | 1,05M / 128K | $1/$5 · $0.20/$1.20 | |
| **GPT-5.5** | `gpt-5.5`, `gpt-5.5-pro` | 1,05M / 128K | $5/$30 · Pro $30/$180 | efforts none→xhigh; **Pro só Responses** |
| **GPT-5.4** | `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5.4-pro` | 1,05M / 128K | $2.50/$15 · $0.75/$4.50 · $0.20/$1.25 · Pro $30/$180 | primeiro com computer-use nativo |
| **GPT-5.2** | `gpt-5.2`, `gpt-5.2-pro` | 400K / 128K | $1.75/$14 · Pro $21/$168 | endpoint `/compact` estende o contexto efetivo |
| **GPT-5** | `gpt-5`, `gpt-5-mini`, `gpt-5-nano` | 400K / 128K | $1.25/$10 · $0.25/$2 · $0.05/$0.40 | efforts minimal→high; `gpt-5-mini` Deprecated |
| **Reasoning o-series** | `o3`, `o3-pro` | 200K / 100K | $2/$8 · $20/$80 | o3-pro só Responses; `o3-mini`/`o4-mini` saem 2027-01-14 |
| **Web search** | `gpt-5-search-api` | — | — | web search em Chat Completions (`web_search_options`) |
| **Chat alias** | `chat-latest` | — | — | alias mutável do Instant do ChatGPT — **não usar em produção** |

Modalidades dos modelos de texto: **entrada texto+imagem, saída só texto**
(sem áudio/vídeo). Long context: prompts >272K tokens faturam 2× (input) e
1,5× (output) nas janelas 1,05M.

## Deprecations — atenção a estas datas

| Data | O que sai |
| --- | --- |
| 2026-07-23 | `gpt-5-chat-latest`, `gpt-5-codex`, `gpt-5.1(-codex*)` e snapshots legacy (gpt-3.5/4/4-turbo/o1/o3-mini/o4-mini…) |
| 2026-08-10 | `gpt-5.2-chat-latest`, `gpt-5.3-chat-latest` |
| **2027-01-14** | **`gpt-4o`, `gpt-4.1`, `gpt-4.1-mini`, `o4-mini`** (notificados 2026-10-14) |
| sem data | `gpt-5.1`, `gpt-5.3-codex`, `gpt-5.4-nano`, `gpt-5`, `gpt-5-mini` — marcados "Deprecated" no catálogo |

**Substitutos recomendados**: `gpt-5.6-terra/sol/luna` e `gpt-6-*`. Um ID
"Deprecated" em `/v1/models` continua a responder hoje — mas não construa
nada novo sobre ele.

## Regras de escolha rápida

1. **Novo projeto → Responses API** com `gpt-6.1-sol` (qualidade/preço) ou
   `gpt-6-luna`/`gpt-5.6-luna` (custo mínimo).
2. **Melhor qualidade possível** → `gpt-6-astra` (ou `gpt-5.5-pro`/`o3-pro`
   para reasoning profundo, só Responses).
3. **Raciocínio barato** → `gpt-5.4-mini`/`gpt-5-nano`.
4. **Produção = snapshot/ID estável**, nunca aliases mutáveis (`chat-latest`,
   `gpt-5.6`); confirme IDs com `python scripts/openai.py models`.
