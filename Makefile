# =========================================================
# Stable Engineering Makefile (Odoo 17 + Docker Compose)
# - Thin Makefile: all logic lives in scripts/
# - Windows Git Bash / MSYS2 friendly
# =========================================================

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ------------------ Compose ------------------
COMPOSE ?= docker compose
# Prefer v2 `docker compose` if subcommand exists, otherwise fallback to `docker-compose`
COMPOSE_BIN ?= $(shell \
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; \
  elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then echo "docker-compose"; \
  else echo "docker compose"; fi)
COMPOSE_PROJECT_NAME ?= sc-backend-odoo
PROJECT    ?= $(COMPOSE_PROJECT_NAME)

# Compose files / overlays
COMPOSE_FILE_BASE ?= docker-compose.yml
COMPOSE_FILE_TESTDEPS ?= docker-compose.testdeps.yml
COMPOSE_FILE_CI ?= docker-compose.ci.yml
COMPOSE_FILES ?= -f $(COMPOSE_FILE_BASE)
COMPOSE_TEST_FILES ?= -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_TESTDEPS)
COMPOSE_CI_FILES ?= -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_CI)

# Canonical compose commands
COMPOSE_BASE      = $(COMPOSE_BIN) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE_BASE)
COMPOSE_TESTDEPS  = $(COMPOSE_BIN) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_TESTDEPS)
COMPOSE_CI        = $(COMPOSE_BIN) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_CI)

# ------------------ DB / Module ------------------
DB_NAME := sc_odoo
DB_CI   ?= sc_test
DB_USER := odoo
DB_PASSWORD ?= $(DB_USER)
DEMO_TIMEOUT ?= 600
DEMO_LOG_TAIL ?= 200
DEMO_LOG_SERVICE ?= $(ODOO_SERVICE)

# === Odoo Runtime (Single Source of Truth) ===
ODOO_SERVICE ?= odoo
ODOO_CONF    ?= /var/lib/odoo/odoo.conf
ODOO_DB      ?= $(DB_NAME)

# Unified Odoo execution (never bypass entrypoint config)
ODOO_EXEC = $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) odoo -c $(ODOO_CONF) -d $(ODOO_DB)

# ------------------ DB override (single entry) ------------------
# Use one knob to control dev/test db: `make test DB=sc_test`
# CI keeps its own DB_CI unless你显式覆盖。
DB ?=
ifneq ($(strip $(DB)),)
DB_NAME := $(DB)
endif

MODULE ?= smart_construction_core
WITHOUT_DEMO ?= --without-demo=all
ODOO_ARGS ?=

# ------------------ Addons / Docs mount ------------------
# 外部 addons 仓库（git submodule）默认路径：项目内 addons_external/...
ADDONS_EXTERNAL_HOST ?= $(ROOT_DIR)/addons_external/oca_server_ux
# odoo 容器内的挂载路径
ADDONS_EXTERNAL_MOUNT ?= /mnt/addons_external/oca_server_ux
BASE_ADDONS_PATH := /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
EXTRA_ADDONS_PATH := $(shell \
  if [ -n "$(ADDONS_EXTERNAL_HOST)" ] && [ -d "$(ADDONS_EXTERNAL_HOST)" ]; then \
    echo ",$(ADDONS_EXTERNAL_MOUNT)"; \
  fi)
ODOO_ADDONS_PATH := $(BASE_ADDONS_PATH)$(EXTRA_ADDONS_PATH)
DOCS_MOUNT_HOST ?= $(ROOT_DIR)/docs
DOCS_MOUNT_CONT ?= /mnt/docs

# ------------------ Test tags ------------------
# 你写 sc_gate,sc_perm，脚本会自动变成 /smart_construction_core:sc_gate,/smart_construction_core:sc_perm
TEST_TAGS ?= sc_smoke,sc_gate

# ------------------ CI artifacts ------------------
CI_LOG          ?= test-ci.log
CI_ARTIFACT_DIR ?= artifacts/ci
CI_PASS_SIG_RE  ?= (0 failed, 0 error\(s\))

