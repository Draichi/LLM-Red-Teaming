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
| 6 | Forged conversation history (synthetic prior turns, deliberation, or refusal-history claims) | ~22 | extends B11 from logs to full arcs, including model-authored reasoning; exact markup is omitted |
| 7 | Authorization/consent simulation (synthetic approval history and staged consent; verification-handshake mimicry) | ~13 | A14-adjacent but INSIDE untrusted content it converts |
| 8 | Dictated verbatim payload + output contract | ~15 | origination-style risk: the artifact must look self-generated |
| 9 | Conditional triggers (error conditions, artifact-processing, secret codes, read-time execution) | 5 | extends B12 |
| 10 | Recursive agent spawning (child agents with inherited instructions; violation = one flag inside an argument) | 5 | new class: agent-to-agent |
| — | Real obfuscation (unicode-tag etc.) | **1/95** | **forged structure does all the work — "channel-shape beats content-plausibility" at corpus scale** |

New candidate labels beyond B08–B13 include guardrail pre-rebuttal,
retry claims, fabricated tool-state paired with a repair procedure,
compound-operation sequencing, requirements framing, and social-proof cues.
These are hypotheses, not field-ready recipes: require a real carrier, verified
state, a preregistered criterion, and judge-visible evidence. NEW surface classes:
memory/agent-state fields, code/PR/CI write surfaces, agent-to-agent
recursion, physical actuators, moderation-decision flips.

