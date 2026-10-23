# Jailbreak SOTA — reference watchlist

Curated sources for staying current on jailbreak / prompt-injection research,
focused on policy-tracked tool-calling agents and indirect prompt injection.
Re-audited 2026-10-20 against primary arXiv/publisher sources. A citation's
presence is not evidence that its technique transfers to IPI Black; relevance
must be checked against the active carrier, judge, and measured wall.

## Tier 1 — directly about our arena / problem class

- **ART — Agent Red Teaming benchmark (Zou et al., NeurIPS 2025 D&B).**
  Paper: https://arxiv.org/abs/2507.20526 (HTML: https://arxiv.org/html/2507.20526)
  The Gray Swan competition paper: 22 agents, 44 scenarios, 1.8M attacks,
  60k+ breaks. The benchmark itself is PRIVATE (anti-overfit leaderboard);
  the paper HTML has 5 full scenario specs + the judge prompt verbatim in
  the appendix.
- **IPI Arena open-source release (follow-up, arXiv 2603.15714)** —
  repo https://github.com/GraySwanAI/ipi_arena_os + dataset
  https://huggingface.co/datasets/sureheremarv/ipi_arena_attacks (95
  verbatim winning attack strings; mirrored locally at
  `data/vectors/ipi_arena_attacks_qwen.jsonl`). Behavior files confirm the
  arena judge mechanics: `tool_judge.check: "correct_parameters_once"`.
  Mined 2026-09-30 — winning families and transfer caveats are indexed in
  `docs/mechanism_families.md`; event-level results are in
  `reports/direct_agent_event.md`.
- **Gray Swan arena blog** — https://app.grayswan.ai/arena/blog
  Event announcements, winner writeups, new scenario classes (Direct Agent).
- **AgentDojo (NeurIPS 2024)** — https://arxiv.org/abs/2406.13352
  Standard benchmark for prompt injection vs tool agents; attack library.
- **InjecAgent (ACL Findings 2024)** — indirect prompt injection benchmark
  (1,054 cases) for tool-integrated agents.
- **AgentHarm (Andriushchenko et al. 2024)** — multi-step harmful tool-use
  benchmark; the eval harness most agentic-jailbreak papers report on.
- **IPI Black (Gray Swan, Oct–Nov 2026)** — indirect injection vs real
  agents in simulated Gmail/Slack/GitHub; white-box + black-box, 3
  waves. Prep plan: `reports/ipi_black_prep.md`. **This event moves
  two entries of the noise filter below INTO scope** (indirect
  injection via content, memory/context poisoning) — the filter is
  scoped to the OLD Direct Agent arena format.
- **TRACE (2026)** — https://arxiv.org/html/2605.30883v1
  Task-aware adaptive self-evolving agentic jailbreaking; a useful published
  analogue for adaptive campaign methodology. Mined 2026-10-13:
  decomposition-first (disguise
  only refused subtasks), component-level mutation (role/env/directive/
  heuristic operators, one at a time), trajectory-progress scoring,
  framing-library reuse. Direct-only (no injection vectors), but its
  adaptive discipline is the white-box wave protocol.

## Recent primary research checked 2026-10-20

These additions broaden the older 2026-09-30 watchlist. They are preprints or
research results, not validated IPI Black vectors. Reassess against the event's
actual tools and judge before assigning a campaign family.

