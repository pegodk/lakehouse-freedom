#!/usr/bin/env bash
# Start, stop and inspect the OpenLakehouse services Portable Lakehouse needs:
# storage (SeaweedFS + PostgreSQL), Spark 4.1 (master, worker, Connect) and
# Unity Catalog OSS.
#
# This runs OpenLakehouse's own compose files and its init-storage.sh unchanged.
# It does not call the ./lakehouse CLI, because that CLI probes ports with
# `nc`, which many machines lack. The services, images, versions and config
# are exactly the ones `./lakehouse start storage|spark|unity-catalog` would use.
#
# Usage: stack.sh up | down | destroy | status | restart-spark
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK="${HERE}/stack"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-openlakehouse}"

FILES=(
  -f "${STACK}/docker-compose-storage.yml"
  -f "${STACK}/docker-compose-spark41.yml"
  -f "${STACK}/docker-compose-unity-catalog.yml"
)

compose() { (cd "${STACK}" && docker compose "${FILES[@]}" "$@"); }

wait_for() {
  local name=$1 timeout=$2; shift 2
  local start=$SECONDS
  printf '  waiting for %s ' "${name}"
  until "$@" >/dev/null 2>&1; do
    if (( SECONDS - start > timeout )); then
      echo " timed out after ${timeout}s"
      return 1
    fi
    printf '.'
    sleep 3
  done
  echo " ready"
}

tcp_open() { (exec 3<>"/dev/tcp/$1/$2") 2>/dev/null; }
# Docker publishes 15002 before the Connect server listens, so a TCP probe is
# not enough: run a real query when the project venv exists, else read the log.
PYTHON="${PYTHON:-${HERE}/../../.venv/bin/python}"
spark_ready() {
  if [ -x "${PYTHON}" ]; then
    "${PYTHON}" -c "from pyspark.sql import SparkSession as S; S.builder.remote('sc://localhost:15002').getOrCreate().sql('select 1').collect()"
  else
    docker logs spark-connect-41 2>&1 | grep -q "Spark Connect server started"
  fi
}
http_ok() { curl -sf -o /dev/null "$1"; }

up() {
  [ -f "${STACK}/.env" ] || "${HERE}/scripts/configure.sh"
  echo "Starting storage (SeaweedFS + PostgreSQL)"
  compose up -d postgres seaweedfs
  wait_for "PostgreSQL" 90 docker exec postgres pg_isready -q
  wait_for "SeaweedFS S3" 90 tcp_open localhost 8333
  (cd "${STACK}" && bash scripts/tools/init-storage.sh)

  echo "Starting Unity Catalog OSS"
  compose up -d unity-catalog
  wait_for "Unity Catalog" 120 http_ok http://localhost:8081/api/2.1/unity-catalog/catalogs

  echo "Starting Spark 4.1 (master, worker, Connect)"
  compose up -d spark-master-41 spark-worker-41 spark-connect-41
  wait_for "Spark Connect" 240 spark_ready
  echo "OpenLakehouse is up: Spark Connect sc://localhost:15002, Unity Catalog http://localhost:8081, S3 http://localhost:8333"
}

case "${1:-}" in
  up) up ;;
  restart-spark)
    compose restart spark-connect-41
    wait_for "Spark Connect" 240 spark_ready ;;
  down) compose stop ;;
  destroy) compose down -v ;;
  status) compose ps ;;
  *) echo "usage: $0 up|down|destroy|status|restart-spark" >&2; exit 2 ;;
esac
