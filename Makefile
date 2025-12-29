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
COMPOSE_BIN ?= $(COMPOSE)
COMPOSE_PROJECT_NAME ?= sc
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
# 外部 addons 仓库在容器中的 mount 位置（你已在 addons-path 里用到）
ADDONS_EXTERNAL_MOUNT ?= /mnt/addons_external/oca_server_ux
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
up:
	@$(RUN_ENV) bash scripts/dev/up.sh
down:
	@$(RUN_ENV) bash scripts/dev/down.sh
restart:
	@$(RUN_ENV) bash scripts/dev/restart.sh
logs:
	@$(RUN_ENV) bash scripts/dev/logs.sh
ps:
	@$(RUN_ENV) bash scripts/dev/ps.sh
odoo-shell:
	@$(RUN_ENV) bash scripts/dev/shell.sh
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
.PHONY: mod.install mod.upgrade
mod.install:
	@echo "[mod.install] module=$(MODULE) db=$(DB_NAME)"
	@test -n "$(MODULE)" || (echo "ERROR: MODULE is required. e.g. make mod.install MODULE=smart_construction_core" && exit 2)
	@$(RUN_ENV) $(COMPOSE_BASE) run --rm -T \
		--entrypoint /usr/bin/odoo odoo \
		--config=/etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,$(ADDONS_EXTERNAL_MOUNT) \
		-i $(MODULE) \
		$(WITHOUT_DEMO) \
		--no-http --workers=0 --max-cron-threads=0 \
		--stop-after-init $(ODOO_ARGS)

mod.upgrade:
	@echo "[mod.upgrade] module=$(MODULE) db=$(DB_NAME)"
	@test -n "$(MODULE)" || (echo "ERROR: MODULE is required. e.g. make mod.upgrade MODULE=smart_construction_core" && exit 2)
	@$(RUN_ENV) $(COMPOSE_BASE) run --rm -T \
		--entrypoint /usr/bin/odoo odoo \
		--config=/etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,$(ADDONS_EXTERNAL_MOUNT) \
		-u $(MODULE) \
		$(WITHOUT_DEMO) \
		--no-http --workers=0 --max-cron-threads=0 \
		--stop-after-init $(ODOO_ARGS)

.PHONY: demo.verify
demo.verify:
	@echo "[demo.verify] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@echo "✓ check projects >= 2"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 2 then 'ok' else 'project < 2' end from project_project;" | grep -qx ok
	@echo "✓ check BOQ nodes >= 2"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 2 then 'ok' else 'boq < 2' end from project_boq_line;" | grep -qx ok
	@echo "✓ check material plans >= 1"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 1 then 'ok' else 'material plan < 1' end from project_material_plan;" | grep -qx ok
	@echo "✓ check invoices >= 2"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 2 then 'ok' else 'invoice < 2' end from account_move where move_type in ('out_invoice','out_refund');" | grep -qx ok
	@echo "✓ check S10 contract record exists"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) = 1 then 'ok' else 'S10 contract missing' end from construction_contract where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_contract_out_010');" | grep -qx ok
	@echo "✓ check S10 payment request record exists"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) = 1 then 'ok' else 'S10 payment request missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_pay_req_010_001');" | grep -qx ok
	@echo "✓ check S10 invoices >= 2"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 2 then 'ok' else 'S10 invoices < 2' end from account_move where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_invoice_s10_001','sc_demo_invoice_s10_002'));" | grep -qx ok
	@echo "✓ check S20 payment record exists"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) = 1 then 'ok' else 'S20 payment missing' end from payment_request where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_payment_020_001');" | grep -qx ok
	@echo "✓ check S20 settlement order exists"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) = 1 then 'ok' else 'S20 settlement missing' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');" | grep -qx ok
	@echo "✓ check S20 settlement lines >= 2"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 2 then 'ok' else 'S20 settlement lines < 2' end from sc_settlement_order_line where id in (select res_id from ir_model_data where module='smart_construction_demo' and name in ('sc_demo_settle_line_020_001','sc_demo_settle_line_020_002'));" | grep -qx ok
	@echo "✓ check S20 settlement links to at least 1 payment request"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 1 then 'ok' else 'S20 settlement has no linked payment_request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_020_001');" | grep -qx ok
	@echo "✓ check S30 settlement exists and stays in draft"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) = 1 then 'ok' else 'S30 settlement missing or not draft' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') and state = 'draft';" | grep -qx ok
	@echo "✓ check S30 settlement has at least one line"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 1 then 'ok' else 'S30 settlement has no lines' end from sc_settlement_order_line where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');" | grep -qx ok
	@echo "✓ check S30 settlement links to payment requests"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) >= 1 then 'ok' else 'S30 settlement has no linked payment_request' end from payment_request where settlement_id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001');" | grep -qx ok
	@echo "✓ check S30 settlement amount matches line sum"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when abs(o.amount_total - sum(l.amount)) < 0.01 then 'ok' else 'S30 settlement amount mismatch' end from sc_settlement_order o join sc_settlement_order_line l on l.settlement_id = o.id where o.id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_001') group by o.amount_total;" | grep -qx ok
	@echo "✓ check S30 gate: bad settlement stays draft"
	@$(COMPOSE_BASE) exec -T db psql -U $(DB_USER) -d $(DB_NAME) -At -v ON_ERROR_STOP=1 -c \
		"select case when count(*) = 1 then 'ok' else 'S30 gate failed' end from sc_settlement_order where id in (select res_id from ir_model_data where module='smart_construction_demo' and name='sc_demo_settlement_030_bad_001') and state = 'draft';" | grep -qx ok
	@echo "🎉 demo.verify PASSED"