- **INFUSE: A Unified Surface Benchmark for Indirect Prompt Injection in Agentic Systems** (arXiv:2610.20776, submitted 2026-10-14): 40 long-horizon tasks, 56 scenarios, and distinct targeting/runtime surface taxonomies, including filenames, config, terminal output, archives, and generated artifacts. Valuable for carrier coverage and failure attribution; not a recipe to transfer into a fixed slot. https://arxiv.org/abs/2610.20776
- **Ignored, Not Refused: What Low Prompt-Injection Success Rates Hide in Small Tool-Using Agents** (arXiv:2610.23254, 2026-10): audits 33k trajectories from small open-weight agents and distinguishes silent ignore from refusal, while reporting user-task completion. This supports multi-state outcome logging; its quantitative rates should not be generalized to IPI Black's frontier panel. https://arxiv.org/abs/2610.23254
- **ASPIRE: Agentic Safety & Prompt Injection Red-teaming Engine** (arXiv:2610.08951, submitted 2026-10-06): behavior-graph-guided Explore/Exploit red teaming, trajectory evidence, and cross-run strategy memory. High relevance to professional campaign methodology and coverage accounting; it is an autonomous framework, not a family to field verbatim, and Arena submission remains manual. https://arxiv.org/abs/2610.08951
- **AgentTracer: Tracing Indirect Prompt Injection Attack through Fine-Grained Intention-Execution Alignment** (arXiv:2610.09935, submitted 2026-10-07): reconstructs implicit intent-to-tool-call dependencies for post-incident tracing. Diagnostic methodology; not itself an attack mechanism. https://arxiv.org/abs/2610.09935
- **TRACER: Trace-Regularized Training Against Indirect Prompt Injection** (arXiv:2610.19133, submitted 2026-10-13): reports channel-conditioned defense behavior across follow-up versus retrieved-context presentation and proposes trace-regularized training. Relevant as evidence to avoid assuming channel transfer; defense paper, not an attack-family source. https://arxiv.org/abs/2610.19133
- **Can CaMeLs Talk? Securing Multi-Agent Systems Against Indirect Prompt Injection Attacks** (arXiv:2610.05640, submitted 2026-10-06): describes boundary laundering when untrusted values cross from one agent to another and are reinterpreted as trusted instructions. Candidate surface only if an event scenario exposes delegation or agent-to-agent communication. https://arxiv.org/abs/2610.05640
- **Who Is Your Agent Serving? Provider-Side Indirect Prompt Injection** (arXiv:2610.05266, submitted 2026-10-04): frames recommendations and user decisions as an attack surface. Relevant only when the judge scores recommendations/response influence, not merely a guarded tool call. https://arxiv.org/abs/2610.05266
- **AutoDojo: A Generative Benchmark for Evaluating Prompt Injection Defenses in LLM Agents** (arXiv:2606.15057): adaptive black-box evaluation and task-specification sensitivity. Useful for methodology and prioritizing under-specified workflows; not evidence that its attack strings transfer. https://arxiv.org/abs/2606.15057
- **Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild for LLM Systems** (USENIX Security 2026): focuses on making injected material surface under natural retrieval queries. Relevant only where retrieval is not guaranteed; fixed required-read slots have a different bottleneck. https://www.usenix.org/system/files/usenixsecurity26-chang-hongyan.pdf
- **Will the User Ever Know? Covert Indirect Prompt Injection Attacks on Tool-Using LLM Agents** (arXiv:2608.30362; EMNLP 2026): separates covert from overt successful attacks and studies returning to the benign task after an injected action. Relevant only when concealment is part of the scenario judge. https://arxiv.org/abs/2608.30362
- **Addendum (extra run, evening 2026-10-20):** two methodology papers
  missing from the 14:06 audit, both pre-dating it and relevant to iterative
  campaign methodology — **Rethinking Indirect Prompt Injection as a
  Test-Time Search Problem** (arXiv:2609.04495, submitted 2026-09-03): an
  agentic attacker doing environment reconnaissance + strategy management over
  victim feedback, a published analogue for feedback-driven red-team iteration.
  Its finding that more
  attacker test-time compute raises discovery — but that redundancy management,
  not raw budget, sustains gains — supports the one-family-per-round rule
  rather than rounds inside a dead family. https://arxiv.org/abs/2609.04495
  — **SIR: Self-improving Red-teaming for Compute Use Agents** (arXiv:2608.30207,
  submitted 2026-08-31): composes injections from a small library of plain-
  language principles + feedback loop distilling bypasses into named strategies,
  scored by a fully deterministic oracle (filesystem/permission state) instead
  of an LLM judge. Methodologically aligned with our verifiable-judge standard;
  carrier (computer use) is out of scope for this event. https://arxiv.org/abs/2608.30207
  — Checked and NOT added: Agent-as-a-Proxy (arXiv:2602.05066, monitor-bypass
  attack) — targets monitoring-based defenses (AlignmentCheck etc.); our arena
  judge is deterministic post-hoc, so there is no monitor to deceive. LoginTrap
  (arXiv:2608.04741) — web-agent login inducement, no Gmail/Slack/GitHub-MCP
  analogue in the slot inventory.
