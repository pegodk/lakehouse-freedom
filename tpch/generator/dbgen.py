"""TPC-H data generation with DuckDB's tpch extension.

Generator of record: the DuckDB `tpch` extension (`CALL dbgen(sf=...)`), which
embeds the reference TPC-H dbgen C code (TPC-H v2.x/3.x data generator) and
produces the same rows as the standalone `dbgen` binary for a given scale factor.
The DuckDB version is pinned in pyproject.toml and recorded in every manifest.

Data is generated in `chunks` steps (dbgen's children/step mechanism) so that
memory stays bounded at large scale factors; each step becomes one Parquet file
per table. The output is plain Parquet ("Raw"), the hand-off point into the
lakehouse on every platform.
"""

from __future__ import annotations

import math
import os
import shutil
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timezone

import duckdb

from portable_lakehouse.common.config import scale_tag
from portable_lakehouse.common.tpch_schema import TABLES


def default_chunks(scale_factor: float) -> int:
    """One chunk per scale-factor unit keeps each step around 1 GB of raw data."""
    return max(1, math.ceil(scale_factor))


def generate(
    scale_factor: float,
    raw_root: str,
    chunks: int | None = None,
    duckdb_setup: Callable[[duckdb.DuckDBPyConnection], None] | None = None,
) -> dict:
    """Generate TPC-H at `scale_factor` into `<raw_root>/<sf-tag>/<table>/part-NNNNN.parquet`.

    `raw_root` may be a local path (including FUSE mounts such as /Volumes/...)
    or any URL DuckDB can write to (s3://...). `duckdb_setup` lets the caller
    configure storage access, e.g. an S3 secret, without this module knowing
    which platform it runs on.

    Returns a manifest describing exactly what was generated.
    """
    chunks = chunks or default_chunks(scale_factor)
    tag = scale_tag(scale_factor)
    is_local = "://" not in raw_root
    # Local targets (including FUSE-mounted volumes) are written to a scratch
    # directory first and copied file by file, which avoids random-access
    # writes on mounts that only support sequential IO.
    staging = tempfile.mkdtemp(prefix="tpch-") if is_local else None
    target = staging if is_local else raw_root.rstrip("/")

    con = duckdb.connect()
    con.execute("INSTALL tpch; LOAD tpch;")
    if duckdb_setup:
        duckdb_setup(con)

    rows = {t: 0 for t in TABLES}
    started = time.time()
    for step in range(chunks):
        if chunks == 1:
            con.execute(f"CALL dbgen(sf={scale_factor})")
        else:
            con.execute(f"CALL dbgen(sf={scale_factor}, children={chunks}, step={step})")
        for table in TABLES:
            directory = f"{target}/{tag}/{table}"
            if is_local:
                os.makedirs(directory, exist_ok=True)
            con.execute(
                f"COPY {table} TO '{directory}/part-{step:05d}.parquet' "
                "(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 1000000)"
            )
            rows[table] += con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            con.execute(f"DROP TABLE {table}")

    if is_local:
        final = f"{raw_root.rstrip('/')}/{tag}"
        shutil.rmtree(final, ignore_errors=True)
        for table in TABLES:
            os.makedirs(f"{final}/{table}", exist_ok=True)
            for name in sorted(os.listdir(f"{staging}/{tag}/{table}")):
                shutil.copyfile(f"{staging}/{tag}/{table}/{name}", f"{final}/{table}/{name}")
        shutil.rmtree(staging, ignore_errors=True)

    ext = con.execute(
        "SELECT extension_version FROM duckdb_extensions() WHERE extension_name = 'tpch'"
    ).fetchone()[0]
    return {
        "generator": "duckdb tpch extension (embedded TPC-H dbgen)",
        "duckdb_version": duckdb.__version__,
        "tpch_extension_version": ext,
        "scale_factor": scale_factor,
        "chunks": chunks,
        "raw_root": raw_root,
        "rows": rows,
        "duration_s": round(time.time() - started, 3),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def answers(scale_factor: float) -> dict[int, str]:
    """Reference answers shipped with the DuckDB tpch extension (SF 0.01, 0.1, 1)."""
    con = duckdb.connect()
    con.execute("INSTALL tpch; LOAD tpch;")
    found = con.execute(
        "SELECT query_nr, answer FROM tpch_answers() WHERE scale_factor = ?", [scale_factor]
    ).fetchall()
    return {int(q): a for q, a in found}
