# Imagem — geração e edição (2026)

Fontes: documentação oficial da OpenAI (ver
`pesquisas/2026-11-06-estado-da-api-openai.md`, Q2). Estado a 2026-11.

## Endpoints

A Image API tem **dois** endpoints:

- `POST /v1/images/generations` — gerar a partir de prompt.
- `POST /v1/images/edits` — editar imagens existentes (até **16 imagens de
  entrada** nos modelos GPT Image; PNG/JPEG/WebP/GIF não animado; data-URL
  até ~20 MB; payload total até 512 MB).

A **Responses API** expõe ainda a ferramenta `image_generation` para
experiências conversacionais com edição multi-turno.

> `POST /v1/images/variations` continua na referência mas **só aceita
> dall-e-2** — e o dall-e-2/dall-e-3 foram **desligados a 2026-05-12**. Use
> `edits` com prompt. `gpt-image-1` foi desligado a **2026-10-23**.

## Modelos ativos

| Modelo | Papel |
| --- | --- |
| `gpt-image-2.6-sunburst` / `gpt-image-2.6-flare` (2026-11-04) | topo atual: complexity, markup-guided edits, **SVG** e **GIF animado** (só generations) |
| `gpt-image-2.5-sunburst` / `gpt-image-2.5-flare` (+ snapshots 2026-09-08) | qualidade/edição precisa (Sunburst) vs velocidade (Flare) |
| `gpt-image-2` (+ snapshot 2026-04-21) | geração/edição rápida, tamanhos flexíveis |
| `gpt-image-1.5` | edição com `input_fidelity` high/low |
| `gpt-image-1-mini` | rápido e barato |
| `chatgpt-image-latest` | alias do modelo do ChatGPT |

**Flare** = modelo pequeno, otimizado para velocidade (qualidade ≈ GPT Image
2). **Sunburst** = modelo base, otimizado para qualidade e **precisão de
edição**. Recomendação oficial: *Sunburst quando a edição precisa importa;
Flare para geração rápida do dia-a-dia*.

## Parâmetros principais (generations/edits)

| Parâmetro | Valores | Notas |
| --- | --- | --- |
| `prompt` | 1–32.000 caracteres | |
| `n` | 1–10 | |
| `size` | `auto`, 1024×1024, 1024×1536, 1536×1024 | `gpt-image-2`: resoluções flexíveis até 3840px de aresta, múltiplos de 16, rácio ≤ 3:1, 655.360–8.294.400 px |
| `quality` | `low`/`medium`/`high`/`auto` (+ `xhigh`/`max` em 2.5/2.6) | |
| `output_format` | `png`/`jpeg`/`webp` (+ `svg`, `gif` **só 2.6 e só generations**) | |
| `output_compression` | 0–100 | jpeg/webp |
| `background` | `transparent`/`opaque`/`auto` | transparente exige png/webp |
| `moderation` | `auto`/`low` | filtro de conteúdo dos GPT Image |
| `input_fidelity` | `high`/`low` | `gpt-image-1.5` (mini: só `low`); **omitir** em `gpt-image-2`+ |
| `stream` + `partial_images` | 0–3 | cada imagem parcial = +100 image output tokens |
| `markup` | PNG transparente sobre a 1.ª imagem | edição guiada (2.5/2.6); não combina com `mask` |

Saída: modelos GPT Image devolvem sempre **`b64_json`** (sem `url`); o
`usage` traz tokens detalhados. SVG: `output_format:"svg"`, `n=1`, sem
streaming/partial/compressão, e o endpoint de **edits não produz SVG**.

## Preços

- **GPT Image 2.5/2.6 (sunburst/flare)** — por tokens: texto $5/1M in
  ($1.25 cache) · imagem $8/1M in ($2 cache) · imagem **$30/1M out**.
- **Por imagem** (guia oficial, 1024×1024 / 1024×1536 / 1536×1024):
  - GPT Image 2: low $0.006/$0.005/$0.005 · medium $0.053/$0.041/$0.041 ·
    high $0.211/$0.165/$0.165
  - GPT Image 1.5: low $0.009/$0.013/$0.013 · medium $0.034/$0.05/$0.05 ·
    high $0.133/$0.2/$0.2
  - gpt-image-1-mini: low $0.005/$0.006/$0.006 · medium $0.011/$0.015/$0.015
    · high $0.036/$0.052/$0.052

## Requisitos e armadilhas

- Para os modelos GPT Image pode ser exigida **API Organization
  Verification** no developer console.
- Envie `safety_identifier` (substitui o `user` depreciado).
- `background: transparent` → `png`/`webp` apenas (em `gpt-image-2` o
  suporte está em preview).
- gpt-image-2.6 **não corre na Batch API** (ao contrário da 2.5).
- Contradições por resolver: aresta máxima 3840px (documentação Leonardo)
  vs 4000px (fal.ai); `size: "auto"` documentado mas rejeitado por terceiros
  — confirme na resposta de erro se um size for recusado.