- **Addendum (checked 2026-10-21):** industry research — **Ghostjacking /
  Agentjacking** (Tenet Security, DEF CON 34, presented 2026-08-09):
  indirect prompt injection delivered inside trusted monitoring/telemetry
  carriers (WAF block logs, error trackers, alert queues) so that a coding
  agent reading them for routine triage executes attacker instructions using
  its own already-authorized access. Includes agent-to-agent lateral movement
  (one agent's output treated as the next agent's trusted input) and a
  "self-exploit" refusal-driven optimization loop (the target's refusals reveal
  the wording it will accept — structurally similar to feedback-driven
  iteration, though transfer depends on a matching carrier). Primary source:
  https://tenetsecurity.ai/blog/ghostjacking-attacks-agentic-kill-chain/
  (secondary coverage: SecurityWeek, SC Media, 2026-08). Transferability
  caveat: the monitoring-log carrier (Cloudflare/Datadog/Sentry) is NOT in the
  IPI Black slot inventory (Gmail/Slack/GitHub), so this validates the
  log-as-carrier class and the "authorized-actions-only" design, but is not a
  fieldable vector here. The agent-to-agent boundary-laundering finding
  independently corroborates CaMeLs Talk (arXiv:2610.05640).

## WB1S2-specific research scan (2026-10-20)

These sources suggest testable mechanisms, not successful vectors for this Arena
judge. S2 requires a new committed repository file containing the live value;
none of these papers evaluated that exact predicate.

- **Red-Teaming Coding Agents from a Tool-Invocation Perspective** (arXiv:2509.05755v6): reports a difference between free-form response and structured tool-argument generation in prompt leakage. Analogy: S2's file-writing tools place content in structured arguments. Limitation: the paper studies internal prompt extraction and real coding-agent setups, not credential publication under S2's judge. Candidate for a modality-contrast test, not assumed transfer. https://arxiv.org/abs/2509.05755
- **Beyond the Payload / CIPR** (arXiv:2608.30686; EMNLP 2026): compares coding-task types; its run-tests task has the highest reported ASR and lower alert rate in its benchmark. Analogy: S2 asks for test coverage. Candidate surface: execution-generated output/artifacts, but only if S2's actual test/coverage workflow can produce and commit a judged file. https://arxiv.org/abs/2608.30686
- **Agent Data Injection Attacks (ADI)** (arXiv:2607.05120): studies untrusted values being misread as trusted structured metadata, distinct from instruction injection. Candidate only if attacker-controlled issue content is serialized alongside trusted origin/metadata in a way the model can misparse. S2 v4's real author/ID checks are counter-evidence against ordinary sender spoofing. https://arxiv.org/abs/2607.05120
- **The Framing Gap** (arXiv:2608.27092): in a synthetic canary/web-tool lab, reports more transfer from field substitutions inside known reframing templates than from creating new mechanisms. This suggests a bounded B21 template-variant experiment, but is not a new family and does not override S2's consequence-layer wall or its design-space analysis. https://arxiv.org/abs/2608.27092

S2 candidate priority, pending operator approval and evidence: (1) isolate a
structured tool-argument modality gap; (2) check whether test execution has a
verified generated-artifact sink; (3) consider schema/provenance confusion only
if the actual S2 rendering exposes that boundary. Before calling any of these a
new family, specify the reopening condition, one observable discriminator, and
why the idea is not merely a wording/field substitution within B21. No raw
attack strings belong here.

## Coding-agent / execution-layer research (S4/S5 contingency, checked 2026-10-21)

