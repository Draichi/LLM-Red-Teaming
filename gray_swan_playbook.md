# Gray Swan Playbook

Operating loop for Gray Swan arena campaigns (IPI Black, Level Up, ...).
AGENTS.md holds the repo-wide rules; this file is the campaign loop
itself. Versioned by design: strategy-level only — no payloads, no
model codenames (those live under gitignored `data/`).

## Division of labor

The agent designs mechanisms, maintains the documentation, and runs the
loop. The operator submits every vector to the arena BY HAND and reports
results. The arena is the only oracle; operator time is the bottleneck —
never ask for work that doesn't change the next round's design.

## The round loop

**Traces are the intel (2026-10-17, operator rule):** the agent ALWAYS
reads every pasted trace — that is where env facts, dispositions, and
the next mechanism come from. No design work ever precedes it.
Operator trigger: **"colei" = the round's trace files are populated =
fire the parallel autopsy agents immediately** ("sem perder nada").
Lightweight reporting (break/no-break in chat) covers the scoreboard
only; it never exempts the agent from reading the traces. When in
doubt, list the round folder — the files, not the chat message, say
what exists.

autópsia → design → entrega → submissão → autópsia …

This loop is the engine of the leaderboard position. Every step has a
defined artifact; a round is not done until the writeup carries it.

1. **Design** — read ALL prior traces + the scenario writeup FIRST
   (dispositions, dead families, env facts harvested from refusals).
   The round FOLDER contents — not the chat report — determine the
   reporting mode: the operator may give a one-line "no breaks" in
   chat while full traces sit pasted in the round files (S3 v1/v2
   lesson: two designs shipped without reading populated trace
   folders). List the folder before classifying anything.
   New mechanism family when the current one has no gradient; never
   more rounds inside a dead family. Cross-check sibling writeups
   before fielding a family a sibling already killed.
   **Pre-register the family's death criterion BEFORE submission**
   (2026-10-18, from reports/ipi_black_operational_checklist.md):
   state what observable in the traces kills the family, so the
   round is decidable the moment traces return — and test the
   candidate against "does this change disposition, surface, or
   judged artifact?" (if not, it's rhetoric, not strategy).
   **Design dossier in every vector file (2026-10-21, supervisor
   gate):** before delivery the vector file carries a header block —
   (1) layer attacked (carrier / interpretation / knowledge /
   decision / execution / sink); (2) evidence the carrier AND the
   sink exist in THIS scenario (not assumed); (3) causal difference
   from every family already dead here, cited by law number (this
   scenario's + cross-scenario — a re-lexed corpse is not a new
   family); (4) premises with an in-chair falsifiability check —
   which claims are session-variable, what the benign failure mode
   is if one is false (law 37: a checkable-false premise starves
   the lever and donates refusal content; the S2-v6 scripts-contract
   premise cost a full round); (5) the criterion in full branches
   (BREAK / DIES / SURVIVES / MEASURED), verbatim; (6) a PREDICTED
   disposition map per model — so the autopsy can tell "family dead"
   from "family misfired"; (7) the scenario's invocable benign
   conventions inventory (the W1 break came from a convention —
   cassette/recorded-fixture — not from payload craft).
   Design from the law catalog + disposition maps, not from the
   last round's vocabulary (L12 cuts both ways: the SE flag rides
   vocabulary, and so does the designer). Keep ≥3 designed-but-
   unfielded families per scenario in the writeup queue — queue
   exhaustion is an order to design, never to close.

