"""Catalog portability probe.

For every Unity Catalog capability the Databricks side of this workload relies
on, try to recreate it in Unity Catalog OSS and read it back. Each item is a
live pass/fail measurement against the running stack, not an opinion.

Catalog portability = items recreated / items used by the workload.
"""

from __future__ import annotations

import json
import uuid

from freedom.uc import UnityCatalog
from freedom_platforms.openlakehouse import adapter as ol

PROBE_SCHEMA = "catalog_probe"
# A fresh prefix per run: SeaweedFS keeps empty directories after their objects
# are deleted, and Delta refuses to create a table over a non-empty directory.
PROBE_PREFIX = "freedom/probe"

# (key, what Databricks provides, how it is probed on UC OSS)
ITEMS = [
    ("catalog", "Catalogs", "create and read back a catalog via REST"),
    ("schema", "Schemas", "create and read back a schema via REST"),
    ("external_table", "External Delta tables created from Spark SQL",
     "CREATE TABLE ... USING DELTA LOCATION from Spark; table appears as EXTERNAL DELTA with its location"),
    ("spark_columns", "Column metadata for tables created from Spark",
     "columns of the Spark-created table are returned by the catalog API"),
    ("spark_comment", "Table comments set from Spark SQL",
     "COMMENT clause of the Spark-created table is returned by the catalog API"),
    ("spark_properties", "Custom table properties set from Spark SQL",
     "TBLPROPERTIES of the Spark-created table are returned by the catalog API"),
    ("alter_metadata", "ALTER TABLE for comments and properties",
     "ALTER TABLE ... SET TBLPROPERTIES from Spark succeeds"),
    ("rest_registration", "Registering an existing Delta table with full column metadata",
     "POST /tables with columns and column comments; read back via API and query from Spark"),
    ("volume", "Volumes for raw files", "create and read back an external volume via REST"),
    ("grants", "Grants (GRANT USE SCHEMA ... TO principal)",
     "PATCH /permissions on a schema for an existing UC user; read the grant back"),
]


