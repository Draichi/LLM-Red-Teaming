# Gray Swan Manual Campaign Workspace

This repository supports strategy, preparation, and documentation for authorized
Gray Swan Arena campaigns. The active campaign workflow is `MANUAL_ARENA`:
submissions are performed by the operator, never by an agent or script.

## Start here

1. Read [`docs/manual_campaign_start_here.md`](docs/manual_campaign_start_here.md).
2. Follow [`gray_swan_playbook.md`](gray_swan_playbook.md) for the round loop.
3. Consult [`docs/mechanism_families.md`](docs/mechanism_families.md) and
   [`docs/jailbreak_sota_references.md`](docs/jailbreak_sota_references.md) when
   researching a materially new mechanism.

The `grayswan-reader/` utility is read-only and retrieves Arena pages from the
operator-provided URLs. It does not submit vectors or interact with submission
controls.

Keep working vectors, traces, and Arena responses in the gitignored `data/`
workspace. Tracked documentation may contain strategy-level findings, but never
functional payloads or raw Arena transcripts.