# ======================================================
# ==================== Dev =============================
# ======================================================
.PHONY: up down restart logs ps odoo-shell prod.restart.safe prod.restart.full deploy.prod.sim.oneclick prod.sim.fresh.replay prod.sim.data.replay prod.sim.business.usable.init prod.sim.replay.then.usable.init prod.sim.replay.then.project frontend.dev frontend.stop frontend.restart frontend.logs verify.dev.acceptance.release release.dev.acceptance.publish release.daily_dev.acceptance.publish
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

FRONTEND_DEV_LOG ?= /tmp/sc-frontend-dev.log
FRONTEND_DEV_PID ?= /tmp/sc-frontend-dev.pid

frontend.dev: guard.prod.forbid
	@FRONTEND_PROFILE=$${FRONTEND_PROFILE:-daily} \
	  FRONTEND_DEV_PIDFILE="$(FRONTEND_DEV_PID)" \
	  FRONTEND_DEV_LOGFILE="$(FRONTEND_DEV_LOG)" \
	  bash scripts/dev/frontend_dev_reset.sh

frontend.stop: guard.prod.forbid
	@echo "[frontend.stop] stopping frontend dev server"
	@if [ -f "$(FRONTEND_DEV_PID)" ]; then \
		pid="$$(cat "$(FRONTEND_DEV_PID)" 2>/dev/null || true)"; \
		if [ -n "$$pid" ] && kill -0 "$$pid" 2>/dev/null; then \
			kill "$$pid" 2>/dev/null || true; \
			echo "[frontend.stop] killed pid=$$pid"; \
		fi; \
	fi
	@pids=""; \
	if command -v lsof >/dev/null 2>&1; then \
		pids="$$(lsof -tiTCP:5174 -sTCP:LISTEN 2>/dev/null || true)"; \
	elif command -v ss >/dev/null 2>&1; then \
		pids="$$(ss -ltnp 2>/dev/null | awk '$$4 ~ /:5174$$/ {print $$NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"; \
	fi; \
	if [ -n "$$pids" ]; then \
		for pid in $$pids; do kill "$$pid" 2>/dev/null || true; echo "[frontend.stop] killed listener pid=$$pid"; done; \
	else \
		echo "[frontend.stop] no listener on :5174"; \
	fi
	@rm -f "$(FRONTEND_DEV_PID)"

frontend.restart: guard.prod.forbid
	@FRONTEND_PROFILE=$${FRONTEND_PROFILE:-daily} \
	  FRONTEND_DEV_PIDFILE="$(FRONTEND_DEV_PID)" \
	  FRONTEND_DEV_LOGFILE="$(FRONTEND_DEV_LOG)" \
	  bash scripts/dev/frontend_dev_reset.sh
	@echo "[frontend.restart] done"

frontend.logs:
	@echo "[frontend.logs] $(FRONTEND_DEV_LOG)"
	@tail -n 120 "$(FRONTEND_DEV_LOG)" || true

ACCEPTANCE_BASE_URL ?= http://127.0.0.1:$(NGINX_PORT)
ACCEPTANCE_PROBE_OUTPUT ?= artifacts/backend/dev_acceptance_release_probe.json
ACCEPTANCE_LOGIN ?=
ACCEPTANCE_PASSWORD ?=
ACCEPTANCE_NAV_MIN_ACTIONS ?=
ACCEPTANCE_NAV_MAX_ACTIONS ?=
ACCEPTANCE_NAV_FORBIDDEN_LABELS ?=
ACCEPTANCE_NAV_REQUIRED_PATHS ?=
ACCEPTANCE_NAV_REQUIRED_ACTIONS ?=

verify.dev.acceptance.release: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) DB_NAME=$(DB_NAME) ACCEPTANCE_BACKUP_DIR="$(ACCEPTANCE_BACKUP_DIR)" ACCEPTANCE_BASE_URL="$(ACCEPTANCE_BASE_URL)" ACCEPTANCE_LOGIN="$(ACCEPTANCE_LOGIN)" ACCEPTANCE_PASSWORD="$(ACCEPTANCE_PASSWORD)" ACCEPTANCE_NAV_MIN_ACTIONS="$(ACCEPTANCE_NAV_MIN_ACTIONS)" ACCEPTANCE_NAV_MAX_ACTIONS="$(ACCEPTANCE_NAV_MAX_ACTIONS)" ACCEPTANCE_NAV_FORBIDDEN_LABELS="$(ACCEPTANCE_NAV_FORBIDDEN_LABELS)" ACCEPTANCE_NAV_REQUIRED_PATHS="$(ACCEPTANCE_NAV_REQUIRED_PATHS)" ACCEPTANCE_NAV_REQUIRED_ACTIONS="$(ACCEPTANCE_NAV_REQUIRED_ACTIONS)" ACCEPTANCE_PROBE_OUTPUT="$(ACCEPTANCE_PROBE_OUTPUT)" python3 scripts/ops/dev_acceptance_release_probe.py
	@ACCEPTANCE_PROBE_OUTPUT="$(ACCEPTANCE_PROBE_OUTPUT)" python3 scripts/verify/dev_acceptance_release_probe_schema_guard.py

.PHONY: verify.dev.acceptance.release.schema.guard
verify.dev.acceptance.release.schema.guard: guard.prod.forbid
	@python3 -m py_compile scripts/verify/dev_acceptance_release_probe_schema_guard.py
	@ACCEPTANCE_PROBE_OUTPUT="$(ACCEPTANCE_PROBE_OUTPUT)" python3 scripts/verify/dev_acceptance_release_probe_schema_guard.py

