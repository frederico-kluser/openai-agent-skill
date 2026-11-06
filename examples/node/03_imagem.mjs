// Geração e edição de imagens — /v1/images/generations e /v1/images/edits (Node 18+).
// Modelos atuais: gpt-image-2.5/2.6 (sunburst | flare), gpt-image-2, gpt-image-1.5.
// A key vem SEMPRE de OPENAI_API_KEY; sem key, o exemplo recusa-se a correr.

import { writeFile, readFile } from "node:fs/promises";
import { basename } from "node:path";

const API_BASE = process.env.OPENAI_API_BASE ?? "https://api.openai.com/v1";

function key() {
  const k = (process.env.OPENAI_API_KEY ?? "").trim();
  if (!k) {
    console.error('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" e volte a correr');
    process.exit(2);
  }
  return k;
}

async function postJSON(caminho, payload) {
  const resp = await fetch(`${API_BASE}${caminho}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(300_000),
  });
  const json = await resp.json();
  if (!resp.ok) {
    console.error(`Erro: HTTP ${resp.status} — Solução: ${json.error?.message ?? "veja platform.openai.com/docs/errors"}`);
    process.exit(1);
  }
  return json;
}

export async function gerar(prompt, { model = "gpt-image-2", size = "1024x1024", quality = "high", out = "out" } = {}) {
  const r = await postJSON("/images/generations", { model, prompt, n: 1, size, quality, output_format: "png" });
  return guardar(r, out);
}

export async function editar(prompt, caminhoImagem, { model = "gpt-image-2", size = "1024x1024", out = "out" } = {}) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("model", model);
  form.append("size", size);
  form.append("n", "1");
  const dados = await readFile(caminhoImagem);
  form.append("image", new Blob([dados]), basename(caminhoImagem));
  const resp = await fetch(`${API_BASE}/images/edits`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}` },
    body: form,
    signal: AbortSignal.timeout(300_000),
  });
  const json = await resp.json();
  if (!resp.ok) {
    console.error(`Erro: HTTP ${resp.status} — Solução: ${json.error?.message ?? "veja platform.openai.com/docs/errors"}`);
    process.exit(1);
  }
  return guardar(json, out);
}

async function guardar(r, out) {
  const { mkdir } = await import("node:fs/promises");
  await mkdir(out, { recursive: true });
  const ficheiros = [];
  for (const [i, item] of (r.data ?? []).entries()) {
    const nome = `${out}/imagem-${Date.now()}-${i}.png`;
    const bytes = item.b64_json
      ? Buffer.from(item.b64_json, "base64")
      : Buffer.from(await (await fetch(item.url)).arrayBuffer());
    await writeFile(nome, bytes);
    ficheiros.push(nome);
  }
  return ficheiros;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const ficheiros = process.argv[2] === "editar"
    ? await editar(process.argv[3], process.argv[4])
    : await gerar(process.argv[2] ?? "Um logótipo minimalista de capivara robótica, fundo escuro, estilo neon suave");
  console.log(ficheiros.join("\n"));
}