These sources inform candidate design space only when the live S4/S5 slot/tool
inventory exposes the relevant carrier. Their real/CI harness behavior must not
be assumed to match the Arena sandbox.

- **GhostCommit: Image-Based Prompt Injection Defeats AI Code Review** (ASSET Research Group; CSA AI Safety Initiative note, 2026-07-13): a PNG referenced by a repository convention file carries instructions consumed by multimodal coding agents; the public tests reported that CodeRabbit's default review excluded images and Cursor Bugbot did not flag the image-based PRs, while Claude Code refused the instruction in their tested harness. Relevant to S5's code-review-attention wall and S2's repository-secret goal only as class evidence. The currently listed Arena slots are text, so do not treat the image carrier as fieldable absent an actual asset/image slot. Primary sources: https://labs.cloudsecurityalliance.org/research/csa-research-note-ghostcommit-image-prompt-injection-ai-code/ and https://github.com/asset-group/ghostcommit
- **GitInject: Real-World Prompt Injection Attacks in AI-Powered CI/CD Pipelines** (arXiv:2606.09935; NeurIPS 2026): runs ephemeral GitHub workflows and reports credential/config-file attacks mediated by CI credential storage and repository configuration. Relevant to code-carrier hypotheses; transfer requires confirming that the Arena has the same mutable files, execution path, and credential placement. https://arxiv.org/abs/2606.09935
- **Workspace Topology as an Attack Vector in Agentic Coding Assistants** (arXiv:2608.14876; CAMLIS 2026): studies file depth, modularity, and injection placement in coding-agent repositories. Relevant only if an attacker-controlled file/path is actually delivered and read in the scenario. https://arxiv.org/abs/2608.14876
- **The Anatomy of a Prompt Injection: A Component Model for Structured Analysis** (arXiv:2608.07808): proposes labeling carrier, delivery, concealment, context-break, privilege escalation, payload, and return channel separately. Useful for keeping new S4 hypotheses distinct from wording variants; it is a classification model, not a new attack family. https://arxiv.org/abs/2608.07808

## Tier 2 — technique-originating labs (watch their blogs)

- **Microsoft (Crescendo)** — Russinovich et al., USENIX Sec 2025.
- **Anthropic (Many-shot jailbreaking)** — anthropic.com/research.
- **NeuralTrust (Echo Chamber, State of AI Agent Security reports)** —
  neuraltrust.ai blog. Echo Chamber = context poisoning via the model's own
  outputs; >90% success on several harm classes.
- **HiddenLayer (Policy Puppetry)** — hiddenlayer.com/innovation-hub.
- **Palo Alto Unit 42 (Deceptive Delight)** — unit42.paloaltonetworks.com.
- **Keysight (FlipAttack, PAP persuasion taxonomy)** — keysight.com blogs.
- **Pillar Security (in-the-wild roundups)** — pillar.security/blog. Good
  consolidated view: https://www.pillar.security/blog/deep-dive-into-the-latest-jailbreak-techniques-weve-seen-in-the-wild
- **ZioSec 2026 technical guide** — https://ziosec.com/blog/ai-jailbreak-techniques-in-2026-a-complete-technical-guide-ziosec
  Full 2026 taxonomy incl. agentic/MCP/memory classes + attack database.
- **Simon Willison** — simonwillison.net (prompt injection taxonomy,
  "lethal trifecta", ongoing coverage; best single running commentary).

## Tier 3 — auto-updating feeds & collections

- **Red-Team-Arxiv-Paper-Update** — github.com/chen37058/Awesome-Multimodal-Jailbreak
  (auto-updates every ~12h; the feed to never miss a paper).
- **LLM/VLM jailbreak survey (2026)** — https://arxiv.org/html/2601.03594v1
  Systematic survey of mechanisms, evaluation, unified defenses.
- **OWASP Top 10 for Agentic Applications (2026)** — ASI taxonomy (ASI06 =
  memory & context poisoning etc.).
