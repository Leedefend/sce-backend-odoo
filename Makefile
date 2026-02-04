# =========================================================
# Stable Engineering Makefile (Odoo 17 + Docker Compose)
# - Thin Makefile: all logic lives in scripts/
# - Windows Git Bash / MSYS2 friendly
# =========================================================

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ======================================================
# ==================== Codex SOP =======================
# ======================================================
# 目标：让执行器（Codex）按“最小动作”迭代，避免每次都 upgrade/reset/gate。
#
# Two modes:
#   - CODEX_MODE=fast (default): 禁止重动作；允许 restart；升级需显式允许。
#   - CODEX_MODE=gate: 允许 demo.reset + gate.full，用于合并/打 tag 前验收。
#
# Knobs:
#   - CODEX_NEED_UPGRADE=1   # 仅当本次改动涉及 views/security/data/schema 才允许升级
#   - CODEX_MODULES=...      # 需要升级的模块列表（逗号或空格分隔，按你 scripts/mod/upgrade.sh 支持的形式）
#   - CODEX_DB=...           # 默认复用 DB_NAME
#
CODEX_MODE        ?= fast
CODEX_NEED_UPGRADE ?= 0
CODEX_MODULES     ?= $(MODULE)
CODEX_DB          ?= $(DB_NAME)

# Load env file (repo-level)
ENV ?= dev
ENV_FILE ?=
ENV_FILE_RESOLVED :=
ifneq ($(strip $(ENV_FILE)),)
ENV_FILE_RESOLVED := $(ENV_FILE)
else ifneq (,$(wildcard .env.$(ENV)))
ENV_FILE_RESOLVED := .env.$(ENV)
else ifneq (,$(wildcard .env))
ENV_FILE_RESOLVED := .env
endif
ENV_FILE := $(ENV_FILE_RESOLVED)

ifneq ($(strip $(ENV_FILE_RESOLVED)),)
include $(ENV_FILE_RESOLVED)
export
endif

# ------------------ Compose ------------------
# Prefer v2 `docker compose` if subcommand exists, otherwise fallback to `docker-compose`
COMPOSE_BIN ?= $(shell \
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; \
  elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then echo "docker-compose"; \
  else echo "docker compose"; fi)

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

# Back-compat alias: BD -> DB_NAME (lower priority than DB)
BD ?=
ifneq ($(strip $(BD)),)
DB_NAME := $(BD)
endif

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

# ------------------ Contract / Snapshot ------------------
CONTRACT_USER   ?= admin
CONTRACT_CASE   ?=
CONTRACT_MODEL  ?= project.project
CONTRACT_ID     ?=
CONTRACT_VIEW   ?= form
CONTRACT_OUTDIR ?= docs/contract/snapshots
CONTRACT_CONFIG ?= $(ODOO_CONF)

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
ENV="$(ENV)" \
ENV_FILE="$(ENV_FILE)" \
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
.PHONY: check-compose-project check.compose.project check-compose-env check-external-addons check-odoo-conf diag.project gate.compose.config

IS_PROD := 0
ifneq (,$(filter prod,$(ENV)))
IS_PROD := 1
endif
ifneq (,$(findstring .env.prod,$(ENV_FILE)))
IS_PROD := 1
endif

.PHONY: guard.prod.forbid guard.prod.danger
guard.prod.forbid:
	@if [ "$(IS_PROD)" = "1" ]; then \
	  echo "❌ forbidden in prod (ENV=prod/ENV_FILE=.env.prod)"; \
	  exit 2; \
	fi

guard.prod.danger:
	@if [ "$(IS_PROD)" = "1" ] && [ "$${PROD_DANGER:-}" != "1" ]; then \
	  echo "❌ prod danger guard: set PROD_DANGER=1 to proceed"; \
	  exit 2; \
	fi

# ------------------ Codex Guards ------------------
.PHONY: guard.codex.fast.noheavy guard.codex.fast.upgrade

guard.codex.fast.noheavy:
	@if [ "$(CODEX_MODE)" = "fast" ]; then \
	  echo "❌ [codex] mode=fast: heavy targets are forbidden (demo.reset/gate.full/dev.rebuild/gate.demo/gate.baseline)"; \
	  exit 2; \
	fi

guard.codex.fast.upgrade:
	@if [ "$(CODEX_MODE)" = "fast" ] && [ "$(CODEX_NEED_UPGRADE)" != "1" ]; then \
	  echo "❌ [codex] mode=fast: module upgrade is blocked by default."; \
	  echo "   Set CODEX_NEED_UPGRADE=1 and CODEX_MODULES=... only when changes touch views/security/data/schema."; \
	  exit 2; \
	fi

# ======================================================
# ================== Contract ==========================
# ======================================================
.PHONY: contract.export contract.export_all gate.contract gate.contract.bootstrap gate.contract.bootstrap-pass

contract.export:
	@DB="$(DB_NAME)" scripts/contract/snapshot_export.sh \
	  --db "$(DB_NAME)" \
	  --user "$(CONTRACT_USER)" \
	  --case "$(CONTRACT_CASE)" \
	  --model "$(CONTRACT_MODEL)" \
	  $(if $(CONTRACT_ID),--id "$(CONTRACT_ID)",) \
	  --view_type "$(CONTRACT_VIEW)" \
	  --config "$(CONTRACT_CONFIG)" \
	  --outdir "$(CONTRACT_OUTDIR)"

