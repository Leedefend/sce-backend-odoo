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
USAGE_TRACK_REQUEST_TOTAL ?= 120
USAGE_TRACK_CONCURRENCY ?= 24
USAGE_TRACK_SCENE_KEY ?= projects.intake
SC_GATE_STRICT ?= 1
SC_SCENE_OBS_STRICT ?= 0
SCENE_OBSERVABILITY_PREFLIGHT_STRICT ?= 1
BASELINE_FREEZE_ENFORCE ?= 1
CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES ?= 1
BUSINESS_INCREMENT_PROFILE ?= base
SC_WARN_ACT_URL_LEGACY_MAX ?= 3
DB_CI        ?= sc_test
DB_USER      ?= odoo
DB_PASSWORD  ?= $(DB_USER)
SCENE_CHANNEL ?= stable
SCENE_USE_PINNED ?= 0

# Back-compat alias: BD -> DB_NAME (lower priority than DB)
BD ?=
ifneq ($(strip $(BD)),)
ifneq ($(filter environment command line,$(origin DB_NAME)),)
else
DB_NAME := $(BD)
endif
endif

# Use one knob to control dev/test db: `make test DB=sc_test`
DB ?=
ifneq ($(strip $(DB)),)
ifneq ($(filter environment command line,$(origin DB_NAME)),)
else
DB_NAME := $(DB)
endif
endif

MODULE       ?= smart_construction_core
WITHOUT_DEMO ?= --without-demo=all
ODOO_ARGS    ?=
E2E_LOGIN    ?=
E2E_PASSWORD ?=
PORTAL_SMOKE_LOGIN ?= svc_e2e_smoke
PORTAL_SMOKE_PASSWORD ?= demo
MVP_MENU_XMLID ?= scene.contract.projects_list
ROOT_XMLID   ?= smart_construction_core.menu_sc_root

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
ifneq (,$(filter .env.prod,$(notdir $(ENV_FILE))))
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
.PHONY: contract.export contract.export_all contract.catalog.export contract.evidence.export verify.contract.catalog verify.scene.contract.shape verify.contract.evidence gate.contract gate.contract.bootstrap gate.contract.bootstrap-pass

INTENT_SURFACE_MD ?= artifacts/intent_surface_report.md
INTENT_SURFACE_JSON ?= artifacts/intent_surface_report.json
CONTRACT_PREFLIGHT_INTENT_SURFACE_MD ?= artifacts/intent_surface_report.md
CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON ?= artifacts/intent_surface_report.json

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

contract.catalog.export:
	@python3 scripts/contract/export_catalogs.py

contract.evidence.export:
	@python3 scripts/contract/export_evidence.py

verify.contract.catalog: guard.prod.forbid
	@python3 scripts/verify/intent_cases_integrity_guard.py --cases-file docs/contract/cases.yml
	@$(MAKE) --no-print-directory contract.catalog.export
	@test -s docs/contract/exports/intent_catalog.json || (echo "❌ intent_catalog.json missing" && exit 2)
	@test -s docs/contract/exports/scene_catalog.json || (echo "❌ scene_catalog.json missing" && exit 2)
	@python3 scripts/verify/intent_cases_catalog_guard.py --cases-file docs/contract/cases.yml --catalog docs/contract/exports/intent_catalog.json
	@python3 scripts/verify/intent_catalog_case_coverage_guard.py --cases-file docs/contract/cases.yml --catalog docs/contract/exports/intent_catalog.json
	@python3 scripts/verify/intent_catalog_inferred_guard.py --catalog docs/contract/exports/intent_catalog.json
	@python3 scripts/verify/intent_catalog_example_shape_guard.py --catalog docs/contract/exports/intent_catalog.json
	@python3 scripts/verify/intent_catalog_snapshot_reference_guard.py --catalog docs/contract/exports/intent_catalog.json
	@python3 -c 'import json; from pathlib import Path; i=json.loads(Path("docs/contract/exports/intent_catalog.json").read_text(encoding="utf-8")); s=json.loads(Path("docs/contract/exports/scene_catalog.json").read_text(encoding="utf-8")); assert isinstance(i.get("intents"), list) and i["intents"]; assert isinstance(s.get("scenes"), list) and s["scenes"]; print("[verify.contract.catalog] PASS")'

verify.scene.contract.shape: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@python3 scripts/verify/scene_contract_shape_guard.py --catalog docs/contract/exports/scene_catalog.json --report artifacts/scene_contract_shape_guard.json

verify.contract.evidence: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.contract.preflight
	@test -s artifacts/contract/phase11_1_contract_evidence.json || (echo "❌ phase11_1_contract_evidence.json missing" && exit 2)
	@test -s artifacts/contract/phase11_1_contract_evidence.md || (echo "❌ phase11_1_contract_evidence.md missing" && exit 2)
	@echo "[verify.contract.evidence] PASS"

gate.contract:
	@$(MAKE) --no-print-directory verify.contract.preflight
	@DB="$(DB_NAME)" CASES_FILE="docs/contract/cases.yml" REF_DIR="docs/contract/snapshots" CONTRACT_CONFIG="$(CONTRACT_CONFIG)" ODOO_CONF="$(ODOO_CONF)" scripts/contract/gate_contract.sh

gate.contract.bootstrap:
	@$(MAKE) --no-print-directory verify.contract.preflight
	@DB="$(DB_NAME)" CASES_FILE="docs/contract/cases.yml" REF_DIR="docs/contract/snapshots" CONTRACT_CONFIG="$(CONTRACT_CONFIG)" ODOO_CONF="$(ODOO_CONF)" scripts/contract/gate_contract.sh --bootstrap

gate.contract.bootstrap-pass:
	@$(MAKE) --no-print-directory verify.contract.preflight
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
	@echo "  make deploy.prod.sim.oneclick ENV=test ENV_FILE=.env.prod.sim"
	@echo "  make verify.prod.sim.isolation   # prod-sim 一键隔离验证"
	@echo "  make verify.prod.sim.isolation.quick   # prod-sim 快速隔离验证（不reset）"
	@echo "  make db.reset DB=<name> | demo.reset DB=<name> | gate.demo"
	@echo "  make verify.platform_baseline|verify.business_baseline|verify.baseline.all DB_NAME=<name>"
	@echo "  make gate.platform_baseline|gate.business_baseline|gate.baseline.all DB_NAME=<name>"
	@echo "  make verify.portal.scene_observability_preflight_smoke.container DB_NAME=<name>"
	@echo "  make verify.portal.scene_observability_preflight.refresh.container DB_NAME=<name>"
	@echo "  make verify.portal.scene_observability_preflight.latest"
	@echo "  make verify.portal.scene_observability_preflight.report"
	@echo "  make verify.portal.scene_observability.structure_guard"
	@echo "  make verify.baseline.freeze_guard"
	@echo "  make verify.scene.runtime_boundary.gate"
	@echo "  make verify.scene.delivery.readiness.role_matrix   # 角色矩阵严格验收（pm/executive/finance/ops）"
	@echo "  make verify.scene.delivery.readiness.role_company_matrix   # 角色+公司双矩阵严格验收"
	@echo "  make verify.scene.delivery.readiness"
	@echo "  make verify.scene.legacy.bundle | verify.scene.legacy.all"
	@echo "  make verify.scene.legacy.contract.guard   # alias to verify.scene.legacy_contract.guard"
	@echo "  make verify.scene.contract_path.gate"
	@echo "  make verify.boundary.guard | verify.contract.snapshot"
	@echo "  make verify.mode.filter | verify.capability.schema | verify.scene.schema"
	@echo "  make verify.seed.demo.isolation | verify.contract.ordering.smoke"
	@echo "  make verify.business.increment.preflight [BUSINESS_INCREMENT_PROFILE=base|strict]"
	@echo "  make verify.business.increment.readiness.brief [BUSINESS_INCREMENT_PROFILE=base|strict]"
	@echo "  make verify.portal.scene_observability_smoke.container DB_NAME=<name>"
	@echo "  make verify.portal.scene_observability_strict.container DB_NAME=<name>"
	@echo "  make mod.install MODULE=... [DB=...] | mod.upgrade MODULE=... [DB=...]"
	@echo "  make guard.customer_seed_external_ids.warn [DB_NAME=...]"
	@echo "  make guard.customer_seed_external_ids.strict [DB_NAME=...]"
	@echo "  make policy.apply.business_full DB=<name> | smoke.business_full DB=<name>"
	@echo "  make policy.apply.role_matrix DB=<name> | smoke.role_matrix DB=<name>"
	@echo "  make demo.list | demo.load SCENARIO=... [STEP=...] | demo.load.all | demo.load.full | demo.verify"
	@echo "  make test | test.safe"
	@echo "  make ci.scene.delivery.readiness | ci.gate | ci.smoke | ci.full | ci.repro"
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
.PHONY: up down restart logs ps odoo-shell prod.restart.safe prod.restart.full deploy.prod.sim.oneclick
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

deploy.prod.sim.oneclick: guard.prod.forbid check-compose-project check-compose-env gate.compose.config
	@$(RUN_ENV) COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml" bash scripts/deploy/prod_sim_oneclick.sh

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
.PHONY: obs.coverage.report scene.export scene.snapshot.update scene.contract.export scene.package.export scene.pin.stable scene.rollback.stable audit.scene.config verify.baseline verify.demo verify.p0 verify.p0.flow verify.overview verify.overview.entry verify.overview.logic verify.portal.dashboard verify.portal.execute_button verify.portal.execute_button_smoke.container verify.portal.envelope_smoke.container verify.portal.fe_smoke.host verify.portal.fe_smoke.container verify.portal.view_state verify.portal.guard_groups verify.portal.menu_no_action verify.menu.scene_resolve verify.menu.scene_resolve.container verify.menu.scene_resolve.summary verify.portal.scene_registry verify.portal.capability_guard verify.portal.capability_policy_smoke verify.portal.semantic_route verify.portal.bridge.e2e verify.portal.scene_contract_smoke.container verify.portal.cross_stack_contract_smoke.container verify.portal.scene_layout_contract_smoke.container verify.portal.layout_stability_smoke.container verify.portal.workbench_tiles_smoke.container verify.portal.workspace_tiles_smoke.container verify.portal.workspace_tile_navigate_smoke.container verify.portal.menu_scene_key_smoke.container verify.portal.search_mvp_smoke.container verify.portal.sort_mvp_smoke.container verify.portal.tree_view_smoke.container verify.portal.kanban_view_smoke.container verify.portal.load_view_smoke.container verify.portal.view_contract_shape.container verify.portal.view_render_mode_smoke.container verify.portal.view_contract_coverage_smoke.container verify.portal.bootstrap_guard_smoke.container verify.portal.recordview_hud_smoke.container verify.portal.one2many_read_smoke.container verify.portal.one2many_edit_smoke.container verify.portal.attachment_list_smoke.container verify.portal.file_upload_smoke.container verify.portal.file_guard_smoke.container verify.portal.edit_tx_smoke.container verify.portal.write_conflict_smoke.container verify.portal.list_shell_title_smoke.container verify.portal.list_shell_no_meta_smoke.container verify.portal.scene_list_profile_smoke.container verify.portal.scene_default_sort_smoke.container verify.portal.scene_schema_smoke.container verify.portal.scene_semantic_smoke.container verify.portal.scene_tiles_semantic_smoke.container verify.portal.scene_targets_resolve_smoke.container verify.portal.scene_filters_semantic_smoke.container verify.portal.scene_versioning_smoke.container verify.portal.scene_target_smoke.container verify.portal.scene_diagnostics_smoke.container verify.portal.scene_warnings_guard.container verify.portal.scene_warnings_limit.container verify.portal.act_url_missing_scene_report.container verify.portal.scene_resolve_errors_debt_guard.container verify.portal.scene_contract_export_smoke.container verify.portal.scene_drift_guard.container verify.portal.scene_channel_smoke.container verify.portal.scene_rollback_smoke.container verify.portal.scene_snapshot_guard.container verify.portal.scene_package_dry_run_smoke.container verify.portal.scene_package_import_smoke.container verify.portal.scene_package_ui_smoke.container verify.portal.my_work_smoke.container verify.portal.payment_request_approval_smoke.container verify.portal.payment_request_approval_handoff_smoke.container verify.portal.v0_5.host verify.portal.v0_5.all verify.portal.v0_5.container verify.portal.v0_6.container verify.portal.ui.v0_7.container verify.portal.ui.v0_8.semantic.container verify.smart_core verify.e2e.contract verify.prod.guard prod.guard.mail_from prod.fix.mail_from gate.baseline gate.demo gate.full
.PHONY: verify.portal.scene_health_contract_smoke.container verify.portal.scene_auto_degrade_smoke.container
.PHONY: verify.portal.scene_health_pagination_smoke.container verify.portal.scene_governance_action_smoke.container verify.portal.scene_auto_degrade_notify_smoke.container
.PHONY: verify.portal.scene_governance_action_strict.container verify.portal.scene_auto_degrade_strict.container verify.portal.scene_auto_degrade_notify_strict.container verify.portal.scene_package_import_strict.container verify.portal.scene_observability_preflight.container verify.portal.scene_observability_preflight_smoke.container verify.portal.scene_observability_preflight.refresh.container verify.portal.scene_observability_preflight.latest verify.portal.scene_observability_preflight.report verify.portal.scene_observability_preflight.report.strict verify.portal.scene_observability_preflight.brief verify.portal.scene_observability_smoke.container verify.portal.scene_observability_gate_smoke.container verify.portal.scene_observability_strict.container
.PHONY: verify.portal.scene_package_dry_run_smoke.container verify.portal.scene_package_import_smoke.container verify.portal.scene_package_ui_smoke.container
.PHONY: verify.portal.scene_package_installed_smoke.container
.PHONY: verify.portal.ui.v0_8.semantic.strict.container
.PHONY: verify.platform_baseline verify.business_baseline verify.baseline.all gate.platform_baseline gate.business_baseline gate.baseline.all
verify.baseline: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/baseline.sh
verify.demo: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh
verify.p0: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_base.sh
verify.p0.flow: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_flow.sh
verify.platform_baseline: verify.baseline
	@echo "[OK] verify.platform_baseline done (env/platform baseline)"
verify.business_baseline: verify.p0.flow
	@echo "[OK] verify.business_baseline done (core+seed business baseline)"
verify.baseline.all: verify.platform_baseline verify.business_baseline
	@echo "[OK] verify.baseline.all done"
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
verify.portal.login_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/fe_login_browser_smoke.mjs
.PHONY: verify.portal.first_release_slice_browser_smoke.host
verify.portal.first_release_slice_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/first_release_slice_browser_smoke.mjs
.PHONY: verify.portal.second_slice_browser_smoke.host
verify.portal.second_slice_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/second_slice_browser_smoke.mjs
.PHONY: verify.portal.cost_slice_browser_smoke.host
verify.portal.cost_slice_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/cost_slice_browser_smoke.mjs
.PHONY: verify.portal.payment_slice_browser_smoke.host
verify.portal.payment_slice_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/payment_slice_browser_smoke.mjs
.PHONY: verify.portal.settlement_slice_browser_smoke.host
verify.portal.settlement_slice_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/settlement_slice_browser_smoke.mjs
.PHONY: verify.portal.release_navigation_browser_smoke.host
verify.portal.release_navigation_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/release_navigation_browser_smoke.mjs
.PHONY: verify.portal.unified_system_menu_click_usability_smoke.host
verify.portal.unified_system_menu_click_usability_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) API_BASE_URL=$(API_BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/unified_system_menu_click_usability_smoke.mjs
.PHONY: verify.portal.host_browser_runtime_probe
verify.portal.host_browser_runtime_probe: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) ARTIFACTS_DIR=$(ARTIFACTS_DIR) node scripts/verify/host_browser_runtime_probe.mjs
.PHONY: verify.portal.project_dashboard_primary_entry_browser_smoke.host
verify.portal.project_dashboard_primary_entry_browser_smoke.host: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.host_browser_runtime_probe
	@bash scripts/verify/bootstrap_playwright_host_runtime.sh
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) \
		node scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs
.PHONY: verify.portal.login_browser_smoke.prod_sim
verify.portal.login_browser_smoke.prod_sim: guard.prod.forbid
	@$(MAKE) --no-print-directory deploy.prod.sim.oneclick \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		DB_NAME=sc_prod_sim
	@$(MAKE) --no-print-directory verify.portal.login_browser_smoke.host \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts \
		DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo
verify.portal.fe_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) AUTH_TOKEN=$(AUTH_TOKEN) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) bash /mnt/scripts/diag/fe_smoke.sh"
verify.portal.view_state: guard.prod.forbid check-compose-project check-compose-env
	@# RC smoke user: demo_pm/demo. svc_* accounts are service-only and may 401 in UI smokes.
	@$(RUN_ENV) node scripts/verify/fe_view_state_smoke.js
verify.portal.guard_groups: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_guard_groups_smoke.js
verify.portal.menu_no_action: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_menu_no_action_smoke.js
verify.menu.scene_resolve: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(if $(MENU_SCENE_ENFORCE_PREFIXES),MENU_SCENE_ENFORCE_PREFIXES="$(MENU_SCENE_ENFORCE_PREFIXES)") $(if $(MENU_SCENE_EXEMPTIONS),MENU_SCENE_EXEMPTIONS="$(MENU_SCENE_EXEMPTIONS)") node scripts/verify/fe_menu_scene_resolve_smoke.js
verify.menu.scene_resolve.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "API_BASE=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) $(if $(MENU_SCENE_ENFORCE_PREFIXES),MENU_SCENE_ENFORCE_PREFIXES='$(MENU_SCENE_ENFORCE_PREFIXES)') $(if $(MENU_SCENE_EXEMPTIONS),MENU_SCENE_EXEMPTIONS='$(MENU_SCENE_EXEMPTIONS)') node /mnt/scripts/verify/fe_menu_scene_resolve_smoke.js"
verify.menu.scene_resolve.summary: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SUMMARY_PATH=artifacts/codex/summary.md ARTIFACTS_DIR=artifacts node scripts/verify/menu_scene_resolve_summary.js
verify.phase_9_8.gate_summary: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) SUMMARY_PATH=artifacts/codex/summary.md ARTIFACTS_DIR=artifacts node scripts/verify/phase_9_8_gate_summary.js
verify.portal.scene_registry: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_scene_registry_validate_smoke.js
verify.portal.capability_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_capability_guard_smoke.js
verify.portal.capability_policy_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_capability_policy_smoke.js
verify.portal.semantic_route: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) node scripts/verify/fe_semantic_route_smoke.js
audit.scene.config: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/audit/scene_config_audit.js"
verify.portal.bridge.e2e: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/portal_bridge_e2e_smoke.js"

.PHONY: verify.portal.payment_request_approval.prepare.container verify.portal.payment_request_approval_smoke.container verify.portal.payment_request_approval_handoff_smoke.container verify.portal.payment_request_approval_all_smoke.container verify.portal.payment_request_approval_field_consumer_audit
verify.portal.payment_request_approval.prepare.container: guard.prod.forbid check-compose-project check-compose-env
	@if [ "$(PAYMENT_APPROVAL_NEED_UPGRADE)" = "1" ]; then \
	  CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=$(DB_NAME) $(MAKE) --no-print-directory mod.upgrade; \
	else \
	  echo "[verify.portal.payment_request_approval.prepare.container] skip mod.upgrade (PAYMENT_APPROVAL_NEED_UPGRADE=$(PAYMENT_APPROVAL_NEED_UPGRADE))"; \
	fi
	@$(MAKE) --no-print-directory restart
	@sleep 5
	@AUTO_FIX_EXTENSION_MODULES=1 $(MAKE) --no-print-directory policy.ensure.extension_modules DB_NAME=$(DB_NAME)

.PHONY: verify.portal.payment_request_approval_smoke.container
verify.portal.payment_request_approval_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@if [ "$(PAYMENT_APPROVAL_SKIP_PREPARE)" != "1" ]; then \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval.prepare.container DB_NAME=$(DB_NAME); \
	fi
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) python3 /mnt/scripts/verify/payment_request_approval_smoke.py"

.PHONY: verify.portal.payment_request_approval_handoff_smoke.container
verify.portal.payment_request_approval_handoff_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@if [ "$(PAYMENT_APPROVAL_SKIP_PREPARE)" != "1" ]; then \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval.prepare.container DB_NAME=$(DB_NAME); \
	fi
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 /mnt/scripts/verify/payment_request_approval_handoff_smoke.py"

.PHONY: verify.portal.payment_request_approval_all_smoke.container
verify.portal.payment_request_approval_all_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.payment_request_approval.prepare.container DB_NAME=$(DB_NAME)
	@PAYMENT_APPROVAL_SKIP_PREPARE=1 $(MAKE) --no-print-directory verify.portal.payment_request_approval_smoke.container DB_NAME=$(DB_NAME)
	@PAYMENT_APPROVAL_SKIP_PREPARE=1 $(MAKE) --no-print-directory verify.portal.payment_request_approval_handoff_smoke.container DB_NAME=$(DB_NAME)
	@if [ "$(PAYMENT_APPROVAL_FIELD_AUDIT_STRICT)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval_field_consumer_audit; \
	else \
	  $(MAKE) --no-print-directory verify.portal.payment_request_approval_field_consumer_audit || \
	    echo "[warn] payment approval field consumer audit failed (set PAYMENT_APPROVAL_FIELD_AUDIT_STRICT=1 to block)"; \
	fi

.PHONY: verify.portal.payment_request_approval_field_consumer_audit
verify.portal.payment_request_approval_field_consumer_audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/payment_request_approval_field_consumer_audit.py
verify.portal.v0_5.host: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) MVP_MENU_XMLID=$(MVP_MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(or $(E2E_LOGIN),$(PORTAL_SMOKE_LOGIN)) E2E_PASSWORD=$(or $(E2E_PASSWORD),$(PORTAL_SMOKE_PASSWORD)) ARTIFACTS_DIR=$(ARTIFACTS_DIR) \
		node scripts/verify/fe_mvp_list_smoke.js
verify.portal.v0_5.all: verify.portal.view_state verify.portal.v0_5.container
	@echo "[OK] verify.portal.v0_5.all done"
verify.portal.v0_5.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MENU_XMLID=$(MVP_MENU_XMLID) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(or $(E2E_LOGIN),$(PORTAL_SMOKE_LOGIN)) E2E_PASSWORD=$(or $(E2E_PASSWORD),$(PORTAL_SMOKE_PASSWORD)) node /mnt/scripts/verify/fe_mvp_list_smoke.js"
verify.portal.v0_6.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) CREATE_NAME=$(CREATE_NAME) UPDATE_NAME=$(UPDATE_NAME) node /mnt/scripts/verify/fe_mvp_write_smoke.js"
verify.portal.recordview_hud_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) ROOT_XMLID=$(ROOT_XMLID) E2E_LOGIN=$(or $(E2E_LOGIN),$(PORTAL_SMOKE_LOGIN)) E2E_PASSWORD=$(or $(E2E_PASSWORD),$(PORTAL_SMOKE_PASSWORD)) node /mnt/scripts/verify/fe_recordview_hud_smoke.js"
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
verify.portal.edit_tx_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_edit_tx_smoke.js"
verify.portal.write_conflict_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) RECORD_ID=$(RECORD_ID) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_write_conflict_smoke.js"
verify.portal.search_mvp_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_search_mvp_smoke.js"
verify.portal.sort_mvp_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_sort_mvp_smoke.js"
verify.portal.tree_view_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) TREE_GROUPED_SNAPSHOT_UPDATE=$(TREE_GROUPED_SNAPSHOT_UPDATE) TREE_GROUPED_BASELINE=$(TREE_GROUPED_BASELINE) REQUIRE_GROUPED_ROWS=$(REQUIRE_GROUPED_ROWS) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_tree_view_smoke.js"
verify.portal.kanban_view_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) MVP_MODEL=$(MVP_MODEL) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_kanban_view_smoke.js"
verify.portal.scene_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_contract_smoke.js"

verify.portal.cross_stack_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env verify.extension_modules.guard
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REPO_ROOT=/mnt BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) node /mnt/scripts/verify/fe_cross_stack_contract_smoke.js"

verify.portal.envelope_smoke.container: verify.portal.scene_contract_smoke.container verify.portal.my_work_smoke.container verify.portal.execute_button_smoke.container verify.portal.cross_stack_contract_smoke.container
	@echo "[OK] verify.portal.envelope_smoke.container done"

verify.portal.scene_layout_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_layout_contract_smoke.js"

verify.portal.layout_stability_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_layout_stability_smoke.js"
verify.portal.workbench_tiles_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_workbench_tiles_smoke.js"

verify.portal.workspace_tiles_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_workspace_tiles_smoke.js"

verify.portal.workspace_tile_navigate_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_workspace_tile_navigate_smoke.js"
verify.portal.menu_scene_key_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_menu_scene_key_smoke.js"
verify.portal.list_shell_title_smoke.container: guard.prod.forbid
	@REPO_ROOT="$(PWD)" node scripts/verify/fe_list_shell_title_smoke.js
verify.portal.list_shell_no_meta_smoke.container: guard.prod.forbid
	@REPO_ROOT="$(PWD)" node scripts/verify/fe_list_shell_no_meta_smoke.js
verify.portal.scene_list_profile_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_list_profile_smoke.js"
verify.portal.scene_default_sort_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_default_sort_smoke.js"
verify.portal.scene_schema_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_schema_smoke.js"
verify.portal.scene_semantic_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_semantic_smoke.js"
verify.portal.scene_tiles_semantic_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_tiles_semantic_smoke.js"
verify.portal.scene_targets_resolve_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_targets_resolve_smoke.js"
verify.portal.scene_filters_semantic_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_filters_semantic_smoke.js"
verify.portal.my_work_smoke.container: guard.prod.forbid check-compose-project check-compose-env verify.extension_modules.guard
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) node /mnt/scripts/verify/fe_my_work_smoke.js"

