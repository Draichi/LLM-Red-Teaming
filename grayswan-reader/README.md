# grayswan-reader

Abre páginas da [Gray Swan Arena](https://app.grayswan.ai) (ou qualquer site com
login) com um navegador controlado (Playwright), reutilizando a sua sessão, e
salva o conteúdo de cada página em **Markdown** — pronto para um agente (Claude,
etc.) ler via `Read`.

```
grayswan-reader/
├── reader.py          # a ferramenta (login | links | fetch | open)
├── browser_profile/   # sessão/cookies do login (NÃO compartilhe esta pasta)
└── pages/             # saída: <titulo>-<hash>.md + manifest.json (índice)
```

Setup já pronto: `.venv/` com Playwright + Chromium instalados.

---

## 1. Login (uma vez — repita só se a sessão expirar)

```bash
.venv/bin/python reader.py login https://app.grayswan.ai
```

Abre uma janela do navegador: faça login normalmente e, quando a página mostrar
você logado, volte ao terminal e pressione **Enter**. Pronto — os outros comandos
rodam sem janela (headless) reusando essa sessão.

## 2. Descobrir as URLs (listagem)

```bash
.venv/bin/python reader.py links "https://app.grayswan.ai/arena" --match challenge
```

Lista todas as URLs da página que casam com `--match` (regex), com o texto do
link ao lado. Rode sem `--match` para ver tudo que existe na página.

## 3. Baixar o conteúdo de todas

```bash
.venv/bin/python reader.py fetch "https://app.grayswan.ai/arena" --match challenge --out pages
```

Extrai os links da listagem, abre **cada um** e salva `pages/<titulo>-<hash>.md`,
mais o índice `pages/manifest.json` (url → arquivo). Páginas já baixadas são
puladas nas próximas execuções (`--force` refaz).

## 4. Uma URL específica

```bash
.venv/bin/python reader.py open "https://app.grayswan.ai/arena/challenge/ipi-black-2026?batchGroupId=..."
```

---

## Opções úteis

| Flag | Default | O que faz |
|---|---|---|
| `--match REGEX` | — | só links cuja URL casa (ex.: `--match "challenge"`) |
| `--exclude REGEX` | — | pula links que casarem |
| `--limit N` | — | no `fetch`: baixa no máx. N páginas nesta execução |
| `--out DIR` | `pages/` | pasta de saída |
| `--settle S` | `2` | espera extra após carregar (SPAs precisam de um pouco) |
| `--delay S` | `1` | pausa entre uma página e outra |
| `--force` | — | rebaixa páginas já salvas |
| `--headed` | — | mostra o navegador (útil para depurar) |
| `--any-origin` | — | inclui links de outros domínios (default: mesmo domínio) |
| `--content-selector SEL` | — | extrai o texto só deste seletor CSS |
| `--wait-selector SEL` | — | espera este elemento aparecer antes de extrair |

## Para agentes (Claude etc.)

1. Rode os comandos acima via Bash (a partir de `Workspace/grayswan-reader/`).
2. Comece por `pages/manifest.json` para ver o que já foi baixado.
3. Leia os `.md` de `pages/` — cada um tem frontmatter com `url`, `title`,
   `fetched_at` e o texto completo da página.
4. Se o conteúdo sair como tela de login ("sign in" etc.), a sessão expirou:
   peça para a pessoa rodar o comando `login` de novo.
5. Não rode dois comandos ao mesmo tempo — o perfil de navegador aceita uma
   instância por vez.

## Solução de problemas

- **Conteúdo vazio ou incompleto** → aumente `--settle 5`, ou use
  `--wait-selector "seletor-do-conteudo"`, ou rode com `--headed` para ver o que
  a página está renderizando. Se o texto estiver num contêiner específico, use
  `--content-selector`.
- **"Browser is closed" / erro de perfil** → outra instância está usando o
  `browser_profile/`; espere a anterior terminar.
- **Site bloqueou o navegador** → tente `--headed` (janela visível passa mais
  fácil por checagens anti-bot).

## Integração com este repositório

- A skill de projeto `.claude/skills/gray-swan-reader/SKILL.md` expõe esta
  ferramenta para os agentes que trabalham neste repo (descoberta automática).
- `browser_profile/` (cookies de login) e `pages/` (conteúdo real da Arena)
  estão no `.gitignore` — nunca versionar, mesma política de `data/`.
- A ferramenta é **somente leitura**: nunca automatiza submissão na Arena
  (guardrail 2 do AGENTS.md).
