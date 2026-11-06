#!/usr/bin/env python3
"""Embeddings e moderação — /v1/embeddings e /v1/moderations.

Embeddings: text-embedding-3-small (1536 dimensões, barato),
text-embedding-3-large (3072), text-embedding-ada-002 (legado).
Moderação: omni-moderation-latest.
A key vem SEMPRE de OPENAI_API_KEY no ambiente; sem key, recusa-se a correr.
"""
import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")


def key() -> str:
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        sys.exit('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" e volte a correr')
    return k


def _post(caminho: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{API_BASE}{caminho}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def embed(textos: "list[str]", model: str = "text-embedding-3-small") -> "list[list[float]]":
    r = _post("/embeddings", {"model": model, "input": textos})
    return [d["embedding"] for d in sorted(r["data"], key=lambda d: d["index"])]


def moderar(texto: str, model: str = "omni-moderation-latest") -> dict:
    r = _post("/moderations", {"model": model, "input": texto})
    return r["results"][0]


if __name__ == "__main__":
    vetores = embed(["cachorro a correr no parque", "um cão a brincar", "a bolsa fechou em alta"])
    print(f"{len(vetores)} vetores com {len(vetores[0])} dimensões")
    res = moderar("exemplo de texto para moderação")
    print(f"flagged={res['flagged']} categorias ativas={[c for c, v in res['categories'].items() if v]}")
