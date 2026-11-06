# Embeddings, moderação, Files, Batch e fine-tuning

Fontes: documentação oficial da OpenAI (ver
`pesquisas/2026-11-06-estado-da-api-openai.md`, Q4). Estado a 2026-11.

## Embeddings — `POST /v1/embeddings`

| Modelo | Dimensões | Preço / 1M tokens |
| --- | --- | --- |
| `text-embedding-3-small` | 1536 (default) | $0.02 |
| `text-embedding-3-large` | 3072 (default) | $0.13 |
| `text-embedding-ada-002` (legado, **não** descontinuado) | 1536 | $0.10 |

- `dimensions` encurta o vetor (ex.: 512) sem perda relevante nos -3.
- Limites: **8192 tokens por input** · arrays até **2048 itens** (sem
  strings vazias) · **300.000 tokens somados** por pedido.
- Usos: busca semântica, clustering, recomendações, deteção de anomalias,
  classificação.

## Moderação — `POST /v1/moderations` (**gratuito**)

- Modelos: `omni-moderation-latest` (baseado em GPT-4o; snapshot
  `omni-moderation-2024-09-26`), mais `text-moderation-latest/stable`.
- Aceita **texto e imagem** (imagens até 20 MB); melhor precisão em
  não-inglês face à geração anterior.
- Resposta: `flagged`, `categories`, `category_scores` (hate, harassment,
  violence, self-harm, sexual, illicit e subcategorias).

## Files — `POST /v1/files`

- `purpose`: `assistants`, `assistants_output`, `batch`, `batch_output`,
  `fine-tune`, `fine-tune-results`, `vision`, `user_data`, `evals`.
- Ficheiros até **512 MB** cada; **2,5 TB** por projeto.
- `purpose=batch` expira por omissão ao fim de **30 dias**; os restantes
  persistem até delete manual.
- Uploads multipart: o parâmetro `file` é o **objeto ficheiro** (não o nome).

## Batch API — `POST /v1/batches` (−50% de desconto)

- Input: um `.jsonl` com até **50.000 pedidos** e **200 MB**; cada linha tem
  `custom_id`, `method` e `url`.
- Endpoints suportados: `/v1/responses`, `/v1/chat/completions`,
  `/v1/embeddings`, `/v1/completions`, `/v1/moderations`,
  `/v1/images/generations`, `/v1/images/edits`, `/v1/videos` (histórico).
- Batches de embeddings: máx. **50.000 inputs** somados por batch.
- Janela de conclusão: **24 h**; limites de rate muito superiores; resultado
  sai como ficheiro `.jsonl` (`output_file_id`).
- Ideal para: evals, classificação de grandes datasets, indexação.

## Fine-tuning — em ENCERRAMENTO

- Plataforma **sem novos utilizadores** (anúncio 2026-05-07/08); clientes
  existentes elegíveis podem criar jobs **até 2027-01-06** (salvo shutdown
  anterior do modelo base).
- Modelos com preço publicado: `gpt-4.1-2025-04-14` ($25/1M tokens de treino;
  inferência $3/$12) e `gpt-4.1-mini-2025-04-14` ($5/1M; $0.80/$3.20).
- Fluxo: dataset **JSONL** → upload (`purpose=fine-tune`) → job (dashboard ou
  `POST /v1/fine_tuning/jobs`) → avaliar. RFT usa grader próprio.
- Data sharing na criação do job → desconto na inferência do modelo afinado.
- Modelos `ft-*` servem inferência até ao shutdown do base (ex.:
  `ft-gpt-4.1*` a 2027-01-14).
