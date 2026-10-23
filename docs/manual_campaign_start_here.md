# Manual Gray Swan Campaigns — Start Here

This is the entry point for agents joining a live Gray Swan event. The active
workflow in this workspace is manual Arena submission and campaign documentation.

## Default mode

**Default for all future Gray Swan events: `MANUAL_ARENA`.** The operator submits each vector by hand. Agents may read and edit project documentation, inspect permitted event materials, research primary sources, design mechanisms, and prepare local drafts when requested. Do not run local target/model-evaluation loops or automate Arena interaction.

In manual mode, local model calls and automated evaluation tools are not part of the campaign. Record available judge axes and reasons in the event writeup/dashboard; never invent scores.

## Mode router and source precedence

1. **Current user instruction and official event spec/judge mechanics** define the authorized task, success criterion, slots, and event rules.
2. **Current event dashboard and writeup** define campaign state and loop position. Compare timestamps; the newest event evidence wins over old reports, prep notes, or memory. If they disagree, record the exact mismatch and ask the state owner to reconcile it; do not silently choose.
3. **`gray_swan_playbook.md`** is the operating procedure for manual arena campaigns.
4. **`AGENTS.md`** supplies repository-wide guardrails; this page is the
   manual campaign entry point.
5. **`README.md`** describes this workspace. Archived engineering notes are
   historical records, not active campaign instructions.

The supported campaign workflow has no local target/evaluation mode. A new
toolchain would require a separate explicit operator decision and scope.

## Roles

- **Operator:** manually submits the vector and provides the resulting run URLs and available scores.
- **Autopsy owner:** retrieves every supplied URL with `grayswan-reader`, verifies model coverage, owns vector/trace-level analysis, and writes the disposition map, evidence, and laws into the event writeup.
- **Strategic supervisor:** maintains mechanism coverage, SOTA, cross-round priorities, and an independent opinion log; does not duplicate the autopsy or prepare vector v1 unless explicitly assigned.
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
- Use `grayswan-reader` only as a read-only response-retrieval path on operator-provided URLs. Never ask for transcript paste; if the reader cannot connect or coverage is incomplete, report the blocker and missing models without claiming full autopsy.
- Do not run local target calls, proxy evaluations, or budgeted model loops as part of a manual Arena campaign.
- Keep payloads, traces, and Arena responses out of tracked files. Follow repository gitignore/commit guardrails.
- Do not modify another owner's dashboard or postmortem without assignment; report discrepancies to that owner.
- At a wave boundary, refresh the sources and priorities; do not copy a prior wave's state forward as if current.
