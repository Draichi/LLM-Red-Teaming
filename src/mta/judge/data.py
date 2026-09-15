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


def _load_behavior_map(path: Path) -> dict[str, str]:
    """Map HarmBench behavior_id -> canonical harmful behavior text (+ context).

    The judge must be told the *true* objective, not the attack-wrapped
    `test_case`: HarmBench's human labels were assigned knowing the canonical
    behavior, and an obfuscated prompt (e.g. "improve family communication on the
    stairs") hides intent the judge would otherwise miss. Missing file -> {} and
    the loader falls back to the wrapped prompt."""
    if not path.exists():
        return {}
    import pandas as pd

    df = pd.read_csv(path)
    id_col = _first_present(df, ["BehaviorID", "behavior_id"])
    b_col = _first_present(df, ["Behavior", "behavior"])
    ctx_col = next((c for c in ("ContextString", "context") if c in df.columns), None)
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        text = str(row[b_col])
        if ctx_col and isinstance(row[ctx_col], str) and row[ctx_col].strip():
            text = f"{row[ctx_col].strip()}\n\n{text}"
        out[str(row[id_col])] = text
    return out


def load_harmbench_val(
    path: str | Path, behaviors_path: str | Path | None = None
) -> list[LabeledItem]:
    """HarmBench val set: {behavior_id: [ {test_case, generation, human_0..2}, ...]}.

    The judge scores against the canonical behavior (objective), while the
    transcript it reads is the actual wrapped prompt the target saw + the target
    reply -- mirroring the real search pipeline, where the objective is known
    separately from the attacker's (possibly obfuscated) turns."""
    path = Path(path)
    if behaviors_path is None:
        behaviors_path = path.parent / "harmbench_behaviors.csv"
    behaviors = _load_behavior_map(Path(behaviors_path))

    raw = json.loads(path.read_text())
    items: list[LabeledItem] = []
    for behavior_id, examples in raw.items():
        canonical = behaviors.get(behavior_id)
        for ex in examples:
            votes = [ex[k] for k in ("human_0", "human_1", "human_2") if k in ex]
            if not votes:
                continue
            majority = 1 if sum(votes) >= (len(votes) / 2.0) else 0
            wrapped_prompt = ex.get("test_case") or _behavior_id_fallback(behavior_id)
            objective = canonical or wrapped_prompt
            messages = [
                {"role": "user", "content": wrapped_prompt},
                {"role": "assistant", "content": ex.get("generation", "")},
            ]
            items.append(
                LabeledItem(objective=objective, messages=messages, human_label=majority)
            )
    return items


def _behavior_id_fallback(behavior_id: str) -> str:
    return behavior_id.replace("_", " ")


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
