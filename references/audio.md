# Áudio — TTS, transcrição e tradução (2026)

Fontes: documentação oficial da OpenAI (ver
`pesquisas/2026-11-06-estado-da-api-openai.md`, Q3). Estado a 2026-11.

## Endpoints REST

| Endpoint | Função | Modelos |
| --- | --- | --- |
| `POST /v1/audio/speech` | texto → fala (TTS) | `gpt-4o-mini-tts`, `tts-1`, `tts-1-hd` |
| `POST /v1/audio/transcriptions` | áudio → texto | `gpt-transcribe` (recomendado), `whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe-diarize` |
| `POST /v1/audio/translations` | áudio → inglês | `whisper-1` (único) |

> **Datas de desligamento anunciadas**: `tts-1`/`tts-1-hd`/`gpt-4o-mini-tts`
> → **2027-01-06** (substituto apontado: Realtime, ex. `gpt-realtime-2.1-mini`;
> a comunidade contesta para uso single-turn). `whisper-1`,
> `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe-diarize`
> → **2027-02-26** (migrar para `gpt-transcribe` ou `gpt-live-transcribe`).
> `gpt-audio`/`gpt-audio-mini` → migrar para `gpt-audio-1.5` até 2027-01-20.
> **Não há substituto anunciado** para tradução de áudio, diarização, word
> timestamps nem legendas SRT/VTT.

## TTS — `POST /v1/audio/speech`

- **Input**: até **4096 caracteres**. `instructions` (até 4096) controla o
  estilo — **não funciona** com `tts-1`/`tts-1-hd`.
- **Vozes** (13): `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`,
  `onyx`, `sage`, `shimmer`, `verse`, `marin`, `cedar` — recomendadas
  **marin/cedar**. `tts-1`/`tts-1-hd` só têm 9 (sem verse/marin/cedar).
  Vozes custom: criadas a partir de **amostras de áudio** (`{id}`); vozes por
  prompt de texto só em Live.
- **Formatos**: `mp3` (default), `opus`, `aac`, `flac`, `wav`, `pcm` (24 kHz
  16-bit signed LE, sem header). `wav`/`pcm` = resposta mais rápida.
- `speed` 0.25–4.0 (1.0); `stream_format`: `sse` | `audio` (sse não em
  tts-1/hd).
- **Preços**: `tts-1` $15/1M caracteres · `tts-1-hd` $30/1M ·
  `gpt-4o-mini-tts` por tokens ($0.60/1M texto + $12/1M áudio ≈ $0.015/min).
- Política: divulgar ao utilizador final que a voz é **gerada por IA**.

## Transcrição — `POST /v1/audio/transcriptions`

- **Ficheiros até 25 MB**: `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, `webm`.
- **Modelo recomendado: `gpt-transcribe`** ($0.0045/min, performance máxima,
  `languages[]` ISO 639-1/3 e zh-*, keyword hints, contexto). Especializados
  só para speaker labels, word timestamps, legendas ou tradução.
- `whisper-1` ($0.006/min, 98 idiomas, precisão variável): **único** com
  `srt`/`vtt`/`verbose_json` e `timestamp_granularities` (`word`|`segment`;
  exige `verbose_json`; acrescenta latência).
- `gpt-4o-transcribe` ($2.50/$10 por 1M tokens ≈ $0.006/min) e
  `gpt-4o-mini-transcribe` ($1.25/$5 ≈ $0.003/min): só `response_format=json`.
- **Streaming** (SSE) em todos **exceto whisper-1** (ignorado).
- `response_format` do endpoint: `json`, `text`, `srt`, `verbose_json`,
  `vtt`, `diarized_json`.

### Diarização — `gpt-4o-transcribe-diarize`

- `response_format: "diarized_json"` → segmentos com `speaker`, `start`,
  `end`. Áudio > 30 s exige `chunking_strategy` (`auto` ou configuração VAD).
- Até **4 falantes conhecidos** via `known_speaker_names[]` +
  `known_speaker_references[]` (clips de 2–10 s como data URL).
- Comunidade reporta frases saltadas/alucinação de falantes em alguns casos.

## Tradução — `POST /v1/audio/translations`

- Traduz áudio **para inglês**; só `whisper-1`; `prompt` (em inglês) e
  `response_format` json/text/srt/verbose_json/vtt.

## Áudio em chat — `gpt-audio-1.5`

Melhor modelo voz áudio-in/áudio-out para Chat Completions (contexto 128K):
texto $2.50/$10 por 1M tokens + áudio $32/$64 por 1M tokens. É o substituto
recomendado de `gpt-audio`/`gpt-audio-mini`. Para transcrição em direto:
`gpt-live-transcribe` (streaming de baixa latência, $0.017/min, usado em
`/v1/realtime/transcription_sessions` e `/v1/live/sessions`).

## Armadilhas conhecidas

- whisper-1 por vezes **traduz em vez de transcrever** com sotaques →
  fixe `language`.
- Precificação de `gpt-4o-mini-tts` só corroborada por agregadores; confirme
  na página de preços.
- Sem migração documentada para legendas/diarização após 2027-02-26.