CI_ARTIFACT_PURGE ?= 1
CI_ARTIFACT_KEEP  ?= 30

CI_TAIL_ODOO ?= 2000
CI_TAIL_DB   ?= 800
CI_TAIL_REDIS?= 400

# ------------------ MSYS / Git Bash tweaks ------------------
export COMPOSE_ANSI := never
export MSYS_NO_PATHCONV := 1
export MSYS2_ARG_CONV_EXCL := --test-tags

# ------------------ Script runner common env ------------------
define RUN_ENV
ROOT_DIR="$(ROOT_DIR)" \
COMPOSE_BIN="$(COMPOSE_BIN)" \
COMPOSE_PROJECT_NAME="$(COMPOSE_PROJECT_NAME)" \
PROJECT="$(PROJECT)" \
COMPOSE_FILES="$(COMPOSE_FILES)" \
COMPOSE_TEST_FILES="$(COMPOSE_TEST_FILES)" \
COMPOSE_CI_FILES="$(COMPOSE_CI_FILES)" \
DB_NAME="$(DB_NAME)" \
DB_CI="$(DB_CI)" \
DB_USER="$(DB_USER)" \
DB_PASSWORD="$(DB_PASSWORD)" \
MODULE="$(MODULE)" \
TEST_TAGS="$(TEST_TAGS)" \
ADDONS_EXTERNAL_MOUNT="$(ADDONS_EXTERNAL_MOUNT)" \
DOCS_MOUNT_HOST="$(DOCS_MOUNT_HOST)" \
DOCS_MOUNT_CONT="$(DOCS_MOUNT_CONT)" \
CI_LOG="$(CI_LOG)" \
CI_ARTIFACT_DIR="$(CI_ARTIFACT_DIR)" \
CI_PASS_SIG_RE='$(CI_PASS_SIG_RE)' \
CI_ARTIFACT_PURGE="$(CI_ARTIFACT_PURGE)" \
CI_ARTIFACT_KEEP="$(CI_ARTIFACT_KEEP)" \
CI_TAIL_ODOO="$(CI_TAIL_ODOO)" \
CI_TAIL_DB="$(CI_TAIL_DB)" \
CI_TAIL_REDIS="$(CI_TAIL_REDIS)"
endef

# ======================================================
# ==================== Help ============================
# ======================================================
.PHONY: help
help:
	@echo "Targets:"
	@echo "  make up/down/restart/logs/ps/odoo-shell/db.reset/demo.reset"
	@echo "  make mod.install MODULE=... [DB=...] | mod.upgrade MODULE=... [DB=...]"
	@echo "  make db.branch | db.create DB=<name> | db.reset.manual DB=<name>"
	@echo "  make test | test.safe"
	@echo "  make ci.gate | ci.smoke | ci.full | ci.repro"
	@echo "  make ci.clean | ci.ps | ci.logs | ci.repro"
	@echo "  make diag.compose"
	@echo
	@echo "Common vars:"
	@echo "  MODULE=$(MODULE) DB_CI=$(DB_CI) TEST_TAGS=$(TEST_TAGS)"
	@echo "  COMPOSE_BIN='$(COMPOSE_BIN)' PROJECT='$(PROJECT)'"

# ======================================================
# ==================== Dev =============================
# ======================================================
.PHONY: up down restart logs ps odoo-shell
up: check-compose-project
	@$(RUN_ENV) bash scripts/dev/up.sh
down: check-compose-project
	@$(RUN_ENV) bash scripts/dev/down.sh
restart: check-compose-project
	@$(RUN_ENV) bash scripts/dev/restart.sh
logs: check-compose-project
	@$(RUN_ENV) bash scripts/dev/logs.sh
ps: check-compose-project
	@$(RUN_ENV) bash scripts/dev/ps.sh
odoo-shell: check-compose-project
	@$(RUN_ENV) bash scripts/dev/shell.sh
