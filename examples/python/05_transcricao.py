#!/usr/bin/env python3
"""Transcrição e tradução de áudio — /v1/audio/transcriptions|translations.

Modelos: gpt-transcribe (RECOMENDADO), whisper-1 (único com srt/vtt/verbose_json),
gpt-4o-transcribe(-diarize), gpt-4o-mini-transcribe (estes três saem a 2027-02-26).
Aceita mp3, mp4, mpeg, mpga, m4a, wav, webm (até 25 MB).
A key vem SEMPRE de OPENAI_API_KEY no ambiente; sem key, recusa-se a correr.
"""
import json
import mimetypes
import os
import sys
import urllib.request
import uuid

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")


def key() -> str:
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        sys.exit('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" e volte a correr')
    return k


def _upload(caminho: str, endpoint: str, campos: dict, timeout=600) -> dict | str:
    if not os.path.isfile(caminho):
        sys.exit(f"Erro: não encontro o ficheiro {caminho!r} — Solução: indique um caminho válido")
    with open(caminho, "rb") as f:
        dados = f.read()
    tipo = mimetypes.guess_type(caminho)[0] or "audio/mpeg"
    boundary = "----audio-" + uuid.uuid4().hex
    partes: list[bytes] = []
    for nome, valor in campos.items():
        if valor is None:
            continue
        partes.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{nome}\"\r\n\r\n{valor}\r\n".encode())
    partes.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(caminho)}\"\r\n"
                  f"Content-Type: {tipo}\r\n\r\n".encode())
    partes.append(dados)
    partes.append(b"\r\n")
    partes.append(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=b"".join(partes),
        headers={"Authorization": f"Bearer {key()}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        bruto = resp.read()
    try:
        return json.loads(bruto)
    except json.JSONDecodeError:
        return bruto.decode("utf-8")


def transcrever(caminho: str, model: str = "gpt-transcribe", language: str | None = None) -> str:
    r = _upload(caminho, "/audio/transcriptions",
                {"model": model, "language": language, "response_format": "json"})
    return r.get("text", str(r)) if isinstance(r, dict) else str(r)


def traduzir(caminho: str, model: str = "whisper-1") -> str:
    """Traduz áudio em qualquer idioma para INGLÊS."""
    r = _upload(caminho, "/audio/translations", {"model": model, "response_format": "json"})
    return r.get("text", str(r)) if isinstance(r, dict) else str(r)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python 05_transcricao.py <audio.mp3> [traduzir]")
    if len(sys.argv) > 2 and sys.argv[2] == "traduzir":
        print(traduzir(sys.argv[1]))
    else:
        print(transcrever(sys.argv[1], language="pt"))
