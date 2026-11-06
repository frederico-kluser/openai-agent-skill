# Exemplos prontos

Código autónomo (Python stdlib / Node fetch nativo — **zero dependências**) para
cada capacidade da API da OpenAI. Todos exigem `OPENAI_API_KEY` no ambiente e
**recusam-se a correr sem ela** (exit 2) — ver [`../references/credenciais.md`](../references/credenciais.md).

```powershell
# Windows (PowerShell) — uma vez, no sistema
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-…", "User")
```

## Python (`examples/python/`)

| Ficheiro | Comando | O que mostra |
| --- | --- | --- |
| `01_chat_stream.py` | `python 01_chat_stream.py "olá"` | Chat Completions com streaming SSE |
| `02_responses_reasoning.py` | `python 02_responses_reasoning.py "pergunta"` | Responses API com `reasoning.effort` |
| `03_imagem.py` | `python 03_imagem.py gerar "prompt"` · `python 03_imagem.py editar "prompt" in.png` | Gerar/editar imagens (multipart) |
| `04_tts.py` | `python 04_tts.py "texto" out.mp3` | Texto → fala (vozes + instruções de estilo) |
| `05_transcricao.py` | `python 05_transcricao.py som.mp3` · `... som.mp3 traduzir` | Transcrição (gpt-transcribe) e tradução |
| `06_embeddings_moderacao.py` | `python 06_embeddings_moderacao.py` | Embeddings + moderação gratuita |

## Node.js (`examples/node/`)

| Ficheiro | Comando | O que mostra |
| --- | --- | --- |
| `01_chat_stream.mjs` | `node 01_chat_stream.mjs "olá"` | Chat com streaming (fetch nativo) |
| `02_responses_reasoning.mjs` | `node 02_responses_reasoning.mjs "pergunta"` | Responses API com reasoning |
| `03_imagem.mjs` | `node 03_imagem.mjs` · `node 03_imagem.mjs editar "prompt" in.png` | Gerar/editar imagens (FormData) |
| `04_audio_embed.mjs` | `node 04_audio_embed.mjs tts "texto"` · `transcribe som.mp3` · `embed a b` · `moderate "txt"` | TTS, transcrição, embeddings e moderação |

## Notas

- Saídas de imagem/áudio ficam na pasta atual (`out/` para imagens).
- Modelos por omissão seguem a investigação de 2026-11: `gpt-5.2`
  (chat/responses), `gpt-image-2` (imagem), `gpt-4o-mini-tts` (TTS) e
  `gpt-transcribe` (transcrição). Veja `../references/modelos.md` e
  `../references/audio.md` para deprecations e substitutos.
- Para produção, considere os SDKs oficiais
  (`pip install openai` · `npm i openai`) — padrões em
  `../references/sdk-e-erros.md`.
