// Chat com streaming — POST /v1/chat/completions (Node 18+ com fetch nativo).
// A key vem SEMPRE de process.env.OPENAI_API_KEY; sem key, o exemplo recusa-se a correr.

const API_BASE = process.env.OPENAI_API_BASE ?? "https://api.openai.com/v1";

function key() {
  const k = (process.env.OPENAI_API_KEY ?? "").trim();
  if (!k) {
    console.error('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" (PowerShell: $env:OPENAI_API_KEY="sk-…") e volte a correr');
    process.exit(2);
  }
  return k;
}

export async function chatStream(prompt, { model = "gpt-5.2", system } = {}) {
  const messages = [];
  if (system) messages.push({ role: "system", content: system });
  messages.push({ role: "user", content: prompt });

  const resp = await fetch(`${API_BASE}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, stream: true }),
  });
  if (!resp.ok) {
    const t = await resp.text();
    console.error(`Erro: HTTP ${resp.status} — Solução: ${(JSON.parse(t).error?.message ?? t)}`);
    process.exit(1);
  }

  let texto = "";
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const linhas = buffer.split("\n");
    buffer = linhas.pop() ?? "";
    for (const linha of linhas) {
      const l = linha.trim();
      if (!l.startsWith("data:")) continue;
      const dado = l.slice(5).trim();
      if (dado === "[DONE]") return texto;
      const delta = JSON.parse(dado).choices?.[0]?.delta?.content;
      if (delta) { texto += delta; process.stdout.write(delta); }
    }
  }
  console.log();
  return texto;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await chatStream(process.argv[2] ?? "Explica o que é uma API em 2 frases.", {
    system: "Responde em português, de forma concisa.",
  });
}
