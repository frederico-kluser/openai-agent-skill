#!/usr/bin/env python3
"""Texto para fala (TTS) — POST /v1/audio/speech.

Modelos: gpt-4o-mini-tts (voz + instruções de estilo), tts-1, tts-1-hd.
Vozes: alloy, ash, ballad, coral, echo, fable, marin, cedar, nova, onyx, sage, shimmer.
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


def falar(texto: str, out: str = "fala.mp3", model: str = "gpt-4o-mini-tts",
          voice: str = "alloy", formato: str = "mp3",
          instrucoes: str | None = "Fala natural, ritmo calmo e acolhedor.") -> str:
    payload = {"model": model, "input": texto, "voice": voice, "response_format": formato}
    if instrucoes and model.startswith("gpt-4o-mini-tts"):
        payload["instructions"] = instrucoes
    req = urllib.request.Request(
        f"{API_BASE}/audio/speech",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        audio = resp.read()
    with open(out, "wb") as f:
        f.write(audio)
    return out


if __name__ == "__main__":
    texto = sys.argv[1] if len(sys.argv) > 1 else "Olá! Esta voz foi gerada pela API da OpenAI."
    print(falar(texto, out=sys.argv[2] if len(sys.argv) > 2 else "fala.mp3"))