contract.export_all:
	@SC_CONTRACT_STABLE=1 DB="$(DB_NAME)" CASES_FILE="docs/contract/cases.yml" OUTDIR="$(CONTRACT_OUTDIR)" CONTRACT_CONFIG="$(CONTRACT_CONFIG)" ODOO_CONF="$(ODOO_CONF)" scripts/contract/export_all.sh

gate.contract:
	@DB="$(DB_NAME)" CASES_FILE="docs/contract/cases.yml" REF_DIR="docs/contract/snapshots" CONTRACT_CONFIG="$(CONTRACT_CONFIG)" ODOO_CONF="$(ODOO_CONF)" scripts/contract/gate_contract.sh

gate.contract.bootstrap:
	@DB="$(DB_NAME)" CASES_FILE="docs/contract/cases.yml" REF_DIR="docs/contract/snapshots" CONTRACT_CONFIG="$(CONTRACT_CONFIG)" ODOO_CONF="$(ODOO_CONF)" scripts/contract/gate_contract.sh --bootstrap

gate.contract.bootstrap-pass:
	@DB="$(DB_NAME)" CASES_FILE="docs/contract/cases.yml" REF_DIR="docs/contract/snapshots" CONTRACT_CONFIG="$(CONTRACT_CONFIG)" ODOO_CONF="$(ODOO_CONF)" scripts/contract/gate_contract.sh --bootstrap --bootstrap-pass

check.compose.project:
	@if [ -z "$${COMPOSE_PROJECT_NAME:-}" ]; then \
	  echo "[FATAL] COMPOSE_PROJECT_NAME is required. Set it or create .env"; \
	  exit 2; \
	fi
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

check-compose-project: check.compose.project

check-compose-env:
	@bash scripts/common/check_env.sh

gate.compose.config: check-compose-env
	@echo "[gate.compose.config] checking container_name..."
	@$(COMPOSE_BASE) config | grep -nE '^\\s*container_name:' && \
	  (echo "❌ container_name is forbidden (causes cross-project collisions)"; exit 2) || \
	  echo "✅ ok"

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
	@echo "  make demo.list | demo.load SCENARIO=... [STEP=...] | demo.load.all | demo.load.full | demo.verify"
	@echo "  make test | test.safe"
	@echo "  make ci.gate | ci.smoke | ci.full | ci.repro"
	@echo "  make ci.clean | ci.ps | ci.logs"
	@echo "  make diag.compose | verify.ops"
	@echo
	@echo "Codex SOP:"
	@echo "  make codex.fast [CODEX_MODULES=...] [CODEX_NEED_UPGRADE=1]   # 快迭代：默认不升级不重建"
	@echo "  make codex.gate [CODEX_MODULES=...] [CODEX_NEED_UPGRADE=1]   # 门禁验收：reset+contract+gate"
	@echo "  vars: CODEX_MODE=$(CODEX_MODE) CODEX_NEED_UPGRADE=$(CODEX_NEED_UPGRADE) CODEX_DB=$(CODEX_DB)"
	@echo
	@echo "Common vars:"
	@echo "  MODULE=$(MODULE) DB_NAME=$(DB_NAME) DB_CI=$(DB_CI) TEST_TAGS=$(TEST_TAGS)"
	@echo "  ENV=$(ENV) ENV_FILE=$(ENV_FILE)"
	@echo "  COMPOSE_BIN='$(COMPOSE_BIN)' COMPOSE_PROJECT_NAME='$(COMPOSE_PROJECT_NAME)'"

# ======================================================
# ==================== Dev =============================
# ======================================================
.PHONY: up down restart logs ps odoo-shell prod.restart.safe prod.restart.full
up: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/up.sh
down: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/down.sh
restart: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/restart.sh
logs: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/logs.sh
ps: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/ps.sh
odoo-shell: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/shell.sh

prod.restart.safe: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/restart.sh

prod.restart.full: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/down.sh
	@$(RUN_ENV) bash scripts/dev/up.sh

.PHONY: dev.rebuild
dev.rebuild: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env gate.compose.config
	@$(RUN_ENV) bash scripts/dev/down.sh || true
	@$(RUN_ENV) bash scripts/dev/up.sh
	@$(MAKE) db.reset
	@$(MAKE) demo.reset DB=$(DB_NAME)
	@echo "[dev.rebuild] done"

.PHONY: odoo.recreate odoo.logs odoo.exec
odoo.recreate: check-compose-project check-compose-env
	@echo "[odoo.recreate] service=$(ODOO_SERVICE)"
	@$(RUN_ENV) $(COMPOSE_BASE) up -d --force-recreate $(ODOO_SERVICE)
odoo.logs: check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) logs --tail=200 $(ODOO_SERVICE)
odoo.exec: check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) bash

# ======================================================
# ==================== Diagnostics =====================
# ======================================================
.PHONY: diag.project odoo.shell.exec
diag.project: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/diag/project.sh

odoo.shell.exec: check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) bash scripts/ops/odoo_shell_exec.sh

.PHONY: bsi.create bsi.verify
bsi.create: ## Create/update Business Service Identity user (system-bound)
	@DB_NAME=$(DB_NAME) SERVICE_LOGIN=$(SERVICE_LOGIN) SERVICE_PASSWORD=$(SERVICE_PASSWORD) GROUP_XMLIDS="$(GROUP_XMLIDS)" \
		bash scripts/ops/bsi_create.sh

bsi.verify: ## Verify BSI can see business menu/root menu (system-bound)
	@DB_NAME=$(DB_NAME) SERVICE_LOGIN=$(SERVICE_LOGIN) MENU_XMLID=$(MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) \
		bash scripts/ops/bsi_verify.sh

