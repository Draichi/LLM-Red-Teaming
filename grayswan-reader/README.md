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

Por padrão o `open` (e o `fetch`) também abre o painel **"Submissions in
this chat"** (aria-label `#workspaceRailSubmissions`) e grava o judge eval
na seção `## Judge Eval (Submissions)` do `.md` — scores por juiz, texto
da avaliação e condições do break; com múltiplas submissões, uma entrada
`--- Submissão N ---` por submissão. Passe `--no-judge-eval` para pular
(janela lateral não abre; útil se o operador estiver usando o sidebar).

A extração do corpo é higienizada: sidebar de navegação (lista de cenários
e breaks do evento) e blocos de energy do rodapé do chat são removidos da
árvore antes do texto — o `.md` contém só o trace + judge eval.

## 4b. Intake de batch group completo (URLs + transcripts por modelo)

```bash
.venv/bin/python batch_intake.py "<url-do-batch-group>" <dir-saida> [--force]
```

Duas etapas em um só comando, somente leitura:

1. Extrai (modelo, run URL) de cada bloco de run do batch group
   (`extract_batch_group_urls.py`) e cria/atualiza o `URLS.md` no diretório de
   saída — só a coluna Run URL; status e notes existentes são preservados.
2. Abre cada run com `--expand` restrito e salva o transcript como
   `<Modelo>.txt` no mesmo formato dos arquivos de run do workspace
   (frontmatter + corpo + conteúdo colapsado). Arquivos não vazios já
   existentes são pulados; `--force` rebaixa, `--limit N` baixa só N,
   `--urls-only` faz só a etapa 1.

Passe `--no-output-expand` para pular a expansão dos botões **"Show full
(N chars)"** dos cards de tool (a etapa 2 continua expandindo disclosures
"Expand to see details" e cards estruturais de tools). Recomendado para
autopsias: outputs de tool com 15k+ chars ficam colapsados no transcript,
e a leitura econômica (grep + janelas) não precisa deles expandidos.
Expandir tudo aumenta o tamanho dos arquivos em várias vezes sem retorno
analítico — só omita a flag se alguma decisão específica depender do
conteúdo exato e completo de um output (e nesse caso prefira reabrir a
run única com `reader.py open ... --expand` em vez de rebaixar o batch).

`extract_batch_group_urls.py` também funciona sozinho e imprime o JSON bruto
dos blocos (útil para conferência manual de cobertura).

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
| `--no-output-expand` | — | só no `batch_intake.py`: expande disclosures e cards, mas **não** clica em "Show full" dos outputs (economia de tokens; ver seção 4b) |
| `--no-judge-eval` | — | não abre o painel "Submissions in this chat" nem grava a seção `## Judge Eval` (default: grava) |
| `--cdp-port N` | `9222` | porta de debug do Arc (só mude se abrir em outra) |

## Para agentes (Claude etc.)

1. Rode os comandos acima via Bash (a partir de `grayswan-reader/`).
2. Comece por `pages/manifest.json` para ver o que já foi baixado.
3. Leia os `.md` de `pages/` — cada um tem frontmatter com `url`, `title`,
   `fetched_at` e o texto completo da página.
4. Não rode dois comandos ao mesmo tempo.
5. Em chats da Arena, use `--capture-api --expand` (próxima seção).

## Intake de cenários via DOM (responsabilidade do agente)

Para montar ou atualizar o `INTAKE.md` de um cenário, o agente — não o operador
— inspeciona a página e extrai o texto e os atributos do DOM. O operador fornece
a URL do evento e somente informações que realmente não estejam disponíveis na
página. Não peça transcrição manual de formulários nem prints; o intake não tem
seção de screenshots.

### Limites obrigatórios

- Use somente a URL do evento fornecida pelo operador e a sessão já autenticada
  do Arc. A navegação permitida é local e não submissora: cartão do cenário,
  critérios, **New injection**, seletores de site/action, disclosures e menus de
  markers necessários à leitura.
- Clique somente em controles identificados de forma inequívoca, com texto/role
  conferidos e contagem esperada. Nunca use coordenadas arbitrárias.
- **Nunca clique em Launch, Submit Break ou qualquer controle de submissão.**
  Não use `button[type="submit"]`, não preencha campos, não insira markers e não
  adicione comportamento de submissão ao reader. Delete, Upload custom site e
  Use template também não são necessários para o intake.
- Não tente provocar erros de validação por submissão. Registre as regras
  visíveis e marque erros que só apareceriam após submeter como `not visible`.
- Material bruto do Arena fica apenas em `pages/` ou no diretório gitignored do
  cenário sob `data/`; documentação rastreada contém só o procedimento.

### Sequência reutilizável

1. Abra a URL do evento com `reader.py open ... --capture-api --settle 5`. Para
   navegação DOM adicional, use `browser_session` do `reader.py` com Playwright
   em um script pontual, sempre a partir de `grayswan-reader/` e sem comandos de
   navegador concorrentes.
2. Os cartões de cenário são `button[type="button"]`, não necessariamente links.
   Por isso, `reader.py links` pode não encontrar URLs de cenários. Selecione o
   cartão pelo código e nome completos, confirme a wave e verifique o título em
   **Task Details** antes de extrair qualquer coisa. Nunca reutilize o intake de
   um cenário de numeração parecida ou de outra wave.
3. A seleção do cenário pode não mudar a URL, e a página pode restaurar o último
   cenário selecionado. Não confie na URL, no nome do arquivo salvo ou no
   `manifest.json` como prova do cenário: confira sempre o heading de Task
   Details no DOM atual.
