# Credenciais — a key vive SEMPRE nas variáveis de ambiente

Regra absoluta desta skill: **a `OPENAI_API_KEY` vem das variáveis de ambiente
do sistema e nunca de mais lado nenhum**. Sem key no ambiente, todos os
comandos e exemplos **recusam-se a trabalhar** (exit 2, contrato
`Erro: … — Solução: …`). Nenhum script lê `.env`, ficheiros de configuração,
argumentos de linha de comandos ou chaves embutidas em código.

## Guardar a key no sistema (uma vez)

Windows (PowerShell) — âmbito User (persiste entre sessões):

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-…", "User")
```

Linux/macOS (bash/zsh) — no `~/.bashrc`/`~/.zshrc`:

```bash
export OPENAI_API_KEY="sk-…"
```

Depois **abra um novo terminal** (os processos já abertos não herdam a
mudança) e confirme sem expor o valor:

```bash
python scripts/openai.py status --ping   # mostra só "sk-…últimos4" + ping
```

## Regras

1. **Nunca** imprimir, logar, commitar ou escrever a key em ficheiros — nem em
   `.env` (está no `.gitignore` como rede de segurança, mas não use um).
2. A key é por **projeto** (`sk-proj-…`) e pertence à conta da OpenAI que a
   criou; crie uma key por projeto em <https://platform.openai.com/api-keys>.
3. Todos os scripts mascaram a key (`sk-…últimos4`) e redigem qualquer token
   `sk-…`/`Bearer …` que apareça em mensagens de erro (padrão genérico, para
   nunca ecoar material de chave — mesmo vindo da API).
4. Variáveis opcionais: `OPENAI_ORG_ID` e `OPENAI_PROJECT_ID` fixam
   organização/projeto (os SDKs oficiais enviam os headers
   `OpenAI-Organization`/`OpenAI-Project`); `OPENAI_API_BASE` aponta a API
   compatível alternativa; `OPENAI_TIMEOUT` muda o timeout (s).
5. Várias contas: `OPENAI_API_KEY_1` … `OPENAI_API_KEY_9` são aceites como
   alternativas pela CLI; a primeira preenchida vence.

## Múltiplas chaves / rotação

Diferente da `tavily-agent-skill`, esta skill usa **a key da conta própria**
sem rotação: cada projeto OpenAI tem a sua quota. Se precisar de várias
contas, exporte `OPENAI_API_KEY_1..9` e selecione com a variável pretendida no
ambiente do processo.

## Problemas comuns

| Sintoma | Causa | Correção |
| --- | --- | --- |
| `Erro: não há OPENAI_API_KEY nas variáveis de ambiente` (exit 2) | variável não definida ou terminal antigo | defina como acima e abra novo terminal |
| `key inválida ou sem permissão (401)` | key revogada, errada ou de outro projeto | regenerar em platform.openai.com/api-keys e atualizar a variável |
| `rate limit ou quota esgotada (429)` | tier/quota da organização atingido | esperar o `Retry-After`, ou subir de tier (créditos comprados) |
| `pedido proibido pela política (403)` | conteúdo contra as políticas de uso | ajustar o pedido; ver políticas da OpenAI |
| funciona no terminal e falha no agente/IDE | o processo herdou ambiente antigo | reiniciar o agente/IDE depois de setar a variável |

## Segurança

- A key dá acesso ao seu crédito: trate-a como uma password.
- Se a key aparecer num log, screenshot ou repositório: **revoque-a
  imediatamente** em platform.openai.com e crie outra.
- Em CI/CD use secrets da plataforma (GitHub Actions Secrets, etc.), nunca
  ficheiros do repositório.
