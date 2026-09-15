"""Loaders for human-labeled judge-calibration sets.

Each loader yields `LabeledItem`s: an objective, the single-turn transcript the
humans saw, and a binary human ground-truth label (1 = the response is a
successful/harmful completion). The judge's continuous score is binarized at the
success threshold and compared against this label to compute Cohen's kappa.

Two sources:
  * harmbench_val -- HarmBench's classifier validation set. Each item carries
    three human votes (human_0/1/2); we take the majority. Directly downloadable.
  * strongreject_labelbox -- StrongREJECT's LabelBox study: 1-5 human ratings
    rescaled to [0,1]. Binarized at >0 (any jailbreak signal) by default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LabeledItem:
    objective: str
    messages: list[dict]  # single-turn: [{"user"...}, {"assistant"...}]
    human_label: int  # 1 = successful/harmful completion, 0 = not


def _turn(objective: str, response: str) -> list[dict]:
    return [
        {"role": "user", "content": objective},
        {"role": "assistant", "content": response},
    ]


def load_harmbench_val(path: str | Path) -> list[LabeledItem]:
    """HarmBench val set: {behavior_id: [ {test_case, generation, human_0..2}, ...]}."""
    raw = json.loads(Path(path).read_text())
    items: list[LabeledItem] = []
    for _behavior_id, examples in raw.items():
        for ex in examples:
            votes = [ex[k] for k in ("human_0", "human_1", "human_2") if k in ex]
            if not votes:
                continue
            majority = 1 if sum(votes) >= (len(votes) / 2.0) else 0
            objective = ex.get("test_case") or ex.get("behavior") or _behavior_id
            items.append(
                LabeledItem(
                    objective=objective,
                    messages=_turn(objective, ex.get("generation", "")),
                    human_label=majority,
                )
            )
    return items


def load_strongreject_labelbox(path: str | Path) -> list[LabeledItem]:
    """StrongREJECT LabelBox csv. Columns include forbidden_prompt, response,
    and a human score in [0,1] (rescaled from 1-5). Binarize at > 0."""
    import pandas as pd

    df = pd.read_csv(path)
    prompt_col = _first_present(df, ["forbidden_prompt", "prompt", "instruction"])
    resp_col = _first_present(df, ["response", "completion", "output"])
    score_col = _first_present(df, ["score", "human_score", "label"])
    items: list[LabeledItem] = []
    for _, row in df.iterrows():
        objective = str(row[prompt_col])
        response = str(row[resp_col])
        human_label = 1 if float(row[score_col]) > 0.0 else 0
        items.append(
            LabeledItem(objective, _turn(objective, response), human_label)
        )
    return items


def _first_present(df, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"none of {candidates} in columns {list(df.columns)}")


LOADERS = {
    "harmbench_val": load_harmbench_val,
    "strongreject_labelbox": load_strongreject_labelbox,
}


def load_calibration(dataset: str, path: str | Path) -> list[LabeledItem]:
    try:
        loader = LOADERS[dataset]
    except KeyError:
        raise ValueError(
            f"unknown calibration dataset {dataset!r}; known: {list(LOADERS)}"
        ) from None
    return loader(path)
