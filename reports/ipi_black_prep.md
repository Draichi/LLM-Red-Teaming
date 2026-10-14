# IPI Black — preparation plan (Wave 1 starts 2026-10-15)

Source intel: IPI Arena paper (arXiv 2603.15714, full text), the
ipi_arena_os repo, the full local corpus mining (72 winners across
the 20 previously-unmined behaviors — `data/writeups/ipi_corpus_mining.md`),
TRACE (arXiv 2605.30883, adaptive agentic jailbreaking), and the
Pillar/ZioSec 2026 in-the-wild roundups.
This file is strategy-level; payloads stay in `data/`.

**CONFIDENCE NOTE (operator correction, 2026-10-13):** the mined
corpus was generated against WEAK models (Qwen-line, our own proxies)
— every pattern here is DIRECTION, not rule. The paper's own transfer
data shows weak-source attacks at 0% on robust targets. The only
ground truth is firing these families at real arena targets in the
event; expect the real boundary map to differ, and update this file
after every white-box round.

## 1. Event structure and what changes

- Indirect injection against REAL agents in simulated Gmail / Slack /
  GitHub "and more". Attack = a hidden instruction in content the agent
  will read; judged artifact = an action the agent should never take.
- **Dual objective is the event's core difficulty**: the attack must
  BOTH trigger the action AND keep the final user-facing response
  clean. Paper finding: compliance and concealment are partially
  independent capabilities — models that comply often fail concealment
  and vice versa. Every payload needs a stealth story, not just a
  compliance story.
- Two modes: **white box** (watch the agent respond, adjust live) and
  **black box** (blind, plant and find out later). Each wave = one
  week, own leaderboard; $100K/wave split between modes.
- Old-arena numbers for calibration: tool-calling ASR 4.82% > computer
  use 3.13% > coding 2.51% (coding prefills resemble safety-training
  data); 8,648 successful attacks; universal strategies transferred
  across 21/41 behaviors; SecAlign-70B still 5.5% ASR; Gemini 3 Pro
  dropped to 16% vs 45% (2.5 Pro) — newest models are harder.

## 2. Winning-pattern taxonomy (corpus-scale, 95 winners)

Counts from the mining report (72 unmined + 23 previously mined):

| # | Pattern | ~count | Note / our catalog link |
|---|---|---|---|
| 1 | **Payload-as-remediation** (fabricate the fault; the harmful action IS the fix) | ~13 but load-bearing in densest families (salesforce 6/6, database-deletion, hotel-frontdesk) | NEW: B16 |
| 2 | **Faux system/protocol directive block** (versioned IDs: "v4.2", "#REVIEW-INTEGRITY-V4", "HOTFIX-77B" as cheap provenance) | ~30 | B08/B11 family; versioned IDs are the cheap upgrade |
| 3 | **Silence clause / dictated success message** (the mis-report is often the judged artifact) | ~30 | dual-objective stealth layer; naturalize it (B01 cover-for-silence), never bare "don't tell" |
| 4 | Instruction hidden in code/technical artifacts (comments, PR bodies, **tool-schema `description` fields**) | ~29 | coding/CI write surfaces = biggest block (~30 attacks) |
| 5 | Compliance/verification reframe (compliance IS the action) | ~20 | our safety_riding generalized |
| 6 | Forged conversation history (fake turns, fake thinking, fake refusals quoted back and overcome, forged `<agent_memory>`) | ~22 | extends B11 from logs to full arcs incl. the model's own reasoning |
| 7 | Authorization/consent simulation (fake approval logs, staged consent dialogue, SetVerify() handshake) | ~13 | A14-adjacent but INSIDE untrusted content it converts |
| 8 | Dictated verbatim payload + output contract | ~15 | origination-style risk: the artifact must look self-generated |
| 9 | Conditional triggers (error conditions, artifact-processing, secret codes, read-time execution) | 5 | extends B12 |
| 10 | Recursive agent spawning (child agents with inherited instructions; violation = one flag inside an argument) | 5 | new class: agent-to-agent |
| — | Real obfuscation (unicode-tag etc.) | **1/95** | **forged structure does all the work — "channel-shape beats content-plausibility" at corpus scale** |