.PHONY: verify.portal.usage_track_concurrency_smoke.container
verify.portal.usage_track_concurrency_smoke.container: guard.prod.forbid check-compose-project check-compose-env verify.extension_modules.guard
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) USAGE_TRACK_REQUEST_TOTAL=$(USAGE_TRACK_REQUEST_TOTAL) USAGE_TRACK_CONCURRENCY=$(USAGE_TRACK_CONCURRENCY) USAGE_TRACK_SCENE_KEY=$(USAGE_TRACK_SCENE_KEY) node /mnt/scripts/verify/fe_usage_track_concurrency_smoke.js"
verify.portal.scene_versioning_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_versioning_smoke.js"
verify.portal.scene_target_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_target_smoke.js"
verify.portal.scene_diagnostics_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_diagnostics_smoke.js"
verify.portal.scene_warnings_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) DENY_WARNING_CODES=ACT_URL_MISSING_SCENE node /mnt/scripts/verify/scene_warnings_guard_summary.js"
verify.portal.scene_warnings_limit.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) SC_WARN_ACT_URL_LEGACY_MAX=$(SC_WARN_ACT_URL_LEGACY_MAX) node /mnt/scripts/verify/scene_warnings_guard_summary.js"
verify.portal.act_url_missing_scene_report.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node /mnt/scripts/verify/act_url_missing_scene_report.js"
verify.portal.scene_health_contract_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_health_contract_smoke.js"
verify.portal.scene_auto_degrade_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_smoke.js"
verify.portal.scene_health_pagination_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_health_pagination_smoke.js"
verify.portal.scene_governance_action_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_portal_scene_governance_action_smoke.js"
verify.portal.scene_governance_action_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_GOVERNANCE_LOG=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_portal_scene_governance_action_smoke.js"
verify.portal.scene_auto_degrade_notify_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_notify_smoke.js"
verify.portal.scene_auto_degrade_notify_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_NOTIFY_SENT=1 REQUIRE_NOTIFY_AUDIT=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_notify_smoke.js"
verify.portal.scene_auto_degrade_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_GOVERNANCE_LOG=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_auto_degrade_smoke.js"
verify.portal.scene_package_dry_run_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_dry_run_smoke.js"
verify.portal.scene_package_import_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_import_smoke.js"
verify.portal.scene_observability_preflight.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_OBSERVABILITY_PREFLIGHT_STRICT=$(SCENE_OBSERVABILITY_PREFLIGHT_STRICT) BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_observability_preflight_smoke.js"
verify.portal.scene_observability_preflight_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_OBSERVABILITY_PREFLIGHT_STRICT=0 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_observability_preflight_smoke.js"
verify.portal.scene_observability_preflight.refresh.container: verify.portal.scene_observability_preflight_smoke.container verify.portal.scene_observability_preflight.report
	@echo \"[OK] verify.portal.scene_observability_preflight.refresh.container done\"
verify.portal.scene_observability_preflight.latest: guard.prod.forbid
	@latest="$$(ls -1dt artifacts/codex/portal-scene-observability-preflight-v10_4/* 2>/dev/null | head -n 1)"; \
	if [ -z "$$latest" ]; then \
	  echo "❌ no preflight artifacts found under artifacts/codex/portal-scene-observability-preflight-v10_4"; \
	  exit 2; \
	fi; \
	echo "$$latest"
verify.portal.scene_observability_preflight.report: guard.prod.forbid
	@python3 scripts/verify/scene_observability_preflight_report.py
verify.portal.scene_observability_preflight.report.strict: guard.prod.forbid
	@python3 scripts/verify/scene_observability_preflight_report.py --strict
verify.portal.scene_observability_preflight.brief: guard.prod.forbid
	@python3 scripts/verify/scene_observability_preflight_brief.py
verify.portal.scene_observability_smoke.container: verify.portal.scene_governance_action_smoke.container verify.portal.scene_auto_degrade_smoke.container verify.portal.scene_auto_degrade_notify_smoke.container verify.portal.scene_package_import_smoke.container
	@echo \"[OK] verify.portal.scene_observability_smoke.container done\"
verify.portal.scene_observability_gate_smoke.container: verify.portal.scene_observability.structure_guard verify.portal.scene_observability_preflight_smoke.container verify.portal.scene_observability_smoke.container
	@echo \"[OK] verify.portal.scene_observability_gate_smoke.container done\"
verify.portal.scene_package_import_strict.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "REQUIRE_GOVERNANCE_LOG=1 BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_import_smoke.js"
verify.portal.scene_observability_strict.container: verify.portal.scene_observability.structure_guard verify.portal.scene_observability_preflight.container verify.portal.scene_observability_preflight.report.strict verify.portal.scene_governance_action_strict.container verify.portal.scene_auto_degrade_strict.container verify.portal.scene_auto_degrade_notify_strict.container verify.portal.scene_package_import_strict.container
	@echo \"[OK] verify.portal.scene_observability_strict.container done\"
verify.portal.scene_package_ui_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_portal_scene_package_ui_smoke.js"
verify.portal.scene_package_installed_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) node /mnt/scripts/verify/fe_scene_package_installed_smoke.js"
verify.portal.scene_resolve_errors_debt_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "DEBT_ROOT=/mnt DEBT_OUT=/mnt/artifacts/resolve_errors_debt.latest.json BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_resolve_errors_debt_guard.js"
verify.portal.scene_contract_export_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) CONTRACT_OUT=/mnt/artifacts/scenes/scene_contract.latest.json BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_contract_export_smoke.js"
verify.portal.scene_drift_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) SCENE_USE_PINNED=$(SCENE_USE_PINNED) DRIFT_ROOT=/mnt DRIFT_OUT=/mnt/artifacts/scenes/scene_drift_report.latest.json CONTRACT_OUT=/mnt/artifacts/scenes/scene_contract.latest.json CONTRACT_DIFF=/mnt/artifacts/scenes/scene_contract.diff.txt BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_drift_guard.js"
verify.portal.scene_channel_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_channel_smoke.js"
verify.portal.scene_rollback_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SCENE_CHANNEL=$(SCENE_CHANNEL) SCENE_USE_PINNED=$(SCENE_USE_PINNED) BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) node /mnt/scripts/verify/fe_scene_rollback_smoke.js"
verify.portal.scene_snapshot_guard.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "SNAPSHOT_ROOT=/mnt/extra-addons SNAPSHOT_OUT=/mnt/extra-addons/artifacts/scenes/LATEST.snapshot.json BASE_URL=http://localhost:8069 ARTIFACTS_DIR=/mnt/extra-addons/artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) SNAPSHOT_UPDATE=$(SNAPSHOT_UPDATE) node /mnt/scripts/verify/fe_scene_snapshot_guard.js"
scene.contract.export: guard.prod.forbid
	@CONTRACT_ROOT="$(PWD)" SCENE_CHANNEL=$(SCENE_CHANNEL) BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) CONTRACT_OUT=docs/contract/exports/scenes/$(SCENE_CHANNEL)/LATEST.json CONTRACT_LATEST=docs/contract/exports/scenes/$(SCENE_CHANNEL)/LATEST.json node scripts/verify/fe_scene_contract_export.js
scene.package.export: guard.prod.forbid
	@CONTRACT_ROOT="$(PWD)" PACKAGE_NAME="$(PACKAGE_NAME)" PACKAGE_VERSION="$(PACKAGE_VERSION)" SCENE_CHANNEL=$(SCENE_CHANNEL) BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) node scripts/verify/fe_scene_package_export.js
scene.pin.stable: guard.prod.forbid
	@test -f docs/contract/exports/scenes/stable/LATEST.json || (echo "❌ stable/LATEST.json missing" && exit 2)
	@cp docs/contract/exports/scenes/stable/LATEST.json docs/contract/exports/scenes/stable/PINNED.json
	@echo "[scene.pin.stable] stable/PINNED.json updated"
scene.rollback.stable: guard.prod.forbid
	@SCENE_CHANNEL=stable SCENE_USE_PINNED=1 $(MAKE) restart
scene.export: guard.prod.forbid
	@SNAPSHOT_ROOT="$(PWD)" BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) SNAPSHOT_OUT=docs/contract/snapshots/scenes/LATEST.json node scripts/verify/fe_scene_snapshot_guard.js
scene.snapshot.update: guard.prod.forbid
	@SNAPSHOT_ROOT="$(PWD)" BASE_URL=http://localhost:8070 ARTIFACTS_DIR=artifacts DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) AUTH_TOKEN=$(AUTH_TOKEN) BOOTSTRAP_SECRET=$(BOOTSTRAP_SECRET) BOOTSTRAP_LOGIN=$(BOOTSTRAP_LOGIN) SNAPSHOT_UPDATE=1 SNAPSHOT_BASELINE=docs/contract/snapshots/scenes/scenes.v0_9_8.json node scripts/verify/fe_scene_snapshot_guard.js

obs.coverage.report:
	@node scripts/ops/coverage_trend.js

# v0.8.4 aggregate gate
.PHONY: verify.portal.ui.v0_8_4.container
verify.portal.ui.v0_8_4.container: verify.portal.ui.v0_8.semantic.container verify.portal.execute_button_smoke.container verify.portal.bootstrap_guard_smoke.container verify.portal.view_contract_coverage_smoke.container
	@echo \"[OK] verify.portal.ui.v0_8_4.container done\"
verify.portal.ui.v0_7.container: verify.portal.view_state verify.portal.guard_groups verify.portal.menu_no_action verify.portal.load_view_smoke.container verify.portal.fe_smoke.container verify.portal.v0_6.container verify.portal.recordview_hud_smoke.container
	@echo \"[OK] verify.portal.ui.v0_7.container done\"
verify.portal.ui.v0_8.semantic.container: verify.frontend.suggested_action.all verify.portal.view_contract_shape.container verify.portal.view_render_mode_smoke.container verify.portal.view_contract_coverage_smoke.container verify.portal.envelope_smoke.container verify.portal.scene_layout_contract_smoke.container verify.portal.layout_stability_smoke.container verify.portal.workbench_tiles_smoke.container verify.portal.workspace_tiles_smoke.container verify.portal.workspace_tile_navigate_smoke.container verify.portal.menu_scene_key_smoke.container verify.portal.list_shell_title_smoke.container verify.portal.list_shell_no_meta_smoke.container verify.portal.scene_list_profile_smoke.container verify.portal.scene_default_sort_smoke.container verify.portal.scene_schema_smoke.container verify.portal.scene_semantic_smoke.container verify.portal.scene_tiles_semantic_smoke.container verify.portal.scene_targets_resolve_smoke.container verify.portal.scene_versioning_smoke.container verify.portal.scene_diagnostics_smoke.container verify.portal.scene_health_contract_smoke.container verify.portal.scene_health_pagination_smoke.container verify.portal.scene_governance_action_smoke.container verify.portal.scene_auto_degrade_smoke.container verify.portal.scene_auto_degrade_notify_smoke.container verify.portal.scene_package_dry_run_smoke.container verify.portal.scene_package_import_smoke.container verify.portal.scene_resolve_errors_debt_guard.container verify.portal.scene_contract_export_smoke.container verify.portal.scene_drift_guard.container verify.portal.scene_channel_smoke.container verify.portal.scene_rollback_smoke.container verify.portal.scene_snapshot_guard.container verify.portal.scene_target_smoke.container
	@echo \"[OK] verify.portal.ui.v0_8.semantic.container done\"
verify.portal.ui.v0_8.semantic.strict.container: verify.portal.ui.v0_8.semantic.container verify.portal.scene_observability_strict.container
	@echo \"[OK] verify.portal.ui.v0_8.semantic.strict.container done\"
verify.smart_core: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/smart_core.sh

.PHONY: verify.portal.minimum_runtime_surface verify.portal.preload_runtime_surface verify.runtime.fetch_entrypoints verify.product.project_initiation verify.product.project_initiation.roles verify.product.contract_ref_shape_guard verify.product.project_creation_mainline_guard verify.product.project_initiation.full verify.product.project_flow.initiation_dashboard verify.product.suggested_action_shape_guard verify.product.project_context_chain_guard verify.product.project_dashboard_non_empty_guard verify.product.phase12c verify.phase12b.baseline verify.product.v0_1_stability_baseline verify.frontend.zero_business_semantics verify.architecture.final_slice_readiness_audit verify.smart_core.minimum_surface.legacy_group_guard verify.smart_core.minimum_surface.handler_guard verify.smart_core.minimum_surface.contract_guard verify.smart_core.minimum_surface.owner_startup_smoke verify.smart_core.minimum_surface.same_route_guard verify.smart_core.minimum_surface.order_regression_guard verify.smart_core.minimum_surface.app_open_regression_guard verify.smart_core.minimum_surface.nav_isolation_guard verify.smart_core.minimum_surface verify.product.cost_tracking_entry_contract_guard verify.product.cost_tracking_block_contract_guard verify.product.project_flow.execution_cost
verify.portal.minimum_runtime_surface: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/portal_minimum_runtime_surface_guard.py"

verify.portal.preload_runtime_surface: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/portal_preload_runtime_surface_guard.py"

verify.runtime.fetch_entrypoints: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/runtime_fetch_entrypoints_smoke.py"

verify.product.project_initiation: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_initiation_smoke.py"

verify.product.project_initiation.roles: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 /mnt/scripts/verify/product_project_initiation_roles_smoke.py"

verify.product.contract_ref_shape_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_contract_ref_shape_guard.py"

.PHONY: verify.product.project_creation_mainline_guard
verify.product.project_creation_mainline_guard: guard.prod.forbid
	@python3 scripts/verify/product_project_creation_mainline_guard.py

verify.product.project_initiation.full: verify.product.project_creation_mainline_guard verify.product.project_initiation verify.product.contract_ref_shape_guard verify.product.project_initiation.roles
	@echo "[OK] verify.product.project_initiation.full done"

.PHONY: verify.product.v0_1_stability_baseline
verify.product.v0_1_stability_baseline: verify.architecture.orchestration_platform_guard verify.architecture.five_layer_workspace_audit verify.product.native_alignment_guard verify.product.project_initiation.full verify.product.project_flow.initiation_dashboard verify.product.project_dashboard_entry_contract_guard verify.product.project_dashboard_block_contract_guard verify.product.project_plan_entry_contract_guard verify.product.project_plan_block_contract_guard verify.product.project_execution_entry_contract_guard verify.product.project_execution_block_contract_guard verify.product.project_execution_state_smoke verify.product.project_execution_consistency_guard verify.frontend_api
	@echo "[OK] verify.product.v0_1_stability_baseline done"

.PHONY: verify.frontend.zero_business_semantics
verify.frontend.zero_business_semantics: guard.prod.forbid
	@python3 scripts/verify/frontend_zero_business_semantics_guard.py

.PHONY: verify.architecture.final_slice_readiness_audit
verify.architecture.final_slice_readiness_audit: verify.architecture.orchestration_platform_guard verify.architecture.five_layer_workspace_audit verify.product.native_alignment_guard verify.frontend.zero_business_semantics
	@python3 scripts/verify/final_slice_readiness_audit.py

.PHONY: verify.product.final_slice_readiness_audit
verify.product.final_slice_readiness_audit: verify.architecture.final_slice_readiness_audit

.PHONY: verify.release.first_slice_freeze
verify.release.first_slice_freeze: verify.product.final_slice_readiness_audit verify.product.project_creation_mainline_guard verify.product.project_dashboard_entry_contract_guard verify.product.project_dashboard_block_contract_guard verify.product.project_flow.initiation_dashboard verify.portal.first_release_slice_browser_smoke.host
	@echo "[OK] verify.release.first_slice_freeze done"

.PHONY: verify.release.second_slice_prepared
verify.release.second_slice_prepared: verify.architecture.final_slice_readiness_audit verify.product.project_dashboard_baseline verify.product.project_execution_consistency_guard verify.product.project_execution_pilot_precheck_guard
	@echo "[OK] verify.release.second_slice_prepared done"

.PHONY: verify.release.second_slice_freeze
verify.release.second_slice_freeze: verify.release.second_slice_prepared verify.portal.second_slice_browser_smoke.host
	@echo "[OK] verify.release.second_slice_freeze done"

.PHONY: verify.release.cost_slice_prepared
verify.release.cost_slice_prepared: verify.architecture.final_slice_readiness_audit verify.product.cost_entry_contract_guard verify.product.cost_list_block_guard verify.product.cost_summary_block_guard verify.product.project_flow.execution_cost verify.portal.cost_slice_browser_smoke.host
	@echo "[OK] verify.release.cost_slice_prepared done"

.PHONY: verify.release.cost_slice_freeze
verify.release.cost_slice_freeze: verify.release.cost_slice_prepared
	@echo "[OK] verify.release.cost_slice_freeze done"

.PHONY: verify.release.payment_slice_prepared
verify.release.payment_slice_prepared: verify.architecture.final_slice_readiness_audit verify.product.payment_entry_contract_guard verify.product.payment_list_block_guard verify.product.payment_summary_block_guard verify.product.project_flow.execution_payment verify.portal.payment_slice_browser_smoke.host
	@echo "[OK] verify.release.payment_slice_prepared done"

.PHONY: verify.release.payment_slice_freeze
verify.release.payment_slice_freeze: verify.release.payment_slice_prepared
	@echo "[OK] verify.release.payment_slice_freeze done"

.PHONY: verify.release.settlement_slice_prepared
verify.release.settlement_slice_prepared: verify.architecture.final_slice_readiness_audit verify.product.settlement_summary_contract_guard verify.product.project_flow.execution_settlement verify.portal.settlement_slice_browser_smoke.host
	@echo "[OK] verify.release.settlement_slice_prepared done"

.PHONY: verify.release.settlement_slice_freeze
verify.release.settlement_slice_freeze: verify.release.settlement_slice_prepared
	@echo "[OK] verify.release.settlement_slice_freeze done"

.PHONY: verify.release.navigation.contract_guard
verify.release.navigation.contract_guard: verify.product.release_navigation_contract_guard
	@echo "[OK] verify.release.navigation.contract_guard done"

.PHONY: verify.release.navigation.surface
verify.release.navigation.surface: verify.release.navigation.contract_guard verify.portal.release_navigation_browser_smoke.host
	@echo "[OK] verify.release.navigation.surface done"

.PHONY: verify.release.delivery_engine.v1
verify.release.delivery_engine.v1: verify.product.delivery_menu_integrity_guard verify.product.delivery_scene_integrity_guard verify.product.delivery_policy_guard verify.product.scene_contract_guard verify.portal.release_navigation_browser_smoke.host verify.portal.unified_system_menu_click_usability_smoke.host
	@echo "[OK] verify.release.delivery_engine.v1 done"

verify.product.project_flow.initiation_dashboard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_initiation_dashboard_smoke.py"

.PHONY: verify.product.project_dashboard_flow
verify.product.project_dashboard_flow: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_dashboard_flow_smoke.py"

.PHONY: verify.product.project_flow.dashboard_plan
verify.product.project_flow.dashboard_plan: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_dashboard_plan_smoke.py"

.PHONY: verify.product.project_plan_entry_contract_guard
verify.product.project_plan_entry_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_plan_entry_contract_guard.py"

.PHONY: verify.product.project_plan_block_contract_guard
verify.product.project_plan_block_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_plan_block_contract_guard.py"

.PHONY: verify.product.project_flow.full_chain_pre_execution
verify.product.project_flow.full_chain_pre_execution: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_full_chain_pre_execution_smoke.py"

.PHONY: verify.product.project_execution_entry_contract_guard
verify.product.project_execution_entry_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_entry_contract_guard.py"

.PHONY: verify.product.project_execution_block_contract_guard
verify.product.project_execution_block_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_block_contract_guard.py"

.PHONY: verify.product.cost_tracking_entry_contract_guard
verify.product.cost_tracking_entry_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_cost_tracking_entry_contract_guard.py"

.PHONY: verify.product.cost_tracking_block_contract_guard
verify.product.cost_tracking_block_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_cost_tracking_block_contract_guard.py"

.PHONY: verify.product.cost_entry_contract_guard
verify.product.cost_entry_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_cost_entry_contract_guard.py"

.PHONY: verify.product.cost_list_block_guard
verify.product.cost_list_block_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_cost_list_block_guard.py"

.PHONY: verify.product.payment_entry_contract_guard
verify.product.payment_entry_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_payment_entry_contract_guard.py"

.PHONY: verify.product.payment_list_block_guard
verify.product.payment_list_block_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_payment_list_block_guard.py"

.PHONY: verify.product.payment_summary_block_guard
verify.product.payment_summary_block_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_payment_summary_block_guard.py"

.PHONY: verify.product.project_flow.execution_payment
verify.product.project_flow.execution_payment: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_execution_payment_smoke.py"

.PHONY: verify.product.settlement_summary_contract_guard
verify.product.settlement_summary_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_settlement_summary_contract_guard.py"

.PHONY: verify.product.release_navigation_contract_guard
verify.product.release_navigation_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_release_navigation_contract_guard.py"

.PHONY: verify.product.delivery_menu_integrity_guard
verify.product.delivery_menu_integrity_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_delivery_menu_integrity_guard.py"

.PHONY: verify.product.delivery_scene_integrity_guard
verify.product.delivery_scene_integrity_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_delivery_scene_integrity_guard.py"

.PHONY: verify.product.delivery_policy_guard
verify.product.delivery_policy_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_delivery_policy_guard.py"

.PHONY: verify.product.scene_contract_guard
verify.product.scene_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_scene_contract_guard.py"

.PHONY: verify.scene.freeze_snapshot_guard
verify.scene.freeze_snapshot_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_freeze_snapshot_guard.sh

.PHONY: verify.scene.replication_guard
verify.scene.replication_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_replication_guard.sh

.PHONY: verify.scene.version_binding_guard
verify.scene.version_binding_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_version_binding_guard.sh

.PHONY: verify.scene.lifecycle_guard
verify.scene.lifecycle_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_lifecycle_guard.sh

.PHONY: verify.scene.promotion_guard
verify.scene.promotion_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_promotion_guard.sh

.PHONY: verify.scene.active_uniqueness_guard
verify.scene.active_uniqueness_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_active_uniqueness_guard.sh

.PHONY: verify.release.scene_asset.v1
verify.release.scene_asset.v1: verify.product.scene_contract_guard verify.scene.freeze_snapshot_guard verify.scene.replication_guard verify.scene.version_binding_guard verify.scene.lifecycle_guard verify.scene.promotion_guard verify.scene.active_uniqueness_guard verify.portal.release_navigation_browser_smoke.host
	@echo "[OK] verify.release.scene_asset.v1 done"

.PHONY: verify.product.edition_policy_guard
verify.product.edition_policy_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/product_edition_policy_guard.sh

.PHONY: verify.scene.edition_binding_guard
verify.scene.edition_binding_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/scene_edition_binding_guard.sh

.PHONY: verify.release.edition_surface.v1
verify.release.edition_surface.v1: verify.product.edition_policy_guard verify.scene.edition_binding_guard
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/release_edition_surface_guard.sh
	@echo "[OK] verify.release.edition_surface.v1 done"

.PHONY: verify.edition.lifecycle_guard
verify.edition.lifecycle_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/edition_lifecycle_guard.sh

.PHONY: verify.edition.access_guard
verify.edition.access_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/edition_access_guard.sh

.PHONY: verify.edition.promotion_guard
verify.edition.promotion_guard: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(DB_NAME) COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) ENV=$(ENV) ENV_FILE=$(ENV_FILE) bash scripts/verify/edition_promotion_guard.sh

.PHONY: verify.release.edition_lifecycle.v1
verify.release.edition_lifecycle.v1: verify.release.edition_surface.v1 verify.edition.lifecycle_guard verify.edition.access_guard verify.edition.promotion_guard verify.release.delivery_engine.v1
	@echo "[OK] verify.release.edition_lifecycle.v1 done"

.PHONY: verify.edition.runtime_routing_guard
verify.edition.runtime_routing_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/edition_runtime_routing_guard.py"

.PHONY: verify.edition.session_context_guard
verify.edition.session_context_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) \
		node scripts/verify/edition_session_context_guard.mjs

.PHONY: verify.edition.route_fallback_guard
verify.edition.route_fallback_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) \
		node scripts/verify/edition_route_fallback_guard.mjs

.PHONY: verify.release.edition_runtime.v1
verify.release.edition_runtime.v1: verify.release.edition_lifecycle.v1 verify.edition.runtime_routing_guard verify.edition.session_context_guard verify.edition.route_fallback_guard
	@echo "[OK] verify.release.edition_runtime.v1 done"

.PHONY: verify.edition.freeze_surface_guard
verify.edition.freeze_surface_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/edition_freeze_surface_guard.sh

.PHONY: verify.edition.release_snapshot_guard
verify.edition.release_snapshot_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/edition_release_snapshot_guard.sh

.PHONY: verify.edition.rollback_evidence_guard
verify.edition.rollback_evidence_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/edition_rollback_evidence_guard.sh

.PHONY: verify.release.edition_freeze.v1
verify.release.edition_freeze.v1: verify.release.edition_runtime.v1 verify.edition.freeze_surface_guard verify.edition.release_snapshot_guard verify.edition.rollback_evidence_guard
	@echo "[OK] verify.release.edition_freeze.v1 done"

.PHONY: verify.release_snapshot.promotion_guard
verify.release_snapshot.promotion_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_snapshot_promotion_guard.sh

.PHONY: verify.release_snapshot.active_uniqueness_guard
verify.release_snapshot.active_uniqueness_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_snapshot_active_uniqueness_guard.sh

.PHONY: verify.release_snapshot.lineage_guard
verify.release_snapshot.lineage_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/release_snapshot_lineage_guard.py"

.PHONY: verify.release.snapshot_lineage.v1
verify.release.snapshot_lineage.v1: verify.release.edition_freeze.v1 verify.release_snapshot.promotion_guard verify.release_snapshot.active_uniqueness_guard verify.release_snapshot.lineage_guard
	@echo "[OK] verify.release.snapshot_lineage.v1 done"

