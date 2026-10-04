# Portable Lakehouse
#
#   make setup                       one-off: submodule, Python env, OpenLakehouse config and JARs
#   make openlakehouse-up            start SeaweedFS, PostgreSQL, Unity Catalog OSS, Spark 4.1
#   make demo SCALE=1                pipeline, benchmark, check and report
#
# Individual steps take SCALE (TPC-H scale factor, default 1) and REPEATS.

SCALE   ?= 1
REPEATS ?= 3
PY      := .venv/bin/python
PORTABLE_LAKEHOUSE := .venv/bin/portable-lakehouse
OL      := platforms/openlakehouse/scripts
DBX_DIR := platforms/databricks
DATABRICKS_PROFILE ?=
TABLE_ROOT ?=
DBX     := databricks $(if $(DATABRICKS_PROFILE),-p $(DATABRICKS_PROFILE),)

.DEFAULT_GOAL := help
.PHONY: help setup venv openlakehouse-configure openlakehouse-up openlakehouse-down \
        openlakehouse-destroy openlakehouse-status generate-data pipeline portability-benchmark \
        portability-check portability-report portability-assess demo test test-stack lint docs-serve docs-build \
        databricks-validate databricks-deploy databricks-run databricks-fetch-results clean-results

help:
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'

setup: venv openlakehouse-configure ## One-off setup: submodule, venv, OpenLakehouse config, Spark JARs
	cd platforms/openlakehouse/stack && bash scripts/tools/download-jars.sh

venv: ## Create .venv and install Portable Lakehouse with local extras
	git submodule update --init --recursive
	uv venv --allow-existing -p 3.12 .venv
	uv pip install --python $(PY) -e '.[local,dev,databricks]'

openlakehouse-configure: ## Write OpenLakehouse runtime config from its examples + our overlay
	$(OL)/configure.sh

openlakehouse-up: ## Start the OpenLakehouse services used here
	$(OL)/stack.sh up

openlakehouse-down: ## Stop OpenLakehouse (data kept in Docker volumes)
	$(OL)/stack.sh down

openlakehouse-destroy: ## Stop OpenLakehouse and delete its volumes (all data)
	$(OL)/stack.sh destroy

openlakehouse-status: ## Show OpenLakehouse containers
	$(OL)/stack.sh status

generate-data: ## Generate TPC-H Raw Parquet into OpenLakehouse storage (SCALE=)
	$(PORTABLE_LAKEHOUSE) generate --scale $(SCALE)

pipeline: ## Run the full pipeline on OpenLakehouse (SCALE=)
	$(PORTABLE_LAKEHOUSE) pipeline --scale $(SCALE)

portability-benchmark: ## Portability Benchmark: Spark + DuckDB + DataFusion (+ Databricks if configured)
	$(PORTABLE_LAKEHOUSE) benchmark --scale $(SCALE) --repeats $(REPEATS)
ifneq ($(DATABRICKS_PROFILE),)
	$(MAKE) databricks-run databricks-fetch-results
endif

portability-check: ## Portability Check: validate the workload without Databricks (SCALE=)
	$(PORTABLE_LAKEHOUSE) check --scale $(SCALE)

portability-report: ## Generate reports/portability-report.md (SCALE=)
	$(PORTABLE_LAKEHOUSE) report --scale $(SCALE)

portability-assess: ## Scan a repository for Databricks-specific code (REPO_PATH=)
	$(PORTABLE_LAKEHOUSE) assess $(or $(REPO_PATH),.)

demo: ## Everything, end to end, on OpenLakehouse (SCALE=)
	$(MAKE) pipeline SCALE=$(SCALE)
	$(MAKE) portability-benchmark SCALE=$(SCALE)
	-$(MAKE) portability-check SCALE=$(SCALE)
	$(MAKE) portability-report SCALE=$(SCALE)

test: ## Unit and portability tests that need no running stack
	$(PY) -m pytest -m "not stack"

test-stack: ## Tests against the running OpenLakehouse stack (SF0.01)
	$(PY) -m pytest -m stack

lint: ## Lint with ruff
	.venv/bin/ruff check src tpch benchmarks portability platforms tests --exclude platforms/openlakehouse/stack

docs-serve: ## Preview the documentation site on http://localhost:8000
	uv pip install --python $(PY) -q -e '.[docs]'
	.venv/bin/zensical serve

docs-build: ## Build the documentation site into ./site
	uv pip install --python $(PY) -q -e '.[docs]'
	.venv/bin/zensical build --clean

# ── Databricks (managed implementation) ─────────────────────────────────────
databricks-validate: ## Validate the Asset Bundle (DATABRICKS_PROFILE=)
	cd $(DBX_DIR) && $(DBX) bundle validate

databricks-deploy: ## Deploy the bundle (DATABRICKS_PROFILE=, TABLE_ROOT=abfss://...)
	cd $(DBX_DIR) && $(DBX) bundle deploy --var="scale_factor=$(SCALE)" --var="table_root=$(TABLE_ROOT)" --var="repeats=$(REPEATS)"

databricks-run: databricks-deploy ## Deploy and run the job on Databricks (costs compute)
	cd $(DBX_DIR) && $(DBX) bundle run portable_lakehouse

databricks-fetch-results: ## Copy Databricks results from the results volume into benchmarks/results/databricks
	$(DBX) fs cp -r --overwrite dbfs:/Volumes/portable_lakehouse/landing/results/databricks benchmarks/results/databricks

clean-results: ## Delete local benchmark results and reports (not the data)
	rm -rf benchmarks/results/openlakehouse reports/*.json reports/*.md
