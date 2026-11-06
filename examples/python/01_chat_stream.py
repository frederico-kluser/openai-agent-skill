#!/usr/bin/env python3
"""Chat com streaming — POST /v1/chat/completions (stdlib, sem dependências).

A key vem SEMPRE da variável de ambiente OPENAI_API_KEY; sem key, o exemplo
recusa-se a correr. Nunca escreva a key em código ou ficheiros.
"""
import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")


def key() -> str:
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        sys.exit('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" '
                 "(PowerShell: $env:OPENAI_API_KEY='sk-…') e volte a correr")
    return k


def chat_stream(prompt: str, model: str = "gpt-5.2", system: str | None = None) -> str:
    mensagens = []
    if system:
        mensagens.append({"role": "system", "content": system})
    mensagens.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": mensagens, "stream": True}

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"},
        method="POST",
    )
    partes: list[str] = []
    with urllib.request.urlopen(req, timeout=120) as resp:
        for linha in resp:
            linha = linha.decode("utf-8").strip()
            if not linha.startswith("data:"):
                continue
            dado = linha[5:].strip()
            if dado == "[DONE]":
                break
            delta = json.loads(dado)["choices"][0].get("delta", {})
            pedaco = delta.get("content")
            if pedaco:
                partes.append(pedaco)
                print(pedaco, end="", flush=True)
    print()
    return "".join(partes)


if __name__ == "__main__":
    texto = sys.argv[1] if len(sys.argv) > 1 else "Explica o que é uma API em 2 frases."
    chat_stream(texto, system="Responde em português, de forma concisa.")
