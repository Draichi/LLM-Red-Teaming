# Jailbreak SOTA — reference watchlist

Curated sources for staying current on jailbreak / prompt-injection research,
focused on our problem class: policy-tracked tool-calling agents (arena-style
targets with guarded tool parameters and escalation rules). Compiled
2026-09-30; update when a source dies or a better one appears.

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
  Mined 2026-09-30 — winning families recorded in AGENTS.md (ART mining
  addendum).
- **Gray Swan arena blog** — https://app.grayswan.ai/arena/blog
  Event announcements, winner writeups, new scenario classes (Direct Agent).
- **AgentDojo (NeurIPS 2024)** — https://arxiv.org/abs/2406.13352
  Standard benchmark for prompt injection vs tool agents; attack library.
- **InjecAgent (ACL Findings 2024)** — indirect prompt injection benchmark
  (1,054 cases) for tool-integrated agents.
- **AgentHarm (Andriushchenko et al. 2024)** — multi-step harmful tool-use
  benchmark; the eval harness most agentic-jailbreak papers report on.
- **TRACE (2026)** — https://arxiv.org/html/2605.30883v1
  Task-aware adaptive self-evolving agentic jailbreaking; closest published
  system to our harness. Mine its strategy set.

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

Measured dead or inapplicable against arena-style tool-policy agents:
encoding/obfuscation attacks (TokenBreak, FlipAttack, Base64, low-resource
languages) — they defeat *filter classifiers*, not the model's own policy
reasoning, and cannot produce a guarded parameter value; memory poisoning
(MINJA/ASI06) — arena has no cross-session memory; MCP/protocol exploits —
we don't control the tool servers; indirect injection via tool output —
arena agents are pre-hardened against it by name.

## Standing gap list (untested SOTA vs our walls, 2026-09-30)

- **Echo Chamber** — never fired; structurally different from Crescendo
  (no early refusal to quote back — the model authors the premises).
  Candidate v11.
- **PAP persuasion sweep** — only ~5 of ~40 levers informally tried
  (urgency, authority, scarcity). Systematic social-proof / commitment
  levers unmeasured.
- **Many-shot in-conversation (F15)** — queued, unmeasured at horizon >2
  turns.
- **ART benchmark mining** — in progress (subagent, 2026-09-30).