.PHONY: verify.release.action_guard
verify.release.action_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_action_guard.sh

.PHONY: verify.release.orchestration_guard
verify.release.orchestration_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_orchestration_guard.sh

.PHONY: verify.release.orchestration.v1
verify.release.orchestration.v1: verify.release.snapshot_lineage.v1 verify.release.action_guard verify.release.orchestration_guard
	@echo "[OK] verify.release.orchestration.v1 done"

.PHONY: verify.release.audit_surface_guard
verify.release.audit_surface_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_audit_surface_guard.sh

.PHONY: verify.release.audit_lineage_consistency_guard
verify.release.audit_lineage_consistency_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_audit_lineage_consistency_guard.sh

.PHONY: verify.release.audit_runtime_consistency_guard
verify.release.audit_runtime_consistency_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/release_audit_runtime_consistency_guard.py"

.PHONY: verify.release.audit_trail.v1
verify.release.audit_trail.v1: verify.release.orchestration.v1 verify.release.audit_surface_guard verify.release.audit_lineage_consistency_guard verify.release.audit_runtime_consistency_guard
	@echo "[OK] verify.release.audit_trail.v1 done"

.PHONY: verify.release.policy_guard
verify.release.policy_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_policy_guard.sh

.PHONY: verify.release.approval_guard
verify.release.approval_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_approval_guard.sh

.PHONY: verify.release.approval.v1
verify.release.approval.v1: verify.release.audit_trail.v1 verify.release.policy_guard verify.release.approval_guard
	@echo "[OK] verify.release.approval.v1 done"

.PHONY: verify.release.operator_surface_guard
verify.release.operator_surface_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_operator_surface_guard.sh

.PHONY: verify.release.operator_orchestration_guard
verify.release.operator_orchestration_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_operator_orchestration_guard.sh

.PHONY: verify.portal.release_operator_surface_browser_smoke.host
verify.portal.release_operator_surface_browser_smoke.host:
	@mkdir -p $(ARTIFACTS_DIR)/codex
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node scripts/verify/release_operator_surface_browser_smoke.mjs

.PHONY: verify.release.operator_surface.v1
verify.release.operator_surface.v1: verify.release.approval.v1 verify.release.operator_surface_guard verify.release.operator_orchestration_guard verify.portal.release_operator_surface_browser_smoke.host
	@echo "[OK] verify.release.operator_surface.v1 done"

.PHONY: verify.release.operator_read_model_guard
verify.release.operator_read_model_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_operator_read_model_guard.sh

.PHONY: verify.portal.release_operator_read_model_browser_smoke.host
verify.portal.release_operator_read_model_browser_smoke.host:
	@mkdir -p $(ARTIFACTS_DIR)/codex
	@$(RUN_ENV) BASE_URL=$(BASE_URL) ARTIFACTS_DIR=$(ARTIFACTS_DIR) DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) node scripts/verify/release_operator_read_model_browser_smoke.mjs

.PHONY: verify.release.operator_read_model.v1
verify.release.operator_read_model.v1: verify.release.operator_surface.v1 verify.release.operator_read_model_guard verify.portal.release_operator_read_model_browser_smoke.host
	@echo "[OK] verify.release.operator_read_model.v1 done"

.PHONY: verify.release.operator_write_model_guard
verify.release.operator_write_model_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_operator_write_model_guard.sh

.PHONY: verify.release.operator_write_model.v1
verify.release.operator_write_model.v1: verify.release.operator_read_model.v1 verify.release.operator_write_model_guard
	@echo "[OK] verify.release.operator_write_model.v1 done"

.PHONY: verify.release.operator_contract_guard
verify.release.operator_contract_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_operator_contract_guard.sh

.PHONY: verify.release.operator_contract_freeze.v1
verify.release.operator_contract_freeze.v1: verify.release.operator_write_model.v1 verify.release.operator_contract_guard
	@echo "[OK] verify.release.operator_contract_freeze.v1 done"

.PHONY: verify.release.execution_protocol_guard
verify.release.execution_protocol_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_execution_protocol_guard.sh

.PHONY: verify.release.execution_trace_guard
verify.release.execution_trace_guard:
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/release_execution_trace_guard.sh

.PHONY: verify.release.execution_protocol.v1
verify.release.execution_protocol.v1: verify.release.operator_contract_freeze.v1 verify.release.execution_protocol_guard verify.release.execution_trace_guard
	@echo "[OK] verify.release.execution_protocol.v1 done"

.PHONY: verify.product.project_flow.execution_settlement
verify.product.project_flow.execution_settlement: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_execution_settlement_smoke.py"

.PHONY: verify.product.cost_summary_block_guard
verify.product.cost_summary_block_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_cost_summary_block_guard.py"

.PHONY: verify.product.project_execution_action_contract_guard
verify.product.project_execution_action_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_action_contract_guard.py"

.PHONY: verify.product.project_execution_state_transition_guard
verify.product.project_execution_state_transition_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_state_transition_guard.py"

.PHONY: verify.product.project_flow.full_chain_execution
verify.product.project_flow.full_chain_execution: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_full_chain_execution_smoke.py"

.PHONY: verify.product.project_flow.execution_cost
verify.product.project_flow.execution_cost: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_flow_execution_cost_smoke.py"

.PHONY: verify.product.project_execution_advance_smoke
verify.product.project_execution_advance_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_advance_smoke.py"

.PHONY: verify.product.project_execution_state_smoke
verify.product.project_execution_state_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_state_smoke.py"

.PHONY: verify.product.project_execution_consistency_guard
verify.product.project_execution_consistency_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_consistency_guard.py"

.PHONY: verify.product.project_execution_pilot_precheck_guard
verify.product.project_execution_pilot_precheck_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_execution_pilot_precheck_guard.py"

.PHONY: verify.product.native_alignment_guard
verify.product.native_alignment_guard: guard.prod.forbid
	@python3 scripts/verify/product_native_alignment_guard.py

.PHONY: verify.architecture.five_layer_workspace_audit
verify.architecture.five_layer_workspace_audit: guard.prod.forbid
	@python3 scripts/verify/five_layer_workspace_audit.py

.PHONY: verify.architecture.orchestration_platform_guard
verify.architecture.orchestration_platform_guard: guard.prod.forbid
	@python3 scripts/verify/orchestration_platform_guard.py

.PHONY: verify.product.v0_1_pilot_execution_review
verify.product.v0_1_pilot_execution_review: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_v0_1_pilot_execution_review.py"

.PHONY: verify.product.project_dashboard_entry_contract_guard
verify.product.project_dashboard_entry_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_dashboard_entry_contract_guard.py"

.PHONY: verify.product.project_dashboard_block_contract_guard
verify.product.project_dashboard_block_contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_dashboard_block_contract_guard.py"

.PHONY: verify.product.project_dashboard_baseline
verify.product.project_dashboard_baseline: verify.product.project_dashboard_flow verify.product.project_flow.dashboard_plan verify.product.project_flow.full_chain_pre_execution verify.product.project_flow.full_chain_execution verify.product.project_execution_advance_smoke verify.product.project_execution_state_transition_guard verify.product.project_execution_state_smoke verify.product.project_dashboard_entry_contract_guard verify.product.project_dashboard_block_contract_guard verify.product.project_plan_entry_contract_guard verify.product.project_plan_block_contract_guard verify.product.project_execution_entry_contract_guard verify.product.project_execution_block_contract_guard verify.product.project_execution_action_contract_guard verify.product.project_context_chain_guard verify.product.project_dashboard_non_empty_guard
	@echo "[OK] verify.product.project_dashboard_baseline done"

.PHONY: verify.product.v0_1_pilot_readiness
verify.product.v0_1_pilot_readiness: verify.product.project_initiation.full verify.product.project_execution_pilot_precheck_guard verify.product.project_execution_consistency_guard verify.product.project_execution_state_transition_guard verify.product.project_execution_state_smoke verify.product.project_execution_advance_smoke verify.product.project_execution_entry_contract_guard verify.product.project_execution_block_contract_guard verify.product.project_execution_action_contract_guard verify.system_init.latency_budget verify.frontend_api
	@echo "[OK] verify.product.v0_1_pilot_readiness done"

verify.product.suggested_action_shape_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_suggested_action_shape_guard.py"

verify.product.project_context_chain_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_context_chain_guard.py"

verify.product.project_dashboard_non_empty_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/product_project_dashboard_non_empty_guard.py"

.PHONY: verify.product.project_dashboard_decision.v1
verify.product.project_dashboard_decision.v1: guard.prod.forbid
	@bash scripts/verify/project_dashboard_decision_guard.sh
	@echo "[OK] verify.product.project_dashboard_decision.v1 done"

.PHONY: verify.demo.business_closure.v1
verify.demo.business_closure.v1: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/demo_business_closure_guard.sh
	@echo "[OK] verify.demo.business_closure.v1 done"

.PHONY: verify.business_fact_consistency.v1
verify.business_fact_consistency.v1: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/business_fact_consistency_guard.sh
	@echo "[OK] verify.business_fact_consistency.v1 done"

.PHONY: verify.payment_fact_consistency.v1
verify.payment_fact_consistency.v1: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/payment_fact_consistency_guard.sh
	@echo "[OK] verify.payment_fact_consistency.v1 done"

.PHONY: verify.payment_evidence_guard
verify.payment_evidence_guard: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/payment_evidence_guard.sh
	@echo "[OK] verify.payment_evidence_guard done"

.PHONY: verify.cost_evidence_guard
verify.cost_evidence_guard: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/cost_evidence_guard.sh
	@echo "[OK] verify.cost_evidence_guard done"

.PHONY: verify.settlement_evidence_guard
verify.settlement_evidence_guard: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/settlement_evidence_guard.sh
	@echo "[OK] verify.settlement_evidence_guard done"

.PHONY: verify.evidence_chain_project
verify.evidence_chain_project: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/evidence_chain_project_guard.sh
	@echo "[OK] verify.evidence_chain_project done"

.PHONY: verify.intent.evidence_trace
verify.intent.evidence_trace: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/intent_evidence_trace_guard.sh
	@echo "[OK] verify.intent.evidence_trace done"

.PHONY: verify.project_dashboard_evidence_contract
verify.project_dashboard_evidence_contract: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/project_dashboard_evidence_contract_guard.sh
	@echo "[OK] verify.project_dashboard_evidence_contract done"

.PHONY: verify.demo.evidence_completeness
verify.demo.evidence_completeness: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/demo_evidence_completeness_guard.sh
	@echo "[OK] verify.demo.evidence_completeness done"

.PHONY: verify.product.evidence_system.v1
verify.product.evidence_system.v1: guard.prod.forbid verify.payment_evidence_guard verify.cost_evidence_guard verify.settlement_evidence_guard verify.evidence_chain_project verify.intent.evidence_trace verify.project_dashboard_evidence_contract verify.demo.evidence_completeness
	@echo "[OK] verify.product.evidence_system.v1 done"

.PHONY: verify.evidence_production_blocking
verify.evidence_production_blocking: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=blocking bash scripts/verify/evidence_production_runtime_guard.sh
	@echo "[OK] verify.evidence_production_blocking done"

.PHONY: verify.dashboard_read_model_guard
verify.dashboard_read_model_guard: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=dashboard bash scripts/verify/evidence_production_runtime_guard.sh
	@echo "[OK] verify.dashboard_read_model_guard done"

.PHONY: verify.risk_engine_from_evidence
verify.risk_engine_from_evidence: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=risk bash scripts/verify/evidence_production_runtime_guard.sh
	@echo "[OK] verify.risk_engine_from_evidence done"

.PHONY: verify.next_action_from_evidence
verify.next_action_from_evidence: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=action bash scripts/verify/evidence_production_runtime_guard.sh
	@echo "[OK] verify.next_action_from_evidence done"

.PHONY: verify.evidence_immutability
verify.evidence_immutability: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=immutability bash scripts/verify/evidence_production_runtime_guard.sh
	@echo "[OK] verify.evidence_immutability done"

.PHONY: verify.product.evidence_production.v1
verify.product.evidence_production.v1: guard.prod.forbid verify.evidence_production_blocking verify.dashboard_read_model_guard verify.risk_engine_from_evidence verify.next_action_from_evidence verify.evidence_immutability
	@echo "[OK] verify.product.evidence_production.v1 done"

.PHONY: verify.account_move_evidence_guard
verify.account_move_evidence_guard: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/account_move_evidence_guard.sh
	@echo "[OK] verify.account_move_evidence_guard done"

.PHONY: verify.evidence_trace_entry_contract
verify.evidence_trace_entry_contract: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=trace_entry bash scripts/verify/evidence_consumption_runtime_guard.sh
	@echo "[OK] verify.evidence_trace_entry_contract done"

.PHONY: verify.evidence_timeline_contract
verify.evidence_timeline_contract: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=timeline bash scripts/verify/evidence_consumption_runtime_guard.sh
	@echo "[OK] verify.evidence_timeline_contract done"

.PHONY: verify.risk_explainability_contract
verify.risk_explainability_contract: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=risk bash scripts/verify/evidence_consumption_runtime_guard.sh
	@echo "[OK] verify.risk_explainability_contract done"

.PHONY: verify.next_action_explainability_contract
verify.next_action_explainability_contract: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=action bash scripts/verify/evidence_consumption_runtime_guard.sh
	@echo "[OK] verify.next_action_explainability_contract done"

.PHONY: verify.evidence_exception_pipeline
verify.evidence_exception_pipeline: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=pipeline bash scripts/verify/evidence_exception_runtime_guard.sh
	@echo "[OK] verify.evidence_exception_pipeline done"

.PHONY: verify.evidence_exception_lifecycle
verify.evidence_exception_lifecycle: guard.prod.forbid check-compose-project check-compose-env
	@CHECK_MODE=lifecycle bash scripts/verify/evidence_exception_runtime_guard.sh
	@echo "[OK] verify.evidence_exception_lifecycle done"

.PHONY: verify.product.enablement.sprint0
verify.product.enablement.sprint0: guard.prod.forbid check-compose-project check-compose-env
	@bash scripts/verify/company_department_guard.sh
	@DB_NAME=$(or $(DB_NAME),sc_demo) E2E_LOGIN=$(or $(E2E_LOGIN),admin) E2E_PASSWORD=$(or $(E2E_PASSWORD),admin) node scripts/verify/enterprise_enablement_frontend_smoke.mjs
	@echo "[OK] verify.product.enablement.sprint0 done"

.PHONY: verify.product.enablement.sprint1
verify.product.enablement.sprint1: guard.prod.forbid check-compose-project check-compose-env
	@DB_NAME=$(or $(DB_NAME),sc_demo) E2E_LOGIN=$(or $(E2E_LOGIN),admin) E2E_PASSWORD=$(or $(E2E_PASSWORD),admin) node scripts/verify/enterprise_user_role_frontend_smoke.mjs
	@echo "[OK] verify.product.enablement.sprint1 done"

verify.product.phase12c: verify.product.project_initiation.full verify.product.project_flow.initiation_dashboard verify.product.suggested_action_shape_guard verify.product.project_context_chain_guard verify.product.project_dashboard_non_empty_guard
	@echo "[OK] verify.product.phase12c done"

verify.phase12b.baseline: guard.prod.forbid
	@echo "[Layer:platform] verify.smart_core.minimum_surface"
	@$(MAKE) verify.smart_core.minimum_surface DB_NAME=$(or $(PLATFORM_DB_NAME),$(DB_NAME)) E2E_LOGIN=$(or $(PLATFORM_LOGIN),$(E2E_LOGIN)) E2E_PASSWORD=$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD)) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),$(or $(PLATFORM_LOGIN),$(E2E_LOGIN))) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD))) || (echo "❌ [platform] baseline failed" && exit 21)
	@echo "[Layer:portal] verify.portal.minimum_runtime_surface"
	@$(MAKE) verify.portal.minimum_runtime_surface DB_NAME=$(or $(PORTAL_DB_NAME),$(or $(PLATFORM_DB_NAME),$(DB_NAME)) ) E2E_LOGIN=$(or $(PORTAL_LOGIN),$(or $(PLATFORM_LOGIN),$(E2E_LOGIN))) E2E_PASSWORD=$(or $(PORTAL_PASSWORD),$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD))) || (echo "❌ [portal] baseline failed" && exit 22)
	@$(MAKE) verify.portal.preload_runtime_surface DB_NAME=$(or $(PORTAL_DB_NAME),$(or $(PLATFORM_DB_NAME),$(DB_NAME)) ) E2E_LOGIN=$(or $(PORTAL_LOGIN),$(or $(PLATFORM_LOGIN),$(E2E_LOGIN))) E2E_PASSWORD=$(or $(PORTAL_PASSWORD),$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD))) || (echo "❌ [portal preload] baseline failed" && exit 22)
	@$(MAKE) verify.runtime.fetch_entrypoints DB_NAME=$(or $(PORTAL_DB_NAME),$(or $(PLATFORM_DB_NAME),$(DB_NAME)) ) E2E_LOGIN=$(or $(PORTAL_LOGIN),$(or $(PLATFORM_LOGIN),$(E2E_LOGIN))) E2E_PASSWORD=$(or $(PORTAL_PASSWORD),$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD))) || (echo "❌ [runtime fetch] baseline failed" && exit 22)
	@echo "[Layer:product] verify.product.project_initiation.full"
	@$(MAKE) verify.product.project_initiation.full DB_NAME=$(or $(PRODUCT_DB_NAME),$(DB_NAME)) E2E_LOGIN=$(or $(PRODUCT_LOGIN),$(E2E_LOGIN)) E2E_PASSWORD=$(or $(PRODUCT_PASSWORD),$(E2E_PASSWORD)) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) || (echo "❌ [product] baseline failed" && exit 23)
	@echo "[Layer:product] verify.product.project_dashboard_baseline"
	@$(MAKE) verify.product.project_dashboard_baseline DB_NAME=$(or $(PRODUCT_DB_NAME),$(DB_NAME)) E2E_LOGIN=$(or $(PRODUCT_LOGIN),$(E2E_LOGIN)) E2E_PASSWORD=$(or $(PRODUCT_PASSWORD),$(E2E_PASSWORD)) || (echo "❌ [product dashboard baseline] baseline failed" && exit 24)
	@mkdir -p artifacts/baselines/platform artifacts/baselines/portal artifacts/baselines/product
	@cp -f artifacts/backend/smart_core_minimum_contract_surface_guard.json artifacts/baselines/platform/ 2>/dev/null || true
	@cp -f artifacts/backend/smart_core_owner_startup_smoke.json artifacts/baselines/platform/ 2>/dev/null || true
	@cp -f artifacts/backend/smart_core_same_route_residency_guard.json artifacts/baselines/platform/ 2>/dev/null || true
	@cp -f artifacts/backend/smart_core_minimum_surface_order_regression_guard.json artifacts/baselines/platform/ 2>/dev/null || true
	@cp -f artifacts/backend/smart_core_app_open_fallback_regression_guard.json artifacts/baselines/platform/ 2>/dev/null || true
	@cp -f artifacts/backend/smart_core_platform_minimum_nav_isolation_guard.json artifacts/baselines/platform/ 2>/dev/null || true
	@cp -f artifacts/backend/portal_minimum_runtime_surface_guard.json artifacts/baselines/portal/ 2>/dev/null || true
	@cp -f artifacts/backend/portal_preload_runtime_surface_guard.json artifacts/baselines/portal/ 2>/dev/null || true
	@cp -f artifacts/backend/runtime_fetch_entrypoints_smoke.json artifacts/baselines/portal/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_initiation_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_contract_ref_shape_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_initiation_roles_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_dashboard_flow_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_flow_dashboard_plan_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_flow_full_chain_pre_execution_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_flow_full_chain_execution_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_execution_advance_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_execution_state_transition_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_execution_state_smoke.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_dashboard_entry_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_dashboard_block_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_plan_entry_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_plan_block_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_execution_entry_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_execution_block_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_execution_action_contract_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_context_chain_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@cp -f artifacts/backend/product_project_dashboard_non_empty_guard.json artifacts/baselines/product/ 2>/dev/null || true
	@echo "[OK] verify.phase12b.baseline done"

verify.smart_core.minimum_surface.legacy_group_guard: guard.prod.forbid
	@python3 scripts/verify/smart_core_legacy_group_required_groups_guard.py

verify.smart_core.minimum_surface.handler_guard: guard.prod.forbid
	@python3 scripts/verify/smart_core_minimum_handler_surface_guard.py

verify.smart_core.minimum_surface.contract_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_minimum_contract_surface_guard.py"

verify.smart_core.minimum_surface.owner_startup_smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_owner_startup_smoke.py"

verify.smart_core.minimum_surface.same_route_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_same_route_residency_guard.py"

verify.smart_core.minimum_surface.order_regression_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_minimum_surface_order_regression_guard.py"

verify.smart_core.minimum_surface.app_open_regression_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) python3 /mnt/scripts/verify/smart_core_app_open_fallback_regression_guard.py"

verify.smart_core.minimum_surface.nav_isolation_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/smart_core_platform_minimum_nav_isolation_guard.py"

verify.smart_core.minimum_surface: verify.smart_core.minimum_surface.legacy_group_guard verify.smart_core.minimum_surface.handler_guard verify.smart_core.minimum_surface.contract_guard verify.smart_core.minimum_surface.owner_startup_smoke verify.smart_core.minimum_surface.same_route_guard verify.smart_core.minimum_surface.order_regression_guard verify.smart_core.minimum_surface.app_open_regression_guard verify.smart_core.minimum_surface.nav_isolation_guard verify.system_init.minimal_surface
	@echo "[OK] verify.smart_core.minimum_surface done"

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
gate.platform_baseline: gate.baseline
	@echo "[OK] gate.platform_baseline done"
gate.business_baseline: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/p0_flow.sh
	@echo "[OK] gate.business_baseline done"
gate.baseline.all: gate.platform_baseline gate.business_baseline
	@echo "[OK] gate.baseline.all done"

gate.demo: guard.codex.fast.noheavy guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/demo/reset.sh
	@$(RUN_ENV) DB_NAME=sc_demo bash scripts/verify/demo.sh

# ======================================================
# ==================== Module Ops ======================
# ======================================================
.PHONY: mod.install mod.upgrade guard.customer_seed_external_ids.warn guard.customer_seed_external_ids.strict
mod.install: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/mod/install.sh
mod.upgrade: guard.codex.fast.upgrade guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/mod/upgrade.sh

guard.customer_seed_external_ids.warn: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/check_customer_seed_external_ids.sh || { \
		echo "[guard.customer_seed_external_ids.warn] WARN: guard failed but non-blocking mode continues"; \
		true; \
	}

guard.customer_seed_external_ids.strict: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/check_customer_seed_external_ids.sh

# ======================================================
# ==================== Policy Ops ======================
# ======================================================
.PHONY: policy.apply.business_full policy.apply.role_matrix policy.ensure.role_surface_demo smoke.business_full smoke.role_matrix verify.portal.role_surface_preflight.container verify.portal.role_surface_smoke.container p2.smoke p3.smoke p3.audit codex.preflight codex.merge codex.rollback codex.pr.body codex.release.note db.policy stage.preflight stage.run ops.auth.dev.apply ops.auth.dev.rollback ops.auth.dev.verify
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

policy.ensure.role_surface_demo: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	if $(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME); then \
	  echo "[policy.ensure.role_surface_demo] already satisfied"; \
	elif [ "$${AUTO_FIX_ROLE_SURFACE_DEMO:-0}" = "1" ]; then \
	  echo "[policy.ensure.role_surface_demo] applying auto-fix for role surface demo baseline"; \
	  $(MAKE) --no-print-directory mod.install MODULE=smart_construction_custom DB_NAME=$(DB_NAME); \
	  $(MAKE) --no-print-directory mod.install MODULE=smart_construction_seed DB_NAME=$(DB_NAME); \
	  $(MAKE) --no-print-directory mod.install MODULE=smart_construction_demo DB_NAME=$(DB_NAME); \
	  $(RUN_ENV) DB_NAME=$(DB_NAME) ROLE_SMOKE_PASSWORD="$${ROLE_SMOKE_PASSWORD:-demo}" bash scripts/ops/ensure_role_surface_demo.sh; \
	  $(MAKE) --no-print-directory restart; \
	  $(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME); \
	else \
	  echo "[policy.ensure.role_surface_demo] FAIL: role surface demo baseline not satisfied"; \
	  echo "[policy.ensure.role_surface_demo] HINT: re-run with AUTO_FIX_ROLE_SURFACE_DEMO=1"; \
	  echo "[policy.ensure.role_surface_demo] HINT: optional ROLE_SMOKE_PASSWORD=<pwd> to set smoke login password"; \
	  exit 2; \
	fi

verify.portal.role_surface_preflight.container: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/role_surface_preflight.sh

verify.portal.role_surface_smoke.container: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME)
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) python3 /mnt/scripts/verify/role_surface_smoke.py"

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

.PHONY: demo.verify demo.load demo.list demo.load.all demo.load.full demo.load.release demo.install demo.rebuild demo.ci demo.repro demo.full seed.run audit.project.actions audit.nav.alignment audit.nav.role_diff
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

demo.load.release: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/demo/load_release.sh

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

audit.nav.alignment: guard.prod.forbid check-compose-project check-compose-env
	@ENABLE_SUGGESTIONS=1 $(MAKE) --no-print-directory audit.project.actions DB_NAME=$(DB_NAME)
	@$(MAKE) --no-print-directory verify.menu.scene_resolve.container DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD)
	@python3 scripts/audit/nav_alignment_report.py

