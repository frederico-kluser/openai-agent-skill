// Responses API com reasoning — POST /v1/responses (Node 18+ com fetch nativo).
// Endpoint recomendado pela OpenAI para novos projetos; a key vem SEMPRE de OPENAI_API_KEY.

const API_BASE = process.env.OPENAI_API_BASE ?? "https://api.openai.com/v1";

function key() {
  const k = (process.env.OPENAI_API_KEY ?? "").trim();
  if (!k) {
    console.error('Erro: sem OPENAI_API_KEY no ambiente — Solução: export OPENAI_API_KEY="sk-…" e volte a correr');
    process.exit(2);
  }
  return k;
}

export async function responder(prompt, { model = "gpt-5.2", instructions, reasoningEffort, maxOutputTokens } = {}) {
  const payload = { model, input: prompt };
  if (instructions) payload.instructions = instructions;
  if (reasoningEffort) payload.reasoning = { effort: reasoningEffort }; // minimal|low|medium|high
  if (maxOutputTokens) payload.max_output_tokens = maxOutputTokens;

  const resp = await fetch(`${API_BASE}/responses`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key()}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const json = await resp.json();
  if (!resp.ok) {
    console.error(`Erro: HTTP ${resp.status} — Solução: ${json.error?.message ?? "veja platform.openai.com/docs/errors"}`);
    process.exit(1);
  }
  return json.output_text ?? json;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const out = await responder(process.argv[2] ?? "Resolve: um comboio parte às 14h e leva 2h30. A que horas chega?", {
    instructions: "És um tutor paciente. Mostra o raciocínio em 1 linha e a resposta final.",
    reasoningEffort: "low",
  });
  console.log(typeof out === "string" ? out : JSON.stringify(out, null, 2));
}