.PHONY: odoo.recreate odoo.logs odoo.exec
odoo.recreate: check-compose-project
	@echo "[odoo.recreate] service=$(ODOO_SERVICE)"
	@$(RUN_ENV) $(COMPOSE_BASE) up -d --force-recreate $(ODOO_SERVICE)
odoo.logs: check-compose-project
	@$(RUN_ENV) $(COMPOSE_BASE) logs --tail=200 $(ODOO_SERVICE)
odoo.exec: check-compose-project
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) bash
db.reset:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/db/reset.sh
demo.reset:
	@echo "[demo.reset] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(MAKE) db.reset DB_NAME=$(DB_NAME)
db.demo.reset:
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh
db.branch:
	@bash scripts/db/branch_db.sh
db.create:
	@bash scripts/db/create.sh $(DB)
db.reset.manual:
	@bash scripts/db/reset_manual.sh $(DB)
verify.baseline:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
verify.demo:
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh
gate.baseline:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/db/reset.sh
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
gate.demo:
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh

# ======================================================
# ==================== Module Ops ======================
# ======================================================
.PHONY: check-compose-project
check-compose-project:
	@set -e; \
	for c in sc-db sc-redis sc-odoo sc-nginx; do \
	  if docker inspect $$c >/dev/null 2>&1; then \
	    p="$$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' $$c 2>/dev/null || true)"; \
	    if [ -n "$$p" ] && [ "$$p" != "$(COMPOSE_PROJECT_NAME)" ]; then \
	      echo "❌ compose project mismatch: container $$c belongs to '$$p', Makefile wants '$(COMPOSE_PROJECT_NAME)'"; \
	      echo "   Fix: set COMPOSE_PROJECT_NAME=$$p (recommended) or remove conflicting containers."; \
	      exit 2; \
	    fi; \
	  fi; \
	done

.PHONY: check-external-addons
check-external-addons:
	@if [ ! -d "$(ADDONS_EXTERNAL_HOST)" ]; then \
		echo "❌ external addons missing: $(ADDONS_EXTERNAL_HOST)"; \
		echo "   Fix: git submodule update --init --recursive"; \
		exit 2; \
	fi
	@if [ -z "$$(find "$(ADDONS_EXTERNAL_HOST)" -maxdepth 2 -name '__manifest__.py' 2>/dev/null | head -n 1)" ]; then \
		echo "❌ external addons exists but contains no addons: $(ADDONS_EXTERNAL_HOST)"; \
		exit 2; \
	fi

.PHONY: check-odoo-conf
check-odoo-conf:
	@test "$(ODOO_CONF)" = "/var/lib/odoo/odoo.conf" || \
	  (echo "❌ ODOO_CONF must be /var/lib/odoo/odoo.conf" && exit 1)

.PHONY: mod.install mod.upgrade
mod.install: check-compose-project check-odoo-conf check-external-addons
	@echo "[mod.install] module=$(MODULE) db=$(DB_NAME)"
	@test -n "$(MODULE)" || (echo "ERROR: MODULE is required. e.g. make mod.install MODULE=smart_construction_core" && exit 2)
	@$(RUN_ENV) $(ODOO_EXEC) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=$(ODOO_ADDONS_PATH) \
		-i $(MODULE) \
		$(WITHOUT_DEMO) \
		--no-http --workers=0 --max-cron-threads=0 \
		--stop-after-init $(ODOO_ARGS)

mod.upgrade: check-compose-project check-odoo-conf check-external-addons
	@echo "[mod.upgrade] module=$(MODULE) db=$(DB_NAME)"
	@test -n "$(MODULE)" || (echo "ERROR: MODULE is required. e.g. make mod.upgrade MODULE=smart_construction_core" && exit 2)
	@$(RUN_ENV) $(ODOO_EXEC) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=$(ODOO_ADDONS_PATH) \
		-u $(MODULE) \
		$(WITHOUT_DEMO) \
		--no-http --workers=0 --max-cron-threads=0 \
		--stop-after-init $(ODOO_ARGS)

