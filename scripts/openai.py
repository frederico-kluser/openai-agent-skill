#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openai.py — CLI da openai-agent-skill: acesso TOTAL à API da OpenAI.

Stdlib apenas (sem dependências). A key vem SEMPRE das variáveis de ambiente
(OPENAI_API_KEY, ou OPENAI_API_KEY_1..9 para várias contas); sem key no
ambiente o script RECUSA-SE a trabalhar (exit 2). O valor da key nunca é
impresso, logado nem escrito em ficheiro.

Comandos:
  status                    estado da key no ambiente (sem segredos) + ping
  models                    lista os modelos disponíveis (GET /v1/models)
  chat "texto"              Chat Completions (POST /v1/chat/completions)
  responses "texto"         Responses API (POST /v1/responses)
  image "prompt"            geração de imagem (POST /v1/images/generations)
  image-edit "prompt"       edição de imagem (POST /v1/images/edits)
  tts "texto"               fala / TTS (POST /v1/audio/speech)
  transcribe <ficheiro>     transcrição de áudio (POST /v1/audio/transcriptions)
  translate <ficheiro>      tradução de áudio (POST /v1/audio/translations)
  embed "texto"             embeddings (POST /v1/embeddings)
  moderate "texto"          moderação (POST /v1/moderations)
  selftest                  verificação determinística OFFLINE

Contrato de erros:  `Erro: <o quê> — Solução: <o que fazer>`  + exit ≠ 0.
Exit codes: 0 sucesso · 1 erro da API · 2 uso inválido / key em falta ·
            3 ferramenta em falta · 4 rede/timeout.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import io
import json
import mimetypes
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
USER_AGENT = "openai-agent-skill/1.0 (+https://github.com/frederico-kluser/openai-agent-skill)"
TIMEOUT = int(os.environ.get("OPENAI_TIMEOUT", "120"))
MAX_RETRIES = 3
MAX_BYTES = int(os.environ.get("OPENAI_MAX_BYTES", "65536"))  # porta de saída p/ agentes

EXIT_OK, EXIT_API, EXIT_USAGE, EXIT_TOOL, EXIT_NET = 0, 1, 2, 3, 4

MODELOS_TTS_VOZES = (
    "alloy", "ash", "ballad", "coral", "echo", "fable", "marin", "cedar",
    "nova", "onyx", "sage", "shimmer",
)


# --------------------------------------------------------------------------
# Erros e redação de segredos
# --------------------------------------------------------------------------

class ErroSkill(Exception):
    """Erro com contrato `Erro: … — Solução: …`."""

    def __init__(self, codigo: int, erro: str, solucao: str):
        super().__init__(erro)
        self.codigo = codigo
        self.erro = erro
        self.solucao = solucao


def falhar(e: ErroSkill) -> "int":
    print(f"Erro: {e.erro} — Solução: {e.solucao}", file=sys.stderr)
    return e.codigo


_PADRAO_SEGREDO = re.compile(
    r"(sk-[A-Za-z0-9_\-]{2,}"          # chaves estilo OpenAI (mesmo curtas)
    r"|Bearer\s+[A-Za-z0-9_\-\.=]+)"   # qualquer token em cabeçalho Authorization
)


def redigir(texto: str) -> str:
    """Remove qualquer ocorrência de material de chave do texto dado."""
    if not texto:
        return texto
    for nome in _noms_de_chave():
        val = os.environ.get(nome, "")
        if val and val in texto:
            texto = texto.replace(val, f"[REDACTED:{nome}]")
    return _PADRAO_SEGREDO.sub("[REDACTED]", texto)


def _noms_de_chave():
    nomes = ["OPENAI_API_KEY"]
    nomes += [f"OPENAI_API_KEY_{i}" for i in range(1, 10)]
    return nomes


def mascara(ref: str) -> str:
    """Mascara uma referência de chave (nunca mostra o meio)."""
    if not ref:
        return "(vazia)"
    if len(ref) <= 8:
        return "…" + ref[-2:]
    return ref[:3] + "…" + ref[-4:]


# --------------------------------------------------------------------------
# Key: SEMPRE do ambiente; sem key não há trabalho
# --------------------------------------------------------------------------