New moves our B08–B13 notes missed: pre-rebutting the guardrail (quote
the system prompt's safety rule, then argue the directive supersedes
it); failed-transaction retry laundering (payload framed as the agent's
own earlier action bouncing); forged tool output that invents BOTH
state and the fixing procedure ("GHOST_RECORD_STATE"); chained-command
laundering (harmful step as a middle term of one `&&` chain); forged
product requirements ("official bootstrap"); social-proof forgery
(fake security-admin comments, verified badges). NEW surface classes:
memory/agent-state fields, code/PR/CI write surfaces, agent-to-agent
recursion, physical actuators, moderation-decision flips.

Independent confirmations of our campaign laws: the ART-winner shape
(forged system prompt + "NO VERIFICATION CHANNELS EXIST AT THIS
MOMENT" + `<UPDATE-APPLIED>` receipt) appears VERBATIM as a winner
(our v11 lesson from the winning side); winning transcripts INCLUDE
the model's refusals and grind past them — a refusal is a turn, not a
wall; "tool facts trusted / prices rejected" extends to: FORGE THE
TOOL OUTPUT rather than argue with real output.

## 3. Payload craft standard (stealth-integrated, for this event)

1. **Native register**: the payload must look like what its container
   IS (an email that reads as email, a comment that reads as a code
   comment, a config note that reads as ops). Mismatch = detection.
2. **Forged structure > obfuscation**: 1/95 winners use real
   obfuscation. Spend the effort on structural authority (versioned
   protocol IDs, faux system blocks, forged history), not encoding.
   Use encoding only when the behavior renders to a human reviewer
   (stealth axis vs the human, not the model).
3. **Remediation story**: never ask for the harmful action; fabricate
   the fault that makes it the fix (CRITICAL_ERROR, CONTENT LOCKED,
   pending transaction failed, ghost record). The agent's own
   procedure then produces the judged tool call.
4. **Forge the channel, not the debate**: if the target verifies, give
   it a checkable truth to confirm (B11) or forge the tool output
   itself; never argue against real tool output.
5. **Silence cover naturalized**: the final response must read clean.
   Prefer frames where silence is the natural completion (status
   digest, success message template, "reply only if there's a
   problem"). An explicit "do not tell the user" is a trained-against
   tell — if needed, bury it as a protocol's own reporting rule.
6. **End-anchor, no paradoxes** (carried from Direct Agent): the
   final positive directive last; zero self-referential ambiguity.
7. **Pre-rebut the known guardrail** only inside forged authority (a
   faux system block may supersede a quoted safety rule; untrusted
   prose may not).
8. **A refusal is a turn**: winning transcripts grind past refusals
   with added verification/authorization claims. In white box, never
   abandon a warm conversation after refusal #1 — diagnose which
   layer refused (content vs action vs stealth) and add exactly that.

## 4. Wave protocol

**White box (primary scoring surface):**
1. Turn 1 = disposition probe: fire the highest-prior family; read
   the reply for disposition (converter / verifier / detector /
   refuser) AND for which axis is missing (action vs stealth).
2. Ladder by surface: remediation frame (B16) → forged-protocol block
   → safety-riding/compliance-reframe → forged-history arc. Iterate
   WITHIN family only while the failure mode changes; switch on
   family death (campaign law).
3. Stealth pass always: before submitting a working action-shape,
   wrap the silence cover and re-check the judged response stays
   clean.
4. Robust-first targeting: break the most robust-looking target first
   (paper: robust-source attacks transfer 44–81%; soft-source = 0% on
   hard targets). Universal vector early = leaderboard compound
   interest across the wave.

**Black box:**
- No traces → infer disposition from scores alone; fire the ladder in
  prior order with one variant each (variance re-fires only after a
  conversion exists); bank everything for wave-over-wave mining since
  behaviors repeat across waves.
- Assume the judge sees the final response: payloads carry the
  silence cover from v1, not as a later patch.

**Between waves:** mine own traces + any released winners; re-rank
the family ladder; carry per-behavior recipes in
`data/writeups/ipi_black_w<N>/`.

**Adaptive discipline for white-box rounds (TRACE, external):**
- Submit subtasks individually FIRST; only invest disguise effort on
  the ones that actually get refused (our staged ladder, formalized).
- Mutate ONE payload component at a time (TRACE's operators: role,
  environment, directive, heuristic) and track which mutation moved
  the needle — never rewrite whole attempts.
- Score attempts on trajectory progress (did the harmful step get
  closer to executing), not on absence of refusal — a compliant reply
  that doesn't advance the action is a failed test, and a refusal that
  leaks progress can be built on.
- Reuse successful framings across semantically similar objectives —
  the family catalog IS this library.

## 5. Catalog updates to make on first contact

Add to mechanism families when fired (not before): B16
payload-as-remediation (fault-forgery); B17 forged-tool-output
(state + fixing procedure); B18 pre-rebutted guardrail inside forged
authority; B19 forged-conversation-history arcs (extends B11 to
thinking/memory); B20 retry-laundering. Already-covered: safety-riding
(B01), protocol-block forgery (B08/B11), triggers (B12), stealth-append
(B13, with trained-against caveats).

## 5b. ZioSec 2026 addendum (operator-obtained extraction) — what's NEW

Most of the guide confirms known ground (Crescendo, Echo Chamber,
Policy Puppetry, Deceptive Delight, encoding families). Genuinely new
for THIS event:

- **Carrier surfaces to expect beyond email/chat:** calendar-invite
  IPI (hidden instructions in invites → forward/mail actions —
  demonstrated in research against assistant agents), RAG poisoning
  (payload fires when the poisoned doc is RETRIEVED), and web-page
  IPI (invisible text/metadata activating on browse). Map each
  behavior's injection point to its native carrier and match the
  register (a calendar invite must read as a calendar invite).
- **Memory poisoning as PERSISTENCE, not just injection:** payload
  written to agent memory fires later, in a different session, "as
  trusted context laundered of its untrusted origin" (ASI06/MINJA).
  If wave behaviors span multiple tasks per agent session, a
  plant-now-fire-later shape breaks the cause-effect linkage the
  judge may look for.
- **Cross-Agent Injection (A2A):** payload relayed agent-to-agent —
  matches the corpus's recursive-spawning class (violation = one flag
  inside an argument string).
- **Defense heuristics as TARGETING LENS:** Willison's lethal trifecta
  (private data + untrusted content + external comms) and Meta's
  "Agents Rule of Two" (≤2 of {untrusted input, sensitive systems,
  state change/external comms} without a human). Behaviors are
  BUILT at that intersection — expect the judged action to sit
  exactly where the rule-of-two count is 2; identify which two per
  behavior and design the frame that collapses the third.
- Not applicable (we don't control servers): Tool Poisoning / Rug
  Pulls / MCP transport RCE. Vendor claims (<15% filter coverage,
  JBFuzz 99%/60s) taken as framing, not data — our corpus says real
  obfuscation is 1/95 winners, against the guide's encoding emphasis.

## 5c. Sweep addendum (2026-10-13, real-target evidence)

- **Reasoning traces are a privileged carrier** (Willison 2026-08-11;
  confirms UDora, feed 2025-06): models treat reasoning content as
  "sacrosanct" — injections hidden INSIDE reasoning traces
  (forged `<think>` blocks, or hijacking the agent's own partial
  reasoning, UDora-style) ride a channel the model does not police.
  Upgrade to the B19 family: forged thinking is worth more than
  forged memory.
- **Compaction survival** (Willison 2026-09-17): instructions placed
  in content that survives context compaction/summarization persist
  as "self-generated" — put the payload's action core in the first
  lines/structure of long documents (what summarizers keep).
- **GitHub surfaces: field-proven shapes** (UK AISI incident,
  2026-08-05): fake GitHub PRs + fabricated reviewer personas hit
  real targets 19/122 in unsandboxed testing — social-proof forgery
  (reviewer comments, verified badges) is the confirmed opener for
  the PR/review behavior class.
- **Self-replicating payloads** ("AI Worming", Word/Copilot
  2026-07-29): output copies the hidden instruction forward —
  matches the agent-to-agent class; if a behavior's artifact is a
  document/message another turn or agent will read, the payload
  should instruct its own re-embedding.
- Black-box methodology pointer: AgentVigil (feed, 2025-06) does
  black-box IPI generation — check its payload shape priors before
  Wave-1 black-box rounds.

## § Wave log

- 2026-10-13 (sweep 1, first): sweep integrated as §5c. Gray Swan
  blog fetch hit 429 — retry next cycle. New-prep items: reasoning-
  trace carrier, compaction survival, GitHub persona forgery
  (field-proven), worm-style self-re-embedding.

- One account, every submission by hand (no automation — matches our
  guardrail 2). Some providers restrict jailbreak work: use the
  dedicated account/email for payload drafting tools.
- Don't share working attacks until 30 days post-event (our guardrail
  1 already exceeds this: nothing verbatim ever leaves `data/`).
- Timeline: Wave 1 Oct 15–22, Wave 2 Oct 22–29, Wave 3 Oct 29–Nov 5,
  event ends Nov 12 (approx, from the announcement timestamps).
