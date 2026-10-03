"""Measure shared versus platform-specific code.

Lines of code (LOC) are logical source lines: blank lines, comments and Python
docstrings are not counted, so the scores cannot be moved by documentation.

Transformation portability (per target platform P):

    shared transformation LOC
    ------------------------------------------------------------------
    shared transformation LOC + P-specific transformation LOC

i.e. the share of the code that runs the workload on P which is identical to
the code that runs it on the other platform. Orchestration portability uses
the same formula over orchestration LOC.
"""

from __future__ import annotations

import ast
import glob
import io
import tokenize
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
INVENTORY = Path(__file__).with_name("inventory.yaml")
SKIP_TOKENS = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
               tokenize.ENCODING, tokenize.ENDMARKER}


def _docstring_lines(source: str) -> set[int]:
    lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(
                    getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
                lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    return lines


def count_loc(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        code_lines: set[int] = set()
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type not in SKIP_TOKENS:
                code_lines.update(range(tok.start[0], tok.end[0] + 1))
        return len(code_lines - _docstring_lines(text))
    comment = "--" if path.suffix == ".sql" else "#"
    return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith(comment))


def load_inventory() -> dict:
    return yaml.safe_load(INVENTORY.read_text())


def measure() -> dict:
    inv = load_inventory()
    files: list[dict] = []
    totals: dict[str, dict[str, int]] = {}
    for group, categories in inv.items():
        for category, patterns in categories.items():
            for pattern in patterns:
                for name in sorted(glob.glob(str(REPO / pattern))):
                    p = Path(name)
                    if not p.is_file() or p.name == "__init__.py":
                        continue
                    loc = count_loc(p)
                    files.append({"path": str(p.relative_to(REPO)), "group": group,
                                  "category": category, "loc": loc})
                    totals.setdefault(group, {}).setdefault(category, 0)
                    totals[group][category] += loc

    def share(category: str, platform: str) -> dict:
        shared = totals.get("shared", {}).get(category, 0)
        specific = totals.get(platform, {}).get(category, 0)
        return {"shared_loc": shared, "platform_loc": specific,
                "score": shared / (shared + specific) if shared + specific else None}

    return {
        "files": files,
        "totals": totals,
        "transformation": {p: share("transformation", p) for p in ("openlakehouse", "databricks")},
        "orchestration": {p: share("orchestration", p) for p in ("openlakehouse", "databricks")},
    }