audit.nav.role_diff: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) --no-print-directory verify.portal.role_surface_preflight.container DB_NAME=$(DB_NAME)
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) ROOT_XMLID=$(ROOT_XMLID) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 /mnt/scripts/audit/role_nav_diff.py"

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
	@if ! docker info >/dev/null 2>&1; then \
	  echo "❌ docker is required for gate.full (containers not available)"; \
	  echo "   Fix: start docker or run with SC_GATE_STRICT=0 for local-only checks."; \
	  exit 2; \
	fi
	@$(MAKE) --no-print-directory verify.contract.preflight
	@$(MAKE) --no-print-directory verify.frontend.home_suggestion_semantics.guard
	@$(MAKE) --no-print-directory verify.frontend.page_contract_boundary.guard
	@KEEP_TEST_CONTAINER=1 $(MAKE) test TEST_TAGS=sc_gate BD=$(DB_NAME)
	@$(MAKE) verify.demo BD=$(DB_NAME)
	@$(MAKE) --no-print-directory gate.scene.r3.runtime.strict
	@if [ "$(SC_GATE_STRICT)" != "0" ]; then \
	  $(MAKE) verify.menu.scene_resolve.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.menu.scene_resolve.summary; \
	  $(MAKE) verify.portal.scene_warnings_guard.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.scene_warnings_limit.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.act_url_missing_scene_report.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.cross_stack_contract_smoke.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.my_work_smoke.container DB_NAME=$(DB_NAME); \
	  $(MAKE) verify.portal.scene_observability_gate_smoke.container DB_NAME=$(DB_NAME); \
	  if [ "$(SC_SCENE_OBS_STRICT)" = "1" ]; then \
	    $(MAKE) verify.portal.scene_observability_strict.container DB_NAME=$(DB_NAME); \
	  else \
	    echo "[gate.full] SC_SCENE_OBS_STRICT=0: skip strict scene observability checks"; \
	  fi; \
	else \
	  echo "[gate.full] SC_GATE_STRICT=0: skip menu/act_url guard checks"; \
	fi
	@$(MAKE) verify.phase_9_8.gate_summary
	@$(MAKE) audit.pull DB_NAME=$(DB_NAME)

# ======================================================
# ==================== Codex Targets ===================
# ======================================================
.PHONY: codex.fast codex.gate codex.print codex.pr codex.cleanup codex.sync-main codex.cli

codex.print:
	@echo "== Codex SOP =="
	@echo "CODEX_MODE=$(CODEX_MODE) CODEX_DB=$(CODEX_DB) CODEX_MODULES=$(CODEX_MODULES) CODEX_NEED_UPGRADE=$(CODEX_NEED_UPGRADE)"
	@echo "SC_GATE_STRICT=$(SC_GATE_STRICT) SC_SCENE_OBS_STRICT=$(SC_SCENE_OBS_STRICT) SCENE_OBSERVABILITY_PREFLIGHT_STRICT=$(SCENE_OBSERVABILITY_PREFLIGHT_STRICT)"
	@echo "BASELINE_FREEZE_ENFORCE=$(BASELINE_FREEZE_ENFORCE)"
	@echo "BUSINESS_INCREMENT_PROFILE=$(BUSINESS_INCREMENT_PROFILE)"
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
.PHONY: pr.create pr.status pr.push pr.update

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

pr.update: guard.prod.forbid
	@bash -lc '\
	set -euo pipefail; \
	BR="$$(git rev-parse --abbrev-ref HEAD)"; \
	if ! echo "$$BR" | grep -Eq "^(feat|feature|codex|experiment)/.+"; then \
	  echo "[DENY] pr.update: branch not allowed: $$BR"; exit 2; \
	fi; \
	ENV_NAME="$${ENV:-dev}"; \
	if [ "$$ENV_NAME" = "prod" ]; then \
	  echo "[DENY] pr.update: ENV=prod is forbidden"; exit 3; \
	fi; \
	if [ -n "$${PROD_DANGER:-}" ]; then \
	  echo "[DENY] pr.update: PROD_DANGER is set (forbidden)"; exit 4; \
	fi; \
	if ! command -v gh >/dev/null 2>&1; then \
	  echo "[DENY] pr.update: gh CLI not found"; exit 5; \
	fi; \
	PR="$${PR:-}"; \
	if [ -z "$$PR" ]; then \
	  echo "[DENY] pr.update: missing PR=<number>"; exit 6; \
	fi; \
	ARGS=""; \
	if [ -n "$${TITLE:-}" ]; then ARGS="$$ARGS --title \"$${TITLE}\""; fi; \
	if [ -n "$${BODY:-}" ]; then ARGS="$$ARGS --body \"$${BODY}\""; fi; \
	if [ -n "$${BODY_FILE:-}" ]; then ARGS="$$ARGS --body-file \"$${BODY_FILE}\""; fi; \
	if [ -n "$${LABELS:-}" ]; then ARGS="$$ARGS --add-label \"$${LABELS}\""; fi; \
	if [ -n "$${REMOVE_LABELS:-}" ]; then ARGS="$$ARGS --remove-label \"$${REMOVE_LABELS}\""; fi; \
	if [ -z "$$ARGS" ]; then \
	  echo "[DENY] pr.update: nothing to update (set TITLE/BODY/BODY_FILE/LABELS/REMOVE_LABELS)"; exit 7; \
	fi; \
	echo "[pr.update] branch=$$BR ENV=$$ENV_NAME PR=$$PR"; \
	eval "gh pr edit $$PR $$ARGS"; \
	'

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
.PHONY: fe.install fe.dev fe.dev.reset fe.dev.daily fe.dev.test fe.dev.uat ops.runtime.align ops.runtime.align.check dev.rebuild.full fe.gate verify.frontend.build verify.frontend.typecheck.strict verify.frontend.lint.src verify.frontend.quick.gate verify.frontend.relation_entry.contract_guard verify.frontend.relation_read_closure.guard verify.frontend.modifiers_runtime.guard verify.frontend.onchange_roundtrip.guard verify.frontend.onchange_contract_schema.guard verify.frontend.onchange_line_patch.guard verify.frontend.x2many_command_semantic.guard verify.frontend.x2many_inline_edit.guard verify.contract.subviews.guard verify.frontend.view_type_render_coverage.guard verify.frontend.view_type_contract_semantic.guard verify.frontend.search_groupby_savedfilters.guard verify.frontend.group_summary_runtime.guard verify.frontend.grouped_rows_runtime.guard verify.frontend.grouped_pagination_semantic.guard verify.frontend.grouped_pagination_semantic_drift.guard verify.contract.operation_gateway.guard verify.frontend.suggested_action.contract_guard verify.frontend.suggested_action.catalog verify.frontend.suggested_action.parser_guard verify.frontend.suggested_action.runtime_guard verify.frontend.suggested_action.import_boundary_guard verify.frontend.suggested_action.usage_guard verify.frontend.suggested_action.trace_export_guard verify.frontend.suggested_action.topk_guard verify.frontend.suggested_action.since_filter_guard verify.frontend.suggested_action.hud_export_guard verify.frontend.cross_stack_smoke verify.frontend.no_new_any_guard verify.frontend.suggested_action.all verify.portal.scene_observability.structure_guard verify.portal.scene_observability.structure_guard.update

fe.install:
	@pnpm -C frontend install

fe.dev:
	@bash -lc 'source $$HOME/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend dev'

fe.dev.reset: guard.prod.forbid
	@bash scripts/dev/frontend_dev_reset.sh

fe.dev.daily: guard.prod.forbid
	@FRONTEND_PROFILE=daily bash scripts/dev/frontend_dev_reset.sh

fe.dev.test: guard.prod.forbid
	@FRONTEND_PROFILE=test bash scripts/dev/frontend_dev_reset.sh

fe.dev.uat: guard.prod.forbid
	@FRONTEND_PROFILE=uat bash scripts/dev/frontend_dev_reset.sh

ops.runtime.align: guard.prod.forbid
	@bash scripts/dev/runtime_env_align.sh

ops.runtime.align.check: guard.prod.forbid
	@bash scripts/dev/runtime_env_align.sh --check-only

dev.rebuild.full: guard.codex.fast.noheavy guard.prod.forbid
	@$(MAKE) dev.rebuild
	@$(MAKE) fe.dev.reset
	@echo "[dev.rebuild.full] done"

fe.gate:
	@pnpm -C frontend gate

verify.frontend.build: guard.prod.forbid
	@pnpm -C frontend/apps/web build

verify.frontend.typecheck.strict: guard.prod.forbid
	@pnpm -C frontend/apps/web typecheck:strict

verify.frontend.lint.src: guard.prod.forbid
	@pnpm -C frontend/apps/web lint:src

verify.frontend.relation_entry.contract_guard: guard.prod.forbid
	@python3 scripts/verify/relation_entry_contract_guard.py

verify.frontend.relation_read_closure.guard: guard.prod.forbid
	@python3 scripts/verify/relation_read_closure_guard.py

verify.frontend.modifiers_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/modifiers_runtime_guard.py

verify.frontend.onchange_roundtrip.guard: guard.prod.forbid
	@python3 scripts/verify/onchange_roundtrip_guard.py

verify.frontend.onchange_contract_schema.guard: guard.prod.forbid
	@python3 scripts/verify/onchange_contract_schema_guard.py

verify.frontend.onchange_line_patch.guard: guard.prod.forbid
	@python3 scripts/verify/onchange_line_patch_guard.py

.PHONY: verify.scene.maturity.guard
verify.scene.maturity.guard: guard.prod.forbid
	@python3 scripts/verify/scene_maturity_guard.py

.PHONY: verify.scene.coverage.dashboard
verify.scene.coverage.dashboard: guard.prod.forbid
	@python3 scripts/verify/scene_coverage_dashboard_report.py

.PHONY: verify.scene.inventory.freeze.guard
verify.scene.inventory.freeze.guard: guard.prod.forbid
	@python3 scripts/verify/scene_inventory_freeze_guard.py

.PHONY: verify.scene.role.policy.consistency.guard
verify.scene.role.policy.consistency.guard: guard.prod.forbid
	@python3 scripts/verify/scene_role_policy_consistency_guard.py

.PHONY: verify.scene.data_source.schema.guard
verify.scene.data_source.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_data_source_schema_guard.py

.PHONY: verify.scene.r3.runtime.guard
verify.scene.r3.runtime.guard: guard.prod.forbid
	@python3 scripts/verify/scene_r3_runtime_guard.py

.PHONY: verify.scene.r3.runtime.strict
verify.scene.r3.runtime.strict: guard.prod.forbid
	@python3 scripts/verify/scene_r3_runtime_guard.py \
		--max-action-chain-fail-count 0 \
		--min-pass-rate 1.0 \
		--min-action-chain-success-rate 0.50 \
		--max-action-chain-fallback-rate 0.50 \
		--fail-on-warning

.PHONY: gate.scene.r3.runtime.strict
gate.scene.r3.runtime.strict: verify.scene.r3.runtime.strict
	@echo "[gate.scene.r3.runtime.strict] PASS"

.PHONY: verify.scene.r3.runtime.quick
verify.scene.r3.runtime.quick: guard.prod.forbid gate.scene.r3.runtime.strict
	@echo "[verify.scene.r3.runtime.quick] summary"
	@sed -n '/^## Summary/,/^## Gate Thresholds/p' docs/ops/audit/scene_r3_runtime_dashboard.md | sed '$$d'
	@sed -n '/^## Gate Result/,/^## Checks/p' docs/ops/audit/scene_r3_runtime_dashboard.md | sed '$$d'

.PHONY: verify.scene.role.surface.consistency.guard
verify.scene.role.surface.consistency.guard: guard.prod.forbid
	@python3 scripts/verify/scene_role_surface_consistency_guard.py

.PHONY: verify.scene.inventory.draft.diff.report
verify.scene.inventory.draft.diff.report: guard.prod.forbid
	@python3 scripts/verify/scene_inventory_draft_diff_report.py

.PHONY: verify.scene.r1_r2.upgrade.queue.report
verify.scene.r1_r2.upgrade.queue.report: guard.prod.forbid
	@python3 scripts/verify/scene_r1_r2_upgrade_queue_report.py

.PHONY: verify.scene.r2_r3.upgrade.queue.report
verify.scene.r2_r3.upgrade.queue.report: guard.prod.forbid
	@python3 scripts/verify/scene_r2_r3_upgrade_queue_report.py

verify.frontend.x2many_command_semantic.guard: guard.prod.forbid
	@python3 scripts/verify/x2many_command_semantic_guard.py

verify.frontend.x2many_inline_edit.guard: guard.prod.forbid
	@python3 scripts/verify/x2many_inline_edit_guard.py

verify.contract.subviews.guard: guard.prod.forbid
	@python3 scripts/verify/subviews_contract_guard.py

verify.frontend.view_type_render_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/view_type_render_coverage_guard.py

verify.frontend.view_type_contract_semantic.guard: guard.prod.forbid
	@python3 scripts/verify/view_type_contract_semantic_guard.py

verify.frontend.search_groupby_savedfilters.guard: guard.prod.forbid
	@python3 scripts/verify/search_groupby_savedfilters_guard.py

verify.frontend.group_summary_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/group_summary_runtime_guard.py

verify.frontend.grouped_rows_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_rows_runtime_guard.py

verify.frontend.grouped_pagination_semantic.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_pagination_semantic_guard.py

verify.frontend.grouped_pagination_semantic_drift.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_pagination_semantic_drift_guard.py

.PHONY: verify.frontend.grouped_contract_consistency.guard
verify.frontend.grouped_contract_consistency.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_contract_consistency_guard.py

.PHONY: verify.frontend.grouped_drift_summary.guard
verify.frontend.grouped_drift_summary.guard: guard.prod.forbid
	@python3 scripts/verify/grouped_drift_summary_guard.py

.PHONY: verify.frontend.grouped_drift_summary.schema.guard
verify.frontend.grouped_drift_summary.schema.guard: guard.prod.forbid verify.frontend.grouped_drift_summary.guard
	@python3 scripts/verify/grouped_drift_summary_schema_guard.py

.PHONY: verify.frontend.grouped_drift_summary.baseline.guard
verify.frontend.grouped_drift_summary.baseline.guard: guard.prod.forbid verify.frontend.grouped_drift_summary.schema.guard
	@python3 scripts/verify/grouped_drift_summary_baseline_guard.py

.PHONY: verify.frontend.grouped_governance_brief.guard
verify.frontend.grouped_governance_brief.guard: guard.prod.forbid verify.frontend.grouped_drift_summary.baseline.guard verify.contract.governance.coverage
	@python3 scripts/verify/grouped_governance_brief_guard.py

.PHONY: verify.frontend.grouped_governance_brief.schema.guard
verify.frontend.grouped_governance_brief.schema.guard: guard.prod.forbid verify.frontend.grouped_governance_brief.guard
	@python3 scripts/verify/grouped_governance_brief_schema_guard.py

.PHONY: verify.frontend.grouped_governance_brief.baseline.guard
verify.frontend.grouped_governance_brief.baseline.guard: guard.prod.forbid verify.frontend.grouped_governance_brief.schema.guard
	@python3 scripts/verify/grouped_governance_brief_baseline_guard.py

.PHONY: verify.frontend.grouped_governance_policy_matrix
verify.frontend.grouped_governance_policy_matrix: guard.prod.forbid verify.frontend.grouped_governance_brief.baseline.guard
	@python3 scripts/verify/grouped_governance_policy_matrix.py

.PHONY: verify.frontend.grouped_governance_policy_matrix.schema.guard
verify.frontend.grouped_governance_policy_matrix.schema.guard: guard.prod.forbid verify.frontend.grouped_governance_policy_matrix
	@python3 scripts/verify/grouped_governance_policy_matrix_schema_guard.py

.PHONY: verify.frontend.grouped_governance_trend_consistency.guard
verify.frontend.grouped_governance_trend_consistency.guard: guard.prod.forbid verify.frontend.grouped_governance_policy_matrix.schema.guard
	@python3 scripts/verify/grouped_governance_trend_consistency_guard.py

.PHONY: verify.frontend.grouped_governance_trend_consistency.schema.guard
verify.frontend.grouped_governance_trend_consistency.schema.guard: guard.prod.forbid verify.frontend.grouped_governance_trend_consistency.guard
	@python3 scripts/verify/grouped_governance_trend_consistency_schema_guard.py

.PHONY: verify.frontend.grouped_governance_trend_consistency.baseline.guard
verify.frontend.grouped_governance_trend_consistency.baseline.guard: guard.prod.forbid verify.frontend.grouped_governance_trend_consistency.schema.guard
	@python3 scripts/verify/grouped_governance_trend_consistency_baseline_guard.py

.PHONY: verify.grouped.governance.bundle
verify.grouped.governance.bundle: guard.prod.forbid verify.frontend.grouped_rows_runtime.guard verify.frontend.grouped_pagination_semantic.guard verify.frontend.grouped_pagination_semantic_drift.guard verify.frontend.grouped_contract_consistency.guard verify.frontend.grouped_drift_summary.baseline.guard verify.frontend.grouped_governance_brief.baseline.guard verify.frontend.grouped_governance_policy_matrix.schema.guard verify.frontend.grouped_governance_trend_consistency.baseline.guard
	@python3 scripts/contract/export_evidence.py
	@python3 scripts/verify/contract_evidence_schema_guard.py
	@python3 scripts/verify/contract_evidence_guard.py
	@echo "[OK] verify.grouped.governance.bundle done"

verify.contract.operation_gateway.guard: guard.prod.forbid
	@python3 scripts/verify/operation_gateway_contract_guard.py

verify.frontend.quick.gate: guard.prod.forbid verify.frontend.relation_entry.contract_guard verify.frontend.relation_read_closure.guard verify.frontend.modifiers_runtime.guard verify.frontend.onchange_roundtrip.guard verify.frontend.onchange_contract_schema.guard verify.frontend.onchange_line_patch.guard verify.frontend.x2many_command_semantic.guard verify.frontend.x2many_inline_edit.guard verify.contract.subviews.guard verify.frontend.view_type_render_coverage.guard verify.frontend.view_type_contract_semantic.guard verify.frontend.search_groupby_savedfilters.guard verify.frontend.group_summary_runtime.guard verify.frontend.grouped_rows_runtime.guard verify.frontend.grouped_pagination_semantic.guard verify.frontend.grouped_pagination_semantic_drift.guard verify.frontend.grouped_contract_consistency.guard verify.frontend.grouped_drift_summary.baseline.guard verify.frontend.typecheck.strict verify.frontend.build
	@echo "[OK] verify.frontend.quick.gate done"

verify.frontend.suggested_action.contract_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_contract_guard.py

verify.frontend.suggested_action.catalog: guard.prod.forbid
	@python3 scripts/verify/suggested_action_catalog_export.py

verify.frontend.suggested_action.parser_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_parser_guard.py

verify.frontend.suggested_action.runtime_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_runtime_guard.py

verify.frontend.suggested_action.import_boundary_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_import_boundary_guard.py

verify.frontend.suggested_action.usage_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_usage_guard.py

verify.frontend.suggested_action.trace_export_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_trace_export_guard.py

verify.frontend.suggested_action.topk_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_topk_guard.py

verify.frontend.suggested_action.since_filter_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_since_filter_guard.py

verify.frontend.suggested_action.hud_export_guard: guard.prod.forbid
	@python3 scripts/verify/suggested_action_hud_export_guard.py

verify.frontend.cross_stack_smoke: guard.prod.forbid
	@python3 scripts/verify/cross_stack_suggested_action_smoke.py

verify.frontend.no_new_any_guard: guard.prod.forbid
	@python3 scripts/verify/no_new_any_guard.py

verify.portal.scene_observability.structure_guard: guard.prod.forbid
	@python3 scripts/verify/scene_observability_structure_guard.py

verify.portal.scene_observability.structure_guard.update: guard.prod.forbid
	@python3 scripts/verify/scene_observability_structure_guard.py --update

verify.frontend.suggested_action.all: guard.prod.forbid verify.frontend.suggested_action.contract_guard verify.frontend.suggested_action.parser_guard verify.frontend.suggested_action.runtime_guard verify.frontend.suggested_action.import_boundary_guard verify.frontend.suggested_action.usage_guard verify.frontend.suggested_action.trace_export_guard verify.frontend.suggested_action.topk_guard verify.frontend.suggested_action.since_filter_guard verify.frontend.suggested_action.hud_export_guard verify.frontend.cross_stack_smoke verify.frontend.no_new_any_guard verify.frontend.suggested_action.catalog verify.frontend.typecheck.strict verify.frontend.build
	@echo "[OK] verify.frontend.suggested_action.all done"

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

.PHONY: verify.e2e.contract verify.e2e.scene verify.e2e.scene_admin verify.e2e.capability_smoke verify.e2e.marketplace_smoke verify.e2e.subscription_smoke verify.e2e.ops_batch_smoke verify.capability.lint verify.frontend_api verify.frontend.intent_channel.guard verify.scene.legacy_endpoint.guard verify.scene.legacy_contract.guard verify.scene.legacy.contract.guard verify.scene.legacy_docs.guard verify.scene.legacy_auth.smoke verify.scene.legacy_deprecation.smoke verify.scene.legacy.bundle verify.scene.legacy.all verify.scene.runtime_boundary.gate verify.scene.contract_path.gate verify.intent.router.purity verify.scene.definition.semantics verify.scene.catalog.source.guard verify.scene.catalog.runtime_alignment.guard verify.scene.catalog.governance.guard verify.load_view.access.contract.guard verify.model.ui_dependency.guard verify.business.shape.guard verify.controller.delegate.guard verify.controller.allowlist.routes.guard verify.controller.route.policy.guard verify.controller.boundary.report verify.controller.boundary.baseline.guard verify.controller.boundary.guard verify.business.core_journey.guard verify.role.capability_floor.guard verify.role.capability_floor.prod_like verify.role.capability_floor.prod_like.schema.guard verify.contract.assembler.semantic.smoke verify.contract.assembler.semantic.strict verify.contract.assembler.semantic.schema.guard verify.project.form.contract.surface.guard verify.runtime.surface.dashboard.report verify.runtime.surface.dashboard.schema.guard verify.runtime.surface.dashboard.strict.guard verify.capability.core.health.report verify.capability.core.health.schema.guard verify.scene.contract.semantic.v2.guard verify.phase_next.evidence.bundle verify.phase_next.evidence.bundle.strict verify.business.capability_baseline.report verify.business.capability_baseline.report.schema.guard verify.business.capability_baseline.report.guard verify.business.capability_baseline.guard verify.contract.evidence.export verify.contract.evidence.schema.guard verify.contract.evidence.guard verify.baseline.policy_integrity.guard verify.scene.demo_leak.guard verify.contract.ordering.smoke verify.contract.catalog.determinism verify.contract.envelope verify.contract.envelope.guard verify.seed.demo.import_boundary.guard verify.seed.demo.isolation verify.boundary.guard verify.contract.snapshot verify.system_init.snapshot_equivalence verify.mode.filter verify.capability.schema verify.scene.schema verify.backend.architecture.full verify.backend.architecture.full.report verify.backend.architecture.full.report.schema.guard verify.backend.architecture.full.report.guard verify.backend.architecture.full.report.guard.schema.guard verify.backend.evidence.manifest verify.backend.evidence.manifest.schema.guard verify.backend.evidence.manifest.guard verify.extension_modules.guard verify.test_seed_dependency.guard verify.contract_drift.guard verify.intent.side_effect_policy_guard verify.baseline.freeze_guard verify.business.increment.preflight verify.business.increment.preflight.strict verify.business.increment.readiness verify.business.increment.readiness.strict verify.business.increment.readiness.brief verify.business.increment.readiness.brief.strict verify.docs.inventory verify.docs.links verify.docs.temp_guard verify.docs.contract_sync verify.docs.all verify.boundary.import_guard verify.boundary.import_guard.schema.guard verify.boundary.import_guard.strict.guard verify.backend.boundary_guard verify.scene.provider.guard verify.capability.provider.guard verify.capability.registry.smoke verify.scene.hud.trace.smoke verify.scene.meta.trace.smoke verify.contract.governance.coverage verify.scene_capability.contract.guard verify.contract.governance.brief verify.contract.scene_coverage.brief verify.contract.scene_coverage.guard verify.contract.mode.smoke verify.contract.api.mode.smoke verify.contract.preflight verify.round.v0_6.mini verify.intent.capability.matrix.report verify.write_intent.permission.audit verify.scene.intent.matrix.report verify.etag.validation.report verify.auto_degrade.smoke.report verify.scene.drift.smoke.report verify.capability.orphan.report verify.platform.kernel.ready audit.intent.surface policy.apply.extension_modules policy.ensure.extension_modules verify.system_init.init_meta_minimal_guard verify.system_init.latency_budget verify.phase12f
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

.PHONY: verify.usage.product.clean
verify.usage.product.clean: guard.prod.forbid
	@python3 scripts/verify/usage_product_clean_guard.py

verify.frontend_api: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/frontend_api_smoke.py

.PHONY: verify.project.dashboard.contract
verify.project.dashboard.contract: guard.prod.forbid
	@python3 scripts/verify/project_management_contract_guard.py
	@python3 scripts/verify/project_dashboard_assembly_guard.py
	@python3 scripts/verify/project_dashboard_block_schema_guard.py
	@python3 scripts/verify/project_dashboard_block_payload_guard.py
	@python3 scripts/verify/project_dashboard_metric_semantics_guard.py
	@python3 scripts/verify/project_dashboard_intent_guard.py
	@python3 scripts/verify/project_dashboard_runtime_chain_guard.py
	@python3 scripts/verify/project_dashboard_project_id_order_guard.py
	@python3 -m py_compile addons/smart_construction_core/handlers/project_dashboard.py addons/smart_construction_core/services/project_dashboard_service.py addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py addons/smart_construction_core/services/project_dashboard_builders/base.py addons/smart_construction_core/services/project_dashboard_builders/project_header_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_metrics_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_progress_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_contract_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_cost_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_finance_builder.py addons/smart_construction_core/services/project_dashboard_builders/project_risk_builder.py
	@echo "[OK] verify.project.dashboard.contract done"

.PHONY: verify.workbench.extraction_hit_rate.report
verify.workbench.extraction_hit_rate.report: guard.prod.forbid
	@python3 scripts/verify/workbench_extraction_hit_rate_report.py
	@echo "[OK] verify.workbench.extraction_hit_rate.report done"

