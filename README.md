# openai-agent-skill

<p align="center">
  <a href="https://github.com/frederico-kluser/openai-agent-skill/actions/workflows/ci.yml"><img src="https://github.com/frederico-kluser/openai-agent-skill/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://securityscorecards.dev/viewer/?uri=github.com/frederico-kluser/openai-agent-skill"><img src="https://api.securityscorecards.dev/projects/github.com/frederico-kluser/openai-agent-skill/badge" alt="OpenSSF Scorecard"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-mit-blue.svg" alt="License: mit"></a>
  <a href="https://github.com/frederico-kluser/openai-agent-skill/releases"><img src="https://img.shields.io/github/v/release/frederico-kluser/openai-agent-skill" alt="GitHub release"></a>
</p>

**Agent skill que dá acesso a TUDO da API da OpenAI** — modelos de chat e
reasoning, geração e edição de imagem, áudio (TTS, transcrição, tradução,
diarização), embeddings, moderação, Batch, Realtime — com **código pronto**
em Python e Node.js e uma CLI stdlib que funciona em qualquer lado.

A regra que define a skill: **a `OPENAI_API_KEY` vem sempre das variáveis de
ambiente do sistema** — sem key no ambiente, os comandos e exemplos
**recusam-se a trabalhar** (exit 2). A key nunca é lida de ficheiros, nunca é
impressa e é sempre redigida nas saídas.

## O que traz

- **`scripts/openai.py`** — CLI (Python stdlib, zero dependências):
  `status`, `models`, `chat`, `responses`, `image`, `image-edit`, `tts`,
  `transcribe`, `translate`, `embed`, `moderate`, `selftest`.
- **`examples/python/` e `examples/node/`** — código pronto para copiar:
  chat com streaming, Responses API com reasoning, imagem (gerar/editar),
  TTS, transcrição de áudio, embeddings e moderação.
- **`references/`** — referência técnica: modelos, imagem, áudio, realtime e
  vídeo, embeddings/moderação/Batch, preços e rate limits, SDKs/erros/
  retentativas, credenciais.
- **`pesquisas/`** — dossiê de pesquisa profunda que fundamenta a referência
  (estado da API a 2026-11, com fontes).

## Instalação

A skill instala-se **globalmente por symlink** (uma fonte em
`~/Agent-Skills/openai-agent-skill`, links em todos os skill roots: `.agents`,
`.claude*`, `.jcode`, `.pi`, `.dsh`, `.config/opencode/skill`, `.codex`) —
comandos em [`SKILL.md`](SKILL.md). Requisitos de runtime:

- Python ≥ 3.10 (CLI e exemplos Python) ou Node ≥ 18 (exemplos Node).
- Uma API key da OpenAI — <https://platform.openai.com/api-keys>.

## Instalação da key (uma vez, no sistema)

```powershell
# Windows (PowerShell)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-…", "User")
```

```bash
# Linux/macOS (~/.bashrc / ~/.zshrc)
export OPENAI_API_KEY="sk-…"
```

Abra um novo terminal e confirme sem expor o valor:

```bash
python scripts/openai.py status --ping
```

## Quick start

```bash
# Ver modelos disponíveis na conta
python scripts/openai.py models --filter gpt-5

# Chat (com streaming via --stream)
python scripts/openai.py chat "Explica a API da OpenAI em 2 frases" --model gpt-5.2

# Imagem
python scripts/openai.py image "capivara robótica neon" --model gpt-image-2 --quality high

# Fala
python scripts/openai.py tts "Olá mundo" --voice alloy --out olamundo.mp3

# Transcrição de áudio
python scripts/openai.py transcribe ./gravacao.mp3 --model gpt-transcribe

# Embeddings e moderação
python scripts/openai.py embed "busca semântica"
python scripts/openai.py moderate "texto a verificar"
```

Os exemplos em `examples/` são autónomos (stdlib/fetch, sem SDK):

```bash
python examples/python/01_chat_stream.py "olá"
node examples/node/01_chat_stream.mjs "olá"
```

## Notas de estado (2026-11)

- **Vídeo por API não existe**: a Videos API (Sora 2) foi removida a
  2026-09-24, sem substituto — ver `references/realtime-e-video.md`.
- **DALL·E 2/3 e `gpt-image-1` desligados**; use `gpt-image-2.5/2.6`
  (`sunburst` = qualidade/edição, `flare` = velocidade).
- **TTS** (`tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`) sai a 2027-01-06;
  **transcrição** (`whisper-1`, `gpt-4o-transcribe*`) sai a 2027-02-26 —
  migre para `gpt-transcribe`/`gpt-live-transcribe`.
- **Fine-tuning** em encerramento (novos jobs até 2027-01-06 para clientes
  existentes); **moderação** é gratuita.

## Documentação

- Instruções para agentes: [`SKILL.md`](SKILL.md).
- Referências técnicas: [`references/`](references/).
- Dossiê de pesquisa (fontes e datas): [`pesquisas/`](pesquisas/).

## Contributing

Contributions are welcome — please read [CONTRIBUTING.md](CONTRIBUTING.md) for the development
workflow, commit conventions, and pull request process, and our
[Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

## Security

Please **do not** report security vulnerabilities through public issues. See
[SECURITY.md](SECURITY.md) for private reporting and our response SLA.

## Versioning

This project follows [Semantic Versioning](https://semver.org/) and keeps a detailed changelog in
[CHANGELOG.md](CHANGELOG.md), generated from Conventional Commits. Releases are published
automatically from `main`; see the
[releases page](https://github.com/frederico-kluser/openai-agent-skill/releases) for the latest version.

## License

Distributed under the `mit` license. See [LICENSE](LICENSE) for details.

## Acknowledgements

- Everyone who has contributed code, documentation, and bug reports.
- [Contributor Covenant](https://www.contributor-covenant.org/) for the Code of Conduct.
- [Keep a Changelog](https://keepachangelog.com/) and [Conventional Commits](https://www.conventionalcommits.org/)
  for the conventions this project builds on.
