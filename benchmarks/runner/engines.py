"""Query engines for the Portability Benchmark.

SparkSqlEngine works with any SparkSession: Databricks (classic or serverless)
and Spark Connect against OpenLakehouse. DuckDbEngine and DataFusionEngine read
Delta tables directly from storage through independent Delta implementations.
"""

from __future__ import annotations

from collections.abc import Callable

import duckdb

from portable_lakehouse.common.tpch_schema import TABLES


class SparkSqlEngine:
    name = "spark"

    def __init__(self, spark, catalog: str, schema: str, platform: str, environment: dict):
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self.platform = platform
        self.environment = environment

    def prepare(self) -> None:
        self.spark.sql(f"USE {self.catalog}.{self.schema}")

    def execute(self, query: str):
        df = self.spark.sql(query)
        rows = df.collect()
        return df.columns, [tuple(r) for r in rows]

    def info(self) -> dict:
        return {"engine_version": self.spark.version, **self.environment}


class DuckDbEngine:
    name = "duckdb"

    def __init__(
        self,
        table_locations: dict[str, str],
        platform: str,
        environment: dict,
        setup: Callable[[duckdb.DuckDBPyConnection], None] | None = None,
        threads: int | None = None,
    ):
        """table_locations maps each TPC-H table to the storage path of its Delta table."""
        self.table_locations = table_locations
        self.platform = platform
        self.environment = environment
        self.setup = setup
        self.threads = threads
        self.con: duckdb.DuckDBPyConnection | None = None

    def prepare(self) -> None:
        self.con = duckdb.connect()
        self.con.execute("INSTALL delta; LOAD delta; INSTALL httpfs; LOAD httpfs;")
        if self.threads:
            self.con.execute(f"SET threads = {int(self.threads)}")
        if self.setup:
            self.setup(self.con)
        for table in TABLES:
            self.con.execute(
                f"CREATE OR REPLACE VIEW {table} AS "
                f"SELECT * FROM delta_scan('{self.table_locations[table]}')"
            )

    def execute(self, query: str):
        cur = self.con.execute(query)
        rows = cur.fetchall()
        return [d[0] for d in cur.description], rows

    def info(self) -> dict:
        return {"engine_version": duckdb.__version__, **self.environment}


class DataFusionEngine:
    """DataFusion SQL over Delta tables exposed as Arrow datasets.

    Imports are intentionally delayed: DataFusion is part of the ``local``
    extra and must not become a dependency of the wheel installed on
    Databricks.
    """

    name = "datafusion"

    def __init__(
        self,
        table_locations: dict[str, str],
        platform: str,
        environment: dict,
        storage_options: dict[str, str] | None = None,
    ):
        self.table_locations = table_locations
        self.platform = platform
        self.environment = environment
        self.storage_options = storage_options or {}
        self.ctx = None
        self._version = None

    def prepare(self) -> None:
        import datafusion
        from deltalake import DeltaTable

        self._version = datafusion.__version__
        self.ctx = datafusion.SessionContext()
        for table in TABLES:
            delta = DeltaTable(self.table_locations[table], storage_options=self.storage_options)
            self.ctx.register_dataset(table, delta.to_pyarrow_dataset())

    def execute(self, query: str):
        if self.ctx is None:
            raise RuntimeError("DataFusionEngine.prepare() must be called before execute()")
        batches = self.ctx.sql(query).collect()
        if not batches:
            return [], []
        columns = list(batches[0].schema.names)
        rows = []
        for batch in batches:
            rows.extend(tuple(record[column] for column in columns) for record in batch.to_pylist())
        return columns, rows

    def info(self) -> dict:
        return {"engine_version": self._version, **self.environment}
