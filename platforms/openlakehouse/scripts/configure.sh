#!/usr/bin/env bash
# Writes the gitignored runtime config that the OpenLakehouse stack expects
# (.env, spark-defaults.conf, server.properties) into the pinned submodule.
#
# Everything is derived from the stack's own *.example files plus the small
# Portable Lakehouse overlay in ../config, so upgrading the submodule picks up
# upstream changes automatically. Nothing tracked in the submodule is modified.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK="${HERE}/stack"
CONFIG="${HERE}/config"

if [ ! -f "${STACK}/lakehouse" ]; then
  echo "OpenLakehouse submodule missing. Run: git submodule update --init" >&2
  exit 1
fi

export PORTABLE_LAKEHOUSE_SPARK_DRIVER_MEMORY="${PORTABLE_LAKEHOUSE_SPARK_DRIVER_MEMORY:-2g}"
export PORTABLE_LAKEHOUSE_SPARK_EXECUTOR_MEMORY="${PORTABLE_LAKEHOUSE_SPARK_EXECUTOR_MEMORY:-7g}"
export PORTABLE_LAKEHOUSE_SPARK_EXECUTOR_CORES="${PORTABLE_LAKEHOUSE_SPARK_EXECUTOR_CORES:-6}"
export PORTABLE_LAKEHOUSE_SPARK_SHUFFLE_PARTITIONS="${PORTABLE_LAKEHOUSE_SPARK_SHUFFLE_PARTITIONS:-24}"

cp "${CONFIG}/portable-lakehouse.env" "${STACK}/.env"
set -a
# shellcheck disable=SC1091
. "${STACK}/.env"
set +a

# Spark: upstream example with credentials filled in, then our overrides.
{
  sed -e "s|^spark.hadoop.fs.s3a.access.key .*|spark.hadoop.fs.s3a.access.key            ${S3_ACCESS_KEY}|" \
      -e "s|^spark.hadoop.fs.s3a.secret.key .*|spark.hadoop.fs.s3a.secret.key            ${S3_SECRET_KEY}|" \
      "${STACK}/config/spark/spark-defaults.conf.example"
  echo
  envsubst < "${CONFIG}/spark-defaults.portable-lakehouse.conf"
} > "${STACK}/config/spark/spark-defaults.conf"

# Unity Catalog OSS: upstream example with the SeaweedFS key pair filled in.
sed -e "s|^s3.accessKey.0=.*|s3.accessKey.0=${S3_ACCESS_KEY}|" \
    -e "s|^s3.secretKey.0=.*|s3.secretKey.0=${S3_SECRET_KEY}|" \
    "${STACK}/config/unity-catalog/server.properties.example" \
    > "${STACK}/config/unity-catalog/server.properties"

echo "OpenLakehouse configured:"
echo "  ${STACK}/.env"
echo "  ${STACK}/config/spark/spark-defaults.conf (executor ${PORTABLE_LAKEHOUSE_SPARK_EXECUTOR_CORES} cores / ${PORTABLE_LAKEHOUSE_SPARK_EXECUTOR_MEMORY})"
echo "  ${STACK}/config/unity-catalog/server.properties"
