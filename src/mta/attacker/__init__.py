"""The attacker: proposes strategy-conditioned next turns for the search.

Deliberately ships the machinery and the strategy *taxonomy*, never a payload
library. `propose()` asks an attacker LLM to instantiate a high-level strategy
label into a concrete next turn at run time; no working attack strings live in
the repo.
"""