def obter_chave() -> "tuple[str, str]":
    """Devolve (nome_da_variavel, valor). Recusa sem key no ambiente."""
    for nome in _noms_de_chave():
        val = os.environ.get(nome, "").strip()
        if val:
            return nome, val
    raise ErroSkill(
        EXIT_USAGE,
        "não há OPENAI_API_KEY nas variáveis de ambiente — a skill recusa-se a trabalhar sem a key",
        'defina a key no ambiente (ex.: PowerShell: [Environment]::SetEnvironmentVariable("OPENAI_API_KEY","sk-…","User"); '
        'bash: export OPENAI_API_KEY="sk-…") e volte a correr; nunca escreva a key em ficheiros nem em código',
    )


# --------------------------------------------------------------------------
# HTTP (urllib, com retentativas para 429/5xx)
# --------------------------------------------------------------------------

def _montar_multipart(campos: "dict[str, str]", ficheiros: "dict[str, tuple[str, bytes, str]]") -> "tuple[bytes, str]":
    """Constrói um corpo multipart/form-data (stdlib)."""
    boundary = "----openai-agent-skill-" + uuid.uuid4().hex
    partes: "list[bytes]" = []
    for nome, valor in campos.items():
        if valor is None:
            continue
        partes.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{nome}"\r\n\r\n'
                f"{valor}\r\n"
            ).encode("utf-8")
        )
    for nome, (filename, dados, content_type) in ficheiros.items():
        partes.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{nome}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        partes.append(dados)
        partes.append(b"\r\n")
    partes.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(partes), f"multipart/form-data; boundary={boundary}"


def _http(
    metodo: str,
    caminho: str,
    payload: "dict | None" = None,
    campos: "dict | None" = None,
    ficheiros: "dict | None" = None,
    binario: bool = False,
    stream: bool = False,
    timeout: int = TIMEOUT,
):
    """Faz um pedido à API. Devolve dict (JSON), bytes (binário) ou itera SSE."""
    _, key = obter_chave()
    url = API_BASE.rstrip("/") + caminho
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": USER_AGENT,
    }
    body = None
    if ficheiros or campos:
        body, ctype = _montar_multipart(campos or {}, ficheiros or {})
        headers["Content-Type"] = ctype
    elif payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    ultimo_erro = None
    for tentativa in range(MAX_RETRIES + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method=metodo)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            if stream:
                return _iterar_sse(resp)
            dados = resp.read()
            if binario:
                return dados
            return json.loads(dados.decode("utf-8")) if dados else {}
        except urllib.error.HTTPError as e:
            bruto = e.read() if hasattr(e, "read") else b""
            try:
                detalhe = json.loads(bruto.decode("utf-8"))
                msg = detalhe.get("error", {}).get("message", "") or str(detalhe)
            except Exception:
                msg = redigir(bruto.decode("utf-8", "replace")[:500])
            codigo = e.code
            if codigo in (429, 500, 502, 503, 504) and tentativa < MAX_RETRIES:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                espera = float(retry_after) if retry_after and str(retry_after).replace(".", "", 1).isdigit() else min(2 ** tentativa + random.random(), 30)
                time.sleep(espera)
                ultimo_erro = (codigo, msg)
                continue
            raise _mapear_http(codigo, msg)
        except urllib.error.URLError as e:
            ultimo_erro = (0, str(getattr(e, "reason", e)))
            if tentativa < MAX_RETRIES:
                time.sleep(min(2 ** tentativa + random.random(), 30))
                continue
            raise ErroSkill(EXIT_NET, f"rede/timeout após {MAX_RETRIES + 1} tentativas: {redigir(ultimo_erro[1])}",
                            "verifique a ligação à internet e o firewall; aumente o timeout com --timeout")
        except TimeoutError:
            if tentativa < MAX_RETRIES:
                time.sleep(2 ** tentativa)
                continue
            raise ErroSkill(EXIT_NET, f"timeout após {MAX_RETRIES + 1} tentativas",
                            "aumente o timeout com --timeout (segundos) ou tente com um ficheiro/pedido menor")
    codigo, msg = ultimo_erro
    raise _mapear_http(codigo, msg)


