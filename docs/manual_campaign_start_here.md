# Manual Gray Swan Campaigns — Start Here

This is the entry point for agents joining a live Gray Swan event. The operator
has retired the local MTA harness; its code remains historical and must not be
used for active campaigns.

## Default mode

**Default for all future Gray Swan events: `MANUAL_ARENA`.** The operator submits each vector by hand. Agents may read and edit project documentation, inspect permitted event materials, research primary sources, design mechanisms, and prepare local drafts when requested. Do not run the local MTA attack/mining/evaluation pipeline or automate Arena interaction. MTA reactivation requires an explicit reversal of the retirement decision.

In manual mode, do not assume these are part of the campaign: `mta agentic`, `refine`, `replay-vectors`, `proxy-eval`, DecompJudge, or `record-eval`. `arena_truth.jsonl` backfill is optional unless the operator names an active consumer. Preserve judge axes and reasons in the event writeup/dashboard when available; never invent scores.

## Mode router and source precedence

1. **Current user instruction and official event spec/judge mechanics** define the authorized task, success criterion, slots, and event rules.
2. **Current event dashboard and writeup** define campaign state and loop position. Compare timestamps; the newest event evidence wins over old reports, prep notes, or memory. If they disagree, record the exact mismatch and ask the state owner to reconcile it; do not silently choose.
3. **`gray_swan_playbook.md`** is the operating procedure for manual arena campaigns.
4. **`AGENTS.md`** supplies repository-wide guardrails; this page is the
   manual-vs-MTA mode router.
5. **`README.md` and `ROADMAP.md`** are historical MTA references; do not treat their command tables or backlog as active work instructions.

There is no active `MTA_HARNESS` mode while retirement stands. If the operator
explicitly reverses the retirement, update this guide and the repo instructions
before running any MTA code.

## Roles

- **Operator:** manually submits the vector. For IPI Black W2, the operator reports `grayswan-reader` can retrieve Arena responses without transcript paste; this does not automate submissions.
- **Autopsy owner:** owns vector/trace-level analysis and writes the disposition map, evidence, and laws into the event writeup.
- **Strategic supervisor:** maintains mechanism coverage, SOTA, cross-round priorities, and an independent opinion log; does not duplicate the autopsy.
- **Vector designer:** proposes a materially distinct family, writes a design dossier and pre-registered criterion, and saves working text only in the event's gitignored data area.

Use the event's actual owner assignments; do not infer that a previous event's agents or responsibilities carry over.

## New-event initialization

Before proposing a vector:

- Read the official event spec, judge predicate/axes, submission policy, and allowed carriers/slots.
- Confirm the event's wave schedule, model panel, scenario inventory, manual submission burden, and named owner for the dashboard/writeup/autopsy.
- Create or identify one event writeup and dashboard. Record the current date/time, source freshness, judge mechanics, loop position, and next owner/action.
- Read the mechanism catalog and relevant prior writeups for hypotheses; treat prior event evidence as a lead, not proof of transfer.
- Verify the actual carrier, tools, and judged sink for this scenario; never assume prior event tooling or world details exist.
- Pre-register the vector's break/death/survival/invalid-test criteria and distinguish model resistance from delivery, infrastructure, truncation, or judge failures.

## Manual round loop

Follow `gray_swan_playbook.md`: diagnosis → mechanism design → operator delivery → manual Arena submission → autopsy → same-day writeup/dashboard update. Keep one active vector at a time unless the operator explicitly changes the policy. Every round must state the scenario, vector/family, submission count, owner, and next step.

**No terminal wall:** operate on the campaign axiom that every scenario has a correct vector not yet found. A failed vector may retire its family under its pre-registered criterion; it does not prove the scenario impossible. If no candidate is ready, design/research a new family. A deadline may justify `paused-open` with a reason, next candidate, and resume point; never label the scenario unbreakable or silently abandon it.

**No false positives:** a break is only a break when the official judge criterion is met. The no-wall rule is a search policy, not permission to claim success without evidence.

## Scope boundaries

- Arena submission, browser clicks, or other interaction that would perform a submission must remain human/manual and follow the event rules.
- If `grayswan-reader` is exposed in the current agent session, use it only as a read-only response-retrieval path. Keep the autopsy owner responsible for disposition analysis; if the reader is not exposed, do not claim to have read responses through it.
- Do not run local target calls, MTA jobs, proxy evaluations, or budgeted model loops while MTA is retired.
- Keep payloads, traces, and Arena responses out of tracked files. Follow repository gitignore/commit guardrails.
- Do not modify another owner's dashboard or postmortem without assignment; report discrepancies to that owner.
- At a wave boundary, refresh the sources and priorities; do not copy a prior wave's state forward as if current.
