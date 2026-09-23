"""Ingest proven vectors from event writeups into the mechanism exemplar library.

A campaign's real products live in its writeups, not in any harness log: the
kill log maps models to the vector that converted them, and each vector
section carries the fenced prompt. `learn_writeups` parses both, and for
every vector with at least one judge-PASS row decomposes it into mechanism
features via `learn_vector` -- so an entire event's history becomes design
material for the inventor proposer (the 'feed the loop the trip-stage map'
lesson, automated).

Parser targets the house writeup format (`## Vector N - title`, fenced
prompt, `## Kill log` table with `COMPLIED / judge PASS` verdicts). Unknown
shapes are skipped, never guessed: a malformed file yields fewer exemplars,
never fabricated ones."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from mta.attacker.inventor import MECHANISMS_PATH, learn_vector

_VECTOR_RE = re.compile(r"^## Vector (\d+)\s*[-–—]\s*(.+?)\s*$", re.MULTILINE)
_SECTION_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
_FENCE_RE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)
_PASS_RE = re.compile(r"\bPASS\b|COMPLIED")  # case-SENSITIVE: notes say "full pass"
_CONVERTED_RE = re.compile(r"converted", re.IGNORECASE)
_SCORE_LIKE = re.compile(r"\d\s*/\s*\d")  # "100/100", "90/80/10..."


def _is_pass_row(cells: list[str]) -> bool:
    """A kill-log row is a product row when any cell signals a conversion.
    Guards: score cells (digit/digit) and lowercase free-text notes ('full
    pass after follow-up') must not trip it."""
    for c in cells:
        if _SCORE_LIKE.search(c):
            continue
        if _CONVERTED_RE.search(c):
            return True
        if _PASS_RE.search(c):
            return True
    return False


@dataclass
class ProvenVector:
    scenario: str
    vector_id: str
    title: str
    prompt: str
    passes: list[str] = field(default_factory=list)  # "Model — notes" rows


def parse_writeup(path: Path) -> list[ProvenVector]:
    """Extract every vector + its PASS rows from one writeup."""
    text = Path(path).read_text()
    scenario = Path(path).stem
    heads = [(m.start(), m.group(1), m.group(2)) for m in _VECTOR_RE.finditer(text)]
    sections: list[ProvenVector] = []
    for i, (start, num, title) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        body = text[start:end]
        fence = _FENCE_RE.search(body)
        if not fence:
            continue
        sections.append(ProvenVector(
            scenario=scenario, vector_id=f"V{num}", title=title,
            prompt=fence.group(1).strip()))

    # kill log PASS rows -> map to vectors ("Best vector" like "Vector 1 + follow-up")
    kill = re.search(r"^## Kill log\s*$(.*?)(?=^## |\Z)", text,
                     re.MULTILINE | re.DOTALL)
    if kill:
        for line in kill.group(1).splitlines():
            if not line.strip().startswith("|") or "---" in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # column order varies between writeups (verdict before/after the
            # scores) -- any cell may carry the conversion signal
            if len(cells) < 4 or not _is_pass_row(cells):
                continue
            m = re.search(r"[Vv]ector (\d+)", cells[1])
            if not m:
                continue
            notes = " | ".join(c for c in cells[2:] if c)
            for s in sections:
                if s.vector_id == f"V{m.group(1)}":
                    s.passes.append(f"{cells[0]} — {notes[:120]}")
    return [s for s in sections if s.passes]


def _known_sources(path: Path = MECHANISMS_PATH) -> set[str]:
    if not Path(path).exists():
        return set()
    out = set()
    for line in Path(path).read_text().splitlines():
        if line.strip():
            out.add(json.loads(line).get("source", ""))
    return out


async def learn_writeups(cfg, root: str | Path, event: str = "hazard_hunt") -> dict:
    """Parse every writeup under root, learn each proven vector once.
    Returns counts; rerunnable (source-key dedup)."""
    root = Path(root)
    known = _known_sources()
    files = sorted(root.rglob("*.md"))
    learned, skipped_dup, no_pass = 0, 0, 0
    for f in files:
        domain = f.parent.name if f.parent.name in (
            "chemistry", "biology", "cyber") else ""
        for vec in parse_writeup(f):
            source = f"{event}:{vec.scenario}:{vec.vector_id}"
            if source in known:
                skipped_dup += 1
                continue
            outcome = f"arena judge PASS ({len(vec.passes)} model(s)): " + "; ".join(
                p[:80] for p in vec.passes[:3])
            try:
                await learn_vector(
                    cfg, scenario=vec.scenario, vector=vec.prompt,
                    outcome=outcome, source=source, domain=domain)
                known.add(source)
                learned += 1
            except Exception as e:  # noqa: BLE001 - one bad parse must not stop the batch
                print(f"[learn-writeups] {source}: decomposition failed: "
                      f"{type(e).__name__}: {e}")
                no_pass += 1
    return {"files": len(files), "learned": learned,
            "skipped_duplicate": skipped_dup, "failed": no_pass}