def _mapear_http(codigo: int, msg: str) -> ErroSkill:
    msg = redigir(msg or "")
    tabela = {
        400: ("pedido inválido (400)", f"corrija os parâmetros — a API disse: {msg or 'sem detalhe'}"),
        401: ("key inválida ou sem permissão (401)", "verifique se a OPENAI_API_KEY no ambiente é válida e ativa (`status`)"),
        403: ("pedido proibido pela política da OpenAI (403)", "ajuste o conteúdo/pedido; veja as políticas de uso da OpenAI"),
        404: ("recurso inexistente (404)", "confirme o nome do modelo/endpoint com `models` ou a documentação"),
        413: ("pedido demasiado grande (413)", "reduza o tamanho do ficheiro ou do texto"),
        429: ("rate limit ou quota esgotada (429)", "aguarde (Retry-After) ou aumente o tier da organização em platform.openai.com"),
        500: ("erro interno da OpenAI (500)", "tente novamente passados segundos"),
        503: ("serviço indisponível (503)", "tente novamente passados minutos"),
    }
    if codigo in tabela:
        erro, solucao = tabela[codigo]
        return ErroSkill(EXIT_API, f"{erro} — {msg}".strip(" —"), solucao)
    return ErroSkill(EXIT_API, f"erro HTTP {codigo}: {msg}", "veja https://platform.openai.com/docs/errors")


def _iterar_sse(resp):
    """Itera eventos Server-Sent Events de um stream HTTP."""
    try:
        for linha in resp:
            linha = linha.decode("utf-8", "replace").strip()
            if not linha or not linha.startswith("data:"):
                continue
            dado = linha[5:].strip()
            if dado == "[DONE]":
                break
            try:
                yield json.loads(dado)
            except json.JSONDecodeError:
                continue
    finally:
        try:
            resp.close()
        except Exception:
            pass


def _limitar(texto: str) -> str:
    """Porta de orçamento de contexto: nunca satura a janela do modelo."""
    raw = texto.encode("utf-8")
    if len(raw) <= MAX_BYTES:
        return texto
    corte = raw[:MAX_BYTES].decode("utf-8", "ignore")
    return corte + f"\n… [truncado a {MAX_BYTES} bytes; use --max-bytes para alargar]"


def _emitir(obj, texto: str, args) -> int:
    if getattr(args, "json", False):
        print(_limitar(json.dumps(obj, ensure_ascii=False, indent=2)))
    else:
        print(_limitar(texto))
    return EXIT_OK


# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------

def cmd_status(args) -> int:
    nomes = [n for n in _noms_de_chave() if os.environ.get(n, "").strip()]
    if not nomes:
        return falhar(ErroSkill(
            EXIT_USAGE,
            "não há OPENAI_API_KEY nas variáveis de ambiente",
            'defina a key no ambiente (ex.: $env:OPENAI_API_KEY="sk-…" ou export OPENAI_API_KEY="sk-…")',
        ))
    linhas = [f"{n} = {mascara(os.environ[n].strip())}" for n in nomes]
    print("Key no ambiente (sempre do ambiente; nunca de ficheiros):")
    for l in linhas:
        print(f"  {l}")
    if args.ping:
        try:
            r = _http("GET", "/models")
            print(f"Ping OK — {len(r.get('data', []))} modelos disponíveis em {API_BASE}")
        except ErroSkill as e:
            return falhar(e)
    else:
        print("Ping: omitido (use `status --ping` para validar ao vivo, sem custo)")
    return EXIT_OK


def cmd_models(args) -> int:
    r = _http("GET", "/models")
    ids = sorted(m["id"] for m in r.get("data", []))
    if args.filter:
        ids = [i for i in ids if args.filter.lower() in i.lower()]
    return _emitir({"data": ids, "total": len(ids)}, "\n".join(ids), args)


def _mensagens(args, prompt: str) -> "list[dict]":
    msgs = []
    if args.system:
        msgs.append({"role": "system", "content": args.system})
    if args.ficheiro:
        with open(args.ficheiro, "r", encoding="utf-8") as f:
            prompt = f.read()
    msgs.append({"role": "user", "content": prompt})
    return msgs


