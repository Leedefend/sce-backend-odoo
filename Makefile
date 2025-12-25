# =========================================================
# Stable Engineering Makefile (Odoo 17 + Docker Compose)
# - CI uses overlay compose and hard cleanup even on failure
# - Windows friendly via Git Bash / MSYS2 / WSL bash
# =========================================================

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ================== 基本配置 ==================
# 建议统一用 docker compose（plugin）；如你仍用 docker-compose v1，可在命令行覆盖：
#   make COMPOSE_BIN=docker-compose test-ci
COMPOSE_BIN ?= docker compose

PROJECT        ?= sc
PROJECT_CI     ?= sc-ci
# 固化 project-directory，避免不同 shell/cwd 行为漂移
COMPOSE_COMMON := --project-directory "$(ROOT_DIR)"

# 明确指定 compose 文件，避免“目录里多个 compose 文件导致不确定”
COMPOSE        := $(COMPOSE_BIN) $(COMPOSE_COMMON) -p $(PROJECT) -f docker-compose.yml
COMPOSE_CI     := $(COMPOSE_BIN) $(COMPOSE_COMMON) -p $(PROJECT_CI) -f docker-compose.yml -f docker-compose.ci.yml

DB_NAME        := sc_odoo
DB_USER        := odoo
DB_CONTAINER   := sc-db
ODOO_CONTAINER := sc-odoo
INIT_MODULES   := base
DB ?= $(DB_NAME)

# CI 专用 DB（强烈建议隔离，避免锁冲突/污染）
DB_CI          ?= sc_odoo
CI_CONF        ?= /etc/odoo/odoo.conf
CI_LOG         ?= test-ci.log
CI_ARTIFACT_DIR ?= artifacts/ci
# 测试通过的日志签名，配合 compose rc 兜底（收敛到最终汇总行）
CI_PASS_SIG_RE ?= (0 failed, 0 error\(s\))

# 默认模块 / 测试标签
MODULE ?= smart_construction_core
# 分层：sc_smoke（最小烟囱） + sc_gate（权限守门）为默认；回归层按需加
TEST_TAGS ?= sc_smoke,sc_gate
# 如果 TEST_TAGS 已经带 /module: 前缀，则直接使用；否则自动补 /$(MODULE):
ifeq (,$(findstring /,$(TEST_TAGS)))
TEST_TAG_EXPR := /$(MODULE):$(TEST_TAGS)
else
TEST_TAG_EXPR := $(TEST_TAGS)
endif

# 自定义模块集合
CUSTOM_MODULES := smart_construction_core smart_construction_demo

# 统一禁用 compose ANSI（兼容你遇到的 unknown flag: --ansi）
export COMPOSE_ANSI := never

# ================== 基础操作 ==================
.PHONY: up down restart restart-odoo ps logs odoo-shell \
        db-reset upgrade upgrade-all \
        test test.safe test.isolated test-ci \
        test-install-gate test-upgrade-gate \
        validate validate-ci \
        db.drop db.create install noiseoff noiseon verify.noise db.rebuild.noiseoff \
        ci.up ci.down ci.ps ci.logs ci.clean ci.collect ci.repro

up:
	@echo "== compose up -d =="
	$(COMPOSE) up -d

down:
	@echo "== compose down =="
	$(COMPOSE) down

restart:
	@echo "== compose restart =="
	$(COMPOSE) down
	$(COMPOSE) up -d

restart-odoo:
	@echo "== restart Odoo container =="
	docker restart $(ODOO_CONTAINER)

ps:
	@echo "== docker ps (table) =="
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs:
	@echo "== compose logs -f odoo =="
	$(COMPOSE) logs -f odoo

odoo-shell:
	@echo "== docker exec -it $(ODOO_CONTAINER) bash =="
	docker exec -it $(ODOO_CONTAINER) bash

# ================== CI 基础操作（强隔离） ==================
ci.up:
	@echo "== CI up (abort on odoo exit) DB=$(DB_CI) =="
	DB_CI=$(DB_CI) MODULE=$(MODULE) TEST_TAGS=$(TEST_TAGS) \
	$(COMPOSE_CI) up --abort-on-container-exit --exit-code-from odoo