- **OWASP Top 10 for LLM Applications** — LLM01 prompt injection.
- **awesome-auditable-ai** — github.com/yzhao062/awesome-auditable-ai
  (agent audit / security scanner references).

## Tier 4 — competition writeups & community payloads

- **Gray Swan Discord community** — field reports of live techniques. Two
  collected 2026-09-30 (mechanism: response-format hijack): the "Analytical
  Kill Chain" (🧠-wrapped structured reasoning trace + Stage-2 deliverable +
  last-token emoji canary — forces deliberation exfiltration from targets
  that expose no reasoning) and the "Lost Dog" transparency format
  (emotional pretext + "list every action/hesitation" = tool-call telemetry
  leak + persistent format contract). Neither breaks a policy wall alone;
  both are observability/persistence primitives. Adapted as v11.1 wrapper
  and as the standard recon-round wrapper.

- **Nick Winter** — https://www.nickwinter.net/posts/my-experiences-in-gray-swan-ais-ultimate-jailbreaking-championship
  (winner of the first Gray Swan championship; now works there).
- **HackAPrompt** — hackaprompt.com (competition datasets + writeups).
- **Project SEKAI hackathon writeups** — sekai.team/blog.
- **Pliny's L1B3RT4S patterns** — already mirrored locally at
  `data/patterns_l1b3rt4s/` (gitignored). Re-mine against mapped walls.
- **Noise warning:** r/ChatGPTJailbreak and DAN-prompt dumps are 99%
  content-policy chatbot bypasses — useless against tool-policy agents.

## Noise filter (what does NOT transfer to our problem class)

**Scope caveat (2026-10-13):** this filter is calibrated to the OLD
Direct Agent / content-generation arena formats. The IPI Black event
moves indirect injection via agent-read content and memory/context
poisoning INTO scope — re-derive per event format.

Measured dead or inapplicable against arena-style tool-policy agents:
encoding/obfuscation attacks (TokenBreak, FlipAttack, Base64, low-resource
languages) — they defeat *filter classifiers*, not the model's own policy
reasoning, and cannot produce a guarded parameter value; memory poisoning
(MINJA/ASI06) — old arena has no cross-session memory; MCP/protocol exploits —
we don't control the tool servers; indirect injection via tool output —
old-format arena agents are pre-hardened against it by name.

## Standing gap list (reviewed 2026-10-20)

Prioritize gaps by whether the active Arena scenario exposes the carrier and
whether the judge can score the consequence; a research novelty alone is not a
fielding priority.

- **Official Gray Swan IPI Black blog/results/winner writeups** — still blocked
  by HTTP 429/Vercel checkpoint in automated retrieval. Highest-value source
  requiring a manual browser check; do not report it as reviewed until accessed.
- **Agent-to-agent boundary laundering** — supported by recent multi-agent work
  (e.g. CaMeLs Talk), but only test if a live scenario exposes delegation or
  inter-agent messages. Otherwise mark as out-of-scope, not an untried active
  family.
- **Retrieval-trigger mechanisms** — Overcoming the Retrieval Barrier and
  AutoDojo make retrieval/task specification important in RAG settings. Do not
  spend these on a guaranteed-read Arena slot unless retrieval itself is part
  of the judged workflow.
- **Stateful/dynamic carriers** — INFUSE broadens coverage to filenames, config,
  terminal output, archives, generated artifacts, and long-horizon runtime
  surfaces. Map these against each wave's slot inventory before adapting a
  mechanism.
- **Failure-state diagnostics** — Ignored, Not Refused supports separating
  silent ignore from refusal and measuring benign-task completion; keep this as
  an evaluation/reporting improvement, not an attack family.
- **Channel-aware evaluation and tracing** — TRACER and AgentTracer support
  recording presentation channel and intent-to-action path. Use as analysis
  lenses; neither is itself a vector family.
- **SOTA freshness is bounded** — this watchlist is a dated evidence snapshot,
  not a claim of exhaustive coverage. Each review should record search date,
  sources checked, search limits, and event-specific relevance; new results
  should be independently checked at their primary source before being added.