.ONESHELL: demo.verify
.PHONY: demo.verify
demo.verify:
	@echo "[demo.verify] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@scenario="$(SCENARIO)"; step="$(STEP)"; \
	known="s00_min_path s10_contract_payment s20_settlement_clearing s30_settlement_workflow s40_failure_paths s50_repairable_paths s90_users_roles"; \
	if [ -n "$$scenario" ]; then \
		found=0; for s in $$known; do [ "$$scenario" = "$$s" ] && found=1; done; \
		if [ $$found -eq 0 ]; then \
			echo "ERROR: unknown SCENARIO '$$scenario'. known: $$known"; exit 2; \
		fi; \
	fi; \
	psql_cmd() { $(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -v ON_ERROR_STOP=1 "$$@"; }; \
	run_check() { \
		desc="$$1"; scen="$$2"; ok_sql="$$3"; sample_sql="$$4"; \
		if [ -n "$$scenario" ] && [ "$$scenario" != "$$scen" ]; then return 0; fi; \
		if psql_cmd -At -c "$$ok_sql" | grep -qx ok; then \
			echo "✓ $$desc"; \
			return 0; \
		fi; \
		echo "✗ $$desc"; \
		if [ -n "$$sample_sql" ]; then \
			echo "[sample]"; psql_cmd -c "$$sample_sql" || true; echo "[/sample]"; \
		fi; \
		exit 1; \
	}; \
	run_expect_fail() { \
		desc="$$1"; scen="$$2"; ok_sql="$$3"; sample_sql="$$4"; \
		if [ "$$scenario" != "$$scen" ] || [ "$$step" != "bad" ]; then return 0; fi; \
		if psql_cmd -At -c "$$ok_sql" | grep -qx ok; then \
			echo "✗ $$desc (expected failure)"; \
			if [ -n "$$sample_sql" ]; then \
				echo "[sample]"; psql_cmd -c "$$sample_sql" || true; echo "[/sample]"; \
			fi; \
			exit 1; \
		fi; \
		echo "✗ $$desc (bad condition missing)"; \
		exit 1; \
	}; \
	run_check "S00 projects >= 2" "s00_min_path" \
		"select case when count(*) >= 2 then 'ok' else 'project < 2' end from project_project;" \
		"select id, name from project_project order by id limit 20;"; \
	run_check "S00 BOQ nodes >= 2" "s00_min_path" \
		"select case when count(*) >= 2 then 'ok' else 'boq < 2' end from project_boq_line;" \
		"select id, name, project_id, parent_id from project_boq_line order by id limit 20;"; \
	run_check "S00 material plans >= 1" "s00_min_path" \
		"select case when count(*) >= 1 then 'ok' else 'material plan < 1' end from project_material_plan;" \
		"select id, name, project_id from project_material_plan order by id limit 20;"; \
	run_check "S00 invoices >= 2" "s00_min_path" \
		"select case when count(*) >= 2 then 'ok' else 'invoice < 2' end from account_move where move_type in ('out_invoice','out_refund');" \
		"select id, name, state, move_type, invoice_date from account_move where move_type in ('out_invoice','out_refund') order by id limit 20;"; \
	run_check "S10 contract record exists" "s10_contract_payment" \
		"select case when count(*) = 1 then 'ok' else 'S10 contract missing' end from construction_contract where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_contract_out_010');" \
		"select id, subject, type, project_id, partner_id from construction_contract where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_contract_out_010');"; \
	run_check "S10 payment request record exists" "s10_contract_payment" \
		"select case when count(*) = 1 then 'ok' else 'S10 payment request missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_pay_req_010_001');" \
		"select id, type, amount, project_id, contract_id, partner_id, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_pay_req_010_001');"; \
	run_check "S10 invoices >= 2" "s10_contract_payment" \
		"select case when count(*) >= 2 then 'ok' else 'S10 invoices < 2' end from account_move where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_invoice_s10_001','sc_demo_invoice_s10_002'));" \
		"select id, name, state, move_type, invoice_date, amount_total from account_move where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_invoice_s10_001','sc_demo_invoice_s10_002')) order by id;"; \
	run_check "S20 payment record exists" "s20_settlement_clearing" \
		"select case when count(*) = 1 then 'ok' else 'S20 payment missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_020_001');" \
		"select id, type, amount, project_id, contract_id, partner_id, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_020_001');"; \
	run_check "S20 settlement order exists" "s20_settlement_clearing" \
		"select case when count(*) = 1 then 'ok' else 'S20 settlement missing' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');" \
		"select id, name, state, amount_total, settlement_type from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');"; \
	run_check "S20 settlement lines >= 2" "s20_settlement_clearing" \
		"select case when count(*) >= 2 then 'ok' else 'S20 settlement lines < 2' end from sc_settlement_order_line where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_settle_line_020_001','sc_demo_settle_line_020_002'));" \
		"select id, settlement_id, name, qty, price_unit, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001') order by id;"; \
	run_check "S20 settlement links to at least 1 payment request" "s20_settlement_clearing" \
		"select case when count(*) >= 1 then 'ok' else 'S20 settlement has no linked payment_request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');" \
		"select id, type, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001') order by id;"; \
	run_check "S30 settlement exists and stays in draft" "s30_settlement_workflow" \
		"select case when count(*) = 1 then 'ok' else 'S30 settlement missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') and state = 'draft';" \
		"select id, name, state, amount_total, settlement_type from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');"; \
	run_check "S30 settlement has at least one line" "s30_settlement_workflow" \
		"select case when count(*) >= 1 then 'ok' else 'S30 settlement has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');" \
		"select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') order by id;"; \
	run_check "S30 settlement links to payment requests" "s30_settlement_workflow" \
		"select case when count(*) >= 1 then 'ok' else 'S30 settlement has no linked payment_request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');" \
		"select id, type, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') order by id;"; \
	run_check "S30 settlement amount matches line sum" "s30_settlement_workflow" \
		"select case when abs(o.amount_total - sum(l.amount)) < 0.01 then 'ok' else 'S30 settlement amount mismatch' end from sc_settlement_order o join sc_settlement_order_line l on l.settlement_id = o.id where o.id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') group by o.amount_total;" \
		"select o.id, o.amount_total, sum(l.amount) as line_sum from sc_settlement_order o join sc_settlement_order_line l on l.settlement_id = o.id where o.id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') group by o.id, o.amount_total;"; \
	run_check "S30 gate: bad settlement stays draft" "s30_settlement_workflow" \
		"select case when count(*) = 1 then 'ok' else 'S30 gate failed' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_bad_001') and state = 'draft';" \
		"select id, name, state from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_bad_001');"; \
	run_check "S40 structural settlement stays draft" "s40_failure_paths" \
		"select case when count(*) = 1 then 'ok' else 'S40 structural missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad') and state = 'draft';" \
		"select id, name, state from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');"; \
	run_check "S40 structural has no lines" "s40_failure_paths" \
		"select case when count(*) = 0 then 'ok' else 'S40 structural has lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');" \
		"select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');"; \
	run_check "S40 structural has no payment requests" "s40_failure_paths" \
		"select case when count(*) = 0 then 'ok' else 'S40 structural has payment requests' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');" \
		"select id, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_structural_bad');"; \
	run_check "S40 amount mismatch stays draft" "s40_failure_paths" \
		"select case when count(*) = 1 then 'ok' else 'S40 amount missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad') and state = 'draft';" \
		"select id, name, state, amount_total from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');"; \
	run_check "S40 amount has lines" "s40_failure_paths" \
		"select case when count(*) >= 1 then 'ok' else 'S40 amount has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');" \
		"select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad') order by id;"; \
	run_check "S40 amount links payment request" "s40_failure_paths" \
		"select case when count(*) >= 1 then 'ok' else 'S40 amount has no payment request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');" \
		"select id, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad');"; \
	run_check "S40 amount inconsistency (payment > settlement)" "s40_failure_paths" \
		"select case when (select coalesce(sum(pr.amount), 0) from payment_request pr where pr.settlement_id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) > (select amount_total from sc_settlement_order where id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) then 'ok' else 'S40 amount not inconsistent' end;" \
		"select (select amount_total from sc_settlement_order where id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) as settlement_total, (select coalesce(sum(pr.amount), 0) from payment_request pr where pr.settlement_id = (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_amount_bad')) as payment_total;"; \
	run_check "S40 link bad stays draft" "s40_failure_paths" \
		"select case when count(*) = 1 then 'ok' else 'S40 link missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad') and state = 'draft';" \
		"select id, name, state from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');"; \
	run_check "S40 link bad has lines" "s40_failure_paths" \
		"select case when count(*) >= 1 then 'ok' else 'S40 link has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');" \
		"select id, settlement_id, name, amount from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad') order by id;"; \
	run_check "S40 link bad has no linked payment request" "s40_failure_paths" \
		"select case when count(*) = 0 then 'ok' else 'S40 link unexpectedly linked' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');" \
		"select id, amount, settlement_id from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_040_link_bad');"; \
	run_check "S40 unlinked payment request exists" "s40_failure_paths" \
		"select case when count(*) = 1 then 'ok' else 'S40 unlinked payment missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_040_link_001') and settlement_id is null;" \
		"select id, amount, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_040_link_001');"; \
	run_check "S40 settlements never leave draft" "s40_failure_paths" \
		"select case when count(*) = 0 then 'ok' else 'S40 settlement advanced' end from sc_settlement_order where name like 'S40-%' and state <> 'draft';" \
		"select id, name, state from sc_settlement_order where name like 'S40-%' and state <> 'draft' order by id;"; \
	run_expect_fail "S50 bad seed should fail verification" "s50_repairable_paths" \
		"select case when count(*) = 0 then 'ok' else 'S50 bad still linked' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_050_001');" \
		"select id, amount, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_050_001');"; \
	run_check "S50 settlement links payment request after fix" "s50_repairable_paths" \
		"select case when count(*) = 1 then 'ok' else 'S50 payment not linked' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_050_001');" \
		"select id, amount, settlement_id from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_050_001');"; \
	run_check "S90 users exist" "s90_users_roles" \
		"select case when count(*) >= 5 then 'ok' else 'S90 users missing' end from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly');" \
		"select id, login, active from res_users where login in ('demo_pm','demo_finance','demo_cost','demo_audit','demo_readonly') order by login;"; \
	run_check "S90 finance user lacks contract capability" "s90_users_roles" \
		"select case when count(*) = 0 then 'ok' else 'S90 finance has contract group' end from res_groups_users_rel r where r.uid = (select id from res_users where login='demo_finance') and r.gid in (select id from res_groups where coalesce(name->>'zh_CN', name->>'en_US') like 'SC 能力 - 合同中心%');" \
		"select u.login, coalesce(g.name->>'zh_CN', g.name->>'en_US') as group_name from res_groups_users_rel r join res_users u on u.id = r.uid join res_groups g on g.id = r.gid where u.login='demo_finance' order by group_name;"; \
	run_check "S90 readonly user not in settlement user group" "s90_users_roles" \
		"select case when count(*) = 0 then 'ok' else 'S90 readonly has settlement group' end from res_groups_users_rel r where r.uid = (select id from res_users where login='demo_readonly') and r.gid in (select id from res_groups where coalesce(name->>'zh_CN', name->>'en_US') = 'SC 能力 - 结算中心经办');" \
		"select u.login, coalesce(g.name->>'zh_CN', g.name->>'en_US') as group_name from res_groups_users_rel r join res_users u on u.id = r.uid join res_groups g on g.id = r.gid where u.login='demo_readonly' order by group_name;"; \
	echo "🎉 demo.verify PASSED"

