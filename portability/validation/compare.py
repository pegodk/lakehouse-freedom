"""Result comparison and TPC-H query portability classification."""

from __future__ import annotations

import difflib
import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

from portable_lakehouse.common.config import scale_tag
from portable_lakehouse.tpch import sql as tpch_sql

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "benchmarks" / "results"
EXPECTED = REPO / "tpch" / "expected"

ABS_TOL = Decimal("0.01")
REL_TOL = Decimal("1e-9")

# Classification of a query on a target engine
PORTABLE = "PORTABLE"        # canonical SQL runs unchanged and returns the reference result
ADAPTABLE = "ADAPTABLE"      # needs a small dialect change (<= MINOR_DIFF_RATIO of lines touched)
REIMPLEMENT = "REIMPLEMENT"  # the requirement remains, but the implementation changes substantially
FAILED = "FAILED"            # no variant returns the reference result
MINOR_DIFF_RATIO = 0.2


def _num(v) -> Decimal | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        return Decimal(str(v).strip())
    except (InvalidOperation, ValueError):
        return None


def values_equal(a, b) -> bool:
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return abs(na - nb) <= max(ABS_TOL, REL_TOL * abs(nb))
    if a is None or b is None:
        return (a is None or str(a).strip() in ("", "NULL")) and (
            b is None or str(b).strip() in ("", "NULL"))
    return str(a).strip() == str(b).strip()


def _sort_key(row):
    out = []
    for v in row:
        n = _num(v)
        out.append((0, f"{n:.1f}", "") if n is not None else (1, "", str(v).strip()))
    return out


def _all_null_single_row(rows: list[list]) -> bool:
    return len(rows) == 1 and all(v is None or str(v).strip() in ("", "NULL") for v in rows[0])


def rows_equal(actual: list[list], expected: list[list]) -> tuple[bool, str]:
    # DuckDB's answer files store a single all-NULL aggregate row (Q17 at
    # SF0.01) as an empty result.
    if (not actual and _all_null_single_row(expected)) or (not expected and _all_null_single_row(actual)):
        return True, "equal (single NULL row)"
    if len(actual) != len(expected):
        return False, f"row count {len(actual)} != {len(expected)}"
    if actual and len(actual[0]) != len(expected[0]):
        return False, f"column count {len(actual[0])} != {len(expected[0])}"

    def same(xs, ys):
        return all(values_equal(a, b) for x, y in zip(xs, ys, strict=True) for a, b in zip(x, y, strict=True))

    if same(actual, expected):
        return True, "equal"
    if same(sorted(actual, key=_sort_key), sorted(expected, key=_sort_key)):
        return True, "equal (ignoring order of tied rows)"
    for i, (x, y) in enumerate(zip(actual, expected, strict=True)):
        if not all(values_equal(a, b) for a, b in zip(x, y, strict=True)):
            return False, f"first difference at row {i}: {x} != {y}"
    return False, "different"


def load_result(platform: str, scale_factor: float, engine: str, query: int) -> dict | None:
    path = RESULTS / platform / scale_tag(scale_factor) / engine / f"q{query:02d}.json"
    return json.loads(path.read_text()) if path.exists() else None


def load_expected(scale_factor: float, query: int) -> dict | None:
    path = EXPECTED / scale_tag(scale_factor) / f"q{query:02d}.json"
    return json.loads(path.read_text()) if path.exists() else None


def reference_for(scale_factor: float, query: int, prefer: list[tuple[str, str]]) -> tuple[str, list] | None:
    """Official answers when they exist for this scale factor, else the first available run."""
    exp = load_expected(scale_factor, query)
    if exp:
        return "TPC-H answers (DuckDB tpch_answers)", exp["rows"]
    for platform, engine in prefer:
        r = load_result(platform, scale_factor, engine, query)
        if r and r["success"]:
            return f"{platform}/{engine} results", r["rows"]
    return None


def diff_ratio(a: str, b: str) -> float:
    la, lb = a.splitlines(), b.splitlines()
    changed = sum(1 for d in difflib.ndiff(la, lb) if d[:1] in "+-")
    return changed / max(len(la), 1) / 2


def classify(platform: str, engine: str, scale_factor: float,
             reference_prefer: list[tuple[str, str]]) -> dict | None:
    """Classify all 22 queries for one engine. None if the engine has not been run."""
    if not (RESULTS / platform / scale_tag(scale_factor) / engine).exists():
        return None
    out = {}
    for q in tpch_sql.QUERY_IDS:
        r = load_result(platform, scale_factor, engine, q)
        ref = reference_for(scale_factor, q, [p for p in reference_prefer if p != (platform, engine)])
        entry = {"query": f"q{q:02d}", "reference": ref[0] if ref else None}
        if r is None:
            entry.update(classification=FAILED, detail="no result file")
            out[entry["query"]] = entry
            continue
        canonical = r["canonical"] if r["variant"] == "adapted" else r
        canonical_ok = canonical["success"] and (
            ref is None or rows_equal(canonical["rows"], ref[1])[0])
        if r["variant"] == "canonical":
            if not r["success"]:
                entry.update(classification=FAILED, detail=r["error"])
            elif ref is None:
                entry.update(classification=PORTABLE, detail="ran unchanged; no reference to compare")
            else:
                ok, why = rows_equal(r["rows"], ref[1])
                entry.update(classification=PORTABLE if ok else FAILED, detail=why)
        else:
            adapted_text = tpch_sql.adapted(engine, q) or ""
            ratio = diff_ratio(tpch_sql.canonical(q), adapted_text)
            if not r["success"]:
                ok, why = False, r["error"]
            elif ref is None:
                ok, why = True, "ran; no reference to compare"
            else:
                ok, why = rows_equal(r["rows"], ref[1])
            if canonical_ok:
                entry.update(classification=PORTABLE, detail="canonical ran correctly; adaptation unused")
            elif ok:
                entry.update(classification=ADAPTABLE if ratio <= MINOR_DIFF_RATIO else REIMPLEMENT,
                             detail=f"adapted ({ratio:.0%} of lines changed); canonical: "
                                    f"{canonical.get('error') or 'wrong result'}")
            else:
                entry.update(classification=FAILED, detail=why)
        entry["duration_s"] = r.get("duration_s")
        out[entry["query"]] = entry
    return out


def summarize(classes: dict) -> dict:
    counts = {k: 0 for k in (PORTABLE, ADAPTABLE, REIMPLEMENT, FAILED)}
    for e in classes.values():
        counts[e["classification"]] += 1
    counts["total"] = len(classes)
    return counts


def scd2_matches(platform: str) -> tuple[bool | None, str]:
    from portability.validation.scd2_reference import expected_scd2

    path = RESULTS / platform / "incremental" / "scd2.json"
    if not path.exists():
        return None, "not run"
    got = json.loads(path.read_text())
    ok = got["rows"] == expected_scd2()
    return ok and got["replay_idempotent"] and got["reingest_refused"], (
        f"rows match reference: {ok}, replay idempotent: {got['replay_idempotent']}, "
        f"re-ingest refused: {got['reingest_refused']}")


def results_exist(platform: str, scale_factor: float, *parts: str) -> bool:
    return os.path.exists(RESULTS.joinpath(platform, scale_tag(scale_factor), *parts))
