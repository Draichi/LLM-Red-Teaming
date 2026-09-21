"""Item 6 budget fix: proposals are generated only AFTER checking the remaining
target budget -- the beam never pays for attacker proposals that no remaining
target call will fire."""

import asyncio

from mta.config import SearchConfig
from mta.search.beam import beam_search
from mta.search.state import Conversation


class _Proposer:
    def __init__(self):
        self.calls = 0

    async def __call__(self, conv: Conversation, n: int):
        self.calls += 1
        return [(f"move-{self.calls}-{i}", "s") for i in range(n)]


class _Judge:
    class cfg:
        success_threshold = 0.99

    budget = None  # beam_search assigns its Budget here

    async def score_transcript(self, objective, transcript):
        class V:
            score = 0.1
            axes = {}
            binding_axis = None
        return V()


async def _run(max_calls: int, n_proposals: int, depth: int):
    proposer = _Proposer()
    cfg = SearchConfig(beam_width=2, depth=depth, n_proposals=n_proposals,
                       max_target_calls=max_calls)

    async def target(msgs):
        return "The quick brown fox jumps over the lazy dog."

    result = await beam_search(objective="obj", target=target, propose=proposer,
                               judge=_Judge(), cfg=cfg, on_candidate=None, gate=None)
    return proposer, result


def test_no_proposals_generated_when_budget_cannot_fire():
    proposer, result = asyncio.run(_run(max_calls=2, n_proposals=3, depth=3))
    assert result.reason == "budget_exhausted"
    assert result.budget["target_calls"] == 2
    # depth 0 generated proposals; depth 1 saw remaining == 0 and returned
    # BEFORE generating. Pre-fix, depth 1 burned a 2nd attacker call generating
    # proposals take() would refuse one by one.
    assert proposer.calls == 1


def test_proposals_capped_to_remaining_budget():
    proposer, result = asyncio.run(_run(max_calls=4, n_proposals=3, depth=3))
    assert result.budget["target_calls"] == 4
    # depth 0: 3 proposals (3 of 4 calls); depth 1: 1 call remaining, so the
    # surviving branch got per_beam=1; depth 2: nothing left -> early return.
    assert proposer.calls == 2
