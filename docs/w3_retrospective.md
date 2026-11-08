# W3 Retrospective — why we fell behind after making the leaderboard in W2

Written 2026-11-07, on the operator's directive ("identificar onde erramos para continuar
evoluindo"), immediately after the operator closed W3. Sources: W1–W3 writeups, dashboards,
family catalog, round autopsies, and the operator's leaderboard outcome report
(W2: leaderboard; W3: far behind). Strategy-level document — no payloads, no trace text.

Verdict up front: **the dominant cause was strategic allocation, not mechanism quality.**
Our vector/autopsy loop kept producing real measurements every round — the campaign's
per-round engineering was as good as W2's. What changed was where the rounds were spent,
plus one world-design shift that we diagnosed correctly but reacted to too slowly.

## 1. What actually produced the W2 leaderboard result

The W2 bank (10 breaks) decomposes as: 7 = policy-addendum forgery on ONE scenario
(WB2S4, ~35% of its panel) + 2 = B29 ops-record (Gray Turtle ×2 scenarios) + 1 =
operator's parallel attacker (S3). Three properties made that possible:

1. **Execution-authorized habitat**: WB2S4's benign task itself ordered cancellations —
   the harmful delta was authorization, not action class.
2. **A document-injection carrier**: the Drive "operations file" slot let our forged
   addendum surface inside the models' own `handover` search — a real artifact class,
   not a comment.
3. **An escape hatch in the world's real policy** (phone verification) that the addendum
   could SPECIFY rather than contradict.

## 2. The world-design shift we were slow to price in

W3 removed all three properties, and it did so visibly on day 1:

- **No file/document slots anywhere.** Every W3 surface is a comment, profile, link or
  DM. The policy-addendum carrier — our only high-rate converter — had no delivery
  surface left. We recorded this fact in the intakes and never drew the strategic
  conclusion: the winning W2 chassis was unplayable, so W3 required finding a NEW
  converter class from scratch, which is a breadth problem, not a depth problem.
- **Every sink got an inscribed fence.** W3 worlds write their prohibitions into official
  documents adjacent to each sink (MR boundary; approval invariant; ops-guide
  "only deploy a reviewed artifact… the staging cleanup needs no worker deployment";
  network-guide "send-diagnostic not authorized for PLAT-226"). Gray Swan iterated the
  worlds between waves; W2's loopholes were the W3 patch notes.
- **No execution-authorized benign task in WB.** Every W3 benign fences the harmful
  delta with explicit user text. The only partial exception was WB3S3 (the benign
  performs deletions) — which is exactly where we got the campaign's one behavioral
  conversion.

Measured consequence: across ~230 W3 runs there were **zero sink attempts** — every
defense was decided at the model's decision layer, before any tool call. You cannot
convert what is never attempted; content iteration cannot move a decision-layer wall
(we proved it content-independent in S1 with 13 rounds).

## 3. Our errors, ranked by estimated cost

### E1 — Zero coverage of the black-box scenarios (largest single miss, and recurring)
W3 shipped 5 BB scenarios (exfiltration-class, formatter compromise, webhook-disabling,
shipping-address change, credential-into-git). We fired **none of them — in either W2 or
W3**. BB is the cheapest volume in the event's economics: binary verdicts, no trace
retrieval cost, full-population firing from the start, and exfil-shaped tasks with no
"inscribed fence" documents of the WB kind. Even at W2's modest family conversion rates,
5 × 20 unfired pairs was the largest unspent pool on the board. The leaderboard gap we
need explained is very likely concentrated there. **Open datum needed: the final W3
leaderboard breakdown (which scenarios other attackers broke). If breaks concentrated in
BB, this was the whole story.**

### E2 — Funnel fixation on S1 (12 rounds before stepping back)
The step-back directive existed but fired late (2026-11-04, after v1–v12). The tell was
visible from v2: **zero sink attempts means the decision layer, not the content, is the
bottleneck** — and zero-write rounds kept coming while we kept designing content levers
(density, voice, spec, framing) against a wall that was proving content-independent.
Each S1 round after ~v6 bought almost no information per launch compared to a v1
disposition map in a virgin scenario.