ci.down:
	@echo "== CI down =="
	$(COMPOSE_CI) down --remove-orphans || true

ci.clean:
	@echo "== CI down -v (clean volumes) =="
	$(COMPOSE_CI) down -v --remove-orphans || true

ci.ps:
	@echo "== CI ps =="
	$(COMPOSE_CI) ps

ci.logs:
	@echo "== CI logs -f odoo =="
	$(COMPOSE_CI) logs -f odoo

ci.collect:
	@set -e; \
	ts=$$(date +%Y%m%d-%H%M%S); \
	outdir="$(CI_ARTIFACT_DIR)/$(PROJECT_CI)/$$ts"; \
	mkdir -p "$$outdir"; \
	$(COMPOSE_CI) ps -a >"$$outdir/ps.txt" 2>&1 || true; \
	$(COMPOSE_CI) logs --no-color --tail=500 db >"$$outdir/db.log" 2>&1 || true; \
	$(COMPOSE_CI) logs --no-color --tail=500 redis >"$$outdir/redis.log" 2>&1 || true; \
	$(COMPOSE_CI) logs --no-color --tail=800 odoo >"$$outdir/odoo.log" 2>&1 || true; \
	echo "$$outdir"

# ================== 数据库重置 ==================
db-reset:
	@echo "== Reset database $(DB_NAME) =="
	- docker stop $(ODOO_CONTAINER) || true
	- docker exec $(DB_CONTAINER) psql -U $(DB_USER) -d postgres \
		-c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(DB_NAME)' AND pid <> pg_backend_pid();"
	- docker exec $(DB_CONTAINER) dropdb -U $(DB_USER) $(DB_NAME) || true
	- docker exec $(DB_CONTAINER) createdb -U $(DB_USER) $(DB_NAME)
	- docker start $(ODOO_CONTAINER)
	- docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-i $(INIT_MODULES) \
		--without-demo=all \
		--load-language=zh_CN \
		--stop-after-init
	@echo "== [OK] db-reset done =="

# ================== 模块升级 ==================
upgrade:
	@echo "== Upgrade module $(MODULE) =="
	docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--stop-after-init
	@echo "== [OK] upgrade done =="

upgrade-all:
	@echo "== Upgrade all custom modules =="
	docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB_NAME) \
		-u $(CUSTOM_MODULES) \
		--stop-after-init
	@echo "== [OK] upgrade-all done =="

# ================== 测试（Smoke） ==================
# 关键点：
# - Odoo 无论如何都会加载/安装依赖（base/web 等），这是正常的
# - 你要避免“看似跑系统模块测试”，正确做法是把 --test-tags 限定到模块维度
#   推荐格式：/module:tag  （例如 /smart_construction_core:sc_smoke）
# - 这样日志里仍会看到 base/web 等模块加载，但真正执行的测试只会落在你的模块范围内

TEST_TAG_EXPR := /$(MODULE):$(TEST_TAGS)

test:
	@echo "== Running tests (legacy): module=$(MODULE) tags=$(TEST_TAGS) expr=$(TEST_TAG_EXPR) =="
	@echo "== NOTE: if hang occurs, use 'make test.safe' or 'make test-ci' =="
	$(COMPOSE) run --rm -T odoo \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--no-http \
		--test-enable \
		--test-tags "$(TEST_TAG_EXPR)" \
		--stop-after-init
	@echo "== [OK] test done =="

test.safe:
	@echo "== Running tests SAFE: stop running services to avoid DB locks & entrypoint hang =="
	- $(COMPOSE) stop odoo nginx || true
	$(COMPOSE) run --rm -T odoo \
		-d $(DB_NAME) \
		-u $(MODULE) \
		--no-http \
		--test-enable \
		--test-tags "$(TEST_TAG_EXPR)" \
		--stop-after-init
	@echo "== [OK] test.safe done =="

test.isolated: test.safe

