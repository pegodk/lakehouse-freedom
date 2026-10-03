# Lakehouse Freedom
#
#   make setup                       one-off: submodule, Python env, OpenLakehouse config and JARs
#   make openlakehouse-up            start SeaweedFS, PostgreSQL, Unity Catalog OSS, Spark 4.1
#   make demo SCALE=1                pipeline, benchmark, Freedom Day, check and report
#
# Individual steps take SCALE (TPC-H scale factor, default 1) and REPEATS.

SCALE   ?= 1
REPEATS ?= 3
PY      := .venv/bin/python
FREEDOM := .venv/bin/freedom
OL      := platforms/openlakehouse/scripts
DBX_DIR := platforms/databricks
DATABRICKS_PROFILE ?=
TABLE_ROOT ?=
DBX     := databricks $(if $(DATABRICKS_PROFILE),-p $(DATABRICKS_PROFILE),)

.DEFAULT_GOAL := help
.PHONY: help setup venv openlakehouse-configure openlakehouse-up openlakehouse-down \
        openlakehouse-destroy openlakehouse-status generate-data pipeline freedom-benchmark \
        freedom-check freedom-day freedom-report freedom-assess demo test test-stack lint \
        databricks-validate databricks-deploy databricks-run databricks-fetch-results clean-results

help:
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'

setup: venv openlakehouse-configure ## One-off setup: submodule, venv, OpenLakehouse config, Spark JARs
	cd platforms/openlakehouse/stack && bash scripts/tools/download-jars.sh

venv: ## Create .venv and install Lakehouse Freedom with local extras
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
	$(FREEDOM) generate --scale $(SCALE)

pipeline: ## Run the full pipeline on OpenLakehouse (SCALE=)
	$(FREEDOM) pipeline --scale $(SCALE)

freedom-benchmark: ## Freedom Benchmark: TPC-H on OpenLakehouse Spark + DuckDB (+ Databricks if DATABRICKS_PROFILE)
	$(FREEDOM) benchmark --scale $(SCALE) --repeats $(REPEATS)
ifneq ($(DATABRICKS_PROFILE),)
	$(MAKE) databricks-run databricks-fetch-results
endif

freedom-day: ## Freedom Day: rebuild the catalog from storage and query with Spark + DuckDB (SCALE=, SOURCE=)
	$(FREEDOM) day --scale $(SCALE) $(if $(SOURCE),--source $(SOURCE),)

freedom-check: ## Freedom Check: validate the workload without Databricks (SCALE=)
	$(FREEDOM) check --scale $(SCALE)

freedom-report: ## Generate reports/freedom-report.md (SCALE=)
	$(FREEDOM) report --scale $(SCALE)

freedom-assess: ## Scan a repository for Databricks-specific code (REPO_PATH=)
	$(FREEDOM) assess $(or $(REPO_PATH),.)

demo: ## Everything, end to end, on OpenLakehouse (SCALE=)
	$(MAKE) pipeline SCALE=$(SCALE)
	$(MAKE) freedom-benchmark SCALE=$(SCALE)
	$(MAKE) freedom-day SCALE=$(SCALE)
	-$(MAKE) freedom-check SCALE=$(SCALE)
	$(MAKE) freedom-report SCALE=$(SCALE)

test: ## Unit and portability tests that need no running stack
	$(PY) -m pytest -m "not stack"

test-stack: ## Tests against the running OpenLakehouse stack (SF0.01)
	$(PY) -m pytest -m stack

lint:
	.venv/bin/ruff check src tpch benchmarks freedom platforms --exclude platforms/openlakehouse/stack

# ── Databricks (managed implementation) ─────────────────────────────────────
databricks-validate: ## Validate the Asset Bundle (DATABRICKS_PROFILE=)
	cd $(DBX_DIR) && $(DBX) bundle validate

databricks-deploy: ## Deploy the bundle (DATABRICKS_PROFILE=, TABLE_ROOT=abfss://...)
	cd $(DBX_DIR) && $(DBX) bundle deploy --var="scale_factor=$(SCALE)" --var="table_root=$(TABLE_ROOT)" --var="repeats=$(REPEATS)"

databricks-run: databricks-deploy ## Deploy and run the job on Databricks (costs compute)
	cd $(DBX_DIR) && $(DBX) bundle run lakehouse_freedom

databricks-fetch-results: ## Copy Databricks results from the results volume into benchmarks/results/databricks
	$(DBX) fs cp -r --overwrite dbfs:/Volumes/freedom/landing/results/databricks benchmarks/results/databricks

clean-results: ## Delete local benchmark results and reports (not the data)
	rm -rf benchmarks/results/openlakehouse benchmarks/results/freedom_day reports/*.json reports/*.md