.PHONY: verify.project.dashboard.snapshot
verify.project.dashboard.snapshot: guard.prod.forbid
	@python3 scripts/verify/project_dashboard_contract_snapshot_export.py
	@python3 scripts/verify/project_dashboard_snapshot_schema_guard.py
	@python3 scripts/verify/project_dashboard_snapshot_freshness_guard.py
	@python3 scripts/verify/project_dashboard_evidence_export.py

.PHONY: verify.project.dashboard.evidence
verify.project.dashboard.evidence: guard.prod.forbid
	@python3 scripts/verify/project_dashboard_evidence_export.py

.PHONY: verify.project.management.productization
verify.project.management.productization: guard.prod.forbid verify.project.dashboard.contract verify.project.dashboard.snapshot verify.project.lifecycle.semantic.guard
	@python3 scripts/verify/project_management_productization_flow_guard.py

.PHONY: verify.project.lifecycle.semantic.guard
verify.project.lifecycle.semantic.guard: guard.prod.forbid
	@python3 scripts/verify/project_lifecycle_semantic_guard.py

.PHONY: verify.frontend.project_management.scene_bridge.guard
verify.frontend.project_management.scene_bridge.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_project_management_scene_bridge_guard.py

.PHONY: verify.frontend.scene_contract_v1.consumption.guard
verify.frontend.scene_contract_v1.consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_contract_v1_consumption_guard.py

.PHONY: verify.project.management.acceptance
verify.project.management.acceptance: guard.prod.forbid verify.project.management.productization verify.frontend.project_management.scene_bridge.guard
	@python3 scripts/verify/project_management_productization_acceptance_export.py

.PHONY: verify.product.main_entry_convergence_guard
verify.product.main_entry_convergence_guard: guard.prod.forbid
	@bash scripts/verify/main_entry_convergence_guard.sh

.PHONY: verify.product.main_entry_convergence.v1
verify.product.main_entry_convergence.v1: guard.prod.forbid verify.product.main_entry_convergence_guard verify.project.management.acceptance verify.portal.project_dashboard_primary_entry_browser_smoke.host

verify.frontend.intent_channel.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_intent_channel_guard.py

.PHONY: verify.frontend.contract_runtime.guard
verify.frontend.contract_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_runtime_guard.py

.PHONY: verify.frontend.contract_route.guard
verify.frontend.contract_route.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_route_guard.py

.PHONY: verify.frontend.contract_normalized_fields.guard
verify.frontend.contract_normalized_fields.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_normalized_fields_guard.py

.PHONY: verify.frontend.contract_query_context.guard
verify.frontend.contract_query_context.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_query_context_guard.py

.PHONY: verify.frontend.contract_record_layout.guard
verify.frontend.contract_record_layout.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_record_layout_guard.py

.PHONY: verify.frontend.product.contract_consumption.guard
verify.frontend.product.contract_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_product_contract_consumption_guard.py

.PHONY: verify.frontend.runtime_navigation_hud.guard
verify.frontend.runtime_navigation_hud.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_runtime_navigation_hud_guard.py

.PHONY: verify.frontend.home_suggestion_semantics.guard
verify.frontend.home_suggestion_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_home_suggestion_semantics_guard.py

.PHONY: verify.frontend.home_layout_section_coverage.guard
verify.frontend.home_layout_section_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_home_layout_section_coverage_guard.py

.PHONY: verify.frontend.home_orchestration_consumption.guard
verify.frontend.home_orchestration_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_home_orchestration_consumption_guard.py

.PHONY: verify.scene.ready.strict_contract.guard
verify.scene.ready.strict_contract.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_strict_contract_guard.py

.PHONY: verify.scene.ready.strict_gap.full_audit
verify.scene.ready.strict_gap.full_audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_ready_strict_gap_full_audit.py

.PHONY: verify.workspace_home.sections_schema.guard
verify.workspace_home.sections_schema.guard: guard.prod.forbid
	@python3 scripts/verify/workspace_home_sections_schema_guard.py

.PHONY: verify.workspace_home.orchestration_schema.guard
verify.workspace_home.orchestration_schema.guard: guard.prod.forbid
	@python3 scripts/verify/workspace_home_orchestration_schema_guard.py

.PHONY: verify.workspace_home.provider_split.guard
verify.workspace_home.provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/workspace_home_provider_split_guard.py

.PHONY: verify.frontend.contract_text_hardcode.guard
verify.frontend.contract_text_hardcode.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_contract_text_hardcode_guard.py

.PHONY: verify.frontend.page_contract_boundary.guard
verify.frontend.page_contract_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_boundary_guard.py

.PHONY: verify.frontend.page_contract.sections_coverage.guard
verify.frontend.page_contract.sections_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_sections_coverage_guard.py

.PHONY: verify.frontend.page_contract.key_consistency.guard
verify.frontend.page_contract.key_consistency.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_key_consistency_guard.py

.PHONY: verify.frontend.page_contract.section_tag_coverage.guard
verify.frontend.page_contract.section_tag_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_section_tag_coverage_guard.py

.PHONY: verify.frontend.page_contract.section_style_coverage.guard
verify.frontend.page_contract.section_style_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_section_style_coverage_guard.py

.PHONY: verify.frontend.page_contract.orchestration_consumption.guard
verify.frontend.page_contract.orchestration_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_orchestration_consumption_guard.py

.PHONY: verify.frontend.page_contract.runtime_universal.guard
verify.frontend.page_contract.runtime_universal.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_contract_runtime_universal_guard.py

.PHONY: verify.frontend.page_block_renderer_smoke
verify.frontend.page_block_renderer_smoke: guard.prod.forbid
	@python3 scripts/verify/frontend_page_block_renderer_smoke_guard.py

.PHONY: verify.frontend.page_block_visual_snapshot_guard
verify.frontend.page_block_visual_snapshot_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_block_visual_snapshot_guard.py

.PHONY: verify.frontend.portal_dashboard_block_migration
verify.frontend.portal_dashboard_block_migration: guard.prod.forbid
	@python3 scripts/verify/frontend_portal_dashboard_block_migration_guard.py

.PHONY: verify.frontend.workbench_block_migration
verify.frontend.workbench_block_migration: guard.prod.forbid
	@python3 scripts/verify/frontend_workbench_block_migration_guard.py

.PHONY: verify.frontend.my_work_block_migration
verify.frontend.my_work_block_migration: guard.prod.forbid
	@python3 scripts/verify/frontend_my_work_block_migration_guard.py

.PHONY: verify.frontend.page_block_registry_guard
verify.frontend.page_block_registry_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_block_registry_guard.py

.PHONY: verify.frontend.page_legacy_renderer_residue_guard
verify.frontend.page_legacy_renderer_residue_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_legacy_renderer_residue_guard.py

.PHONY: verify.frontend.page_renderer_default_guard
verify.frontend.page_renderer_default_guard: guard.prod.forbid
	@python3 scripts/verify/frontend_page_renderer_default_guard.py

.PHONY: verify.page_orchestration.target_completion.guard
verify.page_orchestration.target_completion.guard: guard.prod.forbid
	@python3 scripts/verify/page_orchestration_target_completion_guard.py

.PHONY: verify.page_contract.sections_schema.guard
verify.page_contract.sections_schema.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_sections_schema_guard.py

.PHONY: verify.page_contract.orchestration_schema.guard
verify.page_contract.orchestration_schema.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_orchestration_schema_guard.py

.PHONY: verify.page_contract.role_orchestration_variance.guard
verify.page_contract.role_orchestration_variance.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_role_orchestration_variance_guard.py

.PHONY: verify.page_contract.action_schema_semantics.guard
verify.page_contract.action_schema_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_action_schema_semantics_guard.py

.PHONY: verify.page_contract.data_source_semantics.guard
verify.page_contract.data_source_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_data_source_semantics_guard.py

.PHONY: verify.orchestration.semantics_registry.guard
verify.orchestration.semantics_registry.guard: guard.prod.forbid
	@python3 scripts/verify/orchestration_semantics_registry_guard.py

.PHONY: verify.page_contract.text_key_coverage.guard
verify.page_contract.text_key_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_text_key_coverage_guard.py

.PHONY: verify.page_contract.provider_split.guard
verify.page_contract.provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_provider_split_guard.py

.PHONY: verify.page_contract.semantic_provider_split.guard
verify.page_contract.semantic_provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_semantic_provider_split_guard.py

.PHONY: verify.page_contract.strategy_provider_split.guard
verify.page_contract.strategy_provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_strategy_provider_split_guard.py

.PHONY: verify.page_contract.role_strategy_provider_split.guard
verify.page_contract.role_strategy_provider_split.guard: guard.prod.forbid
	@python3 scripts/verify/page_contract_role_strategy_provider_split_guard.py

.PHONY: verify.list.surface.clean
verify.list.surface.clean: guard.prod.forbid
	@python3 scripts/verify/list_surface_clean_guard.py

.PHONY: verify.frontend.scene_record_semantics.guard
verify.frontend.scene_record_semantics.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_record_semantics_guard.py

.PHONY: verify.frontend.scene_contract_auto_render.guard
verify.frontend.scene_contract_auto_render.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_contract_auto_render_guard.py

.PHONY: verify.frontend.actionview.scene_specialcase.guard
verify.frontend.actionview.scene_specialcase.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_actionview_scene_specialcase_guard.py

.PHONY: verify.frontend.error_context.contract.guard
verify.frontend.error_context.contract.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_error_context_contract_guard.py

.PHONY: verify.render.semantic.ready
verify.render.semantic.ready: guard.prod.forbid
	@python3 scripts/verify/render_semantic_ready_guard.py

.PHONY: verify.contract.governance.determinism.guard
verify.contract.governance.determinism.guard: guard.prod.forbid
	@python3 scripts/verify/contract_governance_determinism_guard.py

.PHONY: verify.render.policy.ready
verify.render.policy.ready: guard.prod.forbid verify.contract.governance.determinism.guard
	@python3 scripts/verify/render_policy_ready_guard.py

.PHONY: verify.frontend.product.ready
verify.frontend.product.ready: guard.prod.forbid \
	verify.scene.ready.strict_contract.guard \
	verify.frontend.contract_runtime.guard \
	verify.frontend.contract_route.guard \
	verify.frontend.contract_normalized_fields.guard \
	verify.frontend.contract_query_context.guard \
	verify.frontend.contract_record_layout.guard \
	verify.frontend.product.contract_consumption.guard \
	verify.frontend.runtime_navigation_hud.guard \
	verify.frontend.home_suggestion_semantics.guard \
	verify.frontend.home_layout_section_coverage.guard \
	verify.frontend.home_orchestration_consumption.guard \
	verify.workspace_home.sections_schema.guard \
	verify.workspace_home.orchestration_schema.guard \
	verify.workspace_home.provider_split.guard \
	verify.frontend.contract_text_hardcode.guard \
	verify.frontend.page_contract_boundary.guard \
	verify.frontend.page_contract.sections_coverage.guard \
	verify.frontend.page_contract.key_consistency.guard \
	verify.frontend.page_contract.section_tag_coverage.guard \
	verify.frontend.page_contract.section_style_coverage.guard \
	verify.frontend.page_contract.orchestration_consumption.guard \
	verify.frontend.page_contract.runtime_universal.guard \
	verify.frontend.page_block_renderer_smoke \
	verify.frontend.page_block_visual_snapshot_guard \
	verify.frontend.portal_dashboard_block_migration \
	verify.frontend.workbench_block_migration \
	verify.frontend.my_work_block_migration \
	verify.frontend.page_block_registry_guard \
	verify.frontend.page_legacy_renderer_residue_guard \
	verify.frontend.page_renderer_default_guard \
	verify.page_orchestration.target_completion.guard \
	verify.page_contract.sections_schema.guard \
	verify.page_contract.orchestration_schema.guard \
	verify.page_contract.role_orchestration_variance.guard \
	verify.page_contract.action_schema_semantics.guard \
	verify.page_contract.data_source_semantics.guard \
	verify.orchestration.semantics_registry.guard \
	verify.page_contract.text_key_coverage.guard \
	verify.page_contract.provider_split.guard \
	verify.page_contract.semantic_provider_split.guard \
	verify.page_contract.strategy_provider_split.guard \
	verify.page_contract.role_strategy_provider_split.guard \
	verify.list.surface.clean \
	verify.frontend.scene_contract_auto_render.guard \
	verify.frontend.actionview.scene_specialcase.guard \
	verify.frontend.scene_record_semantics.guard \
	verify.frontend.error_context.contract.guard \
	verify.render.semantic.ready \
	verify.render.policy.ready \
	verify.frontend_api \
	verify.ui.product.stability
	@echo "[OK] verify.frontend.product.ready done"

.PHONY: verify.product.fullstack.ready
verify.product.fullstack.ready: guard.prod.forbid verify.product.release.ready verify.usage.product.clean verify.frontend.product.ready
	@echo "[OK] verify.product.fullstack.ready done"

verify.scene.legacy_endpoint.guard: guard.prod.forbid
	@python3 scripts/verify/legacy_scene_endpoint_guard.py

verify.scene.legacy_contract.guard: guard.prod.forbid
	@python3 scripts/verify/scene_legacy_contract_guard.py

verify.scene.legacy.contract.guard: verify.scene.legacy_contract.guard
	@echo "[OK] verify.scene.legacy.contract.guard alias -> verify.scene.legacy_contract.guard"

verify.scene.legacy_docs.guard: guard.prod.forbid
	@python3 scripts/verify/scene_legacy_docs_guard.py

verify.scene.legacy_auth.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_legacy_auth_smoke.py

.PHONY: verify.scene.legacy_auth.smoke.semantic
verify.scene.legacy_auth.smoke.semantic: guard.prod.forbid
	@python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py

.PHONY: verify.scene.legacy_auth.runtime_probe
verify.scene.legacy_auth.runtime_probe: guard.prod.forbid
	@python3 scripts/verify/scene_legacy_auth_runtime_probe.py

.PHONY: verify.native.business_fact.static
verify.native.business_fact.static: guard.prod.forbid
	@python3 scripts/verify/native_business_fact_static_usability_verify.py

verify.scene.legacy_deprecation.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_legacy_deprecation_smoke.py

verify.scene.legacy.bundle: guard.prod.forbid verify.scene.legacy_contract.guard verify.scene.legacy_docs.guard verify.scene.legacy_auth.smoke verify.scene.legacy_deprecation.smoke
	@echo "[OK] verify.scene.legacy.bundle done"

verify.scene.legacy.all: guard.prod.forbid verify.scene.legacy_endpoint.guard verify.scene.legacy.bundle
	@echo "[OK] verify.scene.legacy.all done"

verify.intent.router.purity: guard.prod.forbid
	@python3 scripts/verify/intent_router_purity_guard.py

verify.scene.definition.semantics: guard.prod.forbid
	@python3 scripts/verify/scene_definition_semantics_guard.py

verify.scene.catalog.source.guard: guard.prod.forbid
	@python3 scripts/verify/scene_catalog_source_guard.py

verify.model.ui_dependency.guard: guard.prod.forbid
	@python3 scripts/verify/model_ui_dependency_guard.py

verify.business.shape.guard: guard.prod.forbid
	@python3 scripts/verify/business_shape_assembly_guard.py

verify.controller.delegate.guard: guard.prod.forbid
	@python3 scripts/verify/controller_delegate_guard.py

verify.controller.allowlist.routes.guard: guard.prod.forbid
	@python3 scripts/verify/controller_allowlist_routes_guard.py

verify.controller.route.policy.guard: guard.prod.forbid
	@python3 scripts/verify/controller_route_policy_guard.py

.PHONY: verify.controller.platform_no_industry_import.guard
verify.controller.platform_no_industry_import.guard: guard.prod.forbid
	@python3 scripts/verify/controller_platform_no_industry_import_guard.py

.PHONY: verify.controller.platform_no_industry_service_import.guard
verify.controller.platform_no_industry_service_import.guard: guard.prod.forbid
	@python3 scripts/verify/controller_platform_no_industry_service_import_guard.py

.PHONY: verify.adapter.protocol.hook.guard
verify.adapter.protocol.hook.guard: guard.prod.forbid
	@python3 scripts/verify/adapter_protocol_hook_guard.py

.PHONY: verify.orchestration.adapter.protocol.hook.guard
verify.orchestration.adapter.protocol.hook.guard: guard.prod.forbid
	@python3 scripts/verify/orchestration_adapter_protocol_hook_guard.py

verify.controller.boundary.report: guard.prod.forbid
	@python3 scripts/verify/controller_boundary_report.py

verify.controller.boundary.baseline.guard: guard.prod.forbid
	@python3 scripts/verify/controller_boundary_baseline_guard.py

verify.controller.boundary.guard: guard.prod.forbid verify.controller.delegate.guard verify.controller.allowlist.routes.guard verify.controller.route.policy.guard verify.controller.platform_no_industry_import.guard verify.controller.platform_no_industry_service_import.guard verify.adapter.protocol.hook.guard verify.orchestration.adapter.protocol.hook.guard verify.controller.boundary.report verify.controller.boundary.baseline.guard
	@echo "[OK] verify.controller.boundary.guard done"

verify.scene.catalog.runtime_alignment.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_catalog_runtime_alignment_guard.py

verify.scene.catalog.governance.guard: guard.prod.forbid verify.scene.catalog.source.guard verify.scene.catalog.runtime_alignment.guard
	@echo "[OK] verify.scene.catalog.governance.guard done"

verify.load_view.access.contract.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/load_view_access_contract_guard.py

verify.business.core_journey.guard: guard.prod.forbid
	@python3 scripts/verify/business_core_journey_guard.py

verify.role.capability_floor.guard: guard.prod.forbid
	@python3 scripts/verify/role_capability_floor_guard.py

verify.role.capability_floor.prod_like: guard.prod.forbid
	@python3 scripts/verify/role_capability_floor_prod_like.py

verify.role.capability_floor.prod_like.schema.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/role_capability_floor_prod_like_schema_guard.py

verify.role.management_viewer.readonly.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/management_viewer_readonly_guard.py

verify.role.project_member.unification.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/project_member_unification_guard.py

verify.role.system_admin.minimum_permission_audit.guard: guard.prod.forbid verify.role.capability_floor.prod_like verify.write_intent.permission.audit
	@python3 scripts/verify/system_admin_minimum_permission_audit_guard.py

verify.role.acl.minimum_set.guard: guard.prod.forbid
	@python3 scripts/verify/role_acl_minimum_set_guard.py

verify.project.dashboard.role_runtime.guard: guard.prod.forbid
	@python3 scripts/verify/project_dashboard_role_runtime_guard.py

verify.scene.permission_reasoncode_deeplink.guard: guard.prod.forbid verify.release.capability.audit.schema.guard verify.scene.contract.shape verify.project.dashboard.snapshot
	@python3 scripts/verify/scene_permission_reasoncode_deeplink_guard.py

verify.contract.assembler.semantic.smoke: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/contract_assembler_semantic_smoke.py

verify.contract.assembler.semantic.strict: guard.prod.forbid verify.role.capability_floor.prod_like
	@SC_P4_SEMANTIC_STRICT=1 python3 scripts/verify/contract_assembler_semantic_smoke.py

verify.contract.assembler.semantic.schema.guard: guard.prod.forbid verify.contract.assembler.semantic.smoke
	@python3 scripts/verify/contract_assembler_semantic_schema_guard.py

verify.project.form.contract.surface.guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/project_form_contract_surface_guard.py

.PHONY: verify.relation.access_policy.consistency.audit
verify.relation.access_policy.consistency.audit: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/relation_access_policy_consistency_audit.py

.PHONY: verify.native_surface_integrity_guard verify.governed_surface_policy_guard verify.contract.native_integrity_guard verify.contract.governed_policy_guard verify.contract.surface_mapping_guard verify.contract.parse_boundary.guard verify.contract.production_chain.guard
verify.native_surface_integrity_guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/native_surface_integrity_guard.py

verify.governed_surface_policy_guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/governed_surface_policy_guard.py

verify.contract.native_integrity_guard: guard.prod.forbid verify.native_surface_integrity_guard
	@echo "[OK] verify.contract.native_integrity_guard done"

verify.contract.governed_policy_guard: guard.prod.forbid verify.governed_surface_policy_guard
	@echo "[OK] verify.contract.governed_policy_guard done"

verify.contract.surface_mapping_guard: guard.prod.forbid verify.role.capability_floor.prod_like
	@python3 scripts/verify/surface_mapping_guard.py

verify.contract.parse_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/contract_parse_boundary_guard.py

verify.contract.production_chain.guard: guard.prod.forbid
	@python3 scripts/verify/contract_production_chain_guard.py

verify.runtime.surface.dashboard.report: guard.prod.forbid verify.scene.catalog.runtime_alignment.guard verify.role.capability_floor.prod_like
	@python3 scripts/verify/runtime_surface_dashboard_report.py

verify.runtime.surface.dashboard.schema.guard: guard.prod.forbid verify.runtime.surface.dashboard.report
	@python3 scripts/verify/runtime_surface_dashboard_schema_guard.py

verify.runtime.surface.dashboard.strict.guard: guard.prod.forbid verify.runtime.surface.dashboard.report verify.runtime.surface.dashboard.schema.guard
	@python3 scripts/verify/runtime_surface_dashboard_strict_guard.py

verify.backend.architecture.full.report: guard.prod.forbid
	@python3 scripts/verify/backend_architecture_full_report.py

verify.backend.architecture.full.report.schema.guard: guard.prod.forbid verify.backend.architecture.full.report
	@python3 scripts/verify/backend_architecture_full_report_schema_guard.py

verify.backend.architecture.full.report.guard: guard.prod.forbid verify.backend.architecture.full.report.schema.guard
	@python3 scripts/verify/backend_architecture_full_report_guard.py

verify.backend.architecture.full.report.guard.schema.guard: guard.prod.forbid verify.backend.architecture.full.report.guard
	@python3 scripts/verify/backend_architecture_full_report_guard_schema_guard.py

verify.backend.evidence.manifest: guard.prod.forbid verify.contract.evidence.guard verify.backend.architecture.full.report.guard
	@python3 scripts/verify/backend_evidence_manifest.py

verify.backend.evidence.manifest.schema.guard: guard.prod.forbid verify.backend.evidence.manifest
	@python3 scripts/verify/backend_evidence_manifest_schema_guard.py

verify.backend.evidence.manifest.guard: guard.prod.forbid verify.backend.evidence.manifest.schema.guard
	@python3 scripts/verify/backend_evidence_manifest_guard.py

verify.capability.core.health.report: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/capability_core_health_report.py

verify.capability.core.health.schema.guard: guard.prod.forbid verify.capability.core.health.report
	@python3 scripts/verify/capability_core_health_report_schema_guard.py

verify.scene.contract.semantic.v2.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_contract_semantic_v2_guard.py

verify.phase_next.evidence.bundle: guard.prod.forbid verify.role.capability_floor.prod_like verify.role.capability_floor.prod_like.schema.guard verify.load_view.access.contract.guard verify.contract.assembler.semantic.smoke verify.contract.assembler.semantic.schema.guard verify.project.form.contract.surface.guard verify.runtime.surface.dashboard.report verify.runtime.surface.dashboard.schema.guard verify.scene.capability.matrix.schema.guard verify.capability.core.health.schema.guard verify.scene.contract.semantic.v2.guard verify.native_view.semantic_page
	@echo "[OK] verify.phase_next.evidence.bundle done"

verify.phase_next.evidence.bundle.strict: guard.prod.forbid verify.phase_next.evidence.bundle verify.contract.assembler.semantic.strict verify.runtime.surface.dashboard.strict.guard verify.backend.architecture.full.report.guard
	@$(MAKE) --no-print-directory verify.backend.evidence.manifest.guard
	@echo "[OK] verify.phase_next.evidence.bundle.strict done"

verify.business.capability_baseline.report: guard.prod.forbid
	@python3 scripts/verify/business_capability_baseline_report.py

verify.business.capability_baseline.report.schema.guard: guard.prod.forbid verify.business.capability_baseline.report
	@python3 scripts/verify/business_capability_baseline_report_schema_guard.py

verify.business.capability_baseline.report.guard: guard.prod.forbid verify.business.capability_baseline.report.schema.guard
	@python3 scripts/verify/business_capability_baseline_report_guard.py

verify.business.capability_baseline.guard: guard.prod.forbid verify.scene.catalog.runtime_alignment.guard verify.business.core_journey.guard verify.role.capability_floor.guard verify.business.capability_baseline.report.guard
	@echo "[OK] verify.business.capability_baseline.guard done"

verify.contract.evidence.export: guard.prod.forbid audit.intent.surface verify.scene.contract.shape verify.business.capability_baseline.guard verify.contract.scene_coverage.brief verify.backend.architecture.full.report.schema.guard
	@python3 scripts/contract/export_evidence.py

verify.contract.evidence.schema.guard: guard.prod.forbid verify.contract.evidence.export
	@python3 scripts/verify/contract_evidence_schema_guard.py

verify.contract.evidence.guard: guard.prod.forbid verify.contract.evidence.schema.guard
	@python3 scripts/verify/contract_evidence_guard.py

verify.baseline.policy_integrity.guard: guard.prod.forbid
	@python3 scripts/verify/baseline_policy_integrity_guard.py

verify.scene.demo_leak.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_demo_leak_guard.py

verify.contract.ordering.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_order_determinism_smoke.py

verify.contract.catalog.determinism: guard.prod.forbid
	@python3 scripts/verify/contract_catalog_determinism_guard.py

verify.contract.envelope.guard: guard.prod.forbid
	@python3 scripts/verify/contract_envelope_guard.py

verify.contract.envelope: guard.prod.forbid verify.contract.envelope.guard verify.contract.mode.smoke verify.contract.api.mode.smoke verify.scene_capability.contract.guard
	@echo "[OK] verify.contract.envelope done"