def probe(uc_url: str | None = None) -> dict:
    uc = UnityCatalog(uc_url or ol.UC_URL)
    run_prefix = f"{PROBE_PREFIX}/{uuid.uuid4().hex[:8]}"
    probe_root = f"s3://lakehouse/{run_prefix}"
    spark = ol.spark_session()
    results: dict[str, dict] = {}

    def record(key: str, ok: bool, evidence: str):
        results[key] = {"recreated": bool(ok), "evidence": evidence}

    # catalog
    name = "freedom_catalog_probe"
    try:
        if uc.get_catalog(name):
            uc.delete_catalog(name)
        uc.create_catalog(name, comment="probe")
        record("catalog", uc.get_catalog(name) is not None, "created and read back")
    except Exception as e:
        record("catalog", False, str(e)[:300])
    finally:
        uc.delete_catalog(name)

    # schema (in the Spark-configured catalog so Spark can use it too)
    spark.sql(f"DROP SCHEMA IF EXISTS freedom.{PROBE_SCHEMA} CASCADE")
    try:
        uc.create_schema("freedom", PROBE_SCHEMA, comment="probe")
        record("schema", any(s["name"] == PROBE_SCHEMA for s in uc.schemas("freedom")), "created and listed")
    except Exception as e:
        record("schema", False, str(e)[:300])

    # Spark-created external table
    table = f"freedom.{PROBE_SCHEMA}.spark_created"
    try:
        spark.sql(
            f"CREATE TABLE {table} (id BIGINT COMMENT 'identifier', label STRING) USING DELTA "
            f"LOCATION '{probe_root}/spark_created' COMMENT 'probe comment' "
            f"TBLPROPERTIES ('freedom.layer' = 'probe')"
        )
        spark.sql(f"INSERT INTO {table} VALUES (1, 'a')")
        meta = uc.get_table(table)
        record("external_table",
               meta.get("table_type") == "EXTERNAL" and meta.get("data_source_format") == "DELTA"
               and meta.get("storage_location", "").endswith("spark_created"),
               f"table_type={meta.get('table_type')}, format={meta.get('data_source_format')}, "
               f"location={meta.get('storage_location')}")
        cols = meta.get("columns") or []
        record("spark_columns", len(cols) == 2, f"catalog API returned {len(cols)} of 2 columns")
        record("spark_comment", meta.get("comment") == "probe comment",
               f"catalog API comment={meta.get('comment')!r}")
        props = meta.get("properties") or {}
        record("spark_properties", props.get("freedom.layer") == "probe",
               f"catalog API properties={json.dumps(props)}")
        try:
            spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES ('freedom.owner' = 'probe')")
            record("alter_metadata", True, "ALTER TABLE succeeded")
        except Exception as e:
            record("alter_metadata", False, str(e).splitlines()[0][:300])
    except Exception as e:
        for k in ("external_table", "spark_columns", "spark_comment", "spark_properties", "alter_metadata"):
            results.setdefault(k, {"recreated": False, "evidence": str(e).splitlines()[0][:300]})

    # REST registration of the existing Delta data with full column metadata
    try:
        registered = f"freedom.{PROBE_SCHEMA}.rest_registered"
        uc.create_table({
            "name": "rest_registered", "catalog_name": "freedom", "schema_name": PROBE_SCHEMA,
            "table_type": "EXTERNAL", "data_source_format": "DELTA",
            "storage_location": f"{probe_root}/spark_created", "comment": "registered via REST",
            "properties": {"freedom.layer": "probe"},
            "columns": [
                {"name": "id", "type_name": "LONG", "type_text": "bigint", "position": 0,
                 "type_json": json.dumps({"name": "id", "type": "long", "nullable": True, "metadata": {}}),
                 "nullable": True, "comment": "identifier"},
                {"name": "label", "type_name": "STRING", "type_text": "string", "position": 1,
                 "type_json": json.dumps({"name": "label", "type": "string", "nullable": True, "metadata": {}}),
                 "nullable": True},
            ],
        })
        meta = uc.get_table(registered)
        rows = spark.sql(f"SELECT count(*) AS n FROM {registered}").collect()[0]["n"]
        cols = meta.get("columns") or []
        ok = len(cols) == 2 and cols[0].get("comment") == "identifier" and rows == 1 and (
            meta.get("properties") or {}).get("freedom.layer") == "probe"
        record("rest_registration", ok, f"{len(cols)} columns, column comment "
               f"{cols[0].get('comment') if cols else None!r}, properties "
               f"{json.dumps(meta.get('properties'))}, Spark read {rows} row(s)")
    except Exception as e:
        record("rest_registration", False, str(e)[:300])

    # volume
    try:
        uc.create_volume({"catalog_name": "freedom", "schema_name": PROBE_SCHEMA, "name": "raw_files",
                          "volume_type": "EXTERNAL", "storage_location": f"{probe_root}/volume"})
        vols = uc.volumes("freedom", PROBE_SCHEMA)
        record("volume", any(v["name"] == "raw_files" for v in vols), f"{len(vols)} volume(s) listed")
    except Exception as e:
        record("volume", False, str(e)[:300])

    # grants
    try:
        principal = "freedom-analyst@example.com"
        uc.session.post(uc.base.replace("/api/2.1/unity-catalog", "/api/1.0/unity-control/scim2/Users"),
                        json={"displayName": "freedom analyst",
                              "emails": [{"value": principal, "primary": True}]}, timeout=30)
        uc.session.patch(f"{uc.base}/permissions/schema/freedom.{PROBE_SCHEMA}", timeout=30,
                         json={"changes": [{"principal": principal, "add": ["USE SCHEMA"]}]})
        got = uc._get(f"permissions/schema/freedom.{PROBE_SCHEMA}")
        stored = got.get("privilege_assignments") or []
        record("grants", bool(stored),
               f"grant read back: {json.dumps(stored)}; server.authorization is "
               f"'disable' in the OpenLakehouse default config")
    except Exception as e:
        record("grants", False, str(e)[:300])

    spark.sql(f"DROP SCHEMA IF EXISTS freedom.{PROBE_SCHEMA} CASCADE")
    try:
        bucket, prefix = "lakehouse", run_prefix + "/"
        s3 = ol.boto3_client()
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                s3.delete_object(Bucket=bucket, Key=obj["Key"])
    except Exception:
        pass

    items = [{"key": k, "capability": cap, "probe": how, **results.get(k, {"recreated": False,
              "evidence": "not probed"})} for k, cap, how in ITEMS]
    passed = sum(i["recreated"] for i in items)
    return {"items": items, "recreated": passed, "total": len(items), "score": passed / len(items)}