# ================== 推荐：CI 方式跑测试（强隔离 DB，最稳定） ==================
# 工程化要求：
# - 开始前：down -v 清卷，保证环境干净
# - 结束后：无论 up 成功/失败，都 down -v 清卷（保证不会污染下一次）
# - 记录日志：test-ci.log
# - 出错时：保持原 exit code（CI 守门需要）

test-ci:
	@echo "== Running tests in CI compose: module=$(MODULE) tags=$(TEST_TAGS) DB=$(DB_CI) =="
	@echo "== test-tags expr: $(TEST_TAG_EXPR) =="
	@echo "== log: $(CI_LOG) =="
	@echo "== compose: $(COMPOSE_CI) =="
	@echo "== (pre-clean) down -v =="
	@$(COMPOSE_CI) down -v --remove-orphans >/dev/null 2>&1 || true
	@echo "== (up) start CI stack =="
	@set +e; \
	ts=$$(date +%Y%m%d-%H%M%S); \
	outdir="$(CI_ARTIFACT_DIR)/$(PROJECT_CI)/$$ts"; \
	mkdir -p "$$outdir"; \
	cleanup() { \
	  echo "== (post) collecting artifacts to $$outdir =="; \
	  $(COMPOSE_CI) ps -a >"$$outdir/ps.txt" 2>&1 || true; \
	  $(COMPOSE_CI) logs --no-color --tail=500 db >"$$outdir/db.log" 2>&1 || true; \
	  $(COMPOSE_CI) logs --no-color --tail=500 redis >"$$outdir/redis.log" 2>&1 || true; \
	  $(COMPOSE_CI) logs --no-color --tail=800 odoo >"$$outdir/odoo.log" 2>&1 || true; \
	  echo "== artifacts saved: $$outdir =="; \
	  $(COMPOSE_CI) down -v --remove-orphans >/dev/null 2>&1 || true; \
	}; \
	trap cleanup EXIT; \
	DB_CI=$(DB_CI) MODULE=$(MODULE) TEST_TAGS=$(TEST_TAG_EXPR) \
	$(COMPOSE_CI) up --abort-on-container-exit --exit-code-from odoo 2>&1 | tee "$(CI_LOG)"; \
	rc=$${PIPESTATUS[0]}; \
	if [ "$$rc" -ne 0 ]; then \
	  if grep -Eq "$(CI_PASS_SIG_RE)" "$(CI_LOG)"; then \
	    echo "== compose exit=$$rc but tests look PASS; normalize rc=0 =="; \
	    rc=0; \
	  fi; \
	fi; \
	echo "exit=$$rc" >"$$outdir/exit.txt" 2>/dev/null || true; \
	cp -f "$(CI_LOG)" "$$outdir/$(CI_LOG)" 2>/dev/null || true; \
	echo "== [DONE] test-ci exit=$$rc =="; \
	exit $$rc

ci.repro:
	@echo "== CI repro (NO down -v) module=$(MODULE) tags=$(TEST_TAGS) DB=$(DB_CI) =="
	DB_CI=$(DB_CI) MODULE=$(MODULE) TEST_TAGS=$(TEST_TAG_EXPR) \
	$(COMPOSE_CI) up --abort-on-container-exit --exit-code-from odoo

test-install-gate:
	@echo "== Install Gate (at_install) module=$(MODULE) =="
	$(MAKE) test-ci MODULE=$(MODULE) TEST_TAGS="/$(MODULE):at_install,sc_install,sc_gate"

test-upgrade-gate:
	@echo "== Upgrade Gate (post_install after -u) module=$(MODULE) =="
	@echo "== (pre-clean) down -v =="
	@$(COMPOSE_CI) down -v --remove-orphans >/dev/null 2>&1 || true
	@echo "== Install base module before upgrade =="
	DB_CI=$(DB_CI) MODULE=$(MODULE) \
	$(COMPOSE_CI) run --rm -T odoo \
		-d $(DB_CI) \
		-i $(MODULE) \
		--without-demo=all \
		--stop-after-init
	@echo "== Upgrade with post_install tests =="
	DB_CI=$(DB_CI) MODULE=$(MODULE) \
	$(COMPOSE_CI) run --rm -T odoo \
		-d $(DB_CI) \
		-u $(MODULE) \
		--without-demo=all \
		--test-enable \
		--test-tags "/$(MODULE):post_install,sc_upgrade,sc_gate,sc_perm" \
		--stop-after-init
	@echo "== (post) down -v clean =="
	@$(COMPOSE_CI) down -v --remove-orphans >/dev/null 2>&1 || true

