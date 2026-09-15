# Out of scope for v1 (close this file and stop thinking about them)

These are explicitly deferred. Writing them down is how they stay out of v1.

- Multimodal attacks (image/audio inputs).
- Agentic / tool-use targets.
- Fine-tuning the attacker or the judge (v1 uses off-the-shelf models via litellm).
- Transfer across languages.
- Any second harm category — v1 is one target family, one benchmark, one metric.
- Automated submission to any held-out arena. Gray Swan stays manual, by their
  rules, permanently.
- A learned (non-LLM) judge. v1's judge is the calibrated StrongREJECT-style
  rubric; a trained classifier is a later cost lever only if the LLM judge is
  the bottleneck after Phase 2.
