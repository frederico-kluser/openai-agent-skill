# Realtime API e vídeo — o que existe hoje (2026)

Fontes: documentação oficial da OpenAI (ver
`pesquisas/2026-11-06-estado-da-api-openai.md`, Q6). Estado a 2026-11.

## TL;DR

- **Realtime API (voz/visão em tempo real): EM GA** — interface GA desde
  2025-08-28; a interface Beta foi removida da API a 2026-05-12.
- **Vídeo por API: NÃO EXISTE** — a Videos API (Sora 2) foi descontinuada
  (aviso a 2026-03-24, app fechada a 2026-04-26, **API removida a
  2026-09-24**) e não há sucessor anunciado. «Tudo que tem direito» cobre
  voz e visão em tempo real, **mas não vídeo**.

## Realtime API

### Modelos ativos

| Modelo | O que faz | Preços (por 1M tokens) |
| --- | --- | --- |
| `gpt-realtime-2.1` | voz+visão full-duplex, function calling, reasoning configurável; contexto 128K, saída 32K | áudio $32 in / $64 out ($0.40 cache) · texto $4/$24 · imagem $5 in |
| `gpt-realtime-2.1-mini` | versão leve | áudio $10/$20 · texto $0.60/$2.40 · imagem $0.80 in |
| `gpt-realtime-translate` | tradução de fala em streaming, 70+ idiomas de entrada → 13 de saída (`/v1/realtime/translations`) | $0.034/min |
| `gpt-realtime-whisper` · `gpt-live-transcribe` | transcrição em tempo real (`/v1/realtime/transcription_sessions`) | $0.017/min |
| `gpt-live-1` | voz full-duplex (`/v1/live/sessions`), com raciocínio e tools delegados a backend (cobrado à parte) | $0.05/min de sessão de voz, **faturado ao segundo** |

### Como ligar

- **WebRTC** (browser/apps): `POST /v1/realtime/client_secrets` cria
  credenciais efémeras; `POST /v1/realtime/calls` estabelece a sessão
  (o cliente envia SDP com a configuração da sessão).
- **WebSocket** (servidor): a via clássica, com eventos JSON.
- Sessões: **duração máxima 60 min** (`expires_at` em `session.created`);
  sem limite de sessões simultâneas desde 2025-02-03.

### Vozes

`alloy`, `ash`, `ballad`, `coral`, `cedar`, `echo`, `marin`, `sage`,
`shimmer`, `verse` — a OpenAI recomenda **marin** ou **cedar**. A voz não
muda depois de o modelo emitir áudio na sessão.

### Limitações

- Modalidades: texto e áudio (entrada/saída) + **imagem só de entrada**
  (visão); **vídeo não suportado**.
- Não suporta structured outputs, fine-tuning nem predicted outputs.
- O 2.1 suporta function calling e reasoning configurável (mais esforço =
  mais latência e tokens).

## Vídeo (Sora) — histórico, já não disponível

| Data | Evento |
| --- | --- |
| 2025-10-07 | Sora 2 lançado na API (`POST /v1/videos`, `sora-2`, `sora-2-pro`) |
| 2026-03-24 | aviso de depreciação da Videos API e aliases |
| 2026-04-26 | app/site do Sora encerrados |
| **2026-09-24** | **API removida** (`sora-2`, `sora-2-pro`, snapshots), sem substituto |

Preços históricos (para referência): sora-2 $0.10/s a 720p (batch $0.05/s);
sora-2-pro $0.30/s 720p, $0.50/s 1024p, $0.70/s 1080p; clips 4–25 s.

**O que fazer quando precisar de vídeo hoje**: a OpenAI não oferece geração
de vídeo por API. Alternativas estão fora do âmbito desta skill (ver
concorrentes se necessário). A geração de **GIF animado** e **SVG** continua
disponível na Image API (gpt-image-2.6).