.PHONY: diag.nav_root
diag.nav_root: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/diag/nav_root_db_check.sh

# ======================================================
# ==================== DB / Demo =======================
# ======================================================
.PHONY: db.reset demo.reset db.branch db.create db.reset.manual
db.reset: guard.prod.forbid check-compose-project check-compose-env diag.project
	@$(RUN_ENV) bash scripts/db/reset.sh

# demo.reset 必须走 scripts/demo/reset.sh（含 seed/demo 安装）
demo.reset: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env diag.project
	@$(RUN_ENV) bash scripts/demo/reset.sh

# 兼容旧快捷命令：固定 sc_demo
.PHONY: db.demo.reset
db.demo.reset: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh

db.branch:
	@bash scripts/db/branch_db.sh
db.create:
	@bash scripts/db/create.sh $(DB)
db.reset.manual: guard.prod.forbid check-compose-env
	@bash scripts/db/reset_manual.sh $(DB)

# ======================================================
# ==================== Verify / Gate ===================
# ======================================================
.PHONY: verify.baseline verify.demo verify.p0 verify.p0.flow verify.overview verify.overview.entry verify.overview.logic verify.portal.dashboard verify.portal.execute_button verify.portal.execute_button_smoke.container verify.portal.fe_smoke.host verify.portal.fe_smoke.container verify.portal.view_state verify.portal.guard_groups verify.portal.menu_no_action verify.portal.scene_registry verify.portal.capability_guard verify.portal.capability_policy_smoke verify.portal.semantic_route verify.portal.load_view_smoke.container verify.portal.view_contract_shape.container verify.portal.view_render_mode_smoke.container verify.portal.view_contract_coverage_smoke.container verify.portal.bootstrap_guard_smoke.container verify.portal.recordview_hud_smoke.container verify.portal.one2many_read_smoke.container verify.portal.one2many_edit_smoke.container verify.portal.attachment_list_smoke.container verify.portal.file_upload_smoke.container verify.portal.file_guard_smoke.container verify.portal.v0_5.host verify.portal.v0_5.all verify.portal.v0_5.container verify.portal.v0_6.container verify.portal.ui.v0_7.container verify.portal.ui.v0_8.semantic.container verify.smart_core verify.e2e.contract verify.prod.guard prod.guard.mail_from prod.fix.mail_from gate.baseline gate.demo gate.full
verify.baseline: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
verify.demo: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh
verify.p0: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_base.sh
verify.p0.flow: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_flow.sh
verify.overview: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/overview_rules.sh
verify.overview.entry: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/overview_entry.sh
verify.overview.logic: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/overview_logic.sh
verify.portal.dashboard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/portal_dashboard.sh
verify.portal.execute_button: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/portal_execute_button.sh
verify.portal.execute_button_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_execute_button_smoke.js"
verify.portal.fe_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) BASE_URL=$(BASE_URL) DB_NAME=$(DB_NAME) AUTH_TOKEN=$(AUTH_TOKEN) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		bash scripts/diag/fe_smoke.sh
verify.portal.fe_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) AUTH_TOKEN=$(AUTH_TOKEN) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) bash /mnt/scripts/diag/fe_smoke.sh"
verify.portal.view_state: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_view_state_smoke.js
verify.portal.guard_groups: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_guard_groups_smoke.js
verify.portal.menu_no_action: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_menu_no_action_smoke.js
verify.portal.scene_registry: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_scene_registry_validate_smoke.js
verify.portal.capability_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_capability_guard_smoke.js
verify.portal.capability_policy_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_capability_policy_smoke.js
verify.portal.semantic_route: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_semantic_route_smoke.js
verify.portal.v0_5.host: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MVP_MENU_XMLID=$(MVP_MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) ARTIFACTS_DIR=$(ARTIFACTS_DIR) \
		node scripts/verify/fe_mvp_list_smoke.js
verify.portal.v0_5.all: verify.portal.view_state verify.portal.v0_5.container
	@echo "[OK] verify.portal.v0_5.all done"
verify.portal.v0_5.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MENU_XMLID=$(MVP_MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/fe_mvp_list_smoke.js"
verify.portal.v0_6.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) CREATE_NAME=$(CREATE_NAME) UPDATE_NAME=$(UPDATE_NAME) node /mnt/scripts/verify/fe_mvp_write_smoke.js"
verify.portal.recordview_hud_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/fe_recordview_hud_smoke.js"
verify.portal.load_view_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/fe_load_view_smoke.js"
verify.portal.view_contract_shape.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_view_contract_shape_smoke.js"
verify.portal.view_render_mode_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_view_render_mode_smoke.js"
verify.portal.view_contract_coverage_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) ALLOWED_MISSING=$(ALLOWED_MISSING) node /mnt/scripts/verify/fe_view_contract_coverage_smoke.js"
verify.portal.bootstrap_guard_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) EXPECT_STATUS=$(EXPECT_STATUS) node /mnt/scripts/verify/fe_bootstrap_guard_smoke.js"
verify.portal.one2many_read_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_one2many_read_smoke.js"
verify.portal.one2many_edit_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) MVP_VIEW_TYPE=$(MVP_VIEW_TYPE) RECORD_ID=$(RECORD_ID) ONE2MANY_FIELD=$(ONE2MANY_FIELD) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_one2many_edit_smoke.js"
verify.portal.attachment_list_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_attachment_list_smoke.js"
verify.portal.file_upload_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_file_upload_smoke.js"
verify.portal.file_guard_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_file_guard_smoke.js"