.ONESHELL: demo.load demo.list
.PHONY: demo.load
demo.load: check-compose-project check-odoo-conf check-external-addons
	@echo "[demo.load] db=$(DB_NAME) scenario=$(SCENARIO) step=$(STEP)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@test -n "$(SCENARIO)" || (echo "ERROR: SCENARIO is required. e.g. make demo.load SCENARIO=s10_contract_payment" && exit 2)
	@$(RUN_ENV) $(ODOO_EXEC) shell \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=$(ODOO_ADDONS_PATH) \
		--no-http --workers=0 --max-cron-threads=0 \
	<<-'PY'
	from odoo.addons.smart_construction_demo.tools.scenario_loader import load_scenario
	print("[demo.load] loading scenario:", "$(SCENARIO)", "step:", "$(STEP)")
	load_scenario(env, "$(SCENARIO)", mode="update", step="$(STEP)")
	print("[demo.load] done")
	PY

.PHONY: demo.list
demo.list: check-compose-project check-odoo-conf check-external-addons
	@$(RUN_ENV) $(ODOO_EXEC) shell \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=$(ODOO_ADDONS_PATH) \
		--no-http --workers=0 --max-cron-threads=0 \
		<<-'PY'
	from odoo.addons.smart_construction_demo.tools.scenario_loader import SCENARIOS
	for k in sorted(SCENARIOS.keys()): print(k)
	PY