4. Extraia **Harmful task** e **Benign task description** de Task Details. Abra
   **See success criteria** / **View scenario criteria** e capture todo o painel:
   descrição, Overview, Victim, Services and Resources, Objective e Criteria.
   Selecionar um critério pode apenas destacá-lo; se eixos, floors, scoring ou
   rationale adicionais não aparecerem, escreva `not visible`, sem inferi-los.
5. Inventarie o injection obrigatório já presente e use **New injection** para
   inspecionar as demais surfaces. Os seletores de site e action expõem opções
   com `role=option`; os triggers têm labels como `Injection N site: ...` e
   `Injection N action: ...`. Uma surface com uma única action pode selecioná-la
   automaticamente e deixar o seletor desabilitado. Enumere tudo na UI atual,
   sem copiar actions de outro cenário.
6. Use uma página nova para cada action, ou restabeleça explicitamente o estado
   inicial, para não carregar campos entre formulários. O injection obrigatório
   costuma ser índice 0 e o primeiro adicionado índice 1. Na estrutura atual, os
   campos têm IDs `world-injection-<índice-zero-based>-field-<nome>`.
7. Para cada campo, extraia o `innerText` do contêiner mais próximo e as
   propriedades DOM: tag, type, value, placeholder, maxLength, required, checked
   e/ou `aria-checked`. Não restrinja a busca a `input, textarea, select`:
   checkboxes podem ser `button[role="checkbox"]`. Para esses controles, leia as
   propriedades via `evaluate`; `input_value()` só vale para input/textarea/select.
8. Não confunda validação visual com atributos HTML: um campo pode ter asterisco
   e aparecer como obrigatório no preflight mesmo com `required=false` no DOM.
   Da mesma forma, `maxLength=-1` significa ausência do atributo de limite, não
   prova de que o backend aceita texto ilimitado; registre `no limit visible`.
9. Capture o máximo global em **New injection (N/M max)** e o limite individual
   no texto do card, como `1 of N ... injections used`. Registre required e
   optional fields, defaults, placeholders, exemplos, descrições, limites de
   caracteres, preflight e custo visível, sem pressupor que sejam iguais entre
   cenários.
10. Para markers, abra um controle **Marker** e leia os itens de menu e submenus.
    Grupos têm `aria-haspopup="menu"`; clicar no grupo abre suas partes, enquanto
    clicar numa folha insere o marker e não deve ser feito. Se hover não abrir de
    forma confiável, clique apenas no grupo e reabra o menu entre grupos. Leia
    também **What are markers?** e confirme ao final que o valor do campo
    continua vazio.
11. **View content** abre um preview do conteúdo; não é necessário para extrair
    os campos do DOM. Não confunda esse preview com expandir o card. Se for
    preciso expandir visualmente, use o disclosure **Injection N**, mas continue
    registrando o texto e os atributos, não screenshots.
12. Se o operador fornecer a mensagem benigna mostrada durante a run, compare-a
    com o texto pré-run preservando quebras de linha e parágrafos. Registre a
    fonte e se a igualdade exata foi confirmada; não normalize espaços antes da
    comparação.
13. Preencha o `INTAKE.md` específico do cenário com data, URL, spec completo,
    mensagem benigna, critérios/judge visíveis, slots/actions/caps, campos,
    defaults, markers, validações e notas. Revise a contagem de actions e blocos
    e deixe `not visible` em tudo que não pôde ser lido, sem usar Launch para
    completar lacunas.

Em scripts pontuais de SPA, `wait_until="networkidle"` pode demorar por causa de
polling/WebSocket. Para essa navegação controlada, prefira
`wait_until="domcontentloaded"` seguido de espera pelo cartão ou seletor
específico necessário. O comando normal do reader continua adequado para salvar
páginas e chats.

## Expandir detalhes e outputs de tool calls (`--expand`)

Nas páginas de chat da Arena, os detalhes das tools são renderizados
client-side, não no payload SSR nem em XHR. Com `--expand`, o reader usa input
real do navegador em três etapas:

1. Abre **"Expand to see details"** para revelar os cards de tools.
2. Abre cada card e captura `ARGUMENTS` e `OUTPUT`.
3. Aciona **"Show full"** ou **"Show full (N chars)"** dentro dos cards para
   capturar argumentos e outputs longos sem truncamento da UI. Esta etapa é
   pulada inteiramente com `--no-output-expand` (só `batch_intake.py`).

Comportamento da etapa 3 (desde 2026-11-04): o passe roda em **duas
passadas**, porque o app renderiza a expansão em estágios — o 1º clique
revela parte do output e pode materializar controles novos, que a 2ª
passada expande. Cada elemento é marcado (`data-gsr-output-expanded`)
antes do clique, então um clique falho não é repetido nem aborta o resto
da passada (antes, a primeira exceção derrubava toda a expansão dos
demais cards).

Limites de segurança, todos no código (`EXPAND_FIND_JS`, `TOOL_CARD_FIND_JS` e
`SHOW_FULL_FIND_JS` em `reader.py`):

- O disclosure geral aceita apenas a whitelist (`expand | show more | ver mais |
  detalhes`) e rejeita sua blacklist de ações. O alvo clicado é SEMPRE um
  ancestral identificável como controle (`cursor-pointer`, `role=button`,
  `BUTTON`, `SUMMARY`); sem esse ancestral o candidato é descartado (fallback
  para `leaf.parentElement` capturava o contêiner da mensagem e anulava o
  clique real — v3 wb3s1, 2026-11-03).
- Cada clique é dado um por vez com a aba em primeiro plano: `scrollIntoView`
  central via JS, pausa, input real via CDP, pausa de render, e o DOM é
  reconsultado após cada clique (a re-render da SPA desanexa handles). Cliques
  em sequência rápida ou com a aba em background caem fora do controle e viram
  no-op. **Durante um `fetch`/`batch_intake` com `--expand`, não navegue no
  Arc.**
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