# v0.8.4 aggregate gate
.PHONY: verify.portal.ui.v0_8_4.container
verify.portal.ui.v0_8_4.container: verify.portal.ui.v0_8.semantic.container verify.portal.execute_button_smoke.container verify.portal.bootstrap_guard_smoke.container verify.portal.view_contract_coverage_smoke.container
	@echo \"[OK] verify.portal.ui.v0_8_4.container done\"
verify.portal.ui.v0_7.container: verify.portal.view_state verify.portal.guard_groups verify.portal.menu_no_action verify.portal.load_view_smoke.container verify.portal.fe_smoke.container verify.portal.v0_6.container verify.portal.recordview_hud_smoke.container
	@echo \"[OK] verify.portal.ui.v0_7.container done\"
verify.portal.ui.v0_8.semantic.container: verify.portal.view_contract_shape.container verify.portal.view_render_mode_smoke.container verify.portal.view_contract_coverage_smoke.container
	@echo \"[OK] verify.portal.ui.v0_8.semantic.container done\"
verify.smart_core: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/smart_core.sh
verify.prod.guard: check-compose-env
	@bash scripts/verify/prod_guard_smoke.sh

# ------------------ Prod Guards ------------------
prod.guard.mail_from: check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) bash scripts/prod/guard_mail_from.sh

prod.fix.mail_from: guard.prod.danger check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) bash scripts/prod/fix_mail_from.sh

gate.baseline: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/db/reset.sh
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh

gate.demo: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh

# ======================================================
# ==================== Module Ops ======================
# ======================================================
.PHONY: mod.install mod.upgrade
mod.install: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/mod/install.sh
mod.upgrade: guard.codex.fast.upgrade guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/mod/upgrade.sh

# ======================================================
# ==================== Policy Ops ======================
# ======================================================
.PHONY: policy.apply.business_full policy.apply.role_matrix smoke.business_full smoke.role_matrix p2.smoke p3.smoke p3.audit codex.preflight codex.merge codex.rollback codex.pr.body codex.release.note db.policy stage.preflight stage.run ops.auth.dev.apply ops.auth.dev.rollback ops.auth.dev.verify
policy.apply.business_full: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) POLICY_MODULE=smart_construction_custom DB_NAME=$(DB_NAME) bash scripts/audit/apply_business_full_policy.sh
policy.apply.role_matrix: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) POLICY_MODULE=smart_construction_custom DB_NAME=$(DB_NAME) bash scripts/audit/apply_role_matrix.sh
	@echo "⚠️  policy.apply.role_matrix finished; restarting Odoo to refresh ACL caches"
	@$(MAKE) restart
smoke.business_full: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/audit/smoke_business_full.sh
smoke.role_matrix: check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/audit/smoke_role_matrix.sh

p2.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) db.policy DB=$(DB_NAME)
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_p2_runtime.sh

p3.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) db.policy DB=$(DB_NAME)
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_p3_runtime.sh

p3.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) db.policy DB=$(DB_NAME)
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/validate_p3_audit.sh

codex.preflight:
	@bash scripts/ops/codex_preflight.sh

codex.merge: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/ops/codex_merge.sh

codex.rollback: guard.prod.forbid
	@bash scripts/ops/codex_rollback.sh

codex.pr.body: guard.prod.forbid
	@bash scripts/ops/codex_pr_body.sh "$(PR_BODY_FILE)" "artifacts/codex/$$(git rev-parse --abbrev-ref HEAD)"

codex.release.note: guard.prod.forbid
	@bash scripts/ops/codex_release_note.sh "docs/ops/releases/README.md"

db.policy:
	@DB=$(DB) bash scripts/ops/check_db_policy.sh

stage.preflight:
	@DB=$(DB_NAME) bash scripts/ops/stage_preflight.sh

stage.run:
	@STAGE=$(STAGE) DB=$(DB_NAME) bash scripts/ops/stage_run.sh

# ------------------ Auth policy (dev-style) ------------------
AUTH_PROJECT ?= sc-backend-odoo-prod
AUTH_DB      ?= sc_prod

ops.auth.dev.apply:
	@./scripts/ops/auth_policy.sh apply -p $(AUTH_PROJECT) -d $(AUTH_DB)

ops.auth.dev.rollback:
	@./scripts/ops/auth_policy.sh rollback -p $(AUTH_PROJECT) -d $(AUTH_DB)

ops.auth.dev.verify:
	@./scripts/ops/auth_policy.sh verify -p $(AUTH_PROJECT) -d $(AUTH_DB)

.PHONY: demo.verify demo.load demo.list demo.load.all demo.load.full demo.install demo.rebuild demo.ci demo.repro demo.full seed.run audit.project.actions
demo.verify: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SCENARIO=$(SCENARIO) STEP=$(STEP) bash scripts/demo/verify.sh

demo.load: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SCENARIO=$(SCENARIO) STEP=$(STEP) bash scripts/demo/load.sh

demo.list: check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/list.sh

demo.load.all: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/load_all.sh

demo.load.full: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/load_full.sh

demo.install: guard.prod.forbid check-compose-project check-compose-env
	@echo "[demo.install] db=$(DB_NAME)"
	@test -n "$(DB_NAME)" || (echo "ERROR: DB_NAME is required" && exit 2)
	@$(MAKE) mod.install MODULE=smart_construction_demo DB_NAME=$(DB_NAME)

demo.rebuild: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/rebuild.sh