.PHONY: demo.load.all
demo.load.all: check-compose-project check-odoo-conf check-external-addons
	@echo "[demo.load.all] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(RUN_ENV) $(ODOO_EXEC) shell \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=$(ODOO_ADDONS_PATH) \
		--no-http --workers=0 --max-cron-threads=0 \
		<<-'PY'
	from odoo.addons.smart_construction_demo.tools.scenario_loader import load_all
	print("[demo.load.all] loading all scenarios")
	load_all(env, mode="update")
	print("[demo.load.all] done")
	PY

.PHONY: demo.install
demo.install:
	@echo "[demo.install] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(MAKE) mod.install MODULE=smart_construction_demo DB_NAME=$(DB_NAME)

.ONESHELL: demo.rebuild demo.ci
.PHONY: demo.rebuild demo.ci
demo.rebuild: check-compose-project check-external-addons
	@echo "[demo.rebuild] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@stage=""
	@log_tail() { $(COMPOSE_BASE) logs --tail=$(DEMO_LOG_TAIL) $(DEMO_LOG_SERVICE) || true; }
	@run_stage() { \
		stage="$$1"; shift; \
		echo "[demo.rebuild] stage=$$stage"; \
		if command -v timeout >/dev/null 2>&1; then \
			timeout $(DEMO_TIMEOUT) "$$@"; \
		else \
			"$$@"; \
		fi; \
	}
	@trap 'status=$$?; echo "[demo.rebuild] FAILED stage=$$stage"; log_tail; exit $$status' ERR
	@run_stage reset $(MAKE) demo.reset DB_NAME=$(DB_NAME)
	@run_stage install $(MAKE) demo.install DB_NAME=$(DB_NAME)
	@run_stage load_all $(MAKE) demo.load.all DB_NAME=$(DB_NAME)
	@run_stage verify $(MAKE) demo.verify DB_NAME=$(DB_NAME)
	@echo "🎉 demo.rebuild PASSED"

