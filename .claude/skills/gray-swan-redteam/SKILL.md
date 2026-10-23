---
name: gray-swan-redteam
description: >-
  Work Gray Swan arena campaigns (authorized red-teaming) in this repo under
  MANUAL_ARENA mode: design attack mechanism families, package vectors for the
  operator's manual submission, autopsy the returned traces, and maintain the
  event writeup/dashboard. Use when the user wants to red-team or harden a
  vector for a Gray Swan scenario, start or join an event, or run a campaign
  round. The supported workflow is manual Arena submission, trace reading, and
  campaign documentation; no local target/evaluation loop is part of the flow.
---

# Gray Swan red-teaming (MANUAL_ARENA)

Active mode is **manual arena**: the agent designs mechanisms, retrieves traces
from operator-provided URLs with `grayswan-reader`, performs or dispatches the
autopsy, and maintains the documentation; the operator submits every vector BY
HAND and returns run URLs and available scores. The arena is the only oracle.

## Execution boundary

Use only the manual campaign loop. Do not run local target/model-evaluation
loops or automate Arena submission. `grayswan-reader` is read-only and may open
only the URLs supplied by the operator; never ask the operator to paste
transcripts. If reader access or coverage is incomplete, report that blocker.

## Authorities — read them, don't duplicate them

In this order:

1. **Current user instruction + official event spec / judge mechanics** — the
   authorized task, success criterion, slots, and rules.
2. **`docs/manual_campaign_start_here.md`** — mode router, source precedence,
   roles, new-event initialization checklist.
3. **`gray_swan_playbook.md`** — the operating procedure: the round loop
   (design → entrega → submissão → autópsia → writeup), trace rules,
   operational checklists, reply discipline, no-terminal-wall rule.
4. **`AGENTS.md`** — repository guardrails (payloads never versioned; the arena
   stays manual; no terminal walls; no false positives; commit only on explicit
   request) and the durable arena/model lessons.
5. **Current event state** — `data/writeups/<event>_dashboard.md` and the event
   writeup; newest evidence wins over prep notes, older reports, and memory.

`README.md` describes the current workspace. Archived engineering material is
historical only and is not an active workflow source.

## The loop, compressed (the playbook is authoritative)

**design** (read ALL prior traces first — dispositions, dead families, env
facts from refusals; new mechanism family when the current one has no
gradient; design dossier + pre-registered death criterion in every vector
file) → **entrega** (plain unformatted text for the arena input + trace-folder
scaffold `data/runs/arena/<event>/<scenario>/v<N>/` with one file per model)
→ **submissão** (operator, by hand; lightweight break/no-break reporting on
reruns) → **autópsia** (retrieve every provided URL with `grayswan-reader`,
verify trace coverage, dispatch analysis if needed, and classify every model's
disposition, zero included) → **writeup same day** (disposition map,
laws the round taught, next design, dashboard update, closure-propagation
sweep).

Reply discipline: every reply states the LOOP POSITION per scenario — current
step, next step, and who holds the ball (operator or agent).

## Scenario writeup template

`writeup_template.md` (in this skill folder) scaffolds a scenario-level
writeup: arena axes, intel log of rounds, kill log (model × vector × per-axis
scores), disposition maps. Event-level state lives in
`data/writeups/<event>.md` + `<event>_dashboard.md` per the playbook — copy
the template into the scenario's section when it fits. Everything under
`data/writeups/` is gitignored work product: working attack strings never
enter tracked files.

## Cross-links

- **`gray-swan-reader` skill** — pulls arena/challenge pages into local
  Markdown for agent reading (read-only; never automates submission).
- Durable mechanism-family catalog: `docs/mechanism_families.md`. External
  SOTA sources: `docs/jailbreak_sota_references.md`.