def cmd_chat(args) -> int:
    payload = {
        "model": args.model,
        "messages": _mensagens(args, args.prompt),
    }
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.max_tokens:
        payload["max_completion_tokens"] = args.max_tokens
    if args.stream:
        payload["stream"] = True
        resposta = _http("POST", "/chat/completions", payload, stream=True, timeout=args.timeout)
        partes = []
        for ev in resposta:
            delta = ev.get("choices", [{}])[0].get("delta", {})
            pedaco = delta.get("content")
            if pedaco:
                partes.append(pedaco)
                if not args.json:
                    print(pedaco, end="", flush=True)
        if not args.json:
            print()
        return _emitir({"model": args.model, "texto": "".join(partes)}, "".join(partes), args)
    r = _http("POST", "/chat/completions", payload, timeout=args.timeout)
    texto = r.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    return _emitir(r, texto, args)


def cmd_responses(args) -> int:
    payload = {"model": args.model, "input": args.prompt}
    if args.system:
        payload["instructions"] = args.system
    if args.max_tokens:
        payload["max_output_tokens"] = args.max_tokens
    r = _http("POST", "/responses", payload, timeout=args.timeout)
    texto = r.get("output_text") or ""
    if not texto:
        for item in r.get("output", []):
            for parte in item.get("content", []):
                if parte.get("type") in ("output_text", "text"):
                    texto += parte.get("text", "")
    return _emitir(r, texto, args)


