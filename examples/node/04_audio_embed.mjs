// TTS, transcrição, embeddings e moderação (Node 18+ com fetch/FormData nativos).
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

async function erro(resp) {
  const t = await resp.text();
  let msg = t;
  try { msg = JSON.parse(t).error?.message ?? t; } catch {}
  console.error(`Erro: HTTP ${resp.status} — Solução: ${msg}`);
  process.exit(1);
}

/** Texto → fala. Vozes: alloy, ash, ballad, coral, echo, fable, marin, cedar, nova, onyx, sage, shimmer. */
export async function falar(texto, { out = "fala.mp3", model = "gpt-4o-mini-tts", voice = "alloy", formato = "mp3", instructions } = {}) {
  const payload = { model, input: texto, voice, response_format: formato };
  if (instructions && model.startsWith("gpt-4o-mini-tts")) payload.instructions = instructions;
  const resp = await fetch(`${API_BASE}/audio/speech`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(300_000),
  });
  if (!resp.ok) await erro(resp);
  await writeFile(out, Buffer.from(await resp.arrayBuffer()));
  return out;
}

/** Áudio → texto. Modelos: gpt-transcribe (recomendado), whisper-1 (srt/vtt), gpt-4o-transcribe*. */
export async function transcrever(caminho, { model = "gpt-transcribe", language } = {}) {
  const form = new FormData();
  form.append("model", model);
  if (language) form.append("language", language);
  form.append("response_format", "json");
  form.append("file", new Blob([await readFile(caminho)]), basename(caminho));
  const resp = await fetch(`${API_BASE}/audio/transcriptions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}` },
    body: form,
    signal: AbortSignal.timeout(600_000),
  });
  if (!resp.ok) await erro(resp);
  return (await resp.json()).text;
}

/** Textos → vetores. */
export async function embed(textos, { model = "text-embedding-3-small" } = {}) {
  const resp = await fetch(`${API_BASE}/embeddings`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, input: textos }),
  });
  if (!resp.ok) await erro(resp);
  return (await resp.json()).data.sort((a, b) => a.index - b.index).map((d) => d.embedding);
}

/** Moderação de conteúdo. */
export async function moderar(texto, { model = "omni-moderation-latest" } = {}) {
  const resp = await fetch(`${API_BASE}/moderations`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, input: texto }),
  });
  if (!resp.ok) await erro(resp);
  return (await resp.json()).results[0];
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [cmd, ...rest] = process.argv.slice(2);
  if (cmd === "tts") console.log(await falar(rest[0] ?? "Olá! Esta voz foi gerada pela API da OpenAI."));
  else if (cmd === "transcribe") console.log(await transcrever(rest[0]));
  else if (cmd === "embed") console.log((await embed(rest)).length + " vetores gerados");
  else if (cmd === "moderate") console.log(JSON.stringify(await moderar(rest.join(" ")), null, 2));
  else console.log("Uso: node 04_audio_embed.mjs [tts|transcribe|embed|moderate] ...");
}