demo.ci: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/ci.sh

demo.repro: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) demo.reset DB=$(DB_NAME)
	@$(MAKE) demo.load DB=$(DB_NAME) SCENARIO=s00_min_path
	@$(MAKE) demo.verify DB=$(DB_NAME)

demo.full: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/full.sh

seed.run: check-compose-project check-compose-env
	@$(RUN_ENV) STEPS=$(STEPS) bash scripts/seed/run.sh

audit.project.actions: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) OUT=$(OUT) bash scripts/ops/audit_project_actions.sh

.PHONY: prod.upgrade.core
prod.upgrade.core: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) MODULE=smart_construction_core DB_NAME=$(DB_NAME) bash scripts/mod/upgrade.sh
	@$(MAKE) restart

.PHONY: audit.pull
audit.pull:
	@DB=$(DB_NAME) bash scripts/audit/pull.sh

.PHONY: audit.boundary
audit.boundary:
	@bash scripts/audit/boundary_lint.sh

gate.full: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@KEEP_TEST_CONTAINER=1 $(MAKE) test TEST_TAGS=sc_gate BD=$(DB_NAME)
	@$(MAKE) verify.demo BD=$(DB_NAME)
	@$(MAKE) audit.pull DB_NAME=$(DB_NAME)

# ======================================================
# ==================== Codex Targets ===================
# ======================================================
.PHONY: codex.fast codex.gate codex.print codex.pr codex.cleanup codex.sync-main codex.cli

codex.print:
	@echo "== Codex SOP =="
	@echo "CODEX_MODE=$(CODEX_MODE) CODEX_DB=$(CODEX_DB) CODEX_MODULES=$(CODEX_MODULES) CODEX_NEED_UPGRADE=$(CODEX_NEED_UPGRADE)"
	@echo "fast: restart (optional upgrade only if CODEX_NEED_UPGRADE=1) ; forbid demo.reset/gate.full"
	@echo "gate: optional upgrade + demo.reset + contract.export_all + gate.full"

CODEX_CLI_ARGS ?=
codex.cli: guard.prod.forbid
	@bash scripts/ops/codex_cli.sh $(CODEX_CLI_ARGS)

codex.fast: guard.prod.forbid check-compose-project check-compose-env
	@echo "[codex.fast] mode=fast db=$(CODEX_DB) modules=$(CODEX_MODULES) need_upgrade=$(CODEX_NEED_UPGRADE)"
	@$(MAKE) restart CODEX_MODE=fast DB=$(CODEX_DB)
	@if [ "$(CODEX_NEED_UPGRADE)" = "1" ]; then \
	  echo "[codex.fast] upgrading modules (explicitly allowed) ..."; \
	  $(MAKE) mod.upgrade CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE="$(CODEX_MODULES)" DB="$(CODEX_DB)"; \
	else \
	  echo "[codex.fast] skip module upgrade (default)"; \
	fi
	@echo "[codex.fast] done. (No demo.reset / No gate.full)"

codex.gate: guard.prod.forbid check-compose-project check-compose-env
	@echo "[codex.gate] mode=gate db=$(CODEX_DB) modules=$(CODEX_MODULES) need_upgrade=$(CODEX_NEED_UPGRADE)"
	@if [ "$(CODEX_NEED_UPGRADE)" = "1" ]; then \
	  echo "[codex.gate] upgrading modules ..."; \
	  $(MAKE) mod.upgrade CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE="$(CODEX_MODULES)" DB="$(CODEX_DB)"; \
	else \
	  echo "[codex.gate] skip module upgrade (not needed)"; \
	fi
	@$(MAKE) demo.reset CODEX_MODE=gate DB="$(CODEX_DB)"
	@$(MAKE) contract.export_all DB="$(CODEX_DB)"
	@$(MAKE) gate.full CODEX_MODE=gate BD="$(CODEX_DB)"
	@echo "[codex.gate] ✅ gate flow done."

codex.snapshot: guard.prod.forbid check-compose-project check-compose-env
	@echo "[codex.snapshot] db=$(CODEX_DB)"
	@$(MAKE) contract.export_all DB="$(CODEX_DB)"

.PHONY: codex.pr codex.cleanup codex.sync-main

codex.pr: guard.prod.forbid
	@$(MAKE) codex.pr.body
	@$(MAKE) pr.push
	@$(MAKE) pr.create

codex.cleanup: guard.prod.forbid
	@$(MAKE) branch.cleanup

codex.sync-main: guard.prod.forbid
	@$(MAKE) main.sync

.PHONY: codex.run
codex.run: guard.prod.forbid
	@if [ -z "$(FLOW)" ]; then \
	  echo "❌ FLOW is required (fast|snapshot|gate|pr|merge|cleanup|rollback|release|main)"; exit 2; \
	fi
	@case "$(FLOW)" in \
	  fast) FLOW=fast bash scripts/ops/codex_run.sh ;; \
	  snapshot) FLOW=snapshot bash scripts/ops/codex_run.sh ;; \
	  gate) FLOW=gate bash scripts/ops/codex_run.sh ;; \
	  pr) $(MAKE) codex.pr ;; \
	  merge) $(MAKE) codex.merge ;; \
	  rollback) $(MAKE) codex.rollback ;; \
	  release) $(MAKE) codex.release.note ;; \
	  cleanup) $(MAKE) codex.cleanup ;; \
	  main) $(MAKE) codex.sync-main ;; \
	  *) echo "❌ unknown FLOW=$(FLOW)"; exit 2 ;; \
	esac