verify.scene.runtime_boundary.gate: guard.prod.forbid verify.boundary.import_guard verify.backend.boundary_guard verify.model.ui_dependency.guard verify.business.shape.guard verify.controller.boundary.guard verify.frontend.intent_channel.guard verify.frontend.no_base_contract_direct_consume.guard verify.frontend.scene_governance_consumption.guard verify.scene.provider.guard verify.scene.provider_shape.guard verify.scene.contract_v1.field_schema.guard verify.scene.engine_migration.matrix.guard verify.scene.legacy_endpoint.guard verify.intent.router.purity verify.scene.input_boundary.guard verify.scene.governance_payload.guard verify.scene.asset_queue_trend.guard verify.scene.ready.consumption_trend.guard verify.scene.governance_history_report.guard verify.scene.governance_history_archive.guard verify.scene.registry_asset_snapshot.guard verify.scene.base_contract_source_mix.guard verify.scene.source_fallback_burndown.guard verify.scene.no_action_scene.guard verify.scene.sample_registry_diff.guard verify.scene.sample_registry_diff_trend.guard verify.scene.base_contract_asset_coverage.guard verify.scene.orchestrator.input.schema.guard verify.scene.orchestrator.output.schema.guard verify.scene.orchestrator.base_fact_binding.guard verify.scene.orchestrator.industry_interface.guard verify.scene.orchestrator.merge_priority.guard verify.scene.orchestrator.scene_type_surface.guard verify.scene.orchestrator.action_surface.guard verify.scene.orchestrator.key_scene_compile.guard verify.scene.action_surface_strategy.wiring.guard verify.scene.action_surface_strategy.schema.guard verify.scene.action_surface_strategy.payload.guard verify.scene.action_surface_strategy.priority.guard verify.scene.action_surface_strategy.live_matrix.guard verify.scene.ready.scene_type_consumption_metrics.guard verify.scene.validation_recovery_strategy.guard verify.scene.validation_recovery_strategy.payload_path.guard verify.scene.validation_recovery_strategy.e2e_smoke.guard verify.scene.ui_base_contract_canonicalizer.guard verify.scene.ready.strict_contract.guard
	@echo "[OK] verify.scene.runtime_boundary.gate done"

.PHONY: verify.scene.product_delivery.readiness.guard
verify.scene.product_delivery.readiness.guard: guard.prod.forbid
	@python3 scripts/verify/scene_product_delivery_readiness_guard.py

.PHONY: verify.scene.delivery.readiness
verify.scene.delivery.readiness: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_SAMPLE_REGISTRY_DIFF_REQUIRE_SCENES=$${SC_SCENE_SAMPLE_REGISTRY_DIFF_REQUIRE_SCENES:-1} \
	SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE=$${SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE:-1} \
	SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE=$${SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE:-1} \
	SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE=$${SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE:-1} \
	SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_ENABLED=$${SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_ENABLED:-1} \
	$(MAKE) --no-print-directory verify.scene.runtime_boundary.gate
	@SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=$${SC_SCENE_READY_STRICT_GAP_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL:-1} \
	SC_SCENE_READY_STRICT_GAP_FULL_AUDIT_STATE_FILE=$${SC_SCENE_READY_STRICT_GAP_FULL_AUDIT_STATE_FILE:-artifacts/backend/scene_contract_v1_field_schema_state.json} \
	$(MAKE) --no-print-directory verify.scene.ready.strict_gap.full_audit
	@$(MAKE) --no-print-directory verify.scene.product_delivery.readiness.guard
	@echo "[INFO] strict guard report: docs/ops/audits/scene_ready_strict_contract_guard_report.md"
	@echo "[INFO] strict full audit report: docs/ops/audits/scene_ready_strict_gap_full_audit.md"
	@echo "[OK] verify.scene.delivery.readiness done"

.PHONY: verify.scene.delivery.readiness.role_matrix
verify.scene.delivery.readiness.role_matrix: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.scene.base_contract_source_mix.role_matrix.guard
	@$(MAKE) --no-print-directory verify.scene.delivery.readiness
	@echo "[OK] verify.scene.delivery.readiness.role_matrix done"

.PHONY: verify.scene.delivery.readiness.role_company_matrix
verify.scene.delivery.readiness.role_company_matrix: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.architecture.platformization_boundary_closure_bundle
	@$(MAKE) --no-print-directory verify.scene.delivery.readiness.role_matrix
	@$(MAKE) --no-print-directory verify.delivery.journey.role_matrix.guard
	@$(MAKE) --no-print-directory verify.scene.company_snapshot.collect
	@$(MAKE) --no-print-directory verify.scene.company_access.preflight.guard
	@$(MAKE) --no-print-directory verify.scene.base_contract_source_mix.company_matrix.guard
	@$(MAKE) --no-print-directory verify.scene.multi_company.evidence.guard
	@echo "[OK] verify.scene.delivery.readiness.role_company_matrix done"

.PHONY: verify.delivery.journey.role_matrix.guard
verify.delivery.journey.role_matrix.guard: guard.prod.forbid
	@python3 scripts/verify/delivery_journey_role_matrix_guard.py

.PHONY: verify.scene.engine_migration.matrix.guard
verify.scene.engine_migration.matrix.guard: guard.prod.forbid
	@python3 scripts/verify/scene_engine_migration_matrix_guard.py

.PHONY: verify.scene.source_fallback_burndown.guard
verify.scene.source_fallback_burndown.guard: guard.prod.forbid
	@python3 scripts/verify/scene_source_fallback_burndown_guard.py

.PHONY: verify.scene.multi_company.evidence.guard
verify.scene.multi_company.evidence.guard: guard.prod.forbid
	@python3 scripts/verify/scene_multi_company_evidence_guard.py

.PHONY: verify.scene.company_snapshot.collect
verify.scene.company_snapshot.collect: guard.prod.forbid
	@python3 scripts/verify/scene_company_snapshot_collect.py

.PHONY: verify.scene.company_access.preflight.guard
verify.scene.company_access.preflight.guard: guard.prod.forbid
	@python3 scripts/verify/scene_company_access_preflight_guard.py

.PHONY: ops.scene.company_secondary.access
ops.scene.company_secondary.access: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc " \
	E2E_BASE_URL=http://localhost:8069 \
	DB_NAME=$(DB_NAME) \
	ADMIN_LOGIN=$${ADMIN_LOGIN:-admin} \
	ADMIN_PASSWD=$${ADMIN_PASSWD:-admin} \
	TARGET_LOGIN=$${TARGET_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	TARGET_COMPANY_ID=$${TARGET_COMPANY_ID:-2} \
	APPLY=$${APPLY:-0} \
	python3 /mnt/scripts/ops/ensure_company_secondary_access.py \
	"

.PHONY: ops.scene.company_secondary.seed
ops.scene.company_secondary.seed: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc " \
	E2E_BASE_URL=http://localhost:8069 \
	DB_NAME=$(DB_NAME) \
	ADMIN_LOGIN=$${ADMIN_LOGIN:-admin} \
	ADMIN_PASSWD=$${ADMIN_PASSWD:-admin} \
	TARGET_LOGIN=$${TARGET_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	TARGET_USER_NAME='$${TARGET_USER_NAME:-Demo PM Company2}' \
	TARGET_USER_PASSWORD=$${TARGET_USER_PASSWORD:-demo} \
	TARGET_COMPANY_ID=$${TARGET_COMPANY_ID:-2} \
	TARGET_COMPANY_NAME='$${TARGET_COMPANY_NAME:-Demo Secondary Company}' \
	CREATE_COMPANY_IF_MISSING=$${CREATE_COMPANY_IF_MISSING:-1} \
	CREATE_USER_IF_MISSING=$${CREATE_USER_IF_MISSING:-0} \
	SET_PRIMARY_COMPANY=$${SET_PRIMARY_COMPANY:-0} \
	APPLY=$${APPLY:-0} \
	python3 /mnt/scripts/ops/seed_company_secondary_access.py \
	"

.PHONY: verify.scene.input_boundary.guard
verify.scene.input_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/scene_input_boundary_guard.py

.PHONY: verify.scene.governance_payload.guard
verify.scene.governance_payload.guard: guard.prod.forbid
	@python3 scripts/verify/scene_governance_payload_guard.py

.PHONY: verify.scene.asset_queue_trend.guard
verify.scene.asset_queue_trend.guard: guard.prod.forbid
	@python3 scripts/verify/scene_asset_queue_trend_guard.py

.PHONY: verify.scene.orchestrator.input.schema.guard
verify.scene.orchestrator.input.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_input_schema_guard.py

.PHONY: verify.scene.orchestrator.output.schema.guard
verify.scene.orchestrator.output.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_output_schema_guard.py

.PHONY: verify.scene.orchestrator.base_fact_binding.guard
verify.scene.orchestrator.base_fact_binding.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_base_fact_binding_guard.py

.PHONY: verify.scene.orchestrator.industry_interface.guard
verify.scene.orchestrator.industry_interface.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_industry_interface_guard.py

.PHONY: verify.scene.orchestrator.merge_priority.guard
verify.scene.orchestrator.merge_priority.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_merge_priority_guard.py

.PHONY: verify.scene.orchestrator.scene_type_surface.guard
verify.scene.orchestrator.scene_type_surface.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_scene_type_surface_guard.py

.PHONY: verify.scene.orchestrator.action_surface.guard
verify.scene.orchestrator.action_surface.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_action_surface_guard.py

.PHONY: verify.scene.orchestrator.key_scene_compile.guard
verify.scene.orchestrator.key_scene_compile.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestrator_key_scene_compile_guard.py

.PHONY: verify.scene.action_surface_strategy.wiring.guard
verify.scene.action_surface_strategy.wiring.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_wiring_guard.py

.PHONY: verify.scene.action_surface_strategy.schema.guard
verify.scene.action_surface_strategy.schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_schema_guard.py

.PHONY: verify.scene.action_surface_strategy.payload.guard
verify.scene.action_surface_strategy.payload.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_payload_guard.py

.PHONY: verify.scene.action_surface_strategy.priority.guard
verify.scene.action_surface_strategy.priority.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_priority_guard.py

.PHONY: verify.scene.action_surface_strategy.live_matrix.guard
verify.scene.action_surface_strategy.live_matrix.guard: guard.prod.forbid
	@python3 scripts/verify/scene_action_surface_strategy_live_matrix_guard.py

.PHONY: verify.scene.ready.scene_type_consumption_metrics.guard
verify.scene.ready.scene_type_consumption_metrics.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_scene_type_consumption_metrics_guard.py

.PHONY: verify.scene.ready.consumption_trend.guard
verify.scene.ready.consumption_trend.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ready_consumption_trend_guard.py

.PHONY: verify.scene.governance_history_report.guard
verify.scene.governance_history_report.guard: guard.prod.forbid
	@python3 scripts/verify/scene_governance_history_report_guard.py

.PHONY: verify.scene.governance_history_archive.guard
verify.scene.governance_history_archive.guard: guard.prod.forbid
	@python3 scripts/verify/scene_governance_history_archive_guard.py

.PHONY: verify.scene.registry_asset_snapshot.guard
verify.scene.registry_asset_snapshot.guard: guard.prod.forbid
	@python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.base_contract_source_mix.guard
verify.scene.base_contract_source_mix.guard: guard.prod.forbid
	@python3 scripts/verify/scene_base_contract_source_mix_guard.py

.PHONY: verify.scene.no_action_scene.guard
verify.scene.no_action_scene.guard: guard.prod.forbid
	@python3 scripts/verify/scene_no_action_scene_guard.py

.PHONY: verify.scene.registry_asset_snapshot.executive
verify.scene.registry_asset_snapshot.executive: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.executive.json \
	E2E_LOGIN=$${ROLE_EXECUTIVE_LOGIN:-demo_role_executive} \
	E2E_PASSWORD=$${ROLE_EXECUTIVE_PASSWORD:-demo} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.pm
verify.scene.registry_asset_snapshot.pm: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.pm.json \
	E2E_LOGIN=$${ROLE_PM_LOGIN:-demo_role_pm} \
	E2E_PASSWORD=$${ROLE_PM_PASSWORD:-demo} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.finance
verify.scene.registry_asset_snapshot.finance: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.finance.json \
	E2E_LOGIN=$${ROLE_FINANCE_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	E2E_PASSWORD=$${ROLE_FINANCE_PASSWORD:-$${ROLE_PM_PASSWORD:-demo}} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.ops
verify.scene.registry_asset_snapshot.ops: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.ops.json \
	E2E_LOGIN=$${ROLE_OPS_LOGIN:-$${ROLE_EXECUTIVE_LOGIN:-demo_role_executive}} \
	E2E_PASSWORD=$${ROLE_OPS_PASSWORD:-$${ROLE_EXECUTIVE_PASSWORD:-demo}} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.company_primary
verify.scene.registry_asset_snapshot.company_primary: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.company_primary.json \
	E2E_LOGIN=$${COMPANY_PRIMARY_LOGIN:-admin} \
	E2E_PASSWORD=$${COMPANY_PRIMARY_PASSWORD:-$${ADMIN_PASSWD:-admin}} \
	E2E_COMPANY_ID=$${COMPANY_PRIMARY_ID:-1} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.registry_asset_snapshot.company_secondary
verify.scene.registry_asset_snapshot.company_secondary: guard.prod.forbid
	@SC_SCENE_REGISTRY_ASSET_SNAPSHOT_REQUIRE_LIVE=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_RETRIES:-3} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC=$${SC_SCENE_REGISTRY_ASSET_SNAPSHOT_FETCH_BACKOFF_SEC:-1} \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL=1 \
	SC_SCENE_REGISTRY_ASSET_SNAPSHOT_STATE_FILE=artifacts/backend/scene_registry_asset_snapshot_state.company_secondary.json \
	E2E_LOGIN=$${COMPANY_SECONDARY_LOGIN:-$${ROLE_PM_LOGIN:-demo_role_pm}} \
	E2E_PASSWORD=$${COMPANY_SECONDARY_PASSWORD:-$${ROLE_PM_PASSWORD:-demo}} \
	E2E_COMPANY_ID=$${COMPANY_SECONDARY_ID:-2} \
	python3 scripts/verify/scene_registry_asset_snapshot_guard.py

.PHONY: verify.scene.base_contract_source_mix.role_matrix.guard
verify.scene.base_contract_source_mix.role_matrix.guard: guard.prod.forbid verify.scene.registry_asset_snapshot.executive verify.scene.registry_asset_snapshot.pm verify.scene.registry_asset_snapshot.finance verify.scene.registry_asset_snapshot.ops
	@python3 scripts/verify/scene_base_contract_source_mix_role_matrix_guard.py

.PHONY: verify.scene.base_contract_source_mix.company_matrix.guard
verify.scene.base_contract_source_mix.company_matrix.guard: guard.prod.forbid verify.scene.registry_asset_snapshot.company_primary verify.scene.registry_asset_snapshot.company_secondary
	@python3 scripts/verify/scene_base_contract_source_mix_company_matrix_guard.py

.PHONY: verify.scene.sample_registry_diff.guard
verify.scene.sample_registry_diff.guard: guard.prod.forbid
	@python3 scripts/verify/scene_sample_registry_diff_guard.py

.PHONY: verify.scene.sample_registry_diff_trend.guard
verify.scene.sample_registry_diff_trend.guard: guard.prod.forbid
	@python3 scripts/verify/scene_sample_registry_diff_trend_guard.py

.PHONY: verify.scene.validation_recovery_strategy.guard
verify.scene.validation_recovery_strategy.guard: guard.prod.forbid
	@python3 scripts/verify/scene_validation_recovery_strategy_guard.py

.PHONY: verify.scene.validation_recovery_strategy.payload_path.guard
verify.scene.validation_recovery_strategy.payload_path.guard: guard.prod.forbid
	@python3 scripts/verify/scene_validation_recovery_strategy_payload_path_guard.py

.PHONY: verify.scene.validation_recovery_strategy.e2e_smoke.guard
verify.scene.validation_recovery_strategy.e2e_smoke.guard: guard.prod.forbid
	@python3 scripts/verify/scene_validation_recovery_strategy_e2e_smoke_guard.py

.PHONY: verify.scene.ui_base_contract_canonicalizer.guard
verify.scene.ui_base_contract_canonicalizer.guard: guard.prod.forbid
	@python3 scripts/verify/scene_ui_base_contract_canonicalizer_guard.py

.PHONY: verify.frontend.no_base_contract_direct_consume.guard
verify.frontend.no_base_contract_direct_consume.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_no_base_contract_direct_consume_guard.py

.PHONY: verify.frontend.scene_governance_consumption.guard
verify.frontend.scene_governance_consumption.guard: guard.prod.forbid
	@python3 scripts/verify/frontend_scene_governance_consumption_guard.py

.PHONY: verify.scene.base_contract_asset_coverage.guard
verify.scene.base_contract_asset_coverage.guard: guard.prod.forbid
	@python3 scripts/verify/scene_base_contract_asset_coverage_guard.py

verify.scene.contract_path.gate: guard.prod.forbid verify.scene.runtime_boundary.gate verify.scene.legacy.bundle
	@echo "[OK] verify.scene.contract_path.gate done"

verify.seed.demo.import_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/seed_demo_import_boundary_guard.py

verify.seed.demo.isolation: guard.prod.forbid verify.scene.provider.guard verify.seed.demo.import_boundary.guard verify.test_seed_dependency.guard verify.scene.demo_leak.guard
	@echo "[OK] verify.seed.demo.isolation done"

# Unified aliases for CI/operations wording.
.PHONY: verify.contract.handler_boundary.guard
verify.contract.handler_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/contract_handler_layout_boundary_guard.py

verify.boundary.guard: guard.prod.forbid verify.scene.contract_path.gate verify.contract.handler_boundary.guard
	@echo "[OK] verify.boundary.guard done"

.PHONY: verify.system_init.runtime_context.stability verify.system_init.minimal_shape verify.system_init.duplication_guard verify.system_init.scene_subset_guard verify.system_init.no_page_contract_payload verify.system_init.payload_budget verify.system_init.startup_layer_contract verify.system_init.minimal_surface
verify.system_init.snapshot_equivalence: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/system_init_snapshot_equivalence.py

verify.system_init.runtime_context.stability: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/system_init_runtime_context_stability.py

verify.system_init.minimal_shape: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_minimal_shape_guard.py"

verify.system_init.duplication_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_duplication_guard.py"

verify.system_init.scene_subset_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_scene_subset_guard.py"

verify.system_init.no_page_contract_payload: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_no_page_contract_payload_guard.py"

verify.system_init.payload_budget: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) SYSTEM_INIT_MAX_BYTES=$(or $(SYSTEM_INIT_MAX_BYTES),65536) SYSTEM_INIT_MAX_NAV_COUNT=$(or $(SYSTEM_INIT_MAX_NAV_COUNT),80) SYSTEM_INIT_MAX_INTENT_COUNT=$(or $(SYSTEM_INIT_MAX_INTENT_COUNT),300) python3 /mnt/scripts/verify/system_init_payload_budget_guard.py"

verify.system_init.startup_layer_contract: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_startup_layer_contract_guard.py"

verify.system_init.init_meta_minimal_guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_init_meta_minimal_guard.py"

verify.system_init.latency_budget: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) $(COMPOSE_BASE) exec -T $(ODOO_SERVICE) sh -lc "E2E_BASE_URL=http://localhost:8069 DB_NAME=$(DB_NAME) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) python3 /mnt/scripts/verify/system_init_latency_budget_guard.py"

verify.system_init.minimal_surface: verify.system_init.minimal_shape verify.system_init.duplication_guard verify.system_init.scene_subset_guard verify.system_init.no_page_contract_payload verify.system_init.payload_budget verify.system_init.startup_layer_contract verify.system_init.init_meta_minimal_guard verify.system_init.latency_budget
	@echo "[OK] verify.system_init.minimal_surface done"

verify.phase12f: guard.prod.forbid
	@echo "[Phase12F] platform/portal/runtime/product baseline"
	@$(MAKE) verify.phase12b.baseline PLATFORM_DB_NAME=$(or $(PLATFORM_DB_NAME),$(DB_NAME)) PLATFORM_LOGIN=$(or $(PLATFORM_LOGIN),$(E2E_LOGIN)) PLATFORM_PASSWORD=$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD)) PORTAL_DB_NAME=$(or $(PORTAL_DB_NAME),$(or $(PLATFORM_DB_NAME),$(DB_NAME))) PORTAL_LOGIN=$(or $(PORTAL_LOGIN),$(or $(PLATFORM_LOGIN),$(E2E_LOGIN))) PORTAL_PASSWORD=$(or $(PORTAL_PASSWORD),$(or $(PLATFORM_PASSWORD),$(E2E_PASSWORD))) PRODUCT_DB_NAME=$(or $(PRODUCT_DB_NAME),$(DB_NAME)) PRODUCT_LOGIN=$(or $(PRODUCT_LOGIN),$(E2E_LOGIN)) PRODUCT_PASSWORD=$(or $(PRODUCT_PASSWORD),$(E2E_PASSWORD)) E2E_LOGIN=$(E2E_LOGIN) E2E_PASSWORD=$(E2E_PASSWORD) || (echo "❌ [phase12f baseline] failed" && exit 31)
	@echo "[OK] verify.phase12f done"

verify.intent.capability.matrix.report: guard.prod.forbid
	@python3 scripts/verify/intent_capability_matrix_report.py

verify.intent.layered.catalog: guard.prod.forbid verify.intent.capability.matrix.report
	@python3 scripts/verify/intent_layered_catalog_report.py

.PHONY: verify.intent.write.guard
verify.intent.write.guard: guard.prod.forbid
	@python3 addons/smart_core/tools/intent_write_guard.py

.PHONY: verify.intent.acl.mode
verify.intent.acl.mode: guard.prod.forbid
	@python3 addons/smart_core/tools/intent_acl_mode_guard.py

verify.write_intent.permission.audit: guard.prod.forbid
	@python3 scripts/verify/write_intent_permission_audit.py

verify.scene.intent.matrix.report: guard.prod.forbid
	@python3 scripts/verify/scene_intent_matrix_report.py

verify.scene.intent.consistency: guard.prod.forbid verify.intent.layered.catalog
	@python3 scripts/verify/scene_intent_consistency_guard.py

verify.intent.orphan.report: guard.prod.forbid
	@python3 scripts/verify/intent_orphan_report.py

verify.capability.scene.matrix.report: guard.prod.forbid
	@python3 scripts/verify/capability_scene_matrix_report.py

verify.intent.execution.path.report: guard.prod.forbid verify.intent.permission.matrix.report
	@python3 scripts/verify/intent_execution_path_report.py

verify.platform.kernel.baseline: guard.prod.forbid verify.intent.layered.catalog
	@python3 scripts/verify/platform_kernel_baseline_guard.py

.PHONY: verify.platform_kernel_baseline_guard
verify.platform_kernel_baseline_guard: verify.platform.kernel.baseline

verify.owner.industry.isolation: guard.prod.forbid
	@python3 scripts/verify/owner_industry_isolation_probe.py

verify.owner.intent.non_intrusion: guard.prod.forbid
	@python3 scripts/verify/owner_intent_non_intrusion_guard.py

verify.capability.isolation.report: guard.prod.forbid
	@python3 scripts/verify/capability_isolation_report.py

verify.owner.scene.independent.deploy: guard.prod.forbid
	@python3 scripts/verify/owner_scene_independent_deploy_report.py

verify.platform.multi_domain.ready: guard.prod.forbid
	@python3 scripts/verify/platform_multi_domain_ready_report.py

verify.scene.conflict.stress: guard.prod.forbid
	@python3 scripts/verify/scene_conflict_stress_report.py

verify.capability.scale.stress: guard.prod.forbid
	@python3 scripts/verify/capability_scale_stress_report.py

verify.intent.concurrent.smoke: guard.prod.forbid
	@python3 scripts/verify/intent_concurrent_smoke_report.py

verify.kernel.immutable.guard: guard.prod.forbid
	@python3 scripts/verify/kernel_immutable_guard.py

verify.kernel.freeze.guard: guard.prod.forbid
	@python3 scripts/verify/kernel_freeze_guard.py

verify.intent.public.surface.ready: guard.prod.forbid
	@python3 scripts/verify/intent_public_surface_ready_report.py

verify.platform.sla.guard: guard.prod.forbid
	@python3 scripts/verify/platform_sla_guard.py

verify.multi_tenant.evolution.smoke: guard.prod.forbid
	@python3 scripts/verify/multi_tenant_evolution_smoke.py

verify.contract.version.evolution.drill: guard.prod.forbid
	@python3 scripts/verify/contract_version_evolution_drill.py

verify.product.capability.matrix.ready: guard.prod.forbid
	@python3 scripts/verify/product_capability_matrix_ready.py

.PHONY: verify.capability.asset.map verify.scene.compression.model verify.scene.domain.taxonomy.guard verify.button.semantic.report verify.capability.dormant.explain.guard verify.phasex.p1
verify.capability.asset.map: guard.prod.forbid
	@python3 scripts/verify/capability_asset_map_report.py

verify.scene.compression.model: guard.prod.forbid
	@python3 scripts/verify/scene_compression_model_report.py

verify.scene.domain.taxonomy.guard: guard.prod.forbid
	@python3 scripts/verify/scene_domain_taxonomy_guard.py

verify.button.semantic.report: guard.prod.forbid
	@python3 scripts/verify/button_semantic_report.py

verify.capability.dormant.explain.guard: guard.prod.forbid
	@python3 scripts/verify/capability_dormant_explain_guard.py

verify.phasex.p1: guard.prod.forbid verify.capability.asset.map verify.scene.compression.model verify.scene.domain.taxonomy.guard verify.button.semantic.report verify.capability.dormant.explain.guard
	@echo "[OK] verify.phasex.p1 done"

.PHONY: verify.role.capability.diff.report verify.runtime.trend.report verify.catalog.runtime.explain.report verify.catalog.runtime.source.rules.guard verify.phasex.p2
verify.role.capability.diff.report: guard.prod.forbid
	@python3 scripts/verify/role_capability_diff_report.py