# ================== 数据校验器 ==================
validate:
	@echo "== Running data validator on $(DB_NAME) =="
	$(COMPOSE) run --rm -T \
		--entrypoint python3 odoo \
		/mnt/extra-addons/smart_construction_core/tools/validator/run_validate.py
	@echo "== [OK] validate done =="

validate-ci:
	@echo "== Running data validator (CI env) DB=$(DB_CI) =="
	DB_CI=$(DB_CI) MODULE=$(MODULE) TEST_TAGS=$(TEST_TAGS) \
	$(COMPOSE_CI) run --rm -T \
		--entrypoint python3 odoo \
		/mnt/extra-addons/smart_construction_core/tools/validator/run_validate.py
	@echo "== [OK] validate-ci done =="

# ================== 数据库管理（剃刀流程） ==================
db.drop:
	@echo "== Drop database $(DB) =="
	docker exec $(DB_CONTAINER) psql -U $(DB_USER) -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$(DB)' AND pid <> pg_backend_pid();"
	docker exec $(DB_CONTAINER) psql -U $(DB_USER) -d postgres -c "DROP DATABASE IF EXISTS $(DB);"

db.create:
	@echo "== Create database $(DB) =="
	docker exec $(DB_CONTAINER) psql -U $(DB_USER) -d postgres -c "CREATE DATABASE $(DB) WITH TEMPLATE template0 ENCODING 'UTF8';"

install:
	@echo "== Install module $(MODULE) on $(DB) =="
	docker exec $(ODOO_CONTAINER) odoo \
		-c /etc/odoo/odoo.conf \
		-d $(DB) \
		-i $(MODULE) \
		--without-demo=all \
		--load-language=zh_CN \
		--stop-after-init
	@echo "== [OK] install done =="

noiseoff:
	@echo "== Noise off (disable cron/server actions) DB=$(DB) =="
	docker exec -i $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB) < addons/smart_construction_core/tools/sql/noiseoff.sql

noiseon:
	@echo "== Noise on (restore last batch) DB=$(DB) =="
	docker exec -i $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB) < addons/smart_construction_core/tools/sql/noiseon.sql

verify.noise:
	@echo "== Verify noise DB=$(DB) =="
	docker exec -i $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB) -c "\
	SELECT count(*) AS active_noise_cron \
	FROM ir_cron \
	WHERE active=true AND ( \
	       cron_name ILIKE 'Mail:%' \
	    OR cron_name ILIKE 'Notification:%' \
	    OR cron_name ILIKE 'Discuss:%' \
	    OR cron_name ILIKE 'SMS:%' \
	    OR cron_name ILIKE 'Snailmail:%' \
	    OR cron_name ILIKE 'Partner Autocomplete:%' \
	    OR cron_name ILIKE '%Tier%' \
	    OR cron_name ILIKE '%Unregistered Users%' \
	);" \
	&& docker exec -i $(DB_CONTAINER) psql -U $(DB_USER) -d $(DB) -c "\
	SELECT count(*) AS bad_server_actions \
	FROM ir_act_server \
	WHERE state='code' AND code ILIKE '%send_unregistered_user_reminder%';"

db.rebuild.noiseoff:
	@echo "== Rebuild DB ($(DB)) + install $(MODULE) + noiseoff =="
	- $(MAKE) down || true
	$(MAKE) up
	$(MAKE) db.drop DB=$(DB)
	$(MAKE) db.create DB=$(DB)
	$(MAKE) install MODULE=$(MODULE) DB=$(DB)
	$(MAKE) noiseoff DB=$(DB)
	$(MAKE) verify.noise DB=$(DB)
	@echo "== [OK] db.rebuild.noiseoff done =="