.ONESHELL: demo.load demo.list
.PHONY: demo.load
demo.load:
	@echo "[demo.load] db=$(DB_NAME) scenario=$(SCENARIO)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@test -n "$(SCENARIO)" || (echo "ERROR: SCENARIO is required. e.g. make demo.load SCENARIO=s10_contract_payment" && exit 2)
	@$(RUN_ENV) $(COMPOSE_BASE) run --rm -T \
		--entrypoint /usr/bin/odoo odoo \
		shell --config=/etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,$(ADDONS_EXTERNAL_MOUNT) \
		--no-http --workers=0 --max-cron-threads=0 \
		<<-'PY'
	from odoo.addons.smart_construction_demo.tools.scenario_loader import load_scenario
	print("[demo.load] loading scenario:", "$(SCENARIO)")
	load_scenario(env, "$(SCENARIO)", mode="update")
	print("[demo.load] done")
	PY

.PHONY: demo.list
demo.list:
	@$(RUN_ENV) $(COMPOSE_BASE) run --rm -T \
		--entrypoint /usr/bin/odoo odoo \
		shell --config=/etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,$(ADDONS_EXTERNAL_MOUNT) \
		--no-http --workers=0 --max-cron-threads=0 \
		<<-'PY'
	from odoo.addons.smart_construction_demo.tools.scenario_loader import SCENARIOS
	for k in sorted(SCENARIOS.keys()): print(k)
	PY

.PHONY: demo.load.all
demo.load.all:
	@echo "[demo.load.all] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(RUN_ENV) $(COMPOSE_BASE) run --rm -T \
		--entrypoint /usr/bin/odoo odoo \
		shell --config=/etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		--db_host=db --db_port=5432 --db_user=$(DB_USER) --db_password=$(DB_PASSWORD) \
		--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,$(ADDONS_EXTERNAL_MOUNT) \
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

.PHONY: demo.rebuild
demo.rebuild:
	@echo "[demo.rebuild] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(MAKE) demo.reset DB_NAME=$(DB_NAME)
	@$(MAKE) demo.install DB_NAME=$(DB_NAME)
	@$(MAKE) demo.load.all DB_NAME=$(DB_NAME)
	@$(MAKE) demo.verify DB_NAME=$(DB_NAME)
	@echo "🎉 demo.rebuild PASSED"

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