demo.ci: check-compose-project check-external-addons
	@echo "[demo.ci] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@stage=""
	@log_tail() { $(COMPOSE_BASE) logs --tail=$(DEMO_LOG_TAIL) $(DEMO_LOG_SERVICE) || true; }
	@run_stage() { \
		stage="$$1"; shift; \
		echo "[demo.ci] stage=$$stage"; \
		if command -v timeout >/dev/null 2>&1; then \
			timeout $(DEMO_TIMEOUT) "$$@"; \
		else \
			"$$@"; \
		fi; \
	}
	@trap 'status=$$?; echo "[demo.ci] FAILED stage=$$stage"; log_tail; exit $$status' ERR
	@run_stage reset $(MAKE) demo.reset DB_NAME=$(DB_NAME)
	@run_stage install_demo $(MAKE) demo.install DB_NAME=$(DB_NAME)
	@run_stage upgrade_core $(MAKE) mod.upgrade MODULE=smart_construction_core DB_NAME=$(DB_NAME)
	@run_stage upgrade_demo $(MAKE) mod.upgrade MODULE=smart_construction_demo DB_NAME=$(DB_NAME)
	@run_stage load_all $(MAKE) demo.load.all DB_NAME=$(DB_NAME)
	@run_stage verify $(MAKE) demo.verify DB_NAME=$(DB_NAME)
	@echo "🎉 demo.ci PASSED"

