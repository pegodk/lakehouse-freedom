"""Separate pure-Python SCD2 reference implementation.

Applies the synthetic change feed without Spark or SQL so that the MERGE-based
implementation on each platform can be checked against something that shares
none of its code.
"""

from __future__ import annotations

from portable_lakehouse.ingestion.incremental import BATCHES


def expected_scd2() -> list[dict]:
    rows: list[dict] = []
    for _, effective, changes in BATCHES:
        for op, cid, name, segment, city in changes:
            current = next((r for r in rows if r["customer_id"] == cid and r["is_current"]), None)
            same = current is not None and (current["name"], current["segment"], current["city"]) == (
                name, segment, city)
            if op == "D":
                if current:
                    current.update(is_current=False, valid_to=effective)
                continue
            if same:
                continue
            if current:
                current.update(is_current=False, valid_to=effective)
            rows.append({"customer_id": cid, "name": name, "segment": segment, "city": city,
                         "valid_from": effective, "valid_to": None, "is_current": True})
    return sorted(rows, key=lambda r: (r["customer_id"], r["valid_from"]))