verify.runtime.trend.report: guard.prod.forbid
	@python3 scripts/verify/runtime_trend_report.py

verify.catalog.runtime.explain.report: guard.prod.forbid
	@python3 scripts/verify/catalog_runtime_explain_report.py

verify.catalog.runtime.source.rules.guard: guard.prod.forbid
	@python3 scripts/verify/catalog_runtime_source_rules_guard.py

verify.phasex.p2: guard.prod.forbid verify.role.capability.diff.report verify.runtime.trend.report verify.catalog.runtime.explain.report verify.catalog.runtime.source.rules.guard
	@echo "[OK] verify.phasex.p2 done"

.PHONY: verify.semantic.behavior.guard.report
verify.semantic.behavior.guard.report: guard.prod.forbid
	@python3 scripts/verify/semantic_behavior_guard_report.py

.PHONY: verify.product.capability.matrix.v2.report
verify.product.capability.matrix.v2.report: guard.prod.forbid
	@python3 scripts/verify/product_capability_matrix_v2_report.py

.PHONY: verify.stress.regression.policy.guard verify.system.stability.stress.regression
verify.stress.regression.policy.guard: guard.prod.forbid
	@python3 scripts/verify/stress_regression_policy_guard.py

verify.system.stability.stress.regression: guard.prod.forbid verify.stress.regression.policy.guard
	@python3 scripts/verify/system_stability_stress_regression.py

.PHONY: verify.sprint.week1.audit.report verify.sprint.week2.final.report
verify.sprint.week1.audit.report: guard.prod.forbid
	@$(MAKE) verify.capability.dormant.explain.guard
	@python3 scripts/verify/sprint_week1_audit_report.py

verify.sprint.week2.final.report: guard.prod.forbid
	@python3 scripts/verify/sprint_week2_final_report.py

.PHONY: verify.phasex.operating.summary
verify.phasex.operating.summary: guard.prod.forbid
	@python3 scripts/verify/phasex_operating_summary_report.py

verify.bundle.installation.ready: guard.prod.forbid
	@python3 scripts/verify/bundle_installation_ready.py

verify.product.tier.ready: guard.prod.forbid
	@python3 scripts/verify/product_tier_ready.py

verify.ui.surface.stability.ready: guard.prod.forbid
	@python3 scripts/verify/ui_surface_stability_ready.py

verify.delivery.simulation.ready: guard.prod.forbid
	@python3 scripts/verify/delivery_simulation_ready.py

# prod-sim 全量隔离验证：适合发布前/环境漂移后（会重置并重建 sc_prod_sim）
.PHONY: verify.prod.sim.isolation
verify.prod.sim.isolation: guard.prod.forbid
	@echo "[verify.prod.sim.isolation] step=up"
	@$(MAKE) up \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation] step=demo.reset"
	@$(MAKE) demo.reset CODEX_MODE=gate \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation] step=odoo.recreate"
	@$(MAKE) odoo.recreate \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation] step=wait.odoo.ready"
	@bash -lc 'for i in $$(seq 1 30); do \
	  if curl -fsS --max-time 2 http://127.0.0.1:18069/web/login >/dev/null 2>/dev/null; then exit 0; fi; \
	  sleep 2; \
	done; \
	echo "❌ odoo not ready on :18069"; exit 2'
	@echo "[verify.prod.sim.isolation] step=delivery.simulation.ready"
	@E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo \
	$(MAKE) verify.delivery.simulation.ready \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim
	@echo "[verify.prod.sim.isolation] PASS"

# prod-sim 快速隔离回归：适合日常联调（不 reset，仅健康检查 + e2e 验证）
.PHONY: verify.prod.sim.isolation.quick
verify.prod.sim.isolation.quick: guard.prod.forbid
	@echo "[verify.prod.sim.isolation.quick] step=up"
	@$(MAKE) up \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim \
		COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml"
	@echo "[verify.prod.sim.isolation.quick] step=wait.odoo.ready"
	@bash -lc 'for i in $$(seq 1 30); do \
	  if curl -fsS --max-time 2 http://127.0.0.1:18069/web/login >/dev/null 2>/dev/null; then exit 0; fi; \
	  sleep 2; \
	done; \
	echo "❌ odoo not ready on :18069"; exit 2'
	@echo "[verify.prod.sim.isolation.quick] step=delivery.simulation.ready"
	@E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo \
	$(MAKE) verify.delivery.simulation.ready \
		ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim
	@echo "[verify.prod.sim.isolation.quick] PASS"


.PHONY: verify.product.delivery.gap
verify.product.delivery.gap: guard.prod.forbid
	@python3 scripts/verify/product_delivery_gap_report.py

.PHONY: verify.product.delivery.v1.map
verify.product.delivery.v1.map: guard.prod.forbid
	@python3 scripts/verify/module_scene_capability_map_report.py

.PHONY: verify.phasea.a0a1
verify.phasea.a0a1: guard.prod.forbid verify.product.delivery.v1.map
	@echo "[OK] verify.phasea.a0a1 done"

.PHONY: verify.product.delivery.journeys
verify.product.delivery.journeys: guard.prod.forbid
	@python3 scripts/verify/delivery_user_journey_guard.py

.PHONY: verify.product.delivery.roles
verify.product.delivery.roles: guard.prod.forbid
	@python3 scripts/verify/role_capability_profiles_export.py
	@python3 scripts/verify/role_home_openability_report.py

.PHONY: verify.product.delivery.role_home_openability
verify.product.delivery.role_home_openability: guard.prod.forbid
	@python3 scripts/verify/role_home_openability_report.py

.PHONY: verify.product.delivery.visibility
verify.product.delivery.visibility: guard.prod.forbid
	@python3 scripts/verify/visibility_filter_verification.py

.PHONY: verify.product.delivery.demo_data verify.demo.release.seed
verify.product.delivery.demo_data: guard.prod.forbid
	@python3 scripts/verify/demo_data_presence_report.py

verify.demo.release.seed: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/demo_release_seed.sh

.PHONY: verify.product.delivery.execute_button_whitelist
verify.product.delivery.execute_button_whitelist: guard.prod.forbid
	@python3 scripts/verify/execute_button_whitelist_verification.py

.PHONY: verify.product.delivery.menu
verify.product.delivery.menu: guard.prod.forbid
	@python3 scripts/verify/delivery_menu_tree_report.py

.PHONY: verify.product.delivery.freshness
verify.product.delivery.freshness: guard.prod.forbid
	@python3 scripts/verify/product_delivery_freshness_guard.py

.PHONY: verify.product.delivery.governance_truth
verify.product.delivery.governance_truth: guard.prod.forbid
	@python3 scripts/verify/product_delivery_governance_truth_guard.py

.PHONY: verify.product.delivery.action_closure.smoke
verify.product.delivery.action_closure.smoke: guard.prod.forbid
	@python3 scripts/verify/product_delivery_action_closure_smoke.py

.PHONY: verify.product.delivery.module9.smoke
verify.product.delivery.module9.smoke: guard.prod.forbid
	@python3 scripts/verify/product_delivery_module9_smoke.py

.PHONY: verify.backend.contract.closure.guard
verify.backend.contract.closure.guard: guard.prod.forbid
	@python3 scripts/verify/backend_contract_closure_guard.py
	@python3 scripts/verify/backend_contract_closure_snapshot_guard.py
	@python3 scripts/verify/intent_canonical_alias_snapshot_guard.py

.PHONY: verify.backend.contract.closure.snapshot.guard
verify.backend.contract.closure.snapshot.guard: guard.prod.forbid
	@python3 scripts/verify/backend_contract_closure_snapshot_guard.py

.PHONY: verify.intent.canonical_alias.snapshot.guard
verify.intent.canonical_alias.snapshot.guard: guard.prod.forbid
	@python3 scripts/verify/intent_canonical_alias_snapshot_guard.py

.PHONY: verify.backend.contract.closure.mainline
verify.backend.contract.closure.mainline: guard.prod.forbid
	@STRUCTURE=PASS; SNAPSHOT=PASS; ALIAS=PASS; \
	echo "[verify.backend.contract.closure.mainline] step=closure_structure_guard"; \
	if ! python3 scripts/verify/backend_contract_closure_guard.py; then STRUCTURE=FAIL; fi; \
	echo "[verify.backend.contract.closure.mainline] step=closure_snapshot_guard"; \
	if ! python3 scripts/verify/backend_contract_closure_snapshot_guard.py; then SNAPSHOT=FAIL; fi; \
	echo "[verify.backend.contract.closure.mainline] step=intent_alias_snapshot_guard"; \
	if ! python3 scripts/verify/intent_canonical_alias_snapshot_guard.py; then ALIAS=FAIL; fi; \
	python3 scripts/verify/backend_contract_closure_mainline_summary.py --structure $$STRUCTURE --snapshot $$SNAPSHOT --alias $$ALIAS; \
	python3 scripts/verify/backend_contract_closure_mainline_summary_schema_guard.py; \
	if [ "$$STRUCTURE" = "PASS" ] && [ "$$SNAPSHOT" = "PASS" ] && [ "$$ALIAS" = "PASS" ]; then \
	  echo "[OK] verify.backend.contract.closure.mainline done"; \
	else \
	  echo "[FAIL] verify.backend.contract.closure.mainline"; \
	  exit 1; \
	fi

.PHONY: verify.backend.contract.closure.mainline.summary.schema.guard
verify.backend.contract.closure.mainline.summary.schema.guard: guard.prod.forbid
	@python3 scripts/verify/backend_contract_closure_mainline_summary_schema_guard.py

.PHONY: verify.product.delivery.ready
verify.product.delivery.ready: guard.prod.forbid verify.product.delivery.gap verify.product.delivery.freshness verify.product.delivery.governance_truth
	@echo "[OK] verify.product.delivery.ready done"

.PHONY: verify.product.delivery.mainline
verify.product.delivery.mainline: guard.prod.forbid
	@PROFILE=$${CI_SCENE_DELIVERY_PROFILE:-restricted}; \
	FRONTEND_STATUS=PASS; SCENE_STATUS=PASS; ACTION_STATUS=PASS; MODULE9_STATUS=PASS; CONTRACT_CLOSURE_STATUS=PASS; GOVERNANCE_STATUS=PASS; \
	echo "[verify.product.delivery.mainline] step=frontend_gate"; \
	if ! pnpm -C frontend gate; then FRONTEND_STATUS=FAIL; fi; \
	echo "[verify.product.delivery.mainline] step=scene_delivery_readiness profile=$$PROFILE"; \
	if [ "$$FRONTEND_STATUS" = "PASS" ]; then \
	  if ! CI_SCENE_DELIVERY_PROFILE=$$PROFILE SC_MULTI_COMPANY_EVIDENCE_STRICT=1 $(MAKE) --no-print-directory ci.scene.delivery.readiness; then \
	    SCENE_STATUS=FAIL; \
	  fi; \
	else \
	  SCENE_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=action_closure_smoke"; \
	if [ "$$SCENE_STATUS" = "PASS" ]; then \
	  if ! $(MAKE) --no-print-directory verify.product.delivery.action_closure.smoke; then ACTION_STATUS=FAIL; fi; \
	else \
	  ACTION_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=module9_smoke"; \
	if [ "$$ACTION_STATUS" = "PASS" ]; then \
	  if ! $(MAKE) --no-print-directory verify.product.delivery.module9.smoke; then MODULE9_STATUS=FAIL; fi; \
	else \
	  MODULE9_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=backend_contract_closure_mainline"; \
	if [ "$$MODULE9_STATUS" = "PASS" ]; then \
	  if ! $(MAKE) --no-print-directory verify.backend.contract.closure.mainline; then CONTRACT_CLOSURE_STATUS=FAIL; fi; \
	else \
	  CONTRACT_CLOSURE_STATUS=SKIP; \
	fi; \
	echo "[verify.product.delivery.mainline] step=governance_truth"; \
	if ! $(MAKE) --no-print-directory verify.product.delivery.governance_truth; then GOVERNANCE_STATUS=FAIL; fi; \
	echo "[verify.product.delivery.mainline] contract_closure_guard=$$CONTRACT_CLOSURE_STATUS"; \
	python3 scripts/verify/delivery_mainline_run_summary.py \
	  --profile $$PROFILE \
	  --frontend $$FRONTEND_STATUS \
	  --scene $$SCENE_STATUS \
	  --action-closure $$ACTION_STATUS \
	  --module9 $$MODULE9_STATUS \
	  --governance $$GOVERNANCE_STATUS; \
		$(MAKE) --no-print-directory refresh.delivery.readiness.scoreboard >/dev/null; \
		python3 -c "import json, pathlib; p=pathlib.Path('artifacts/backend/delivery_readiness_ci_summary.json'); d=json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}; o=d.get('overall') if isinstance(d.get('overall'), dict) else {}; print(f\"[verify.product.delivery.mainline] overall_ok={o.get('ok')} policy={o.get('policy')}\")"; \
	if [ "$$FRONTEND_STATUS" = "PASS" ] && [ "$$SCENE_STATUS" = "PASS" ] && [ "$$ACTION_STATUS" = "PASS" ] && [ "$$MODULE9_STATUS" = "PASS" ] && [ "$$CONTRACT_CLOSURE_STATUS" = "PASS" ] && [ "$$GOVERNANCE_STATUS" = "PASS" ]; then \
	  echo "[OK] verify.product.delivery.mainline done"; \
	else \
	  echo "[FAIL] verify.product.delivery.mainline"; \
	  exit 1; \
	fi

.PHONY: export.product.delivery.package
export.product.delivery.package: guard.prod.forbid
	@python3 scripts/verify/product_delivery_package_manifest.py

verify.complexity.guard: guard.prod.forbid
	@python3 scripts/verify/complexity_guard.py

export.product.documentation: guard.prod.forbid
	@python3 scripts/verify/export_product_documentation.py

verify.product.tier.coverage: guard.prod.forbid
	@python3 scripts/verify/product_tier_coverage.py

seed.delivery.minimum: guard.prod.forbid
	@python3 scripts/verify/seed_delivery_minimum.py

verify.delivery.business.success.ready: guard.prod.forbid seed.delivery.minimum
	@python3 scripts/verify/delivery_business_success_ready.py

verify.product.surface.clean: guard.prod.forbid verify.product.capability.matrix.ready
	@echo "[OK] verify.product.surface.clean done"

verify.product.complexity.bound: guard.prod.forbid verify.complexity.guard
	@echo "[OK] verify.product.complexity.bound done"

verify.product.bundle.isolation: guard.prod.forbid verify.bundle.installation.ready
	@echo "[OK] verify.product.bundle.isolation done"

verify.product.tier.enforcement: guard.prod.forbid verify.product.tier.coverage
	@echo "[OK] verify.product.tier.enforcement done"

verify.ui.product.stability: guard.prod.forbid verify.ui.surface.stability.ready
	@echo "[OK] verify.ui.product.stability done"

verify.delivery.reproducible: guard.prod.forbid verify.delivery.business.success.ready
	@echo "[OK] verify.delivery.reproducible done"

verify.product.sla.baseline: guard.prod.forbid verify.platform.performance.smoke
	@echo "[OK] verify.product.sla.baseline done"

verify.product.release.ready: guard.prod.forbid \
	verify.product.surface.clean \
	verify.product.complexity.bound \
	verify.product.bundle.isolation \
	verify.product.tier.enforcement \
	verify.ui.product.stability \
	verify.delivery.reproducible \
	verify.product.sla.baseline
	@echo "[OK] verify.product.release.ready done"

verify.platform.distribution.report: guard.prod.forbid
	@python3 scripts/verify/platform_distribution_ready_report.py

verify.platform.distribution.ready: guard.prod.forbid \
	verify.owner.industry.isolation \
	verify.owner.intent.non_intrusion \
	verify.capability.isolation.report \
	verify.owner.scene.independent.deploy \
	verify.platform.distribution.report
	@echo "[OK] verify.platform.distribution.ready done"

verify.contract.compat: guard.prod.forbid
	@python3 scripts/verify/contract_compat_report.py

verify.platform.performance.smoke: guard.prod.forbid
	@python3 scripts/verify/platform_performance_smoke.py

verify.platform.maturity.ready: guard.prod.forbid \
	verify.platform.distribution.ready \
	verify.contract.compat \
	verify.platform.performance.smoke \
	verify.platform.kernel.ready
	@echo "[OK] verify.platform.maturity.ready done"

verify.platform.reusability.ready: guard.prod.forbid \
	verify.owner.industry.isolation \
	verify.owner.intent.non_intrusion \
	verify.capability.isolation.report \
	verify.owner.scene.independent.deploy \
	verify.platform.kernel.ready
	@echo "[OK] verify.platform.reusability.ready done"

verify.platform.stability.ready: guard.prod.forbid \
	verify.platform.multi_domain.ready \
	verify.scene.conflict.stress \
	verify.capability.scale.stress \
	verify.intent.concurrent.smoke \
	verify.kernel.immutable.guard \
	verify.platform.reusability.ready
	@echo "[OK] verify.platform.stability.ready done"

verify.platform.governance.ready: guard.prod.forbid \
	verify.kernel.freeze.guard \
	verify.intent.public.surface.ready \
	verify.platform.sla.guard \
	verify.multi_tenant.evolution.smoke \
	verify.contract.version.evolution.drill \
	verify.platform.stability.ready
	@echo "[OK] verify.platform.governance.ready done"

verify.productization.ready: guard.prod.forbid \
	verify.product.surface.clean \
	verify.product.bundle.isolation \
	verify.product.tier.enforcement \
	verify.ui.product.stability \
	verify.delivery.reproducible \
	verify.product.complexity.bound \
	verify.platform.governance.ready
	@echo "[OK] verify.productization.ready done"

verify.etag.validation.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/etag_validation_report.py

verify.auto_degrade.smoke.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/auto_degrade_smoke_report.py

verify.scene.drift.smoke.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/scene_drift_smoke_report.py

.PHONY: verify.scene.governance.smoke
verify.scene.governance.smoke: guard.prod.forbid
	@python3 scripts/verify/scene_governance_smoke.py

.PHONY: verify.intent.write.smoke
verify.intent.write.smoke: guard.prod.forbid
	@python3 scripts/verify/intent_write_smoke.py

.PHONY: verify.intent.write.runtime.smoke
verify.intent.write.runtime.smoke: guard.prod.forbid
	@python3 scripts/verify/intent_write_runtime_smoke.py

.PHONY: verify.intent.permission.matrix.report
verify.intent.permission.matrix.report: guard.prod.forbid
	@python3 scripts/verify/intent_permission_matrix_report.py

.PHONY: verify.intent.permission.matrix.guard
verify.intent.permission.matrix.guard: guard.prod.forbid verify.intent.permission.matrix.report
	@python3 scripts/verify/intent_permission_matrix_guard.py

.PHONY: verify.intent.write.sudo.guard
verify.intent.write.sudo.guard: guard.prod.forbid verify.intent.permission.matrix.report
	@python3 scripts/verify/write_intent_sudo_guard.py

verify.capability.orphan.report: guard.prod.forbid
	@$(RUN_ENV) python3 scripts/verify/capability_orphan_report.py

.PHONY: verify.platform.security.ready
verify.platform.security.ready: guard.prod.forbid \
	verify.system_group.business_acl.guard \
	verify.intent.write.guard \
	verify.intent.acl.mode \
	verify.intent.write.smoke \
	verify.intent.write.runtime.smoke \
	verify.intent.write.sudo.guard \
	verify.scene.governance.smoke \
	verify.intent.permission.matrix.guard
	@echo "[OK] verify.platform.security.ready done"

.PHONY: verify.system_group.business_acl.guard
verify.system_group.business_acl.guard: guard.prod.forbid
	@python3 scripts/verify/system_group_business_acl_guard.py

verify.platform.kernel.ready: guard.prod.forbid \
	verify.platform.security.ready \
	verify.scene.core_api_boundary.guard \
	verify.scene.provider.registry.guard \
	verify.scene.provider.registry.consumer.guard \
	verify.scene.provider_locator.removed.guard \
	verify.scene_orchestration.provider_shape.guard \
	verify.capability.provider.guard \
	verify.capability.registry.smoke \
	verify.contract.envelope \
	verify.write_intent.permission.audit \
	verify.auto_degrade.smoke.report \
	verify.scene.drift.smoke.report \
	verify.etag.validation.report \
	verify.intent.capability.matrix.report \
	verify.scene.intent.matrix.report \
	verify.intent.orphan.report \
	verify.capability.scene.matrix.report \
	verify.scene.intent.consistency \
	verify.intent.execution.path.report \
	verify.platform.kernel.baseline \
	verify.capability.orphan.report
	@echo "[OK] verify.platform.kernel.ready done"

verify.contract.snapshot: guard.prod.forbid verify.scene.contract.shape verify.contract.ordering.smoke verify.contract.catalog.determinism verify.system_init.snapshot_equivalence
	@echo "[OK] verify.contract.snapshot done"

verify.mode.filter: guard.prod.forbid verify.contract.mode.smoke verify.contract.api.mode.smoke
	@echo "[OK] verify.mode.filter done"

verify.capability.schema: guard.prod.forbid verify.scene_capability.contract.guard
	@echo "[OK] verify.capability.schema done"

verify.scene.schema: guard.prod.forbid verify.scene.definition.semantics verify.scene.catalog.source.guard verify.scene.contract.shape
	@echo "[OK] verify.scene.schema done"

verify.backend.architecture.full: guard.prod.forbid verify.intent.router.purity verify.baseline.policy_integrity.guard verify.boundary.guard verify.contract.envelope verify.mode.filter verify.capability.schema verify.scene.schema verify.seed.demo.isolation verify.scene.catalog.governance.guard verify.load_view.access.contract.guard verify.capability.provider.guard verify.capability.registry.smoke verify.release.capability.audit.schema.guard verify.phase_next.evidence.bundle verify.business.capability_baseline.guard verify.contract.snapshot verify.system_init.runtime_context.stability verify.contract.governance.coverage verify.contract.evidence.guard verify.scene.hud.trace.smoke verify.scene.meta.trace.smoke
	@if [ "$${SC_PHASE_NEXT_STRICT:-0}" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.phase_next.evidence.bundle.strict; \
	else \
	  echo "[verify.backend.architecture.full] SC_PHASE_NEXT_STRICT=0: skip strict phase-next evidence bundle"; \
	fi
	@if [ "$${SC_BOUNDARY_IMPORT_STRICT:-0}" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.boundary.import_guard.strict.guard; \
	else \
	  echo "[verify.backend.architecture.full] SC_BOUNDARY_IMPORT_STRICT=0: skip strict boundary import warning gate"; \
	fi
	@if [ "$${SC_RUNTIME_SURFACE_STRICT:-0}" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.runtime.surface.dashboard.strict.guard; \
	else \
	  echo "[verify.backend.architecture.full] SC_RUNTIME_SURFACE_STRICT=0: skip strict runtime surface warning gate"; \
	fi
	@$(MAKE) --no-print-directory verify.backend.architecture.full.report.guard.schema.guard
	@$(MAKE) --no-print-directory verify.backend.evidence.manifest.guard
	@echo "[OK] verify.backend.architecture.full done"

verify.extension_modules.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/verify/extension_modules_guard.sh

verify.test_seed_dependency.guard: guard.prod.forbid
	@bash scripts/verify/test_seed_dependency_guard.sh

verify.contract_drift.guard: guard.prod.forbid
	@bash scripts/verify/contract_drift_guard.sh
	@$(MAKE) --no-print-directory verify.intent.side_effect_policy_guard

verify.intent.side_effect_policy_guard: guard.prod.forbid
	@python3 scripts/verify/side_effect_intent_policy_guard.py

verify.baseline.freeze_guard: guard.prod.forbid
	@python3 scripts/verify/baseline_freeze_guard.py

verify.business.increment.readiness: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory audit.intent.surface
	@python3 scripts/verify/business_increment_readiness.py --profile $(BUSINESS_INCREMENT_PROFILE)

verify.business.increment.readiness.strict: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory audit.intent.surface
	@python3 scripts/verify/business_increment_readiness.py --profile strict --strict

verify.business.increment.readiness.brief: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.business.increment.readiness
	@python3 scripts/verify/business_increment_readiness_brief.py --profile $(BUSINESS_INCREMENT_PROFILE)

verify.business.increment.readiness.brief.strict: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.business.increment.readiness.strict
	@python3 scripts/verify/business_increment_readiness_brief.py --profile strict --strict

verify.business.increment.preflight: guard.prod.forbid
	@$(MAKE) --no-print-directory contract.catalog.export
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory audit.intent.surface
	@$(MAKE) --no-print-directory verify.business.increment.readiness
	@echo "[OK] verify.business.increment.preflight done"

verify.business.increment.preflight.strict: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.business.increment.preflight
	@$(MAKE) --no-print-directory verify.business.increment.readiness.strict
	@echo "[OK] verify.business.increment.preflight.strict done"

verify.docs.inventory: guard.prod.forbid
	@python3 scripts/verify/docs_inventory.py

verify.docs.links: guard.prod.forbid
	@python3 scripts/verify/docs_links.py

verify.docs.temp_guard: guard.prod.forbid
	@python3 scripts/verify/docs_temp_guard.py

verify.docs.contract_sync: guard.prod.forbid
	@python3 scripts/verify/docs_contract_sync.py

verify.docs.all: guard.prod.forbid verify.docs.inventory verify.docs.links verify.docs.temp_guard verify.docs.contract_sync
	@echo "[OK] verify.docs.all done"

.PHONY: verify.portal.scene_product_filter_guard verify.portal.product_scene_mapping_guard verify.portal.role_home_scene_guard verify.portal.template_schema_guard verify.portal.entry_registry_guard verify.portal.entry_registry_quality_guard verify.portal.navigation_entry_registry_guard verify.portal.role_scene_navigation_guard verify.portal.navigation_registry_quality_guard
verify.portal.scene_product_filter_guard: guard.prod.forbid
	@python3 scripts/verify/portal_scene_product_filter_guard.py

verify.portal.product_scene_mapping_guard: guard.prod.forbid
	@python3 scripts/verify/portal_product_scene_mapping_guard.py

verify.portal.role_home_scene_guard: guard.prod.forbid
	@python3 scripts/verify/portal_role_home_scene_guard.py

verify.portal.template_schema_guard: guard.prod.forbid
	@python3 scripts/verify/portal_template_schema_guard.py

verify.portal.entry_registry_guard: guard.prod.forbid
	@python3 scripts/verify/portal_entry_registry_guard.py

verify.portal.entry_registry_quality_guard: guard.prod.forbid
	@python3 scripts/verify/portal_entry_registry_quality_guard.py

verify.portal.navigation_entry_registry_guard: guard.prod.forbid
	@python3 scripts/verify/portal_navigation_entry_registry_guard.py

verify.portal.role_scene_navigation_guard: guard.prod.forbid
	@python3 scripts/verify/portal_role_scene_navigation_guard.py

verify.portal.navigation_registry_quality_guard: guard.prod.forbid
	@python3 scripts/verify/portal_navigation_registry_quality_guard.py

verify.boundary.import_guard: guard.prod.forbid
	@python3 scripts/verify/boundary_import_guard.py
	@python3 scripts/verify/boundary_import_guard_schema_guard.py
	@python3 scripts/verify/model_ui_dependency_guard.py

verify.boundary.import_guard.schema.guard: guard.prod.forbid verify.boundary.import_guard
	@python3 scripts/verify/boundary_import_guard_schema_guard.py

verify.boundary.import_guard.strict.guard: guard.prod.forbid verify.boundary.import_guard.schema.guard
	@python3 scripts/verify/boundary_import_guard_strict_guard.py

verify.backend.boundary_guard: guard.prod.forbid
	@python3 scripts/verify/backend_boundary_guard.py

verify.scene.provider.guard: guard.prod.forbid
	@python3 scripts/verify/scene_provider_guard.py

verify.scene.core_api_boundary.guard: guard.prod.forbid
	@python3 scripts/verify/scene_core_api_boundary_guard.py

verify.scene.provider.registry.guard: guard.prod.forbid
	@python3 scripts/verify/scene_provider_registry_guard.py

verify.scene.provider.registry.consumer.guard: guard.prod.forbid
	@python3 scripts/verify/scene_provider_registry_consumer_guard.py

verify.scene.provider_locator.removed.guard: guard.prod.forbid
	@python3 scripts/verify/provider_locator_removed_guard.py

verify.scene_orchestration.provider_shape.guard: guard.prod.forbid
	@python3 scripts/verify/scene_orchestration_provider_shape_guard.py

.PHONY: verify.scene.provider_shape.guard
verify.scene.provider_shape.guard: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.scene_orchestration.provider_shape.guard

.PHONY: verify.scene.contract_v1.field_schema.guard
verify.scene.contract_v1.field_schema.guard: guard.prod.forbid
	@python3 scripts/verify/scene_contract_v1_field_schema_guard.py

verify.capability.provider.guard: guard.prod.forbid
	@python3 scripts/verify/capability_provider_guard.py

verify.capability.registry.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/capability_registry_smoke.py

verify.scene.hud.trace.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_hud_trace_smoke.py

verify.scene.meta.trace.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_meta_trace_smoke.py

verify.contract.governance.coverage: guard.prod.forbid
	@python3 scripts/verify/contract_governance_coverage.py

verify.scene_capability.contract.guard: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_capability_contract_guard.py

verify.scene.capability.matrix.report: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/scene_capability_matrix_report.py

verify.scene.capability.matrix.schema.guard: guard.prod.forbid verify.scene.capability.matrix.report
	@python3 scripts/verify/scene_capability_matrix_report_schema_guard.py

verify.release.capability.audit: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/release_capability_audit.py

verify.release.capability.audit.schema.guard: guard.prod.forbid verify.release.capability.audit
	@python3 scripts/verify/release_capability_audit_schema_guard.py

verify.contract.governance.brief: guard.prod.forbid
	@python3 scripts/verify/contract_governance_brief.py

verify.contract.scene_coverage.brief: guard.prod.forbid
	@python3 scripts/verify/scene_contract_coverage_brief.py

verify.contract.scene_coverage.guard: guard.prod.forbid verify.contract.scene_coverage.brief
	@python3 scripts/verify/scene_contract_coverage_schema_guard.py
	@python3 scripts/verify/scene_contract_coverage_baseline_guard.py

verify.contract.mode.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/contract_mode_smoke.py

verify.contract.api.mode.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/contract_api_mode_smoke.py

.PHONY: verify.contract.permission_runtime_uid_probe verify.contract.view_type_semantic.smoke verify.contract.view_type_semantic.strict.smoke
verify.contract.permission_runtime_uid_probe: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	LOGIN="$${PERMISSION_PROBE_LOGIN:-$(or $(E2E_LOGIN),admin)}"; \
	PASSWORD="$${PERMISSION_PROBE_PASSWORD:-$(or $(E2E_PASSWORD),admin)}"; \
	ACTION_ID="$${PERMISSION_PROBE_ACTION_ID:-543}"; \
	python3 scripts/verify/permission_runtime_uid_probe.py --db "$(DB_NAME)" --action-id "$$ACTION_ID" --login "$$LOGIN" --password "$$PASSWORD"

verify.contract.view_type_semantic.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) python3 scripts/verify/contract_view_type_semantic_smoke.py

verify.contract.view_type_semantic.strict.smoke: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) VIEW_TYPE_SMOKE_MIN_MODELS=2 python3 scripts/verify/contract_view_type_semantic_smoke.py

verify.round.v0_6.mini: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.frontend.quick.gate
	@$(MAKE) --no-print-directory verify.portal.tree_view_smoke.container
	@BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 $(MAKE) --no-print-directory verify.contract.preflight
	@echo "[OK] verify.round.v0_6.mini done"

verify.contract.preflight: guard.prod.forbid
	@if [ "$(BASELINE_FREEZE_ENFORCE)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.baseline.freeze_guard; \
	else \
	  echo "[verify.contract.preflight] BASELINE_FREEZE_ENFORCE=0: skip baseline freeze guard"; \
	fi
	@$(MAKE) --no-print-directory verify.test_seed_dependency.guard
	@$(MAKE) --no-print-directory verify.contract_drift.guard
	@$(MAKE) --no-print-directory verify.scene.contract_path.gate
	@$(MAKE) --no-print-directory verify.contract.governance.coverage
	@if [ "$(CONTRACT_PREFLIGHT_SKIP_DOCS)" = "1" ]; then \
	  echo "[verify.contract.preflight] CONTRACT_PREFLIGHT_SKIP_DOCS=1: skip docs gates"; \
	else \
	  $(MAKE) --no-print-directory verify.docs.all; \
	fi
	@if [ "$(CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE)" = "1" ]; then \
	  echo "[verify.contract.preflight] CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1: skip grouped governance bundle"; \
	else \
	  $(MAKE) --no-print-directory verify.grouped.governance.bundle; \
	fi
	@$(MAKE) --no-print-directory audit.intent.surface INTENT_SURFACE_MD="$(CONTRACT_PREFLIGHT_INTENT_SURFACE_MD)" INTENT_SURFACE_JSON="$(CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON)"
	@if [ "$(CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD)" = "1" ]; then \
	  echo "[verify.contract.preflight] CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1: skip scene capability contract guard"; \
	else \
	  $(MAKE) --no-print-directory verify.scene_capability.contract.guard; \
	fi
	@$(MAKE) --no-print-directory verify.contract.governance.brief
	@$(MAKE) --no-print-directory verify.contract.scene_coverage.guard
	@$(MAKE) --no-print-directory verify.contract.permission_runtime_uid_probe
	@$(MAKE) --no-print-directory verify.contract.mode.smoke
	@$(MAKE) --no-print-directory verify.project.form.contract.surface.guard
	@$(MAKE) --no-print-directory verify.relation.access_policy.consistency.audit
	@$(MAKE) --no-print-directory verify.system_group.business_acl.guard
	@$(MAKE) --no-print-directory verify.native_surface_integrity_guard
	@$(MAKE) --no-print-directory verify.governed_surface_policy_guard
	@$(MAKE) --no-print-directory verify.contract.surface_mapping_guard
	@$(MAKE) --no-print-directory verify.contract.parse_boundary.guard
	@$(MAKE) --no-print-directory verify.contract.production_chain.guard
	@$(MAKE) --no-print-directory verify.contract.ordering.smoke
	@$(MAKE) --no-print-directory verify.scene.hud.trace.smoke
	@$(MAKE) --no-print-directory verify.scene.meta.trace.smoke
	@$(MAKE) --no-print-directory verify.contract.api.mode.smoke
	@$(MAKE) --no-print-directory verify.contract.view_type_semantic.smoke
	@$(MAKE) --no-print-directory verify.frontend.search_groupby_savedfilters.guard
	@$(MAKE) --no-print-directory verify.frontend.x2many_command_semantic.guard
	@$(MAKE) --no-print-directory verify.frontend.view_type_render_coverage.guard
	@$(MAKE) --no-print-directory verify.native_view.semantic_page
	@if [ "$(CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES)" = "1" ]; then \
	  $(MAKE) --no-print-directory verify.contract.view_type_semantic.strict.smoke; \
	else \
	  echo "[verify.contract.preflight] CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0: skip strict view-type semantic smoke"; \
	fi
	@$(MAKE) --no-print-directory verify.scene.contract.shape
	@$(MAKE) --no-print-directory contract.evidence.export

audit.intent.surface: guard.prod.forbid
	@python3 scripts/audit/intent_surface_report.py --output-md "$(INTENT_SURFACE_MD)" --output-json "$(INTENT_SURFACE_JSON)"

policy.apply.extension_modules: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) bash scripts/ops/apply_extension_modules.sh

policy.ensure.extension_modules: guard.prod.forbid check-compose-project check-compose-env
	@set -e; \
	if $(MAKE) --no-print-directory verify.extension_modules.guard DB_NAME=$(DB_NAME); then \
	  echo "[policy.ensure.extension_modules] already satisfied"; \
	elif [ "$${AUTO_FIX_EXTENSION_MODULES:-0}" = "1" ]; then \
	  echo "[policy.ensure.extension_modules] applying auto-fix"; \
	  $(MAKE) --no-print-directory policy.apply.extension_modules DB_NAME=$(DB_NAME); \
	  $(MAKE) --no-print-directory restart; \
	  $(MAKE) --no-print-directory verify.extension_modules.guard DB_NAME=$(DB_NAME); \
	else \
	  echo "[policy.ensure.extension_modules] FAIL: missing smart_construction_core in sc.core.extension_modules"; \
	  echo "[policy.ensure.extension_modules] HINT: re-run with AUTO_FIX_EXTENSION_MODULES=1 to auto-fix + restart"; \
	  exit 2; \
	fi

# ======================================================
# ==================== CI ==============================
# ======================================================
.PHONY: ci.preflight.contract ci.scene.delivery.readiness ci.gate ci.smoke ci.full ci.repro \
	test-install-gate test-upgrade-gate \
	ci.clean ci.ps ci.logs gate.boundary

.PHONY: refresh.delivery.readiness.scoreboard
refresh.delivery.readiness.scoreboard: guard.prod.forbid
	@python3 scripts/verify/delivery_readiness_scoreboard_refresh.py

# CI preflight: fail-fast on contract drift before heavier test suites.
ci.preflight.contract: guard.prod.forbid
	@$(MAKE) --no-print-directory verify.architecture.capability_projection_governance_gate
	@$(MAKE) --no-print-directory verify.architecture.platformization_boundary_closure_bundle
	@$(MAKE) --no-print-directory verify.contract.preflight
	@$(MAKE) --no-print-directory verify.frontend.home_suggestion_semantics.guard
	@$(MAKE) --no-print-directory verify.frontend.page_contract_boundary.guard

ci.scene.delivery.readiness: guard.prod.forbid
	@CI_SCENE_DELIVERY_PROFILE=$${CI_SCENE_DELIVERY_PROFILE:-strict}; \
	 echo "[ci.scene.delivery.readiness] profile=$$CI_SCENE_DELIVERY_PROFILE"; \
	 if [ "$$CI_SCENE_DELIVERY_PROFILE" = "restricted" ]; then \
	   if SC_SCENE_READY_CONSUMPTION_TREND_REQUIRE_LIVE=0 \
	      SC_SCENE_ACTION_SURFACE_STRATEGY_PAYLOAD_REQUIRE_LIVE=0 \
	      SC_SCENE_ACTION_STRATEGY_LIVE_MATRIX_REQUIRE_LIVE=0 \
	      $(MAKE) --no-print-directory verify.scene.delivery.readiness.role_company_matrix; then \
	     python3 scripts/verify/delivery_readiness_scoreboard_refresh.py --profile $$CI_SCENE_DELIVERY_PROFILE --status PASS; \
	     exit 0; \
	   fi; \
	 else \
	   if $(MAKE) --no-print-directory verify.scene.delivery.readiness.role_company_matrix; then \
	     python3 scripts/verify/delivery_readiness_scoreboard_refresh.py --profile $$CI_SCENE_DELIVERY_PROFILE --status PASS; \
	     exit 0; \
	   fi; \
	 fi; \
	 python3 scripts/verify/delivery_readiness_scoreboard_refresh.py --profile $$CI_SCENE_DELIVERY_PROFILE --status FAIL; \
	 python3 scripts/verify/scene_delivery_failure_brief.py; \
	 python3 scripts/verify/scene_delivery_failure_brief_summary.py; \
	 exit 1

# 只跑守门：权限/绕过（最快定位安全回归）
ci.gate: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) TEST_TAGS="sc_gate,sc_perm" bash scripts/ci/run_ci.sh

# 冒烟：基础链路 + 守门
ci.smoke: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) TEST_TAGS="sc_smoke,sc_gate" bash scripts/ci/run_ci.sh

