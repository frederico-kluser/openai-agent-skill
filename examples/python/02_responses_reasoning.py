#!/usr/bin/env python3
"""Responses API com reasoning — POST /v1/responses (stdlib).

A Responses API é o endpoint recomendado pela OpenAI para pedidos novos:
suporta reasoning (gpt-5.x/6.x), instructions persistentes, tool calling e
estruturas de saída. A key vem SEMPRE de OPENAI_API_KEY no ambiente.
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


def responder(prompt: str, model: str = "gpt-5.2", instrucoes: str | None = None,
              reasoning_effort: str | None = None, max_output_tokens: int | None = None) -> dict:
    payload: dict = {"model": model, "input": prompt}
    if instrucoes:
        payload["instructions"] = instrucoes
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}   # minimal | low | medium | high
    if max_output_tokens:
        payload["max_output_tokens"] = max_output_tokens

    req = urllib.request.Request(
        f"{API_BASE}/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())


if __name__ == "__main__":
    r = responder(
        sys.argv[1] if len(sys.argv) > 1 else "Resolve: um comboio parte às 14h e leva 2h30. A que horas chega?",
        instrucoes="És um tutor paciente. Mostra o raciocínio em 1 linha e a resposta final.",
        reasoning_effort="low",
    )
    print(r.get("output_text") or json.dumps(r, ensure_ascii=False, indent=2))
