# <scenario> — engagement writeup

TEMPLATE. Copy to `data/writeups/<scenario>.md` (gitignored — it holds payloads)
when scaffolding a scenario, and populate as you iterate.

## Scenario

- **Objective:** what the attacker must make the target do.
- **Input point:** where your input goes (the `{fill}` / turn / tool result).
- **Arena axes (scored ≥70 each to break):** e.g. Harmful Content, Originality,
  Stealth & Obfuscation. Note which the local judge scores vs which the human sets.
- **Constraints:** forbidden techniques (e.g. no impersonation, no intent disguise).

## Status

- Broken: **X / N** arena models. Best vector: `<name>`. Last updated: <date>.

## Intel (rounds)

Chronological notes — what was tried, how models reacted, the lesson. Example:
- **R1** — <approach>: <result across models>. Lesson: <...>.
- Which models are walls vs soft; proxy behaviour; axis trade-offs discovered.

## Kill log

| Model (arena codename) | Vector | Harmful / Orig / Stealth | Date |
|---|---|---|---|
| | | | |

Near-misses (failed one axis) worth listing separately — they refine cheaply.

## Vectors

The payloads themselves (why this file is gitignored). One block per named vector:
its payload text, which models it broke, its local reliability (breaks/trials).

## Reusable lessons

Cross-round takeaways that generalize (often the axis trade-offs, the framing that
works, the obfuscation that passes Stealth).