Independent confirmations of our campaign laws: an ART-winner family
combines forged authority framing, a verification-status claim, and an
application-state signal. Record the family at this abstract level; literal
fields, wording, and receipt markup are omitted. Winning transcripts INCLUDE
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
  confirms UDora, feed 2025-06): the cited reports describe synthetic
  deliberation structures and manipulation of partial reasoning as candidate
  carriers. Exact tag syntax and sequence construction are omitted. Track this
  under the B19 family; any transfer claim requires scenario-specific evidence.
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
- **Chat-template override channel validated at scale** (Pillar
  2026-02-10, "Chat Template Backdoors Across 18 Models and 4
  Engines"): chat-template-shaped boundary markers and special tokens
  may parse as authority across engines — empirical backing for the
  ART-winner family (B08/B11 forged system block). This is channel-specific
  evidence, not a transferable payload; exact token sequences are omitted
  from this tracked document.
- **Agent-to-agent escalation field-proven** (Pillar 2026-08-03,
  Google ADK CI/CD privilege-boundary failures): agents escalate by
  calling each other across privilege boundaries — confirms corpus
  class 10 (recursive spawning) on real systems. If a behavior's
  surface lets the agent invoke or message another agent, treat the
  second agent as an injection REPEATER: payload can target the
  intermediate agent's instructions instead of the primary's.
- **Selective-context gating as a carrier** (Pillar 2026-05-20,
  untrusted project-local filter files in RTK): attacker-controlled
  filter/config files decide what the agent SEES. If any behavior
  grants write access to a filter/rules/config surface, the payload
  there can gate the visibility of subsequent content (hide the
  injection's own trail) — a stealth primitive, not just a carrier.
- Excluded: BadEngram (Pillar/Fujitsu 2026-10-13) — weight-level
  backdoor in open-weight memory modules; requires controlling the
  model artifact, same bucket as tool poisoning (we don't control
  targets). Willison Oct 2026 entries are rogue-agent INCIDENTS
  (context), not technique — no ladder change.

## § Wave log

- 2026-10-13 (sweep 1, first): sweep integrated as §5c. Gray Swan
  blog fetch hit 429 — retry next cycle. New-prep items: reasoning-
  trace carrier, compaction survival, GitHub persona forgery
  (field-proven), worm-style self-re-embedding.

- 2026-10-15 (sweep 2, Wave 1 opens today): feed clean (no new
  IPI/agentic papers since 2025-07). Blog 429 again — retry next
  cycle. Added to §5c: chat-template override validated at scale
  (18 models/4 engines — keep the B08/B11 shape in the ladder),
  A2A escalation field-proven (second agent = injection repeater),
  selective-context gating via untrusted filter files (stealth
  primitive if a behavior grants config writes). BadEngram
  excluded (weight-level; we don't control targets).

- 2026-10-17 (sweep 3): nothing new — Awesome feed header still
  2026.10.12 (tail of the README verified: no entry newer than
  2025-07), simonwillison newest attack post 10-10, pillar newest
  10-14, all pre-sweep-2. Gray Swan blog now behind a Vercel
  security checkpoint (bot-blocked, not just 429) — needs a manual
  browser look next cycle. Nothing changes the ladder or craft
  standard.

- 2026-10-19 (sweep 4): nothing new for the ladder/craft —
  Awesome feed unchanged (header 2026.10.12), simonwillison clean
  since 10-13, pillar's two post-10-13 items dismissed: opencode
  MCP-OAuth RCE (10-19, tool-chain vuln class — no injection craft,
  no arena surface) and "Rogue AI Agents" (10-14, incident roundup,
  no technique). BadEngram already triaged sweep-2. Gray Swan blog
  still unfetchable (429 again this cycle) — MANUAL BROWSER LOOK
  remains pending; highest-value unchecked source for wave
  results/winner writeups.

- One account, every submission by hand (no automation — matches our
  guardrail 2). Some providers restrict jailbreak work: use the
  dedicated account/email for payload drafting tools.
- Don't share working attacks until 30 days post-event (our guardrail
  1 already exceeds this: nothing verbatim ever leaves `data/`).
- Timeline: Wave 1 Oct 15–22, Wave 2 Oct 22–29, Wave 3 Oct 29–Nov 5,
  event ends Nov 12 (approx, from the announcement timestamps).

### §5d. The Breakdown resource docs (2026-10-15, community intel — all 6 Google Docs accessible via /mobilebasic)

Gray Swan's own tutorial series ("The Breakdown", resource docs in
docs/resources.md) confirms our mechanism catalog is the community
standard and adds acionáveis for IPI Black:

1. **Community scaffold categories** (docs 1/3/6, chat-level Proving Ground):
   the material discusses interaction-configuration imitation, role framing,
   structured-state mimicry, and conversation-history boundary mimicry. These
   are source-reported mechanism classes, not validated IPI Black transfers.
   Exact tags, state fields, schema values, delimiter syntax, and message
   sequences are omitted from this tracked preparation doc. Transfer only if
   the event renderer preserves the relevant structure; WB1S1's structured
   GitHub-comment results do not establish chat-template parsing there.
2. **Tool-action follow-through** (doc 6A): distinguish narrated intent from
   the judged tool action, and treat partial adoption as a diagnostic. Any
   follow-up experiment must isolate one carrier-supported decision boundary
   and preregister the observable tool-call/judge criterion. Synthetic
   deliberation, pre/post-call wording, and repetition sequences are omitted.
3. **Echo-confirmation is their winning move too** (doc 6B): the break
   came from confirming the MODEL's own volunteered theory —
   independent confirmation of our v12 law (echo premise-building
   works only when the model raises the convenient rule).
4. **Structured legitimate-artifact framing** (doc 6): a professional
   artifact can make a substantive content decision part of its ordinary
   structure. Applicability depends on the event's judge and benign workflow;
   this note intentionally omits the source form identifier and field-level
   construction recipe. The transferable question is whether the artifact's
   required fields cause a judge-visible action, not whether the prose sounds
   authoritative.
5. **Defensive intel (ALERT detector, doc 4)**: detection happens
   EARLY in mid-deliberation layers; obfuscation filler tokens are
   an explicit detector feature. Argues payload economy + end-anchoring
   over stuffing; avoid filter-bait tokens in untrusted data (matches
   our v2 provider-block lesson).
6. **New SOTA sources to add to jailbreak_sota_references.md**: Derail
   Yourself (Ren 2024, multi-turn self-discovered clues), WordGame
   (Zhang 2025), Crescendo (Russinovich), ZetaLib, Parseltongue 2.0,
   HiddenLayer universal bypass, Pangea PI taxonomy
   (pangea.cloud/taxonomy).
7. **Synthetic-data and layout discussion:** the resources mention realistic
   task context and boundary markers as carrier variables. Concrete delimiter
   strings, fake-data examples, and payload layouts are intentionally omitted;
   treat these as unvalidated hypotheses and verify the actual event renderer.

### §5e. The Breakdown videos 1–5 (2026-10-15 — FULL TRANSCRIPTS EXTRACTED)

Method: share.descript.com pages carry `descript:transcript` meta
(signed GCS URL to transcript.json, ~12h expiry; re-fetch regenerates).
Transcripts cached at `data/research/breakdown_transcripts/t1–t5.txt`
(41k words total). Episodes 6–9 + IPI Black walkthrough still being
mined. Hosts: NoAutopilot + Audra (Gray Swan red team engineer who
DESIGNS competition behaviors — her advice is near-official intel).

Acionáveis for IPI Black / W1S1:

1. **Judge mechanics confirmed by a Gray Swan engineer**: ~70%
   threshold per criterion; partial credit is SURFACED (near-miss
   scored 50% + tells you how close) — submit near-misses deliberately
   to scaffold; originality axis = "the AI must not have been told how
   to produce it"; most judges evaluate only the LAST message.
2. **Carrier/container observations (Wave-3 walkthrough):** quoting,
   placement inside benign task material, and message/container boundaries
   were reported to affect parsing on the demonstrated surface. This is not
   validated IPI Black transfer; exact phrases, quoting patterns, boundary
   syntax, and assembly sequences are omitted from this tracked file.
3. **Classifier-variation hypotheses:** the videos discuss encoding, locale,
   and formatting as possible sources of model-specific classification changes.
   Treat each as a separate, unvalidated hypothesis requiring an event-specific
   carrier, preregistered contrast, and judge-visible outcome; no transformation
   examples are retained here.
4. **Response-shape influence:** opening-format steering was reported in
   multi-turn or final-response-scored settings. IPI Black's single-turn
   constraints limit transfer; preserve this only as an abstract observation,
   not a fixed response-opening recipe.
5. **Context and sampling effects:** prior refusals may change later behavior,
   and outcomes may vary across runs/models. Record this as a population-level
   measurement question; do not infer that repeated attempts constitute a new
   mechanism or a break.
6. **Derail Yourself (Ren 2024) six harm-framing categories** —
   CREATION / EXECUTION / DISTRIBUTION / RECEPTION / FACILITATION /
   REGULATION: each is a way to discuss the harmful artifact
   DESCRIPTIVELY (history/registration/distribution story) that dodges
   the ask-shape. For W1S1 v4 candidate: frame the value's
   CREATION/REGULATION history (when it was registered, how it is
   distributed in the guide) instead of asking for disclosure.
7. **Their empty-response triage matches classify_turn_outcome**;
   smarter models leak MORE when broken; jailbreaks are adaptive
   methodologies, not fixed exploits. Visible CoT arguing with itself
   = good sign (landing spot exists).

### §5f. IPI Black OFFICIAL mechanics (2026-10-15 — Breakdown 9 preview + post-launch
Walkthrough AMA; transcripts in data/research/breakdown_transcripts/)

