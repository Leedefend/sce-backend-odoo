# =========================================================
# Stable Engineering Makefile (Odoo 17 + Docker Compose)
# - Thin Makefile: all logic lives in scripts/
# - Windows Git Bash / MSYS2 friendly
# =========================================================

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ------------------ Compose ------------------
# Prefer v2 `docker compose` if subcommand exists, otherwise fallback to `docker-compose`
COMPOSE_BIN ?= $(shell \
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; \
  elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then echo "docker-compose"; \
  else echo "docker compose"; fi)

COMPOSE_PROJECT_NAME ?= sc-backend-odoo
PROJECT              ?= $(COMPOSE_PROJECT_NAME)

# Compose files / overlays
COMPOSE_FILE_BASE      ?= docker-compose.yml
COMPOSE_FILE_TESTDEPS  ?= docker-compose.testdeps.yml
COMPOSE_FILE_CI        ?= docker-compose.ci.yml

COMPOSE_FILES       ?= -f $(COMPOSE_FILE_BASE)
COMPOSE_TEST_FILES  ?= -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_TESTDEPS)
COMPOSE_CI_FILES    ?= -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_CI)

# Canonical compose commands
COMPOSE_BASE     = $(COMPOSE_BIN) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE_BASE)
COMPOSE_TESTDEPS = $(COMPOSE_BIN) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_TESTDEPS)
COMPOSE_CI       = $(COMPOSE_BIN) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE_BASE) -f $(COMPOSE_FILE_CI)

# ------------------ DB / Module ------------------
DB_NAME      ?= sc_odoo
DB_CI        ?= sc_test
DB_USER      ?= odoo
DB_PASSWORD  ?= $(DB_USER)

# Use one knob to control dev/test db: `make test DB=sc_test`
DB ?=
ifneq ($(strip $(DB)),)
DB_NAME := $(DB)
endif

MODULE       ?= smart_construction_core
WITHOUT_DEMO ?= --without-demo=all
ODOO_ARGS    ?=

DEMO_TIMEOUT     ?= 600
DEMO_LOG_TAIL    ?= 200

# === Odoo Runtime (Single Source of Truth) ===
ODOO_SERVICE ?= odoo
ODOO_CONF    ?= /var/lib/odoo/odoo.conf
ODOO_DB      ?= $(DB_NAME)

# Unified Odoo execution (never bypass entrypoint config)
ODOO_EXEC = $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) odoo -c $(ODOO_CONF) -d $(ODOO_DB)

# ------------------ Addons / Docs mount ------------------
# 外部 addons 仓库（git submodule）默认路径：项目内 addons_external/...
ADDONS_EXTERNAL_HOST  ?= $(ROOT_DIR)/addons_external/oca_server_ux
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

CI_TAIL_ODOO  ?= 2000
CI_TAIL_DB    ?= 800
CI_TAIL_REDIS ?= 400

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
WITHOUT_DEMO="$(WITHOUT_DEMO)" \
ODOO_ARGS="$(ODOO_ARGS)" \
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
CI_TAIL_REDIS="$(CI_TAIL_REDIS)" \
DEMO_TIMEOUT="$(DEMO_TIMEOUT)" \
DEMO_LOG_TAIL="$(DEMO_LOG_TAIL)"
endef

# ======================================================
# ==================== Guards ==========================
# ======================================================
.PHONY: check-compose-project check-external-addons check-odoo-conf

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

check-odoo-conf:
	@test "$(ODOO_CONF)" = "/var/lib/odoo/odoo.conf" || \
	  (echo "❌ ODOO_CONF must be /var/lib/odoo/odoo.conf" && exit 1)

# ======================================================
# ==================== Help ============================
# ======================================================
.PHONY: help
help:
	@echo "Targets:"
	@echo "  make up/down/restart/logs/ps/odoo-shell"
	@echo "  make db.reset DB=<name> | demo.reset DB=<name> | gate.demo"
	@echo "  make mod.install MODULE=... [DB=...] | mod.upgrade MODULE=... [DB=...]"
	@echo "  make policy.apply.business_full DB=<name> | smoke.business_full DB=<name>"
	@echo "  make policy.apply.role_matrix DB=<name> | smoke.role_matrix DB=<name>"
	@echo "  make demo.list | demo.load SCENARIO=... [STEP=...] | demo.load.all | demo.verify"
	@echo "  make test | test.safe"
	@echo "  make ci.gate | ci.smoke | ci.full | ci.repro"
	@echo "  make ci.clean | ci.ps | ci.logs"
	@echo "  make diag.compose | verify.ops"
	@echo
	@echo "Common vars:"
	@echo "  MODULE=$(MODULE) DB_NAME=$(DB_NAME) DB_CI=$(DB_CI) TEST_TAGS=$(TEST_TAGS)"
	@echo "  COMPOSE_BIN='$(COMPOSE_BIN)' COMPOSE_PROJECT_NAME='$(COMPOSE_PROJECT_NAME)'"

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