def cmd_image(args) -> int:
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "n": args.n,
        "size": args.size,
    }
    if args.quality:
        payload["quality"] = args.quality
    if args.output_format:
        payload["output_format"] = args.output_format
    r = _http("POST", "/images/generations", payload, timeout=max(args.timeout, 300))
    dados = r.get("data", [])
    if not dados:
        return falhar(ErroSkill(EXIT_API, "a API não devolveu imagens", "reformule o prompt ou veja o campo `error` da resposta"))
    geradas = []
    for i, item in enumerate(dados):
        ext = args.output_format or "png"
        nome = args.out or os.path.join("out", f"imagem-{int(time.time())}-{i}.{ext}")
        os.makedirs(os.path.dirname(nome) or ".", exist_ok=True)
        if item.get("b64_json"):
            with open(nome, "wb") as f:
                f.write(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            with open(nome, "wb") as f:
                f.write(_baixar(item["url"], args.timeout))
        geradas.append(nome)
    return _emitir({"imagens": geradas}, "\n".join(geradas), args)


def _baixar(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def cmd_image_edit(args) -> int:
    if not args.image or not os.path.isfile(args.image):
        return falhar(ErroSkill(EXIT_USAGE, f"não encontro a imagem de entrada: {args.image!r}",
                                "indique um caminho de ficheiro válido com --image <ficheiro>"))
    with open(args.image, "rb") as f:
        dados = f.read()
    tipo = mimetypes.guess_type(args.image)[0] or "image/png"
    campos = {"prompt": args.prompt, "model": args.model, "n": str(args.n), "size": args.size}
    ficheiros = {"image": (os.path.basename(args.image), dados, tipo)}
    r = _http("POST", "/images/edits", campos=campos, ficheiros=ficheiros, timeout=max(args.timeout, 300))
    out = []
    for i, item in enumerate(r.get("data", [])):
        nome = args.out or os.path.join("out", f"editada-{int(time.time())}-{i}.png")
        os.makedirs(os.path.dirname(nome) or ".", exist_ok=True)
        with open(nome, "wb") as f:
            f.write(base64.b64decode(item.get("b64_json", "")) if item.get("b64_json") else _baixar(item.get("url", ""), args.timeout))
        out.append(nome)
    return _emitir({"imagens": out}, "\n".join(out), args)


def cmd_tts(args) -> int:
    if args.voice not in MODELOS_TTS_VOZES:
        print(f"Aviso: voz {args.voice!r} fora da lista conhecida ({', '.join(MODELOS_TTS_VOZES)}); a API pode recusar.", file=sys.stderr)
    payload = {
        "model": args.model,
        "input": args.texto,
        "voice": args.voice,
        "response_format": args.format,
    }
    if args.speed:
        payload["speed"] = args.speed
    if args.instructions:
        payload["instructions"] = args.instructions
    audio = _http("POST", "/audio/speech", payload, binario=True, timeout=max(args.timeout, 300))
    nome = args.out or os.path.join("out", f"fala-{int(time.time())}.{args.format}")
    os.makedirs(os.path.dirname(nome) or ".", exist_ok=True)
    with open(nome, "wb") as f:
        f.write(audio)
    return _emitir({"ficheiro": nome, "bytes": len(audio), "formato": args.format}, nome, args)


def _upload_audio(caminho: str, args, endpoint: str, extra: "dict | None" = None):
    if not os.path.isfile(caminho):
        raise ErroSkill(EXIT_USAGE, f"não encontro o ficheiro de áudio: {caminho!r}",
                        "indique um caminho válido (ex.: transcribe ./som.mp3)")
    with open(caminho, "rb") as f:
        dados = f.read()
    tipo = mimetypes.guess_type(caminho)[0] or "audio/mpeg"
    campos = {"model": args.model}
    if extra:
        campos.update({k: v for k, v in extra.items() if v is not None})
    ficheiros = {"file": (os.path.basename(caminho), dados, tipo)}
    return _http("POST", endpoint, campos=campos, ficheiros=ficheiros, timeout=max(args.timeout, 600))


def cmd_transcribe(args) -> int:
    extra = {}
    if args.language:
        extra["language"] = args.language
    if args.response_format:
        extra["response_format"] = args.response_format
    if args.timestamp:
        extra["timestamp_granularities[]"] = "word"
    r = _upload_audio(args.ficheiro, args, "/audio/transcriptions", extra)
    if isinstance(r, dict):
        return _emitir(r, r.get("text", json.dumps(r, ensure_ascii=False)), args)
    return _emitir({"texto": r}, r, args)


def cmd_translate(args) -> int:
    r = _upload_audio(args.ficheiro, args, "/audio/translations", {"response_format": args.response_format} if args.response_format else None)
    if isinstance(r, dict):
        return _emitir(r, r.get("text", json.dumps(r, ensure_ascii=False)), args)
    return _emitir({"texto": r}, r, args)


def cmd_embed(args) -> int:
    payload = {"model": args.model, "input": args.textos if args.multi else args.texto}
    r = _http("POST", "/embeddings", payload, timeout=args.timeout)
    vetores = [d.get("embedding", []) for d in r.get("data", [])]
    resumo = {"model": args.model, "n": len(vetores), "dimensoes": len(vetores[0]) if vetores else 0}
    if args.json:
        return _emitir(r, "", args)
    return _emitir(resumo, f"{resumo['n']} vetor(es) com {resumo['dimensoes']} dimensões (modelo {args.model})", args)


def cmd_moderate(args) -> int:
    payload = {"input": args.texto}
    if args.model:
        payload["model"] = args.model
    r = _http("POST", "/moderations", payload, timeout=args.timeout)
    res = (r.get("results") or [{}])[0]
    linhas = [f"flagged: {res.get('flagged')}"]
    for cat, val in sorted((res.get("categories") or {}).items()):
        if val:
            linhas.append(f"  {cat}: {val}")
    return _emitir(r, "\n".join(linhas), args)


# --------------------------------------------------------------------------
# Selftest OFFLINE (determinístico, sem rede)
# --------------------------------------------------------------------------

def selftest() -> int:
    cenarios = []
    fake_resposta = {"data": [{"id": "gpt-test"}]}

    def fake_http(metodo, caminho, **kw):
        fake_http.chamadas.append((metodo, caminho, kw))
        return fake_resposta

    fake_http.chamadas = []

    # 1 · Sem key no ambiente → RECUSA obrigatória (exit 2)
    guarda = {n: os.environ.pop(n, None) for n in _noms_de_chave()}
    try:
        try:
            obter_chave()
            cenarios.append(("sem key recusa", False, "devolveu key sem haver key no ambiente"))
        except ErroSkill as e:
            cenarios.append(("sem key recusa", e.codigo == EXIT_USAGE and "Solução" not in e.solucao, f"exit {e.codigo}"))
    finally:
        for n, v in guarda.items():
            if v is not None:
                os.environ[n] = v

    # 2 · Com key no ambiente → funciona e deteta o nome
    os.environ.setdefault("OPENAI_API_KEY", "sk-teste-ficticia-nao-usar")
    try:
        nome, val = obter_chave()
        cenarios.append(("key vem do ambiente", nome == "OPENAI_API_KEY" and val.startswith("sk-"), nome))
    except ErroSkill as e:
        cenarios.append(("key vem do ambiente", False, str(e)))

    # 3 · Redação: o valor da key nunca aparece em texto
    sujo = f"falha com Bearer {os.environ['OPENAI_API_KEY']} no cabeçalho"
    limpo = redigir(sujo)
    cenarios.append(("redação de segredos", os.environ["OPENAI_API_KEY"] not in limpo and "[REDACTED:" in limpo, limpo[:40]))

    # 4 · Mascara referências sem expor o meio
    m = mascara(os.environ["OPENAI_API_KEY"])
    cenarios.append(("mascaramento", os.environ["OPENAI_API_KEY"] not in m, m))

    # 5 · Multipart: boundary presente e ficheiro embutido
    corpo, ctype = _montar_multipart({"model": "whisper-1"}, {"file": ("a.mp3", b"ID3dados", "audio/mpeg")})
    ok = b"----openai-agent-skill-" in corpo and b"ID3dados" in corpo and ctype.startswith("multipart/form-data")
    cenarios.append(("multipart montado", ok, ctype))

    # 6 · URL do endpoint
    cenarios.append(("API_BASE é https", API_BASE.startswith("https://"), API_BASE))

    # 7 · Mapeamento de erros HTTP
    e429 = _mapear_http(429, "rate limit")
    e401 = _mapear_http(401, "invalid api key sk-abc")
    cenarios.append(("429 → exit 1 com solução", e429.codigo == EXIT_API and "tier" in e429.solucao, e429.erro))
    cenarios.append(("401 → exit 1 sem ecoar key", e401.codigo == EXIT_API and "sk-abc" not in e401.erro, e401.erro))

    # 8 · Porta de orçamento de contexto
    global MAX_BYTES
    guarda_bytes = MAX_BYTES
    MAX_BYTES = 20
    truncado = _limitar("abcdefghij" * 10)
    MAX_BYTES = guarda_bytes
    cenarios.append(("truncagem de saída", len(truncado.encode()) < 400 and "truncado" in truncado, str(len(truncado))))

    # 9 · Contrato: nenhuma função principal corre sem key (com key falsa há rede; usamos cmd_status --ping falso)
    try:
        fake_http.chamadas = []
        orig = globals()["_http"]
        globals()["_http"] = fake_http
        class A: ping = False
        with contextlib.redirect_stdout(io.StringIO()):
            r = cmd_status(A)
        globals()["_http"] = orig
        cenarios.append(("status sem ping não toca na rede", r == EXIT_OK and not fake_http.chamadas, f"chamadas={len(fake_http.chamadas)}"))
    except ErroSkill as e:
        globals()["_http"] = orig
        cenarios.append(("status sem ping não toca na rede", False, str(e)))

    # 10 · ErroSkill tem contrato `Erro: — Solução:`
    cenarios.append(("contrato de erros", all(x.erro and x.solucao for x in (e429, e401)), "ok"))

    falhas = 0
    print("Selftest OFFLINE da openai-agent-skill")
    print("-" * 60)
    for nome, ok, detalhe in cenarios:
        marca = "PASS" if ok else "FAIL"
        if not ok:
            falhas += 1
        print(f"[{marca}] {nome} · {redigir(str(detalhe))[:80]}")
    print("-" * 60)
    print(f"{len(cenarios) - falhas}/{len(cenarios)} PASS")
    return EXIT_OK if falhas == 0 else EXIT_API


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="openai.py", description="CLI da openai-agent-skill — API OpenAI (key sempre do ambiente).")
    sub = p.add_subparsers(dest="comando", required=True)

    sp = sub.add_parser("status", help="estado da key no ambiente (sem segredos)")
    sp.add_argument("--ping", action="store_true", help="valida ao vivo com GET /models (sem custo)")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("models", help="lista modelos disponíveis")
    sp.add_argument("--filter", help="filtra por substring")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_models, model=None, timeout=TIMEOUT)

    def comuns_chat(sp):
        sp.add_argument("prompt", nargs="?", default="", help="texto do pedido (ou --ficheiro)")
        sp.add_argument("--ficheiro", help="lê o prompt de um ficheiro de texto")
        sp.add_argument("--system", help="mensagem de sistema")
        sp.add_argument("--model", default="gpt-5.2")
        sp.add_argument("--temperature", type=float, default=None)
        sp.add_argument("--max-tokens", type=int, default=0)
        sp.add_argument("--timeout", type=int, default=TIMEOUT)
        sp.add_argument("--json", action="store_true", help="saída JSON integral")

    sp = sub.add_parser("chat", help="Chat Completions")
    comuns_chat(sp)
    sp.add_argument("--stream", action="store_true", help="streaming SSE")
    sp.set_defaults(fn=cmd_chat)

    sp = sub.add_parser("responses", help="Responses API")
    comuns_chat(sp)
    sp.set_defaults(fn=cmd_responses)

    sp = sub.add_parser("image", help="geração de imagem")
    sp.add_argument("prompt")
    sp.add_argument("--model", default="gpt-image-2")
    sp.add_argument("--n", type=int, default=1)
    sp.add_argument("--size", default="1024x1024")
    sp.add_argument("--quality", default="", help="ex.: high | medium | low | auto")
    sp.add_argument("--output-format", default="png", choices=("png", "jpeg", "webp", "svg", "gif"), help="svg/gif só em gerações com gpt-image-2.6")
    sp.add_argument("--out", help="ficheiro de saída")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_image)

    sp = sub.add_parser("image-edit", help="edição de imagem")
    sp.add_argument("prompt")
    sp.add_argument("--image", required=True, help="imagem de entrada")
    sp.add_argument("--model", default="gpt-image-2")
    sp.add_argument("--n", type=int, default=1)
    sp.add_argument("--size", default="1024x1024")
    sp.add_argument("--out", help="ficheiro de saída")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_image_edit)

    sp = sub.add_parser("tts", help="texto → fala")
    sp.add_argument("texto")
    sp.add_argument("--model", default="gpt-4o-mini-tts")
    sp.add_argument("--voice", default="alloy")
    sp.add_argument("--format", default="mp3", choices=("mp3", "wav", "opus", "flac", "pcm"))
    sp.add_argument("--speed", type=float, default=0)
    sp.add_argument("--instructions", help="estilo da fala (modelos gpt-4o-mini-tts)")
    sp.add_argument("--out", help="ficheiro de saída")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_tts)

    sp = sub.add_parser("transcribe", help="áudio → texto")
    sp.add_argument("ficheiro")
    sp.add_argument("--model", default="gpt-transcribe", help="recomendado; whisper-1 p/ srt/vtt até 2027-02-26")
    sp.add_argument("--language", help="código ISO, ex.: pt, en, es")
    sp.add_argument("--response-format", default="json", choices=("json", "text", "verbose_json", "srt", "vtt"))
    sp.add_argument("--timestamp", action="store_true", help="inclui timestamps por palavra")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_transcribe)

    sp = sub.add_parser("translate", help="áudio → inglês")
    sp.add_argument("ficheiro")
    sp.add_argument("--model", default="whisper-1")
    sp.add_argument("--response-format", default="json")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_translate)

    sp = sub.add_parser("embed", help="texto → vetores")
    sp.add_argument("texto", nargs="?", default="")
    sp.add_argument("--multi", action="store_true", help="texto é uma lista JSON de strings")
    sp.add_argument("--model", default="text-embedding-3-small")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_embed)

    sp = sub.add_parser("moderate", help="moderação de conteúdo")
    sp.add_argument("texto")
    sp.add_argument("--model", default="omni-moderation-latest")
    sp.add_argument("--timeout", type=int, default=TIMEOUT)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_moderate)

    sp = sub.add_parser("selftest", help="verificação determinística OFFLINE")
    sp.set_defaults(fn=lambda args: selftest())

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except ErroSkill as e:
        return falhar(e)
    except FileNotFoundError as e:
        return falhar(ErroSkill(EXIT_USAGE, f"ficheiro não encontrado: {e.filename}", "confirme o caminho do ficheiro"))
    except KeyboardInterrupt:
        print("\nErro: interrompido pelo utilizador — Solução: volte a correr quando quiser", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