# ------------------ PR (Codex-safe) ------------------
.PHONY: pr.create pr.status pr.push

PR_BASE ?= main
PR_TITLE ?=
PR_BODY_FILE ?= artifacts/pr_body.md

pr.create: guard.prod.forbid
	@branch="$$(git rev-parse --abbrev-ref HEAD)"; \
	if ! echo "$$branch" | grep -qE '^(codex|feat|feature|experiment)/'; then \
	  echo "❌ pr.create only allowed on codex/*, feat/*, feature/*, experiment/* (current=$$branch)"; exit 2; \
	fi; \
	if [ -z "$(PR_TITLE)" ]; then \
	  echo "❌ PR_TITLE is required"; exit 2; \
	fi; \
	if [ ! -f "$(PR_BODY_FILE)" ]; then \
	  echo "❌ PR_BODY_FILE not found: $(PR_BODY_FILE)"; exit 2; \
	fi; \
	echo "[pr.create] base=$(PR_BASE) head=$$branch title=$(PR_TITLE) body=$(PR_BODY_FILE)"; \
	gh pr create --base "$(PR_BASE)" --head "$$branch" --title "$(PR_TITLE)" --body-file "$(PR_BODY_FILE)"

pr.push: guard.prod.forbid
	@bash scripts/ops/git_safe_push.sh

pr.status:
	@gh pr status || true

# ------------------ Branch cleanup (Codex-safe) ------------------
.PHONY: branch.cleanup branch.cleanup.feature

CLEAN_BRANCH ?=

branch.cleanup: guard.prod.forbid
	@if [ -z "$(CLEAN_BRANCH)" ]; then echo "❌ CLEAN_BRANCH is required"; exit 2; fi
	@if ! echo "$(CLEAN_BRANCH)" | grep -qE '^codex/'; then echo "❌ only codex/* can be deleted"; exit 2; fi
	@echo "[branch.cleanup] checking merged into main: $(CLEAN_BRANCH)"
	@git fetch origin main >/dev/null 2>&1 || true
	@branch_sha="$$(git rev-parse "$(CLEAN_BRANCH)")"; \
	main_sha="$$(git rev-parse origin/main 2>/dev/null || git rev-parse main)"; \
	if git merge-base --is-ancestor "$$branch_sha" "$$main_sha"; then \
	  echo "[branch.cleanup] merge-base check: ok"; \
	else \
	  echo "[branch.cleanup] merge-base check failed; checking merged PR via gh ..."; \
	  if ! command -v gh >/dev/null 2>&1; then \
	    echo "❌ gh not found; cannot verify merged PR for $(CLEAN_BRANCH)"; \
	    exit 2; \
	  fi; \
	  pr_count="$$(gh pr list --state merged --search 'head:$(CLEAN_BRANCH)' --json number --jq 'length')" || \
	    (echo "❌ gh pr list failed; network/auth required to verify merge for $(CLEAN_BRANCH)" && exit 2); \
	  if [ "$$pr_count" -lt 1 ]; then \
	    echo "❌ branch not merged into main yet: $(CLEAN_BRANCH)"; \
	    exit 2; \
	  fi; \
	  echo "[branch.cleanup] merged PR detected for $(CLEAN_BRANCH)"; \
	fi
	@echo "[branch.cleanup] deleting local: $(CLEAN_BRANCH)"
	@git branch -d "$(CLEAN_BRANCH)"
	@echo "[branch.cleanup] deleting remote: $(CLEAN_BRANCH)"
	@git push origin --delete "$(CLEAN_BRANCH)"
	@echo "✅ [branch.cleanup] done"

branch.cleanup.feature: guard.prod.forbid
	@bash scripts/ops/branch_cleanup_safe.sh "$(CLEAN_BRANCH)"

# ------------------ Main sync (safe) ------------------
.PHONY: main.sync

# ======================================================
# ==================== Frontend ========================
# ======================================================
.PHONY: fe.install fe.dev fe.gate

fe.install:
	@pnpm -C frontend install

fe.dev:
	@pnpm -C frontend dev

fe.gate:
	@pnpm -C frontend gate

main.sync: guard.prod.forbid
	@echo "[main.sync] checkout main + fast-forward pull"
	@git checkout main
	@git pull --ff-only origin main

# ======================================================
# ==================== Dev Test ========================
# ======================================================
.PHONY: test test.safe
test: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/test/test.sh
test.safe: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/test/test_safe.sh

.PHONY: verify.e2e.contract verify.e2e.scene verify.e2e.scene_admin verify.e2e.capability_smoke verify.e2e.marketplace_smoke verify.e2e.subscription_smoke verify.e2e.ops_batch_smoke verify.capability.lint verify.frontend_api
verify.e2e.contract: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/e2e_contract_guard.sh
	@$(RUN_ENV) python3 scripts/e2e/e2e_contract_smoke.py
verify.e2e.scene: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/e2e_scene_guard.sh
	@$(RUN_ENV) python3 scripts/e2e/e2e_scene_smoke.py
verify.e2e.scene_admin: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/scene_admin_smoke.sh

verify.e2e.capability_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/capability_smoke.sh

verify.e2e.marketplace_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/marketplace_smoke.sh
verify.e2e.subscription_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/subscription_smoke.sh
verify.e2e.ops_batch_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/ops_batch_smoke.sh

verify.capability.lint: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/verify/capability_lint.sh

verify.frontend_api: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/frontend_api_smoke.py

