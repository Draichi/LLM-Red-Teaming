# grayswan-reader

Abre páginas da [Gray Swan Arena](https://app.grayswan.ai) (ou qualquer site)
**usando o seu Arc já logado** (via porta de debug) e salva o conteúdo de cada
página em **Markdown** — pronto para um agente (Claude, etc.) ler via `Read`.

```
grayswan-reader/
├── reader.py          # a ferramenta (links | fetch | open)
└── pages/             # saída: <titulo>-<hash>.md + manifest.json (índice)
```

Setup já pronto: `.venv/` com Playwright instalado.

---

## 1. Relançar o Arc com a porta de debug (1x por sessão do navegador)

```bash
osascript -e 'quit app "Arc"'; open -na Arc --args --remote-debugging-port=9222
```

O Chromium só aceita a flag na inicialização. Se você fechar/reabrir o Arc
normalmente, a porta cai — basta rodar o comando de novo. Não há `login`: a
ferramenta anexa-se ao navegador e usa a **sua sessão real**. Se uma página
sair como tela de "sign in", é o Arc que está sem sessão — faça login nele
normalmente e refaça o comando.

## 2. Descobrir as URLs (listagem)

```bash
.venv/bin/python reader.py links "https://app.grayswan.ai/arena" --match challenge
```

Lista todas as URLs da página que casam com `--match` (regex), com o texto do
link ao lado. Rode sem `--match` para ver tudo que existe na página.

## 3. Baixar o conteúdo de todas

```bash
.venv/bin/python reader.py fetch "https://app.grayswan.ai/arena" --match challenge
```

Extrai os links da listagem, abre **cada um** e salva `pages/<titulo>-<hash>.md`,
mais o índice `pages/manifest.json` (url → arquivo). Páginas já baixadas são
puladas nas próximas execuções (`--force` refaz).

## 4. Uma URL específica (chat da Arena: capture tudo)

```bash
.venv/bin/python reader.py open "https://app.grayswan.ai/arena/challenge/ipi-black-2026?chatId=..." \
    --capture-api --expand
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
| `--any-origin` | — | inclui links de outros domínios (default: mesmo domínio) |
| `--content-selector SEL` | — | extrai o texto só deste seletor CSS |
| `--wait-selector SEL` | — | espera este elemento aparecer antes de extrair |
| `--capture-api` | — | salva respostas JSON da SPA em `pages/api/` |
| `--expand` | — | clique restrito: expande detalhes, cards e outputs completos de tools |
| `--cdp-port N` | `9222` | porta de debug do Arc (só mude se abrir em outra) |

## Para agentes (Claude etc.)

1. Rode os comandos acima via Bash (a partir de `grayswan-reader/`).
2. Comece por `pages/manifest.json` para ver o que já foi baixado.
3. Leia os `.md` de `pages/` — cada um tem frontmatter com `url`, `title`,
   `fetched_at` e o texto completo da página.
4. Não rode dois comandos ao mesmo tempo.
5. Em chats da Arena, use `--capture-api --expand` (próxima seção).

## Expandir detalhes e outputs de tool calls (`--expand`)

Nas páginas de chat da Arena, os detalhes das tools são renderizados
client-side, não no payload SSR nem em XHR. Com `--expand`, o reader usa input
real do navegador em três etapas:

1. Abre **"Expand to see details"** para revelar os cards de tools.
2. Abre cada card e captura `ARGUMENTS` e `OUTPUT`.
3. Aciona **"Show full"** ou **"Show full (N chars)"** dentro dos cards para
   capturar argumentos e outputs longos sem truncamento da UI.

Limites de segurança, todos no código (`EXPAND_FIND_JS`, `TOOL_CARD_FIND_JS` e
`SHOW_FULL_FIND_JS` em `reader.py`):

- O disclosure geral aceita apenas a whitelist (`expand | show more | ver mais |
  detalhes`) e rejeita sua blacklist de ações.
- Cards só são clicados quando têm toda a estrutura de tool: `main`,
  `button[type="button"]`, nome em `span.font-mono`, `chevron-right` e o card
  visual `bg-muted/30`. Botões em formulários ou com `formaction` são rejeitos.
- **"Submit Break"** e qualquer texto contendo `submit` ou `break` são rejeitados
  no card e no controle. O seletor de cards não corresponde ao botão Submit Break.
- **"Show full"** só é clicado dentro de um card de tool já identificado, com o
  texto exato do controle e as mesmas verificações de formulário e submissão.
- O clique é dado no próprio elemento, nunca por coordenada arbitrária. Marcas
  `data-gsr-*` impedem novos cliques; os limites são 30 disclosures, 200 cards e
  200 controles de output por página.

Esses cliques são restritos à leitura. Submissão na Arena continua 100% manual
— o reader não tem e não deve ganhar caminho de escrita para a Arena.

## Solução de problemas

- **"Nao consegui conectar em 127.0.0.1:9222"** → o Arc está sem a porta de
  debug: rode o comando de relançamento da seção 1.
- **Conteúdo vazio ou incompleto** → aumente `--settle 5`, ou use
  `--wait-selector "seletor-do-conteudo"`. Se o texto estiver num contêiner
  específico, use `--content-selector`. As abas abrem visíveis no Arc — dá
  para ver o que a página está renderizando.
- **Página sai como "sign in"** → a sessão do Arc expirou: faça login no Arc
  normalmente e rode de novo.
- **`--match` é regex**: `?` literal precisa de escape (`challenge\?batch`).
  Descoberta voltou 0 URLs? Suspeite do padrão antes de qualquer outra coisa.

## Integração com este repositório

- A skill de projeto `.claude/skills/gray-swan-reader/SKILL.md` expõe esta
  ferramenta para os agentes que trabalham neste repo (descoberta automática).
- `pages/` (conteúdo real da Arena) está no `.gitignore` — nunca versionar,
  nunca colar em arquivos rastreados, mesma política de `data/`.
- A ferramenta é **somente leitura**: nunca automatiza submissão na Arena
  (guardrail 2 do AGENTS.md).