# 全量：用 TEST_TAGS（默认 sc_smoke,sc_gate，也可你自定义覆盖）
ci.full: guard.prod.forbid ci.preflight.contract
	@$(RUN_ENV) bash scripts/ci/run_ci.sh

# 复现：不清理 artifacts，保留现场
ci.repro: guard.prod.forbid ci.preflight.contract
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

.PHONY: verify.native_view.semantic_page.shape
verify.native_view.semantic_page.shape: guard.prod.forbid
	@python3 scripts/verify/native_view_semantic_page_shape_guard.py --dir docs/contract/snapshots/native_view --output artifacts/backend/native_view_semantic_page_shape_guard.json

.PHONY: verify.native_view.semantic_page.schema
verify.native_view.semantic_page.schema: guard.prod.forbid
	@python3 scripts/verify/native_view_semantic_page_schema_guard.py --schema docs/architecture/native_view_contract/semantic_page_contract_shape_v1.schema.json --dir docs/contract/snapshots/native_view --output artifacts/backend/native_view_semantic_page_schema_guard.json

.PHONY: verify.native_view.semantic_page
verify.native_view.semantic_page: verify.native_view.semantic_page.shape verify.native_view.semantic_page.schema

.PHONY: verify.native_view.coverage.report
verify.native_view.coverage.report: guard.prod.forbid verify.native_view.semantic_page
	@python3 scripts/verify/native_view_coverage_report.py

.PHONY: verify.native_view.samples.compare
verify.native_view.samples.compare: guard.prod.forbid verify.native_view.semantic_page
	@python3 scripts/verify/native_view_sample_compare_report.py

.PHONY: verify.native_view.ecosystem.readiness
verify.native_view.ecosystem.readiness: guard.prod.forbid
	@python3 scripts/verify/native_view_ecosystem_readiness_report.py

VERIFY_CMDS ?=

.PHONY: agent.task.validate agent.risk.scan agent.classify agent.report agent.verify agent.iteration agent.queue.pick agent.queue.run agent.queue.normalize agent.baseline.candidate task.split task.run.low_cost task.validate.low_cost verify.architecture.platform_kernel_alignment

agent.task.validate:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@python3 agent_ops/scripts/validate_task.py "$(TASK)"

agent.risk.scan:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@python3 agent_ops/scripts/risk_scan.py "$(TASK)"

agent.classify:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@python3 agent_ops/scripts/classify_result.py "$(TASK)"

agent.report:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@python3 agent_ops/scripts/build_report.py "$(TASK)"

agent.verify:
	@test -n "$(VERIFY_CMDS)" || (echo "VERIFY_CMDS is required" && exit 2)
	@bash -lc 'set -e; $(VERIFY_CMDS)'

agent.iteration:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@bash agent_ops/scripts/run_iteration.sh "$(TASK)"

task.split:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@python3 agent_ops/scripts/split_task.py "$(TASK)"

task.run.low_cost:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@bash agent_ops/scripts/run_low_cost_iteration.sh "$(TASK)"

task.validate.low_cost:
	@test -n "$(TASK)" || (echo "TASK is required" && exit 2)
	@python3 agent_ops/scripts/validate_task.py "$(TASK)"

agent.queue.pick:
	@python3 agent_ops/scripts/pick_next_task.py

agent.queue.run:
	@python3 agent_ops/scripts/run_queue.py

agent.queue.normalize:
	@test -n "$(QUEUE)" || (echo "QUEUE is required" && exit 2)
	@test -n "$(STATE)" || (echo "STATE is required" && exit 2)
	@python3 agent_ops/scripts/normalize_queue_state.py "$(QUEUE)" --state "$(STATE)"

agent.baseline.candidate:
	@python3 agent_ops/scripts/generate_dirty_baseline_candidate.py $(if $(OUT),--output "$(OUT)",)

verify.architecture.platform_kernel_alignment: guard.prod.forbid
	@python3 scripts/verify/platform_kernel_alignment_guard.py

.PHONY: verify.architecture.intent_registry_single_owner_guard verify.architecture.capability_registry_platform_owner_guard verify.architecture.scene_bridge_industry_proxy_guard verify.architecture.platform_policy_constant_owner_guard verify.architecture.system_init_extension_protocol_guard verify.architecture.system_init_heavy_workspace_payload_guard
.PHONY: verify.architecture.industry_legacy_bridge_residue_guard
.PHONY: verify.architecture.platformization_boundary_closure_bundle
.PHONY: verify.architecture.capability_projection_governance_gate
.PHONY: verify.architecture.native_capability_ingestion_guard
.PHONY: verify.architecture.native_capability_ingestion_lint_bundle
.PHONY: verify.architecture.native_capability_runtime_exposure_baseline_guard
.PHONY: verify.architecture.native_capability_runtime_exposure_payload_guard
.PHONY: verify.architecture.runtime_exposure_projection_schema_snapshot_guard
.PHONY: verify.architecture.runtime_exposure_evidence_export
.PHONY: verify.architecture.runtime_exposure_evidence_snapshot_guard
.PHONY: verify.architecture.native_capability_projection_release_readiness_summary_guard
.PHONY: verify.architecture.non_native_capability_binding_policy_parity_guard
.PHONY: verify.architecture.mixed_source_capability_matrix_snapshot_guard
.PHONY: verify.architecture.non_native_capability_drift_verify_bundle
.PHONY: verify.architecture.native_capability_projection_coverage_report
.PHONY: verify.architecture.native_capability_projection_snapshot_guard
.PHONY: verify.architecture.native_capability_projection_release_guard_bundle

verify.architecture.capability_projection_governance_gate: guard.prod.forbid verify.architecture.native_capability_projection_release_guard_bundle verify.architecture.non_native_capability_drift_verify_bundle
	@echo "[OK] verify.architecture.capability_projection_governance_gate done"

verify.architecture.platformization_boundary_closure_bundle: guard.prod.forbid verify.architecture.intent_registry_single_owner_guard verify.architecture.scene_bridge_industry_proxy_guard verify.architecture.platform_policy_constant_owner_guard verify.architecture.capability_projection_governance_gate
	@echo "[OK] verify.architecture.platformization_boundary_closure_bundle done"

verify.architecture.native_capability_ingestion_guard:
	@python3 scripts/verify/architecture_native_capability_ingestion_guard.py

verify.architecture.native_capability_ingestion_lint_bundle:
	@python3 scripts/verify/architecture_native_capability_ingestion_lint_bundle.py

verify.architecture.native_capability_runtime_exposure_baseline_guard:
	@python3 scripts/verify/architecture_native_capability_runtime_exposure_baseline_guard.py

verify.architecture.native_capability_runtime_exposure_payload_guard:
	@python3 scripts/verify/architecture_native_capability_runtime_exposure_payload_guard.py

verify.architecture.runtime_exposure_projection_schema_snapshot_guard:
	@python3 scripts/verify/runtime_exposure_projection_schema_snapshot_guard.py

verify.architecture.runtime_exposure_evidence_export:
	@python3 scripts/verify/runtime_exposure_evidence_export.py

verify.architecture.runtime_exposure_evidence_snapshot_guard: verify.architecture.runtime_exposure_evidence_export
	@python3 scripts/verify/runtime_exposure_evidence_snapshot_guard.py

verify.architecture.native_capability_projection_release_readiness_summary_guard:
	@python3 scripts/verify/native_capability_projection_release_readiness_summary_guard.py

verify.architecture.non_native_capability_binding_policy_parity_guard:
	@python3 scripts/verify/architecture_non_native_capability_binding_policy_parity_guard.py

verify.architecture.mixed_source_capability_matrix_snapshot_guard:
	@python3 scripts/verify/mixed_source_capability_matrix_snapshot_guard.py

verify.architecture.non_native_capability_drift_verify_bundle: guard.prod.forbid verify.architecture.non_native_capability_binding_policy_parity_guard verify.architecture.mixed_source_capability_matrix_snapshot_guard
	@echo "[OK] verify.architecture.non_native_capability_drift_verify_bundle done"

verify.architecture.native_capability_projection_coverage_report:
	@python3 scripts/verify/native_capability_projection_coverage_report.py

verify.architecture.native_capability_projection_snapshot_guard:
	@python3 scripts/verify/native_capability_projection_snapshot_guard.py

verify.architecture.native_capability_projection_release_guard_bundle: guard.prod.forbid verify.architecture.native_capability_ingestion_guard verify.architecture.native_capability_ingestion_lint_bundle verify.architecture.native_capability_runtime_exposure_baseline_guard verify.architecture.native_capability_runtime_exposure_payload_guard verify.architecture.runtime_exposure_projection_schema_snapshot_guard verify.architecture.runtime_exposure_evidence_snapshot_guard verify.architecture.native_capability_projection_coverage_report verify.architecture.native_capability_projection_snapshot_guard verify.architecture.native_capability_projection_release_readiness_summary_guard
	@echo "[OK] verify.architecture.native_capability_projection_release_guard_bundle done"

verify.architecture.intent_registry_single_owner_guard:
	@python3 scripts/verify/architecture_intent_registry_single_owner_guard.py

verify.architecture.capability_registry_platform_owner_guard:
	@python3 scripts/verify/architecture_capability_registry_platform_owner_guard.py

verify.architecture.scene_bridge_industry_proxy_guard:
	@python3 scripts/verify/architecture_scene_bridge_industry_proxy_guard.py

verify.architecture.platform_policy_constant_owner_guard:
	@python3 scripts/verify/architecture_platform_policy_constant_owner_guard.py

verify.architecture.system_init_extension_protocol_guard:
	@python3 scripts/verify/architecture_system_init_extension_protocol_guard.py

verify.architecture.system_init_heavy_workspace_payload_guard:
	@python3 scripts/verify/architecture_system_init_heavy_workspace_payload_guard.py

verify.architecture.industry_legacy_bridge_residue_guard:
	@python3 scripts/verify/architecture_industry_legacy_bridge_residue_guard.py

.PHONY: verify.native.business_fact.stage_gate
verify.native.business_fact.stage_gate: guard.prod.forbid
	@$(MAKE) verify.native.business_fact.static
	@python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) python3 scripts/verify/scene_legacy_auth_smoke.py
	@python3 scripts/verify/native_business_fact_action_openability_verify.py
	@python3 scripts/verify/native_business_fact_dictionary_completeness_verify.py
	@python3 scripts/verify/native_business_fact_project_org_closure_verify.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) python3 scripts/verify/native_business_fact_isolation_anchor_verify.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) python3 scripts/verify/native_business_fact_authenticated_alignment_smoke.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) python3 scripts/verify/native_business_fact_role_operability_blockers_smoke.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) python3 scripts/verify/native_business_fact_role_alignment_smoke.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 scripts/verify/native_business_fact_role_matrix_alignment_smoke.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) ROLE_OWNER_LOGIN=$(or $(ROLE_OWNER_LOGIN),demo_role_owner) ROLE_OWNER_PASSWORD=$(or $(ROLE_OWNER_PASSWORD),demo) ROLE_PM_LOGIN=$(or $(ROLE_PM_LOGIN),demo_role_pm) ROLE_PM_PASSWORD=$(or $(ROLE_PM_PASSWORD),demo) ROLE_FINANCE_LOGIN=$(or $(ROLE_FINANCE_LOGIN),demo_role_finance) ROLE_FINANCE_PASSWORD=$(or $(ROLE_FINANCE_PASSWORD),demo) ROLE_EXECUTIVE_LOGIN=$(or $(ROLE_EXECUTIVE_LOGIN),demo_role_executive) ROLE_EXECUTIVE_PASSWORD=$(or $(ROLE_EXECUTIVE_PASSWORD),demo) python3 scripts/verify/native_business_fact_role_flow_usability_smoke.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) E2E_LOGIN=$(or $(E2E_LOGIN),$(ROLE_OWNER_LOGIN),admin) E2E_PASSWORD=$(or $(E2E_PASSWORD),$(ROLE_OWNER_PASSWORD),admin) python3 scripts/verify/product_project_flow_full_chain_execution_smoke.py
	@DB_NAME=$(DB_NAME) E2E_BASE_URL=$(or $(E2E_BASE_URL),http://localhost:8069) python3 scripts/verify/native_business_fact_runtime_snapshot.py