# ======================================================
# ==================== CI ==============================
# ======================================================
.PHONY: ci.gate ci.smoke ci.full ci.repro \
	test-install-gate test-upgrade-gate \
	ci.clean ci.ps ci.logs gate.boundary

# 只跑守门：权限/绕过（最快定位安全回归）
ci.gate: guard.prod.forbid
	@$(RUN_ENV) TEST_TAGS="sc_gate,sc_perm" bash scripts/ci/run_ci.sh

# 冒烟：基础链路 + 守门
ci.smoke: guard.prod.forbid
	@$(RUN_ENV) TEST_TAGS="sc_smoke,sc_gate" bash scripts/ci/run_ci.sh

# 全量：用 TEST_TAGS（默认 sc_smoke,sc_gate，也可你自定义覆盖）
ci.full: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/run_ci.sh

# 复现：不清理 artifacts，保留现场
ci.repro: guard.prod.forbid
	@$(RUN_ENV) CI_ARTIFACT_PURGE=0 bash scripts/ci/run_ci.sh

test-install-gate:
	@$(RUN_ENV) bash scripts/ci/install_gate.sh
test-upgrade-gate:
	@$(RUN_ENV) bash scripts/ci/upgrade_gate.sh

ci.clean: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/ci_clean.sh
ci.ps: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/ci_ps.sh
ci.logs: guard.prod.forbid
	@$(RUN_ENV) bash scripts/ci/ci_logs.sh

gate.boundary: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) audit.boundary.smart_core

# ======================================================
# ==================== Diagnostics ======================
# ======================================================
.PHONY: diag.compose verify.ops gate.audit ci.gate.tp08 audit.boundary.smart_core
diag.compose: check-compose-env
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

verify.ops: guard.prod.forbid check-compose-project check-compose-env
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

gate.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/ci/gate_audit.sh

# ======================================================
# ==================== Boundary Audit ==================
# ======================================================
audit.boundary.smart_core: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/audit/boundary_audit_smart_core.py \
		--root "$(ROOT_DIR)" \
		--scan-dir "addons/smart_core" \
		--json-out "artifacts/boundary_audit/smart_core_hits.json" \
		--md-out "docs/ops/boundary_audit_smart_core_20260130.md" \
		--allowlist "scripts/audit/boundary_allowlist.txt" \
		--fail-on-reverse-deps

ci.gate.tp08: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/ci/gate_audit_tp08.sh

# ======================================================
# ==================== Continue CLI ====================
# ======================================================
# Continue CLI 集成
# 注意: `continue` 是 bash 内置关键字，真正的 CLI 是 `cn`
# 
# 使用方式:
#   make cn.p PROMPT="任务描述"          # 无闪烁批处理模式
#   make cn.tui                          # 交互式 TUI 模式（可能闪烁）
#   echo "任务" | make cn.p.stdin        # 管道输入模式

# 项目配置路径
CN_PROJECT_CONFIG ?= $(ROOT_DIR)/tools/continue/config/continue-deepseek.json

# Continue CLI 脚本路径
CN_PRINT_SCRIPT ?= scripts/ops/cn_print.sh

# Continue CLI 超时设置（秒）
CN_TIMEOUT ?= 180

# 验证提示参数
guard.cn.prompt:
	@if [ -z "$(PROMPT)" ] && [ -t 0 ]; then \
		echo "❌ 错误: 需要提供提示 (PROMPT=... 或通过管道输入)"; \
		echo "用法: make cn.p PROMPT=\"任务描述\""; \
		echo "用法: echo \"任务\" | make cn.p.stdin"; \
		exit 2; \
	fi

# 无闪烁批处理模式
cn.p: guard.cn.prompt
	@echo "▶ 执行 Continue 批处理任务 (无闪烁模式)"
	@echo "提示: $(PROMPT)"
	@echo "配置: $(CN_PROJECT_CONFIG)"
	@echo "超时: $(CN_TIMEOUT)秒"
	@CN_CONFIG="$(CN_PROJECT_CONFIG)" CN_TIMEOUT="$(CN_TIMEOUT)" bash "$(CN_PRINT_SCRIPT)" "$(PROMPT)"

# 管道输入模式
cn.p.stdin: guard.cn.prompt
	@echo "▶ 执行 Continue 批处理任务 (管道输入模式)"
	@echo "配置: $(CN_PROJECT_CONFIG)"
	@echo "超时: $(CN_TIMEOUT)秒"
	@CN_CONFIG="$(CN_PROJECT_CONFIG)" CN_TIMEOUT="$(CN_TIMEOUT)" bash "$(CN_PRINT_SCRIPT)"

# 交互式 TUI 模式 (可能闪烁)
cn.tui:
	@echo "⚠ 警告: 交互式 TUI 模式可能导致屏幕闪烁"
	@echo "提示: 按 Ctrl+C 退出"
	@if [ -f "$(CN_PROJECT_CONFIG)" ]; then \
		cn --config "$(CN_PROJECT_CONFIG)"; \
	else \
		cn; \
	fi