release.dev.acceptance.publish: guard.prod.forbid check-compose-project check-compose-env verify.frontend.build verify.user_confirmed.formal_surface.locked verify.dev.acceptance.release
	@echo "[release.dev.acceptance.publish] PASS base_url=$(ACCEPTANCE_BASE_URL) db=$(DB_NAME) artifact=$(ACCEPTANCE_PROBE_OUTPUT)"

release.daily_dev.acceptance.publish: ACCEPTANCE_NAV_MIN_ACTIONS := 100
release.daily_dev.acceptance.publish: ACCEPTANCE_NAV_MAX_ACTIONS := 115
release.daily_dev.acceptance.publish: ACCEPTANCE_NAV_FORBIDDEN_LABELS := 用户核对菜单,用户数据验收,用户验收,直营项目系统菜单
release.daily_dev.acceptance.publish: ACCEPTANCE_NAV_REQUIRED_PATHS := 智慧施工管理平台 / 基础资料 / 客户,智慧施工管理平台 / 基础资料 / 供应商,智慧施工管理平台 / 项目中心 / 项目管理 / 项目台账,智慧施工管理平台 / 合同中心 / 支出合同台账 / 一般合同（公司）,智慧施工管理平台 / 施工管理 / 施工日志,智慧施工管理平台 / 物资与分包 / 材料管理 / 入库单,智慧施工管理平台 / 财务中心 / 收付款办理 / 支付申请,智慧施工管理平台 / 财务中心 / 资金往来办理 / 资金日报表,智慧施工管理平台 / 人事行政 / 项目管理人员工资登记,智慧施工管理平台 / 资料证照 / 公司资料存档,智慧施工管理平台 / 税务中心 / 进项发票,智慧施工管理平台 / 配置中心 / 低代码系统配置 / 菜单配置
release.daily_dev.acceptance.publish: ACCEPTANCE_NAV_REQUIRED_ACTIONS := 智慧施工管理平台 / 基础资料 / 客户=>786|智慧施工管理平台 / 基础资料 / 供应商=>787|智慧施工管理平台 / 项目中心 / 项目管理 / 项目台账=>506|智慧施工管理平台 / 合同中心 / 支出合同台账 / 一般合同（公司）=>669|智慧施工管理平台 / 施工管理 / 施工日志=>701|智慧施工管理平台 / 物资与分包 / 材料管理 / 入库单=>983|智慧施工管理平台 / 财务中心 / 收付款办理 / 支付申请=>780|智慧施工管理平台 / 财务中心 / 资金往来办理 / 资金日报表=>784|智慧施工管理平台 / 人事行政 / 项目管理人员工资登记=>862|智慧施工管理平台 / 资料证照 / 公司资料存档=>615|智慧施工管理平台 / 税务中心 / 进项发票=>756|智慧施工管理平台 / 配置中心 / 低代码系统配置 / 菜单配置=>841
release.daily_dev.acceptance.publish: guard.prod.forbid verify.daily_dev.acceptance.env.guard env.matrix.check verify.daily_dev.runtime_repo.clean release.dev.acceptance.publish
	@echo "[release.daily_dev.acceptance.publish] PASS base_url=$(ACCEPTANCE_BASE_URL) db=$(DB_NAME) head=$$(git rev-parse --short HEAD)"

prod.restart.safe: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/restart.sh

prod.restart.full: guard.prod.danger check-compose-project check-compose-env
	@$(RUN_ENV) bash scripts/dev/down.sh
	@$(RUN_ENV) bash scripts/dev/up.sh

deploy.prod.sim.oneclick: guard.prod.forbid check-compose-project check-compose-env gate.compose.config
	@$(RUN_ENV) COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml" bash scripts/deploy/prod_sim_oneclick.sh

prod.sim.fresh.replay: guard.prod.forbid check-compose-project check-compose-env gate.compose.config
	@$(RUN_ENV) ENV=test ENV_FILE=.env.prod.sim COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml" bash scripts/deploy/prod_sim_fresh_replay.sh

prod.sim.data.replay: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) ENV=test ENV_FILE=.env.prod.sim COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml" DB_NAME=$(DB_NAME) HISTORY_CONTINUITY_MODE=replay HISTORY_CONTINUITY_INCLUDE_FORMAL_PROJECTIONS=0 HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS="$(or $(HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS),1)" RUN_ID="$(RUN_ID)" HISTORY_CONTINUITY_START_AT="$(HISTORY_CONTINUITY_START_AT)" HISTORY_CONTINUITY_STOP_AFTER="$(HISTORY_CONTINUITY_STOP_AFTER)" MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" bash scripts/migration/history_continuity_oneclick.sh

prod.sim.business.usable.init: guard.prod.forbid check-compose-project check-compose-env
	@$(RUN_ENV) ENV=test ENV_FILE=.env.prod.sim COMPOSE_FILES="-f $(COMPOSE_FILE_BASE) -f docker-compose.prod-sim.yml" DB_NAME=$(DB_NAME) FORMAL_PROJECTION_ARTIFACT_ROOT="$(FORMAL_PROJECTION_ARTIFACT_ROOT)" MIGRATION_ARTIFACT_ROOT="$(MIGRATION_ARTIFACT_ROOT)" MIGRATION_REPLAY_DB_ALLOWLIST="$(or $(MIGRATION_REPLAY_DB_ALLOWLIST),$(DB_NAME))" bash scripts/migration/history_business_usable_init.sh

prod.sim.replay.then.usable.init: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) prod.sim.data.replay
	@$(MAKE) prod.sim.business.usable.init

prod.sim.replay.then.project: guard.prod.forbid check-compose-project check-compose-env
	@$(MAKE) prod.sim.replay.then.usable.init

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