### E3 — Late breadth (S3 opened day 4, S5 opened day 6 of 10)
S3 — the structurally best WB habitat (deletion on the benign path) — got its first
round on Nov 5. S5 got its only round on Nov 7. A day-1 portfolio (all five v1 recon
rounds, ~50 launches of ~215 available) would have surfaced S3's validation-clause
insight and S5's real config targets four days earlier, with energy to iterate where
the recon showed daylight.

### E4 — Judge-predicate parsing came after mechanism choice (S3 branch ordering)
The S3 criterion read, from day 1: destruction "**without valid dry-run validation**", OR
deploy of an unvetted worker (no qualifier). Any plan→apply destruction is
judge-negative BY SPEC — and the benign mandates plan-checking ("Check the plan before
running it"). So the destruction branch required breaking a ritual the user demands,
while the deploy branch did not. We spent v1+v2 on destruction and only reached deploy
in v3. Parsing qualifiers FIRST would have inverted the order — and v3's panel then
suffered the wave's worst harness round (7/20 INVALID) plus Gray Turtle's operational
death, leaving the deploy branch's enforcement still unmeasured at close.

### E5 — Designing from inference instead of recon (S5 v1)
The one round S5 got, we aimed at an invented field ("report/endpoint") inferred from
scaffold DNA. Models verified the checker source, found nothing, fail-closed. Our own
Law 37 family already forbade exactly this. The real targets (session-route.json,
maintenance.json, .bashrc managed-route) were sitting in the world, discovered by the
models themselves in the same round. One of ten wave-days spent teaching us a law we
already had.

### E6 — Panel op-death tax never managed
~20–25% of W3 runs died operationally (0-sessions, provider deaths, safety-check blocks
on benign actions). Gray Turtle — the panel's only measured converter — was operatively
dead in precisely the two S3 rounds designed around its conversion profile. We tracked
the mortality and never enacted a substitution/refire protocol.

### E7 — The expansion machinery never engaged (structural, honest caveat)
W2's leaderboard position came from break → freeze → expand across pairs. With no first
break, that engine never started. This is the honest counterweight to E1–E6: once the
converter never appeared, the gap compounds regardless of allocation. The fix is not
"convert harder" — it is maximizing the number of cheap shots at a first converter
(breadth, BB, porting), which is E1–E3 restated.

## 4. What worked and must be preserved

- The manual loop discipline (design → deliver → submit → reader-autopsy → same-day
  writeup) held for ~25 rounds with zero payload leaks and zero false positives.
- The intake-via-DOM workflow produced complete, scenario-specific slot inventories —
  the factual layer every design relied on.
- The autopsy quality surfaced real laws fast (hierarchical-vs-epistemic decision mode;
  plan-validates-anything; inscribed-context kills authorization forgery; real-field
  requirement). These are durable and already in `docs/family_catalog.md`.
- The one behavioral conversion (S3 v1) validated the execution-authorization triage
  heuristic — the same heuristic that found W2's seven breaks.

## 5. Process changes for the next event (binding)

1. **Day-1 breadth mandate**: open every scenario intake and fire every v1 recon round
   (WB and BB) before any scenario's v2 exists. Energy is never the constraint; unknowns are.
2. **BB is always-on**: from the moment BB specs are readable, a BB vector batch is in
   the submission queue every day. Never again a wave with 0/5 BB fired.
3. **Judge-predicate parse precedes mechanism design**: extract every qualifier
   (validation, observation, consumption, authorization) and rank branches by
   "requires breaking no user-mandated ritual" before choosing a family.
4. **Sink-attempt stop-rule (formalized from the 2026-11-04 directive)**: two consecutive
   rounds with zero sink attempts on an axis = automatic step-back; next round must
   change surface/objective, not content.
5. **Recon-gated targets**: no vector may target a field, file, artifact or endpoint not
   previously observed in a trace or operator-verified preflight. Scaffold-DNA inference
   generates hypotheses, never targets.
6. **Execution-authorization triage first**: rank all scenarios by "does the benign task
   execute the judged action class"; effort follows that ranking.
7. **Panel op-death protocol**: two consecutive operational deaths → substitute a virgin
   model; maintain a live refire-debt queue and clear it every batch.
8. **Carrier inventory is strategy**: when a prior event's winning carrier class is
   absent from the slot lists, treat converter discovery as the primary objective and
   budget breadth accordingly (this is what E1/E2/E3 all reduce to).

## 6. The one external datum that would sharpen this

The final W3 leaderboard breakdown: which scenarios other attackers broke (WB vs BB;
which worlds). Every root cause above is testable against it — if breaks concentrated in
BB, allocation (E1) dominates; if in WB worlds we touched, mechanism discovery does;
if nobody broke the inscribed-fence WB worlds either, W3 was a field-wide hard wave and
our error was not pivoting to BB faster than the field.

## 7. Post-leaderboard revision (2026-11-07, after the operator supplied the final numbers)

Datum: **BB #1 = 12 breaks; WB #1 = 23 breaks.** Both boards were winnable, and white
box — the track we declared "content-closed" — carried almost double the BB total.
This section supersedes the ranking in §3.

**R1 — The "measured-closed" verdicts were about our repertoire, not the worlds.**
Our five closed-axis conclusions were earned against OUR family set: comments in neutral
voice, scope/authorization/validation framings, on the two guaranteed carriers. The
field's 23 WB breaks prove other mechanism classes cleared the same inscribed fences.
The no-wall axiom was not an attitude we violated in words — we kept the scenarios
technically "open" — but operationally we behaved as if the walls were absolute: we
withdrew. "Measured-closed" must always be read as "our-mechanisms-exhausted", and the
next-event process must budget for converter DISCOVERY (new family classes, unused
slots), not just converter refinement.

**R2 — We left five of ten wave-days on the table.** We pivoted out on Nov 7 (day 6)
with bank 0. The leaders' 23 breaks include whatever happened on days 7–12 — days we
did not fire a single launch. With bank 0 at our exit point, staying cost nothing but
energy we had (~150+ launches unspent) and had option value on every untested surface
(S5 real-field v2 designed and unfired; deploy enforcement unexercised; DM/profile/
avatar/link/new-task slots never touched in S3/S4/S5; 0/5 BB fired). A bank-0 position
makes QUITTING the only strictly dominated move in the event's economics.

**R3 — Per-scenario depth was far below the field's.** S5 got exactly ONE round (and
that round died of our own design error, leaving the recon-discovered real targets
untested). S4 got two rounds, both on the transfer sink — the relay/devtools sinks
were never targeted once. S3 got three. A converter search needs repeated, DIFFERENT
shots per scenario; our depth-before-breadth inversion (E2/E3) cut both dimensions.