.PHONY: diag.compose
diag.compose:
	@echo "=== base ==="
	@$(COMPOSE_BASE) config | sed -n '/^services:/,/^volumes:/p' | sed -n '1,200p'
	@echo "=== base+ci ==="
	@$(COMPOSE_CI) config | sed -n '/^services:/,/^volumes:/p' | sed -n '1,200p'
	@echo "=== base+testdeps ==="
	@out="$$( $(COMPOSE_TESTDEPS) config 2>&1 )"; \
	status=$$?; \
	echo "$$out" | sed -n '/^services:/,/^volumes:/p' | sed -n '1,200p'; \
	echo "=== base+testdeps err ==="; \
	if [ $$status -ne 0 ]; then echo "$$out" | sed -n '1,120p'; fi
.PHONY: verify.ops
verify.ops: check-compose-project
	@echo "== verify.ops =="
	@echo "[1] docker daemon"
	@docker info >/dev/null && echo "OK docker daemon" || (echo "FAIL docker daemon" && exit 2)
	@echo "[2] compose project"
	@$(COMPOSE_BASE) ps
	@echo "[3] odoo recreate"
	@$(MAKE) odoo.recreate
	@echo "[4] module upgrade smoke"
	@$(MAKE) mod.upgrade MODULE=$(MODULE)
	@echo "🎉 verify.ops PASSED"

# ======================================================
# ==================== Dev Test ========================
# ======================================================
.PHONY: test test.safe
test:
	@$(RUN_ENV) bash scripts/test/test.sh
test.safe:
	@$(RUN_ENV) bash scripts/test/test_safe.sh

# ======================================================
# ==================== CI ==============================
# ======================================================
.PHONY: ci.gate ci.smoke ci.full ci.repro \
        test-install-gate test-upgrade-gate \
        ci.clean ci.ps ci.logs

# 只跑守门：权限/绕过（最快定位安全回归）
ci.gate:
	@$(RUN_ENV) TEST_TAGS="sc_gate,sc_perm" bash scripts/ci/run_ci.sh

# 冒烟：基础链路 + 守门
ci.smoke:
	@$(RUN_ENV) TEST_TAGS="sc_smoke,sc_gate" bash scripts/ci/run_ci.sh

# 全量：用 TEST_TAGS（默认 sc_smoke,sc_gate，也可你自定义覆盖）
ci.full:
	@$(RUN_ENV) bash scripts/ci/run_ci.sh

# 复现：不清理 artifacts，保留现场
ci.repro:
	@$(RUN_ENV) CI_ARTIFACT_PURGE=0 bash scripts/ci/run_ci.sh

test-install-gate:
	@$(RUN_ENV) bash scripts/ci/install_gate.sh
test-upgrade-gate:
	@$(RUN_ENV) bash scripts/ci/upgrade_gate.sh

ci.clean:
	@$(RUN_ENV) bash scripts/ci/ci_clean.sh
ci.ps:
	@$(RUN_ENV) bash scripts/ci/ci_ps.sh
ci.logs:
	@$(RUN_ENV) bash scripts/ci/ci_logs.sh