# 测试 Continue CLI 连接
cn.test:
	@echo "▶ 测试 Continue CLI 连接"
	@if command -v cn >/dev/null 2>&1; then \
		echo "✅ Continue CLI 已安装"; \
		cn --version || echo "⚠ 无法获取版本信息"; \
	else \
		echo "❌ Continue CLI 未安装"; \
		echo "安装: npm install -g @continuedev/cli"; \
		exit 1; \
	fi
	@echo ""
	@echo "▶ 测试主链路配置（与 cn.p 使用相同逻辑）"
	@echo "  配置选择逻辑验证..."
	@# 模拟 cn_print.sh 的配置选择逻辑
	@if [ -f "$(HOME)/.continue/config.json" ]; then \
		echo "✅ 使用用户 JSON 配置: $(HOME)/.continue/config.json"; \
		CONFIG_SOURCE="用户JSON配置"; \
	elif [ -f "$(HOME)/.continue/config.yaml" ]; then \
		echo "✅ 使用用户 YAML 配置: $(HOME)/.continue/config.yaml"; \
		CONFIG_SOURCE="用户YAML配置"; \
	elif [ -f "$(CN_PROJECT_CONFIG)" ]; then \
		echo "⚠ 使用项目配置（用户配置不存在）: $(CN_PROJECT_CONFIG)"; \
		CONFIG_SOURCE="项目配置"; \
	else \
		echo "❌ 错误: 未找到 Continue 配置文件"; \
		exit 1; \
	fi
	@echo "✅ 配置选择逻辑正常（与 cn.p 相同）"
	@echo ""
	@echo "▶ 配置源信息"
	@if [ -f "$(HOME)/.continue/config.json" ]; then \
		echo "✅ 用户 JSON 配置存在: $(HOME)/.continue/config.json"; \
	elif [ -f "$(HOME)/.continue/config.yaml" ]; then \
		echo "✅ 用户 YAML 配置存在: $(HOME)/.continue/config.yaml"; \
	else \
		echo "⚠ 用户配置不存在"; \
	fi
	@if [ -f "$(CN_PROJECT_CONFIG)" ]; then \
		echo "✅ 项目配置存在: $(CN_PROJECT_CONFIG)"; \
	else \
		echo "⚠ 项目配置不存在"; \
	fi

# ======================================================
# ==================== Continue Audit ===================
# ======================================================
# 文档字符串审计
CN_AUDIT_MODULE ?= addons/smart_construction_core
CN_AUDIT_OUTDIR ?= artifacts/continue

# 文档字符串审计主任务
cn.audit.docstrings:
	@echo "▶ 开始文档字符串审计"
	@echo "模块: $(CN_AUDIT_MODULE)"
	@echo "输出目录: $(CN_AUDIT_OUTDIR)"
	@echo "扫描器: tools/continue/auditors/docstrings_scanner.py"
	@mkdir -p "$(CN_AUDIT_OUTDIR)"
	@python3 tools/continue/auditors/docstrings_scanner.py "$(CN_AUDIT_MODULE)" "$(CN_AUDIT_OUTDIR)"
	@echo ""
	@echo "📊 审计报告:"
	@echo "  - $(CN_AUDIT_OUTDIR)/audit_docstrings.md (人读报告)"
	@echo "  - $(CN_AUDIT_OUTDIR)/audit_docstrings.json (机器数据)"
	@echo ""
	@echo "✅ 文档字符串审计完成"

# 文档字符串审计测试（小样本）
cn.audit.docstrings.test:
	@echo "▶ 测试文档字符串审计（小样本）"
	@echo "测试目录: addons/smart_construction_core/controllers"
	@echo "输出目录: $(CN_AUDIT_OUTDIR)"
	@mkdir -p "$(CN_AUDIT_OUTDIR)"
	@python3 tools/continue/auditors/docstrings_scanner.py "addons/smart_construction_core/controllers" "$(CN_AUDIT_OUTDIR)"
	@echo ""
	@echo "✅ 测试审计完成（仅扫描controllers目录）"

# 清理审计产物
cn.audit.docstrings.clean:
	@echo "▶ 清理审计产物"
	@rm -rf "$(CN_AUDIT_OUTDIR)/audit_docstrings.md" "$(CN_AUDIT_OUTDIR)/audit_docstrings.json" 2>/dev/null || true
	@echo "✅ 清理完成"

# ======================================================
# ==================== Continue Help ====================
# ======================================================
# 显示帮助信息
cn.help:
	@echo "Continue CLI 集成帮助:"
	@echo ""
	@echo "无闪烁批处理模式:"
	@echo "  make cn.p PROMPT=\"任务描述\""
	@echo "  示例: make cn.p PROMPT=\"分析代码问题\""
	@echo ""
	@echo "管道输入模式:"
	@echo "  echo \"任务描述\" | make cn.p.stdin"
	@echo "  示例: echo \"修复bug\" | make cn.p.stdin"
	@echo ""
	@echo "交互式 TUI 模式 (可能闪烁):"
	@echo "  make cn.tui"
	@echo ""
	@echo "测试连接:"
	@echo "  make cn.test"
	@echo ""
	@echo "审计功能:"
	@echo "  make cn.audit.docstrings          # 文档字符串审计"
	@echo "  make cn.audit.docstrings.test     # 测试审计（小样本）"
	@echo "  make cn.audit.docstrings.clean    # 清理审计产物"
	@echo ""
	@echo "配置路径: $(CN_PROJECT_CONFIG)"
	@echo "脚本路径: $(CN_PRINT_SCRIPT)"
	@echo "审计模块: $(CN_AUDIT_MODULE)"
	@echo "审计输出: $(CN_AUDIT_OUTDIR)"
	@echo ""
	@echo "注意:"
	@echo "  - 闪烁问题由交互式 TUI 引起，批处理模式可避免"
	@echo "  - 确保已安装 Continue CLI: npm install -g @continuedev/cli"

.PHONY: cn.p cn.p.stdin cn.tui cn.test cn.help guard.cn.prompt