Speakers: Friday (arena product director), Audra + Michael (red team
engineers, IPI Black designers). This is near-official rule text.

1. **Ranking counts distinct (model, scenario) break pairs; repeating
   a break on the same pair does not add another.** IPI Black has three
   standalone waves of approximately $100K each. The event briefing also
   describes bonuses for tagged models that resist community attacks;
   treat these as separate from the base break count. This corrects the
   earlier “not unique” wording; see the scoring clarification in §5g.
2. **White box: ONE REQUIRED injection slot the agent is guaranteed to
   encounter** (+ optional slots, ~18 total; services: GitHub, Slack,
   Gmail, X, calendar, Google Docs). "You can definitely get a break
   just filling out that one field." Black box (WB2S+?): harmful task
   visible, benign task HIDDEN, no required slots, ZERO observability
   ("you'll just see whether or not your attack succeeded") — expected
   extremely difficult. For black-box work, distinguish channel-liveness
   uncertainty from candidate efficacy using only an event-authorized,
   clearly distinguishable probe. Keep all submissions manual; no specific
   probe text or payload is reproduced here.
3. **Custom uploaded sites are NEVER default-read**: "you can point to
   the website in other injections... you're gonna have to convince the
   agent to do that. It may be disinclined to follow instructions in a
   random email to go to a website, but that's really what the red
   teaming is here." Vibe-coding sites for realism is allowed. → For
   W1S1 v3 (publication-service site): the #94 comment must do the
   convincing; site realism is the conversion factor. If nobody
   browses, pivot the mechanism back in-thread.
