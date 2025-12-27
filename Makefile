# =========================================================
# Stable Engineering Makefile (Odoo 17 + Docker Compose)
# - Thin Makefile: all logic lives in scripts/
# - Windows Git Bash / MSYS2 friendly
# =========================================================

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ------------------ Compose ------------------
COMPOSE_BIN ?= docker compose
PROJECT    ?= sc

# Compose files
COMPOSE_FILES ?= -f docker-compose.yml
COMPOSE_TEST_FILES ?= -f docker-compose.yml -f docker-compose.testdeps.yml

# ------------------ DB / Module ------------------
DB_NAME := sc_odoo
DB_CI   ?= sc_test
DB_USER := odoo

# ------------------ DB override (single entry) ------------------
# Use one knob to control dev/test db: `make test DB=sc_test`
# CI keeps its own DB_CI unless你显式覆盖。
DB ?=
ifneq ($(strip $(DB)),)
DB_NAME := $(DB)
endif

MODULE ?= smart_construction_core

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
PROJECT="$(PROJECT)" \
COMPOSE_FILES='$(COMPOSE_FILES)' \
COMPOSE_TEST_FILES='$(COMPOSE_TEST_FILES)' \
DB_NAME="$(DB_NAME)" \
DB_CI="$(DB_CI)" \
DB_USER="$(DB_USER)" \
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
	@echo "  make test | test.safe"
	@echo "  make ci.gate | ci.smoke | ci.full | ci.repro"
	@echo "  make ci.clean | ci.ps | ci.logs | ci.repro"
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
	@$(RUN_ENV) bash scripts/db/reset.sh
demo.reset:
	@$(RUN_ENV) DB=sc_demo bash scripts/demo/reset.sh

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
