# Preços e limites da API OpenAI (2026)

Fontes: página oficial de preços e de rate limits da OpenAI + corroboração
(ver `pesquisas/2026-11-06-estado-da-api-openai.md`, Q5). Recolhido a
2026-11-06 — **preços mudam; confirme em
<https://developers.openai.com/api/docs/pricing> antes de orçamentar.**

## Texto — por 1M tokens (Standard: input / cached / output)

| Família | Modelo | Input | Cached | Output |
| --- | --- | --- | --- | --- |
| GPT-6 | `gpt-6-astra` | $10.00 | $1.00 | $50.00 |
| GPT-6.1 | `gpt-6.1-sol` | $2.00 | $0.10 | $10.00 |
| GPT-6.1 | `gpt-6.1-terra` | $1.00 | $0.05 | $5.00 |
| GPT-6 | `gpt-6-luna` | $0.10 | $0.01 | $0.50 |
| GPT-5.x | `gpt-5.5` | $5.00 | $0.50 | $30.00 |
| GPT-5.x | `gpt-5.4` | $2.50 | $0.25 | $15.00 |
| GPT-5.x | `gpt-5.4-mini` | $0.75 | — | $4.50 |
| GPT-5.x | `gpt-5.4-nano` | $0.20 | — | $1.25 |
| GPT-5.x | `gpt-5.2` | $1.75 | $0.175 | $14.00 |
| GPT-5.x | `gpt-5` / `gpt-5.1` | $1.25 | — | $10.00 |
| GPT-5.x | `gpt-5-mini` | $0.25 | — | $2.00 |
| GPT-5.x | `gpt-5-nano` | $0.05 | — | $0.40 |
| GPT-4.1 | `gpt-4.1` (descontinuada) | $2.00 | $0.50 | $8.00 |
| GPT-4o | `gpt-4o` (descontinuada) | $2.50 | $1.25 | $10.00 |
| Reasoning | `o3` | $2.00 | — | $8.00 |
| Reasoning | `o3-mini` / `o4-mini` | $1.10 | — | $4.40 |
| Reasoning | `o3-pro` | $20.00 | — | $80.00 |

Descontos/sobretaxas: **Batch −50%** e **Flex −50%** (Flex pode devolver
capacity errors); **Fast 2×** e **Ultrafast 6×** (capacidade prioritária);
pedidos **long context** (>272K tokens) faturam input 2× e output 1.5× em
famílias GPT-6; **data residency** (processamento regional) +10% em modelos
elegíveis lançados a partir de 2026-03-05.

## Imagem

- **gpt-image-2.5/2.6 (sunburst/flare)**: faturação por **tokens de imagem**
  — texto $5/1M in · imagem $8/1M in ($2 cached) · imagem $30/1M out
  (Batch: $4/$15/$1).
- **gpt-image-1** (já descontinuado; referência histórica): por imagem —
  1024×1024 low $0.011 / medium $0.042 / high $0.167; retangulares
  (1024×1536, 1536×1024) $0.016 / $0.063 / $0.25.

## Áudio

| Serviço | Modelo | Preço |
| --- | --- | --- |
| TTS | `tts-1` | $15 / 1M caracteres |
| TTS | `tts-1-hd` | $30 / 1M caracteres |
| TTS | `gpt-4o-mini-tts` | $0.60 / 1M tokens de texto + $12 / 1M tokens de áudio (≈ $0.015/min) |
| Transcrição | `gpt-transcribe` | $0.0045 / min |
| Transcrição | `gpt-4o-transcribe` | $2.50/$10 por 1M tokens (≈ $0.006/min) |
| Transcrição | `gpt-4o-mini-transcribe` | $1.25/$5 (≈ $0.003/min) |
| Transcrição | `whisper-1` | $0.006 / min |
| Realtime | `gpt-realtime-2.1` | áudio $32/$64 por 1M tokens ($0.40 cache); texto $4/$24 |
| Realtime | `gpt-realtime-2.1-mini` | áudio $10/$20; texto $0.60/$2.40 |
| Live | `gpt-live-1` | $0.05/min de sessão de voz, faturado ao segundo |
| Translate/Whisper live | `gpt-realtime-translate` / `gpt-realtime-whisper` | $0.034/min · $0.017/min |

## Embeddings e moderação

| Modelo | Preço / 1M tokens | Dimensões |
| --- | --- | --- |
| `text-embedding-3-small` | $0.02 (Batch $0.01) | 1536 |
| `text-embedding-3-large` | $0.13 (Batch $0.065) | 3072 |
| `text-embedding-ada-002` (legado, não descontinuado) | $0.10 | 1536 |
| `omni-moderation-latest` | **gratuito** | — |

## Fine-tuning (plataforma em encerramento)

- **Sem novos utilizadores** desde 2026-05-07/08; clientes existentes podem
  criar jobs **até 2027-01-06** (salvo shutdown do modelo base).
- Preços publicados: `gpt-4.1-2025-04-14` $25/1M tokens de treino (inferência
  $3/$12); `gpt-4.1-mini-2025-04-14` $5/1M (inferência $0.80/$3.20).
  Desconto de inferência com data sharing ativo.
- Modelos `ft-gpt-4.1*` encerram a 2027-01-14.

## Rate limits — tiers atuais

Os tiers são **Free / Build / Launch / Grow**, atribuídos pelo **total de
créditos comprados** na organização (Build $5 · Launch $100 · Grow $500), com
**upgrade automático** e tetos mensais de uso: Free $100/mês · Build $500/mês
· Launch $5.000/mês · Grow $200.000/mês. (O antigo sistema Tier 1–5 por
montante pago foi substituído.)

Limites Standard para `gpt-6-astra`/`sol`/`terra` (RPM / TPM):

| Tier | RPM | TPM |
| --- | --- | --- |
| Build | 5.000 | 1M |
| Launch | 10.000 | 4M |
| Grow | 15.000 | 40M |

(`gpt-6-luna` chega a 30.000 RPM / 180M TPM no Grow.) Os limites definem-se
por **organização e projeto** (não por utilizador) e há tetos próprios para
long context e para a via Ultrafast. Os valores por modelo legado só aparecem
em **Settings → Organization → Limits** na consola.

## Consumo e custos programaticamente

- `GET /v1/organization/usage/completions` — tokens por minuto/hora/dia,
  filtros por API key, projeto, utilizador e modelo.
- `GET /v1/organization/costs` — gasto diário em USD; desde 2026-08-04 ambos
  aceitam `group_by=api_key`.
- **Exigem Admin API key** (criada em organization settings) — uma key `sk-`
  normal não chega. Dashboard:
  <https://platform.openai.com/settings/organization/usage>.

## 429 na prática

- `Retry-After` é **mínimo** → esperar esse valor **+ jitter**; sem header,
  backoff exponencial limitado.
- Pedidos falhados **contam para os limites** por minuto; retentativa cega
  prolonga o problema.
- **Não repetir** 429 de créditos esgotados (`credit_balance_exhausted`).
- O 429 por TPM rejeita antes de gerar quando os tokens reservados
  (input + `max_completion_tokens`) excedem o orçamento que renova a cada 60 s.
