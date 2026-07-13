# ======================================================
# ==================== Guards ==========================
# ======================================================
.PHONY: check-compose-project check.compose.project check-compose-env check-external-addons check-odoo-conf diag.project gate.compose.config env.print.db env.matrix.check verify.environment.topology.guard verify.daily_dev.runtime_repo.clean verify.daily_dev.acceptance.env.guard

IS_PROD := 0
ifneq (,$(filter prod,$(ENV)))
IS_PROD := 1
endif
ifneq (,$(filter .env.prod,$(notdir $(ENV_FILE))))
IS_PROD := 1
endif

.PHONY: guard.prod.forbid guard.prod.readonly guard.prod.danger
guard.prod.forbid:
	@if [ "$(IS_PROD)" = "1" ]; then \
	  echo "❌ forbidden in prod (ENV=prod/ENV_FILE=.env.prod)"; \
	  exit 2; \
	fi

guard.prod.readonly:
	@if [ "$${PROD_READONLY_VERIFY:-}" != "1" ]; then \
	  echo "❌ prod readonly guard: set PROD_READONLY_VERIFY=1 to run this read-only production verifier"; \
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

env.print.db:
	@echo "$(DB_NAME)"

env.matrix.check:
	@set -e; \
	for env_name in dev test prod; do \
	  env_file=".env.$$env_name"; \
	  if [ ! -f "$$env_file" ]; then \
	    echo "❌ [env.matrix.check] missing $$env_file"; \
	    exit 2; \
	  fi; \
	  echo "[env.matrix.check] check $$env_file"; \
	  $(MAKE) --no-print-directory check-compose-env ENV="$$env_name" ENV_FILE="$$env_file"; \
	done; \
	explicit_db_out="$$(ENV=dev ENV_FILE=.env.dev $(MAKE) --no-print-directory -s DB_NAME=sc_matrix_probe env.print.db)"; \
	if [ "$$explicit_db_out" != "sc_matrix_probe" ]; then \
	  echo "❌ [env.matrix.check] DB_NAME precedence broken: expected sc_matrix_probe got '$$explicit_db_out'"; \
	  exit 2; \
	fi; \
	alias_db_out="$$(ENV=dev ENV_FILE=.env.dev $(MAKE) --no-print-directory -s DB=sc_matrix_alias env.print.db)"; \
	if [ "$$alias_db_out" != "sc_matrix_alias" ]; then \
	  echo "❌ [env.matrix.check] DB alias broken: expected sc_matrix_alias got '$$alias_db_out'"; \
	  exit 2; \
	fi; \
	legacy_db_out="$$(ENV=dev ENV_FILE=.env.dev $(MAKE) --no-print-directory -s BD=sc_matrix_legacy env.print.db)"; \
	if [ "$$legacy_db_out" != "sc_matrix_legacy" ]; then \
	  echo "❌ [env.matrix.check] BD alias broken: expected sc_matrix_legacy got '$$legacy_db_out'"; \
	  exit 2; \
	fi; \
	python3 scripts/verify/environment_topology_guard.py; \
	echo "✅ [env.matrix.check] PASS"

verify.environment.topology.guard:
	@python3 -m py_compile scripts/verify/environment_topology_guard.py
	@python3 scripts/verify/environment_topology_guard.py

verify.daily_dev.runtime_repo.clean:
	@bash scripts/ops/daily_dev_runtime_repo_guard.sh

verify.daily_dev.acceptance.env.guard:
	@python3 -m py_compile scripts/verify/daily_dev_acceptance_env_guard.py
	@ENV="$(ENV)" ENV_FILE="$(ENV_FILE)" DB_NAME="$(DB_NAME)" ACCEPTANCE_BASE_URL="$(ACCEPTANCE_BASE_URL)" ACCEPTANCE_LOGIN="$(ACCEPTANCE_LOGIN)" ACCEPTANCE_PASSWORD="$(ACCEPTANCE_PASSWORD)" ACCEPTANCE_NAV_MIN_ACTIONS="$(ACCEPTANCE_NAV_MIN_ACTIONS)" ACCEPTANCE_NAV_MAX_ACTIONS="$(ACCEPTANCE_NAV_MAX_ACTIONS)" ACCEPTANCE_NAV_FORBIDDEN_LABELS="$(ACCEPTANCE_NAV_FORBIDDEN_LABELS)" ACCEPTANCE_NAV_REQUIRED_PATHS="$(ACCEPTANCE_NAV_REQUIRED_PATHS)" ACCEPTANCE_NAV_REQUIRED_ACTIONS="$(ACCEPTANCE_NAV_REQUIRED_ACTIONS)" ACCEPTANCE_PROBE_OUTPUT="$(ACCEPTANCE_PROBE_OUTPUT)" FRONTEND_DIST_DIR="$(FRONTEND_DIST_DIR)" VITE_API_BASE_URL="$(VITE_API_BASE_URL)" VITE_API_PROXY_TARGET="$(VITE_API_PROXY_TARGET)" VITE_ODOO_DB="$(VITE_ODOO_DB)" VITE_ODOO_DB_LOCKED="$(VITE_ODOO_DB_LOCKED)" VITE_APP_ENV="$(VITE_APP_ENV)" VITE_BUILD_MODE="$(VITE_BUILD_MODE)" VITE_BUILD_OUT_DIR="$(VITE_BUILD_OUT_DIR)" VITE_DELIVERY_MODE="$(VITE_DELIVERY_MODE)" VITE_FEATURE_FLAGS="$(VITE_FEATURE_FLAGS)" VITE_LITE_CONTRACT_PILOT="$(VITE_LITE_CONTRACT_PILOT)" VITE_LITE_CONTRACT_ROLLOUT="$(VITE_LITE_CONTRACT_ROLLOUT)" VITE_PLATFORM_ADMIN_DB="$(VITE_PLATFORM_ADMIN_DB)" VITE_TENANT="$(VITE_TENANT)" python3 scripts/verify/daily_dev_acceptance_env_guard.py

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