# ======================================================
# ==================== DB / Demo =======================
# ======================================================
.PHONY: db.reset demo.reset db.branch db.create db.reset.manual
db.reset: check-compose-project
	@$(RUN_ENV) bash scripts/db/reset.sh

# demo.reset 必须走 scripts/demo/reset.sh（含 seed/demo 安装）
demo.reset: check-compose-project
	@$(RUN_ENV) bash scripts/demo/reset.sh

# 兼容旧快捷命令：固定 sc_demo
.PHONY: db.demo.reset
db.demo.reset: check-compose-project
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh

db.branch:
	@bash scripts/db/branch_db.sh
db.create:
	@bash scripts/db/create.sh $(DB)
db.reset.manual:
	@bash scripts/db/reset_manual.sh $(DB)

# ======================================================
# ==================== Verify / Gate ===================
# ======================================================
.PHONY: verify.baseline verify.demo gate.baseline gate.demo
verify.baseline: check-compose-project
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
verify.demo: check-compose-project
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh

gate.baseline: check-compose-project
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/db/reset.sh
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh

gate.demo: check-compose-project
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh

# ======================================================
# ==================== Module Ops ======================
# ======================================================
.PHONY: mod.install mod.upgrade
mod.install: check-compose-project
	@$(RUN_ENV) bash scripts/mod/install.sh
mod.upgrade: check-compose-project
	@$(RUN_ENV) bash scripts/mod/upgrade.sh

# ======================================================
# ==================== Policy Ops ======================
# ======================================================
.PHONY: policy.apply.business_full policy.apply.role_matrix smoke.business_full smoke.role_matrix
policy.apply.business_full: check-compose-project
	@$(RUN_ENV) POLICY_MODULE=smart_construction_custom DB_NAME=$(DB_NAME) bash scripts/audit/apply_business_full_policy.sh
policy.apply.role_matrix: check-compose-project
	@$(RUN_ENV) POLICY_MODULE=smart_construction_custom DB_NAME=$(DB_NAME) bash scripts/audit/apply_role_matrix.sh
smoke.business_full: check-compose-project
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/audit/smoke_business_full.sh
smoke.role_matrix: check-compose-project
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/audit/smoke_role_matrix.sh

.PHONY: demo.verify demo.load demo.list demo.load.all demo.install demo.rebuild demo.ci demo.repro demo.full seed.run audit.project.actions
demo.verify: check-compose-project
	@$(RUN_ENV) SCENARIO=$(SCENARIO) STEP=$(STEP) bash scripts/demo/verify.sh

demo.load: check-compose-project
	@$(RUN_ENV) SCENARIO=$(SCENARIO) STEP=$(STEP) bash scripts/demo/load.sh

demo.list: check-compose-project
	@$(RUN_ENV) bash scripts/demo/list.sh

demo.load.all: check-compose-project
	@$(RUN_ENV) bash scripts/demo/load_all.sh

demo.install: check-compose-project
	@echo "[demo.install] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(MAKE) mod.install MODULE=smart_construction_demo DB_NAME=$(DB_NAME)

demo.rebuild: check-compose-project
	@$(RUN_ENV) bash scripts/demo/rebuild.sh

demo.ci: check-compose-project
	@$(RUN_ENV) bash scripts/demo/ci.sh

demo.repro: check-compose-project
	@$(MAKE) demo.reset DB=$(DB_NAME)
	@$(MAKE) demo.load DB=$(DB_NAME) SCENARIO=s00_min_path
	@$(MAKE) demo.verify DB=$(DB_NAME)

demo.full: check-compose-project
	@$(RUN_ENV) bash scripts/demo/full.sh

seed.run: check-compose-project
	@$(RUN_ENV) STEPS=$(STEPS) bash scripts/seed/run.sh

audit.project.actions: check-compose-project
	@$(RUN_ENV) OUT=$(OUT) bash scripts/ops/audit_project_actions.sh

# ======================================================
# ==================== Dev Test ========================
# ======================================================
.PHONY: test test.safe
test: check-compose-project
	@$(RUN_ENV) bash scripts/test/test.sh
test.safe: check-compose-project
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

# ======================================================
# ==================== Diagnostics ======================
# ======================================================
.PHONY: diag.compose verify.ops gate.audit ci.gate.tp08
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

gate.audit: check-compose-project
	@$(RUN_ENV) bash scripts/ci/gate_audit.sh

ci.gate.tp08: check-compose-project
	@$(RUN_ENV) bash scripts/ci/gate_audit_tp08.sh
