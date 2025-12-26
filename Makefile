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
PROJECT_CI ?= sc-ci

# ------------------ DB / Module ------------------
DB_NAME := sc_odoo
DB_CI   ?= sc_odoo
DB_USER := odoo

MODULE ?= smart_construction_core

# ------------------ Test tags ------------------
TEST_TAGS ?= sc_smoke,sc_gate

# 安全展开：逐个 tag 加 module 前缀
TEST_TAGS_FINAL := $(TEST_TAGS)

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
PROJECT_CI="$(PROJECT_CI)" \
DB_NAME="$(DB_NAME)" \
DB_CI="$(DB_CI)" \
DB_USER="$(DB_USER)" \
MODULE="$(MODULE)" \
TEST_TAGS="$(TEST_TAGS)" \
TEST_TAGS_FINAL="$(TEST_TAGS_FINAL)" \
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


# ======================================================
# ==================== Dev Test ========================
# ======================================================
.PHONY: test test.safe

test:
	@$(RUN_ENV) bash scripts/test/test.sh

test.safe:
	@$(RUN_ENV) bash scripts/test/test_safe.sh


# ======================================================
# ==================== CI v0.3 =========================
# ======================================================
.PHONY: test-ci ci ci.smoke \
        test-install-gate test-upgrade-gate \
        ci.clean ci.ps ci.logs ci.repro

test-ci:
	@echo "== CI v0.3 FINAL =="
	@echo "MODULE=$(MODULE)"
	@echo "DB_CI=$(DB_CI)"
	@echo "TEST_TAGS=$(TEST_TAGS)"
	@echo "TEST_TAGS_FINAL=$(TEST_TAGS_FINAL)"
	@echo "CI_ARTIFACT_PURGE=$(CI_ARTIFACT_PURGE) CI_ARTIFACT_KEEP=$(CI_ARTIFACT_KEEP)"
	@echo
	@$(RUN_ENV) bash scripts/ci/run_ci.sh

ci.smoke:
	@$(RUN_ENV) TEST_TAGS="sc_smoke,sc_gate" bash scripts/ci/run_ci.sh

ci:
	@$(RUN_ENV) bash scripts/ci/install_gate.sh
	@$(RUN_ENV) TEST_TAGS="sc_smoke,sc_gate" bash scripts/ci/run_ci.sh

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

ci.repro:
	@$(RUN_ENV) bash scripts/ci/ci_repro.sh