2. **Entrega** — the vector goes to the operator as: title + where to
   paste + PLAIN UNFORMATTED TEXT (it goes straight into arena input:
   no markdown fences, no formatting). Save a copy under
   `data/vectors/<event>_<scenario>_manual_vN.txt`. Multi-message
   payloads = one SEPARATE slot per message, body as plain text,
   puppet identity in the slot's own fields WHEN the surface exposes
   them — the JSON array seen in the payload view is post-submit
   rendering, never the input format (2026-10-19 operator correction).
   **Identity fields are surface-dependent (2026-10-20):** some
   surfaces (IPI Black Slack DM) expose none — the sender is then the
   arena's fixed burner account. Craft rule: bodies must be
   sender-name-INDEPENDENT (never reference the puppet's name), and
   don't spend profile-setup slots to humanize a burner unless the
   mechanism actually leans on sender credibility — they cost a paste
   per model and profile text is fabricated-checkable surface.

3. **Same message as delivery**: create
   `data/runs/arena/<event>/<scenario>/v<N>/` with one file per model
   in the panel. The codename pool is stable within an event — reuse
   the slugs from prior rounds' folders; a smaller panel is a subset
   (create all known slugs, delete the unused at autopsy). Never
   placeholders.

4. **Submissão** — manual, one account, every submission by hand
   (guardrail 2: never script or automate the arena). Reporting is
   LIGHTWEIGHT on reruns: break/no-break per model (+ "preso na
   mecânica" if visible). Never request full traces for a rerun;
   full traces are for new vectors or breaks.
   **Pre-submit delivery check (2026-10-19, S3 v6 lesson — 2 of 3
   slots were never pasted and the round tested nothing):** the
   attack page renders the payload and a "Payload · N injection"
   counter BEFORE SUBMIT — the operator eyeballs N against the
   vector's slot count (and the rendered slot contents) before
   firing. An under-counted payload is a delivery failure, not a
   mechanism result; re-field it as `<vector>b` (same vector, fresh
   trace folder) instead of redesigning.

5. **Autópsia** — save received traces into the round's files, then
   fire the parallel subagents: they read ALL files and append
   AUTOPSY blocks ("sem perder nada" — lose nothing). Classify each
   model's disposition (converter / detector / silent refuser /
   skipper / escalator); every model scored, including 0s. A round
   that genuinely arrives without pasted traces (rerun-only) says so
   in the writeup and its conclusions stay inference-tier.

6. **Writeup same day** — `data/writeups/<event>.md` gets the
   disposition map, the laws the round taught, and the next round's
   design. This IS the deliverable: documentation outlives vectors.
   Update the event scoreboard in the same pass — the at-a-glance
   progress file is `data/writeups/<event>_dashboard.md` (break
   bank, per-scenario round log, family queues, loop position).
   **CLOSURE-PROPAGATION SWEEP (2026-10-20, after an S2 label
   drift):** when a lever or family DIES later — by criterion, by
   design-space analysis, or by operator decision — the same pass
   must update EVERY record that names it as live/next: the
   scenario's section in the writeup (not just the round section),
   the dashboard, and memory. A "next lever" paragraph that
   outlives its lever makes the writeup contradict the dashboard;
   label closures with their epistemic type (measured-dead vs
   closed-on-analysis + reopen condition).

7. **Commits only on explicit request** — otherwise leave the tree
   dirty. Payloads never enter tracked files (operator policy 2026-10-21:
   model codenames MAY be committed; only working attack strings are
   forbidden).

## Operational checklists (2026-10-18)

Per-round pre-flight/autopsy standard:
`reports/ipi_black_operational_checklist.md` (v2, writeup-aware).
The playbook holds the loop; the checklist holds the detail. Rules
adopted from it, binding at loop level:
- **Evidence hierarchy:** spec/judge > writeup+traces > tool output
  in traces > catalog > prep/sweep (hypotheses only). Model prose
  is testimony; an env fact enters the inventory only on verifiable
  tool output — autopsy "env facts" get tagged `tool`/`testimony`.
- **Delivery check before fielding any slot:** un-ingested slot =
  delivery hypothesis, not a mechanism test (S3 DM lesson: 0/14
  read it — that leg never tested anything). "Slot not ingested"
  is a first-class outcome.
- **Six-state outcomes,** never collapsed to 0: infra / not-ingested
  / parsed-no-adoption / partial-adoption / attempted-wrong-artifact
  / break. Only effective runs (payload delivered, decision point
  reached) count as negative evidence; infra never proves
  resistance.
- **One family per round;** multi-slot packages allowed when they
  are one mechanism, registered as ONE package.
- **Resistance is analyzed per (model × scenario × action-class)** with
  effective denominators — never a general claim about "the model". Record the
  disposition and the tested family; do not turn a refusal or finite set of
  failures into a terminal scenario verdict.

## Reply discipline

Every campaign reply states the LOOP POSITION per scenario: which step
each scenario sits on, what the next step is, and who holds the ball
(operator or agent). Replies are read as loop states, not status prose.

## Correction protocol

Every operator correction becomes a durable rule the same session:
workflow-level rules land in this playbook, campaign-state rules in
agent memory. The operator should never have to repeat a step.

**No-terminal-wall rule (operator directive, 2026-10-21):** treat every
authorized scenario as breakable by some correct vector not yet found. This is
the campaign's search axiom, not evidence that a break has already occurred.
No finite number of failed rounds or spent families proves impossibility; a
family can be `dead`, while the scenario remains `open`. If the candidate queue
is empty, queue exhaustion is an order to discover/design another family, never
to close the scenario. Deadlines or manual-panel cost may justify explicit
reprioritization or `paused-open` status; document the reason, next candidate,
and resume point. A pause is not a wall. Report measured dispositions and
effective denominators, but claim a break only when the Arena judge confirms it.