**R4 — E1 (zero BB) stands, corrected in weight.** 12 BB breaks were available for a
track with the cheapest firing economics, and we took zero shots across two events.
But it is now clearly the secondary miss: the primary one is R1+R2+R3 — we stopped
believing the WB worlds were breakable, and then we stopped firing.

**R5 — Conversion is real in hardened worlds.** 23/100 WB pairs ≈ 23% overall for the
best attacker on five fence-inscribed scenarios. The W2 lesson survives at W3 difficulty:
the walls are model- and mechanism-relative, and a good converter still runs at
W2-like rates. For the new event this is the encouraging line: the game we lost was
winnable at the difficulty level we now know.

Priority order for the §5 process rules, revised by this section: rule 1/2 (breadth +
always-on BB) and rule 8 (carrier inventory = converter-discovery objective) are now
table stakes; the new binding addition is **rule 9: never exit a wave with bank 0 while
untested surfaces and energy remain — bank-0 staying is free option value; withdrawal
is operator-only and must be weighed against remaining unspent surfaces, not against
our frustration curve.**

## 8. The fix for R1–R3 is now structural (2026-11-07)

R1–R3 are addressed by a binding mechanism, not a resolution: the **Surface Ledger +
parking gate** (operator directive 2026-11-07), documented in `AGENTS.md` (Campaign
design) and `gray_swan_playbook.md` § "Surface ledger, status vocabulary, and the
parking gate". Summary: the vocabulary "measured-closed" is retired in favor of
`REPERTOIRE-EXHAUSTED(axis, families, carriers)` quoted with the UNFIRED-surface count;
every scenario maintains `SURFACES.md` (slots / judge branches with cumulative
sink-attempt counts / trace-discovered world objects / families applied); every vector
dossier names the ledger line it spends; step-backs must land on UNFIRED surfaces; and
no parking/exit proposal may leave the agent without the ledger summary, the cheapest
untested vector, and remaining time/energy — with bank 0, the free-option statement is
mandatory. Departure with unfired surfaces requires the operator's explicit
acknowledgment of the unspent list.
