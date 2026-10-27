# AGENTS.md

Operating instructions for agents in this Gray Swan campaign workspace.

## Active workflow

All Gray Swan campaigns use `MANUAL_ARENA`. Start with
`docs/manual_campaign_start_here.md` and `gray_swan_playbook.md`, then read the
official event spec and current event dashboard/writeup. This workspace does
not support local target-model or evaluation loops. Arena submissions remain
manual and operator-controlled.

## Non-negotiable guardrails

1. **Never version working payloads or raw Arena material.** Tracked files may
   contain strategy labels, abstract mechanisms, and evidence summaries, not
   functional attack strings, vectors, run transcripts, or Arena responses.
   Keep those in the gitignored `data/` workspace. Before committing, inspect
   staged paths and ensure no `data/`, transcript, payload, or credential file
   is included.
2. **Arena interaction stays manual.** Do not automate submissions or click
   submission controls. `grayswan-reader` is read-only; use only URLs supplied
   by the operator and never add submission behavior.
3. **Trace intake uses the reader, not copy-paste.** The round owner retrieves
   all supplied run URLs with `grayswan-reader`, checks its manifest for model
   coverage, and coordinates the autopsy. Do not ask the operator to paste
   transcripts. Record missing access or incomplete coverage explicitly.
4. **No terminal walls or false positives.** Resistance is evidence about a
   tested vector, family, disposition, and action class—not proof that a
   scenario is impossible. Families may die by preregistered criteria; scenarios
   remain `open` or `paused-open`, with a next candidate and resume point. Only
   the official judge confirms a break.
5. **Preserve the Arena's full scoring criteria.** Record every available axis
   and judge rationale; a scenario passes only when all required axes meet the
   official floor. Never infer or invent scores, axes, or breaks.
6. **Keep event records current.** After each round, update the event dashboard
   and writeup with the evidence, disposition map, and next loop position. Do
   not overwrite historical snapshots; add timestamped updates.
7. **Commit or push only when the user explicitly asks.** Leave unrelated and
   untracked work untouched; do not stage broadly.

## Campaign design

- Treat official event specs as the authority for success criteria and rules.
- Consult `docs/mechanism_families.md` and
  `docs/jailbreak_sota_references.md` before proposing a materially new family.
- Choose mechanisms from evidence and target disposition; do not repeat a dead
  family with superficial wording changes.
- Keep mechanism documentation context-independent: procedure, constraints,
  verification signals, and applicability belong in tracked docs; literal
  payloads remain local under `data/`.
- **Expand a proven converter before redesigning it.** After an official break,
  freeze the winning vector and delivery slots verbatim and run the remaining
  untested model population before changing family or scenario, unless the
  operator explicitly reprioritizes. Do not reword for non-converters midway
  through the expansion; record per-model conversion and delivery failures.
- Follow explicit event ownership. When assigned to orchestrate a round, the
  agent retrieves traces, coordinates autopsy, and updates the dashboard; do
  not duplicate another owner's analysis without assignment.

## Scope

This workspace supports manual campaign planning, evidence review, and
strategy-level documentation. Do not run local model calls, proxy evaluations,
or automated Arena workflows.