4. **Chaining is THE mechanic but self-declared "difficult"**: use the
   guaranteed-read surface to direct the agent to planted resources.
   Our v3 IS a chain (guaranteed #94 comment → site). Also implies
   sibling-issue corroborators can work (agents DO cross-read issues).
5. **World randomization + MARKERS**: services/orgs/names are
   randomized per run in Arena 2.0 generally — injections should use
   runtime markers ({principal_full}, {principal_email}, {org_name},
   {org_domain}) where applicable. NOTE: the WB1S1 lineguard world has
   been STABLE across our v1–v3 runs (same repo, #94, people, burner
   name) — but template vectors for NEW scenarios until proven stable.
6. **Submission mechanics**: every submit spins a fresh sandbox; the
   agent doesn't know it's simulated; Templates feature = reuse any
   previous submission as base; "known bug overheard: 'This scaffold
   cannot be given a world's tools'" (tool-availability may vary per
   model — explains our per-model toolset differences!).
7. **Cheating policy ENFORCED** ( AMA ep. 8): prompt sharing,
   multi-accounting, automation of submission ("not by using, like,
   Claude and browser to spam and click") are bannable, prizes clawed
   back. → Our manual-submission discipline is not just guardrail, it's
   the event's rule; automation of the ARENA is banned, local design
   work is fine.
8. Top-40/50 finishers on major comps get invited to the paid red-team
   contract network. IPI Black is "the new structure for IPI going
   forward" — the process we build compounds beyond this event.

### §5g. "Give Me a Break" Episode 1 (2026-10-16 — full transcript extracted; WHITE-BOX AMA with the Wave-1 scenario designers)

Source: share.descript.com/view/mG7pgUkJPq1 (same
`descript:transcript`-meta extraction as §5e). Transcript cached at
`data/research/breakdown_transcripts/give_me_a_break_ep1.txt`
(~27 min, ~4k words). Speakers: NoAutopilot (host); **Michael — red
team engineer who built most of the WHITE-BOX scenarios** (his
statements are near-official for WB1S1/S2, same tier as §5f); Audra
built most of the black box. They run one of these DAILY through IPI
Black (Mon–Fri) — keep mining with the same extraction method.
Full transcript available; no gaps.

1. **WB1S1's benign task is CONFIRMED as issue-#94 triage, and the
   single-slot attack is the designer's recommended path.** Michael:
   by default the agent is "only looking into this GitHub issue 94";
   getting it to check Slack "would already require you to write a
   pretty good injection convincing the agent to go and check out
   Slack" — i.e. surface-switching SPENDS payload budget before the
   real ask. Audra: "one prompt might be enough... that might actually
   be more effective than trying to chain it to other resources...
   start with the single prompts and expand." And the designed
   guarantee: "they can all be broken with the single injection
   surface, which is forced for white boxes." → Our v1/v2 single-slot
   failures were payload failures, not channel failures.
2. **Verification boundary (source-reported; no construction recipe).**
   W1 observations and the public discussion both describe verification as a
   frequent pre-action step. Record which sources are checked and whether the
   final tool action follows; do not treat a claimed check as a real check, and
   do not place fake verification transcripts, results, or wording in this
   tracked preparation file. Any experiment requires a real carrier, a separate
   preregistered criterion, and official-judge scoring.
3. **Conversation-history-shaped content (source-reported class, unvalidated
   transfer).** The designer described history/boundary mimicry as a mechanism
   category. Exact syntax, synthetic turns, permission dialogue, and sequence
   construction are omitted. Retain only the hypothesis label; test it only if
   the actual event renderer preserves the relevant structure.
4. **Environment self-consistency:** a live demonstration reportedly made a
   referenced resource exist before the target encountered it, but the later
   harmful request still failed. The useful general lesson is to verify
   scenario state and distinguish a real carrier from an unsupported reference;
   specific resource IDs, text, and construction steps are omitted.
5. **Credential scenarios are designed to be difficult.** Public discussion
   describes strong intrinsic sensitivity to secrets, even when surrounding
   documentation is read. Approval/provenance and task complexity were
   mentioned as dimensions, not validated paths. W1S2 outcomes—not the
   interview—determine the current search direction.
6. **Attacker preview ≠ victim environment.** The preview may omit local
   working state. Ground candidate design only in verified environment facts;
   separate preview visibility, target-side availability, and the judge-visible
   artifact. Do not infer a secret's location or availability from a partial
   preview.
7. **Custom-site carriers: browsing is not trust.** Agents may retrieve an
   uploaded site and still cross-check its claims against repository state.
   Record retrieval and provenance checking as separate outcomes; no fake-check
   construction is prescribed here.
8. **Realism direction is official.** "The frontier models are
   wanting realism too in the attack data that we surface... less and
   less kind of hand-holdy type UI is probably gonna be the future."
   → Hand-holdy UI frames are a depreciating asset; realistic
   artifact frames compound. Matches our realism-scorer reading
   (legitimate artifact > conversational).
9. **Scoring economy clarification (amends §5f item 1).** Breaks are
   unique per (model, scenario) pair — "you can't break the same
   scenario in the same model 10 times to get 10 breaks" — ranking
   rewards total DISTINCT pair-breaks. Parallel tabs allowed; manual
   submit unchanged; breaks <30 days old must not be shared (they
   scan for near-matches, "doesn't have to be byte for byte");
   one account, one person; using breaks/techniques from other
   challenges inside IPI Black is fine.
10. **Marginal evaluation note:** the public discussion highlighted that
    content filtering and framing can affect outcomes independently. Keep this
    as an evaluation variable, not a content recipe. Report genuine sandbox or
    tool errors through the platform rather than tuning a vector around them.

- 2026-10-21 (sweep 5): nothing new for the ladder/craft —
  Awesome feed header bumped to 2026.10.19 but content is
  newest-first with nothing newer than 2025-07 in the agentic/IPI
  sections (tail re-verified: oldest entries). simonwillison: one
  new item, Anthropic agents' unintended visa-form submissions on
  the State Dept site (10-10, accidental-action incident — no
  injection technique, no craft delta). pillar: nothing beyond
  sweep-4's triaged items. Gray Swan blog 429 AGAIN (4th straight
  cycle) — MANUAL BROWSER LOOK still pending, still the
  highest-value unchecked source for W1 wave results/winner
  writeups. One line per sweep logged here as required; W2 opens
  tomorrow — next sweep should prioritize wave-transition
  intel.
