# =========================================================
# Stable Engineering Makefile (Odoo 17 + Docker Compose)
# - Thin Makefile: all logic lives in scripts/
# - Windows Git Bash / MSYS2 friendly
# =========================================================

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
MIGRATION_ASSET_ROOT ?= migration_assets
MIGRATION_ASSET_LOCK ?= docs/migration_alignment/migration_asset_package_lock_v1.json
MIGRATION_FILE_INDEX_CSV ?= /mnt/artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv
CONSTRUCTION_CONTRACT_VISIBLE_XLSX ?= /mnt/artifacts/migration/source_extracts/construction_contract_visible_surface.xlsx
CONSTRUCTION_CONTRACT_RAW_CSV ?= /mnt/tmp/raw/contract/contract.csv
PROJECT_POSITIVE_MIGRATION_EXCEL_PATH ?= /mnt/tmp/001/672施工合同项目名称去重统计.xlsx
PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV ?= $(CONSTRUCTION_CONTRACT_RAW_CSV)
FORMAL_PROJECTION_ARTIFACT_ROOT ?= $(if $(MIGRATION_ARTIFACT_ROOT),$(MIGRATION_ARTIFACT_ROOT),/tmp/history_continuity/$(DB_NAME)/adhoc)
PREPAID_TAX_VISIBLE_XLSX ?= /home/odoo/workspace/partner_import_source/3/+预缴税款639153288551406250.xlsx
FOREIGN_TAX_CERTIFICATE_VISIBLE_XLSX ?= /home/odoo/workspace/partner_import_source/3/外经证登记639153428231093750.xlsx
ATTACHMENT_AUDIT_SOURCE_CONTAINS ?=
ATTACHMENT_AUDIT_STRICT ?=
ATTACHMENT_AUDIT_ALLOW_MISSING_FILES ?=
ATTACHMENT_AUDIT_LIMIT ?=
ATTACHMENT_AUDIT_PRINT_FULL ?=
ATTACHMENT_JOB_AUDIT_JOB_ROOT ?= /mnt/artifacts/backend/legacy-online-mirror-jobs
ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS ?=
ATTACHMENT_JOB_AUDIT_STRICT ?=
ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES ?=
ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES ?=
ATTACHMENT_JOB_AUDIT_INDEX_LIMIT ?=
ATTACHMENT_JOB_AUDIT_PRINT_FULL ?=
ATTACHMENT_MISSING_RESIDUAL_INPUT ?= /data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_latest.tsv
ATTACHMENT_MISSING_RESIDUAL_OUTPUT ?= /data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_unique_summary.json
LEGACY_ATTACHMENT_BROWSER_FRONTEND_URL ?= http://127.0.0.1:5179
LEGACY_ATTACHMENT_BROWSER_SAMPLES ?=
LEGACY_ATTACHMENT_BROWSER_SAMPLES_FILE ?=
LEGACY_ATTACHMENT_BROWSER_SAMPLE_MANIFEST_OUTPUT ?= /mnt/artifacts/backend/legacy_attachment_frontend_browser_samples.json
LEGACY_ATTACHMENT_BROWSER_SAMPLE_PER_MIMETYPE ?= 0
BOUNDARY_AUDIT_JSON_OUT ?= artifacts/boundary_audit/smart_core_hits.json
BOUNDARY_AUDIT_MD_OUT ?= docs/ops/boundary_audit_smart_core_20260130.md
BOUNDARY_AUDIT_GENERATED_AT ?= snapshot

# Snapshot DB knobs from invocation context before .env include so explicit
# shell/CLI inputs are not overridden by values inside .env.<tier>.
REQUESTED_DB_NAME := $(DB_NAME)
REQUESTED_DB := $(DB)
REQUESTED_BD := $(BD)
REQUESTED_DB_NAME_ORIGIN := $(origin DB_NAME)
REQUESTED_DB_ORIGIN := $(origin DB)
REQUESTED_BD_ORIGIN := $(origin BD)

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
DB_NAME      ?=
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
WORKFLOW_CONTRACT_FRONTEND_URL ?= http://127.0.0.1:18081
WORKFLOW_CONTRACT_DB_NAME ?= $(or $(DB_NAME),sc_demo)
WORKFLOW_CONTRACT_EXPENSE_RECORD_ID ?= 273134
WORKFLOW_CONTRACT_CLOSE_RECORD_ID ?= 13159
WORKFLOW_CONTRACT_INVENTORY_OUT ?= docs/ops/audit/workflow_state_inventory_sc_demo.md
DB_CI        ?= sc_test
DB_USER      ?= odoo
DB_PASSWORD  ?= $(DB_USER)
SCENE_CHANNEL ?= stable
SCENE_USE_PINNED ?= 0

# Back-compat aliases:
# - canonical knob: DB_NAME
# - compat knobs: DB (preferred alias), BD (legacy alias)
# Priority: DB_NAME > DB > BD > default.
BD ?=
DB ?=
ifneq (,$(filter command line,$(REQUESTED_DB_NAME_ORIGIN)))
DB_NAME := $(REQUESTED_DB_NAME)
else ifneq (,$(filter command line,$(REQUESTED_DB_ORIGIN)))
DB_NAME := $(REQUESTED_DB)
else ifneq (,$(filter command line,$(REQUESTED_BD_ORIGIN)))
DB_NAME := $(REQUESTED_BD)
else ifneq (,$(filter environment environment\ override,$(REQUESTED_DB_NAME_ORIGIN)))
DB_NAME := $(REQUESTED_DB_NAME)
else ifneq (,$(filter environment environment\ override,$(REQUESTED_DB_ORIGIN)))
DB_NAME := $(REQUESTED_DB)
else ifneq (,$(filter environment environment\ override,$(REQUESTED_BD_ORIGIN)))
DB_NAME := $(REQUESTED_BD)
else ifeq ($(strip $(DB_NAME)),)
ifneq ($(strip $(DB)),)
DB_NAME := $(DB)
else ifneq ($(strip $(BD)),)
DB_NAME := $(BD)
endif
endif
DB_NAME ?= sc_odoo

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
CONFIG_MOUNT_HOST ?= $(ROOT_DIR)/config
CONFIG_MOUNT_CONT ?= /mnt/config

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
CONFIG_MOUNT_HOST="$(CONFIG_MOUNT_HOST)" \
CONFIG_MOUNT_CONT="$(CONFIG_MOUNT_CONT)" \
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


include make/guards.mk
include make/contract.mk
include make/help.mk
include make/dev.mk
include make/runtime_ops.mk make/user_data.mk make/production_blocker.mk

include make/frontend.mk
include make/codex.mk
include make/dev_test.mk
include make/ci.mk
