#!/usr/bin/env python3
"""Geração e edição de imagens — /v1/images/generations e /v1/images/edits.

Modelos atuais: gpt-image-2.5/2.6 (sunburst | flare), gpt-image-2, gpt-image-1.5.
A key vem SEMPRE de OPENAI_API_KEY no ambiente; sem key, recusa-se a correr.
"""
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request
import uuid

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")


def key() -> str:
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        sys.exit('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" e volte a correr')
    return k


def _post(caminho: str, payload: dict | None = None, campos=None, ficheiros=None, timeout=300) -> dict:
    headers = {"Authorization": f"Bearer {key()}"}
    if ficheiros:  # multipart/form-data construído à mão (stdlib)
        boundary = "----img-" + uuid.uuid4().hex
        partes: list[bytes] = []
        for nome, valor in (campos or {}).items():
            partes.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{nome}\"\r\n\r\n{valor}\r\n".encode())
        for nome, (fname, dados, tipo) in ficheiros.items():
            partes.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{nome}\"; filename=\"{fname}\"\r\n"
                          f"Content-Type: {tipo}\r\n\r\n".encode())
            partes.append(dados)
            partes.append(b"\r\n")
        partes.append(f"--{boundary}--\r\n".encode())
        body = b"".join(partes)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API_BASE}{caminho}", data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def gerar(prompt: str, model: str = "gpt-image-2", size: str = "1024x1024",
          quality: str = "high", n: int = 1, out: str = "out") -> list[str]:
    r = _post("/images/generations", {
        "model": model, "prompt": prompt, "n": n, "size": size,
        "quality": quality, "output_format": "png",
    })
    return _guardar(r, out)


def editar(prompt: str, caminho_imagem: str, model: str = "gpt-image-2",
           size: str = "1024x1024", out: str = "out") -> list[str]:
    with open(caminho_imagem, "rb") as f:
        dados = f.read()
    tipo = mimetypes.guess_type(caminho_imagem)[0] or "image/png"
    r = _post("/images/edits",
              campos={"prompt": prompt, "model": model, "size": size, "n": "1"},
              ficheiros={"image": (os.path.basename(caminho_imagem), dados, tipo)})
    return _guardar(r, out)


def _guardar(r: dict, out: str) -> list[str]:
    os.makedirs(out, exist_ok=True)
    ficheiros = []
    for i, item in enumerate(r.get("data", [])):
        nome = os.path.join(out, f"imagem-{int(time.time())}-{i}.png")
        if item.get("b64_json"):
            with open(nome, "wb") as f:
                f.write(base64.b64decode(item["b64_json"]))
        elif item.get("url"):  # modelos antigos (dall-e) devolvem URL temporária
            with open(nome, "wb") as f:
                f.write(urllib.request.urlopen(item["url"], timeout=120).read())
        ficheiros.append(nome)
    return ficheiros


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else "gerar"
    if acao == "editar":
        print("\n".join(editar(sys.argv[2], sys.argv[3])))
    else:
        print("\n".join(gerar(sys.argv[2] if len(sys.argv) > 2 else
                              "Um logótipo minimalista de capivara robótica, fundo escuro, estilo neon suave")))
