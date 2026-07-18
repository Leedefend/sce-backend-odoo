RELEASE_DB ?= sc_release_rehearsal
RELEASE_RESTORE_DB ?= sc_release_rehearsal_restored
RELEASE_ROLLBACK_DB ?= sc_release_rehearsal_rollback
RELEASE_PROJECT ?= sc-release-rehearsal
RELEASE_ARTIFACTS ?= artifacts/release/frontend-pilot-readiness
RELEASE_COMPOSE = $(COMPOSE_BIN) -p $(RELEASE_PROJECT) -f docker-compose.yml -f docker-compose.release-rehearsal.yml
RELEASE_ENV = SC_ENVIRONMENT=release_rehearsal SC_ALLOW_DEMO_DATA=0 DB_NAME=$(RELEASE_DB) ODOO_DB=$(RELEASE_DB) ODOO_DBFILTER=^$(RELEASE_DB)$$ COMPOSE_PROJECT_NAME=$(RELEASE_PROJECT) DB_DATA=$(RELEASE_PROJECT)-db REDIS_DATA=$(RELEASE_PROJECT)-redis ODOO_DATA=$(RELEASE_PROJECT)-odoo ODOO_PORT=18087 NGINX_PORT=18086 FRONTEND_DIST_DIR=./frontend/apps/web/dist-release

.PHONY: verify.release.guard verify.release.tooling release.rehearsal.prepare release.rehearsal.build release.rehearsal.runtime.up release.rehearsal.upgrade verify.release.data_compatibility release.rehearsal.fingerprint release.rehearsal.backup release.rehearsal.filestore.recover release.rehearsal.restore release.rehearsal.rollback verify.release.rehearsal verify.release.monitoring release.rehearsal.cleanup release.production.acceptance release.production.acceptance.report release.readiness.report release.pilot.all

verify.release.guard:
	@SC_ENVIRONMENT=release_rehearsal SC_ALLOW_DEMO_DATA=0 DB_NAME=$(RELEASE_DB) python3 scripts/release/rehearsal_guard.py

verify.release.tooling:
	@python3 -m py_compile scripts/release/rehearsal_guard.py scripts/release/release_data_compatibility.py scripts/release/release_readiness_report.py scripts/release/release_acceptance_report.py scripts/release/release_monitoring_check.py scripts/release/release_fingerprint_compare.py scripts/release/test_rehearsal_guard.py scripts/verify/frontend_pilot_readiness_guard.py
	@python3 scripts/release/test_rehearsal_guard.py
	@node --check scripts/release/release_static_server.mjs
	@python3 scripts/verify/frontend_pilot_readiness_guard.py

release.rehearsal.prepare: verify.release.guard
	@mkdir -p $(RELEASE_ARTIFACTS)/backup $(RELEASE_ARTIFACTS)/fingerprints
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) down -v --remove-orphans
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) up -d --wait db redis odoo
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) exec -T odoo odoo -c /var/lib/odoo/odoo.conf -d $(RELEASE_DB) --no-http --workers=0 --max-cron-threads=0 -i smart_construction_custom --without-demo=all --stop-after-init

release.rehearsal.build:
	@VITE_ODOO_DB=$(RELEASE_DB) VITE_ODOO_DB_LOCKED=1 VITE_APP_ENV=release_rehearsal scripts/dev/pnpm_exec.sh -C frontend/apps/web exec vite build --outDir dist-release-rehearsal
	@mkdir -p $(RELEASE_ARTIFACTS)
	@find frontend/apps/web/dist-release-rehearsal -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $$1}' > $(RELEASE_ARTIFACTS)/frontend-candidate-build.sha256

release.rehearsal.runtime.up: verify.release.guard release.rehearsal.build
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) up -d --wait nginx
	@curl -fsS http://127.0.0.1:18086/login >/dev/null

release.rehearsal.upgrade: verify.release.guard
	@bash scripts/release/with_rehearsal_lock.sh $(RELEASE_DB) env $(RELEASE_ENV) $(RELEASE_COMPOSE) exec -T odoo odoo -c /var/lib/odoo/odoo.conf -d $(RELEASE_DB) --no-http --workers=0 --max-cron-threads=0 -u smart_core,smart_construction_core,smart_construction_custom --without-demo=all --stop-after-init

verify.release.data_compatibility: verify.release.guard
	@mkdir -p $(RELEASE_ARTIFACTS)
	@$(RELEASE_ENV) RELEASE_REPORT_PATH=/tmp/release-data-compatibility.json $(RELEASE_COMPOSE) exec -T -e RELEASE_REPORT_PATH odoo odoo shell -d $(RELEASE_DB) -c /var/lib/odoo/odoo.conf < scripts/release/release_data_compatibility.py
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) cp odoo:/tmp/release-data-compatibility.json $(RELEASE_ARTIFACTS)/data-compatibility.json >/dev/null

release.rehearsal.fingerprint: verify.release.guard
	@mkdir -p $(RELEASE_ARTIFACTS)/fingerprints
	@$(RELEASE_ENV) RELEASE_FINGERPRINT_PATH=/tmp/release-fingerprint.json $(RELEASE_COMPOSE) exec -T -e RELEASE_FINGERPRINT_PATH odoo odoo shell -d $(RELEASE_DB) -c /var/lib/odoo/odoo.conf < scripts/release/release_fingerprint.py
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) cp odoo:/tmp/release-fingerprint.json $(RELEASE_ARTIFACTS)/fingerprints/$${PHASE:-current}.json >/dev/null

release.rehearsal.backup: verify.release.guard
	@$(RELEASE_ENV) RELEASE_PROJECT=$(RELEASE_PROJECT) bash scripts/release/with_rehearsal_lock.sh $(RELEASE_DB) bash scripts/release/rehearsal_backup_restore.sh backup $(RELEASE_DB)

release.rehearsal.filestore.recover: verify.release.guard
	@$(RELEASE_ENV) RELEASE_PROJECT=$(RELEASE_PROJECT) bash scripts/release/with_rehearsal_lock.sh $(RELEASE_DB) bash scripts/release/rehearsal_backup_restore.sh recover-source $(RELEASE_DB)

release.rehearsal.restore: verify.release.guard
	@$(RELEASE_ENV) RELEASE_PROJECT=$(RELEASE_PROJECT) bash scripts/release/with_rehearsal_lock.sh $(RELEASE_DB) bash scripts/release/rehearsal_backup_restore.sh restore $(RELEASE_DB) $(RELEASE_RESTORE_DB)

release.rehearsal.rollback: verify.release.guard
	@$(RELEASE_ENV) RELEASE_PROJECT=$(RELEASE_PROJECT) bash scripts/release/with_rehearsal_lock.sh $(RELEASE_DB) bash scripts/release/rehearsal_backup_restore.sh rollback $(RELEASE_DB) $(RELEASE_ROLLBACK_DB)

verify.release.rehearsal: verify.release.data_compatibility
	@python3 scripts/release/release_fingerprint_compare.py
	@curl -fsS http://127.0.0.1:18087/web/health >/dev/null
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) exec -T db pg_isready -U $(DB_USER) -d $(RELEASE_DB)

verify.release.monitoring:
	@RELEASE_HEALTH_URL=http://127.0.0.1:18087/web/health RELEASE_ARTIFACTS=$(RELEASE_ARTIFACTS) python3 scripts/release/release_monitoring_check.py

release.production.acceptance:
	@bash scripts/release/production_acceptance.sh

release.production.acceptance.report:
	@python3 scripts/release/release_acceptance_report.py

release.readiness.report:
	@python3 scripts/release/release_readiness_report.py

release.pilot.all: verify.release.tooling release.rehearsal.prepare release.rehearsal.runtime.up release.rehearsal.upgrade verify.release.rehearsal release.rehearsal.backup release.rehearsal.restore release.rehearsal.rollback verify.release.monitoring release.production.acceptance release.readiness.report

release.rehearsal.cleanup: verify.release.guard
	@$(RELEASE_ENV) $(RELEASE_COMPOSE) down --remove-orphans

# Immutable production candidate. These targets are restricted to dev/test and
# never point at the production database or production compose project.
CANDIDATE_SOURCE_SHA ?= f465613835c15827cbb511d097c235928ba6083e
CANDIDATE_SHORT_SHA := $(shell printf '%s' '$(CANDIDATE_SOURCE_SHA)' | cut -c1-12)
CANDIDATE_IMAGE ?= sce-production-candidate:$(CANDIDATE_SHORT_SHA)
CANDIDATE_PROJECT ?= sc-production-candidate
CANDIDATE_DB ?= sc_user_data_rehearsal_candidate
HISTORY_SOURCE_DB ?= sc_demo
HISTORY_SOURCE_BACKUP ?= artifacts/production-blocker/source/daily-dev-history-source-backup
DAILY_DEV_PROJECT ?= sc-backend-odoo-dev
CANDIDATE_ARTIFACTS ?= artifacts/release/immutable-production-candidate-v1

.PHONY: release.production.readonly_baseline release.candidate.build release.candidate.scan
.PHONY: release.history.source_probe release.history.backup release.history.restore release.history.upgrade
.PHONY: release.history.source_restore
.PHONY: release.history.runtime_up release.history.runtime_down release.history.fingerprint.source_pre
.PHONY: release.history.fingerprint.candidate_pre release.history.fingerprint.candidate_post

release.production.readonly_baseline: guard.prod.readonly check-compose-project check-compose-env
	@CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" bash scripts/release/production_readonly_baseline.sh

release.candidate.build: guard.prod.forbid
	@CANDIDATE_SOURCE_SHA="$(CANDIDATE_SOURCE_SHA)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" bash scripts/release/immutable_candidate_build.sh

release.candidate.scan: guard.prod.forbid
	@CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" bash scripts/release/immutable_candidate_scan.sh

release.history.source_probe: guard.prod.forbid check-compose-project check-compose-env
	@HISTORY_SOURCE_DB="$(HISTORY_SOURCE_DB)" HISTORY_SOURCE_BACKUP="$(HISTORY_SOURCE_BACKUP)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_history.sh source-probe

release.history.source_restore: guard.prod.forbid check-compose-project check-compose-env
	@HISTORY_SOURCE_DB="$(HISTORY_SOURCE_DB)" DAILY_DEV_PROJECT="$(DAILY_DEV_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" bash scripts/release/restore_authorized_history_source.sh

release.history.backup: guard.prod.forbid check-compose-project check-compose-env
	@HISTORY_SOURCE_DB="$(HISTORY_SOURCE_DB)" HISTORY_SOURCE_BACKUP="$(HISTORY_SOURCE_BACKUP)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_history.sh backup

release.history.restore: guard.prod.forbid check-compose-project check-compose-env
	@HISTORY_SOURCE_DB="$(HISTORY_SOURCE_DB)" CANDIDATE_DB="$(CANDIDATE_DB)" CANDIDATE_PROJECT="$(CANDIDATE_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_history.sh restore

release.history.upgrade: guard.prod.forbid check-compose-project check-compose-env
	@CANDIDATE_DB="$(CANDIDATE_DB)" CANDIDATE_PROJECT="$(CANDIDATE_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" CANDIDATE_FORMAL_MODULES="$${CANDIDATE_FORMAL_MODULES:-smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom}" bash scripts/release/production_candidate_history.sh upgrade

release.history.runtime_up: guard.prod.forbid check-compose-project check-compose-env
	@CANDIDATE_DB="$(CANDIDATE_DB)" CANDIDATE_PROJECT="$(CANDIDATE_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_history.sh runtime-up

release.history.runtime_down: guard.prod.forbid check-compose-project check-compose-env
	@CANDIDATE_DB="$(CANDIDATE_DB)" CANDIDATE_PROJECT="$(CANDIDATE_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_history.sh runtime-down

release.history.fingerprint.source_pre: guard.prod.forbid check-compose-project check-compose-env
	@HISTORY_SOURCE_DB="$(HISTORY_SOURCE_DB)" DAILY_DEV_PROJECT="$(DAILY_DEV_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_fingerprint.sh source source-pre

release.history.fingerprint.candidate_pre: guard.prod.forbid check-compose-project check-compose-env
	@CANDIDATE_DB="$(CANDIDATE_DB)" CANDIDATE_PROJECT="$(CANDIDATE_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_fingerprint.sh candidate candidate-pre

release.history.fingerprint.candidate_post: guard.prod.forbid check-compose-project check-compose-env
	@CANDIDATE_DB="$(CANDIDATE_DB)" CANDIDATE_PROJECT="$(CANDIDATE_PROJECT)" CANDIDATE_ARTIFACTS="$(CANDIDATE_ARTIFACTS)" CANDIDATE_IMAGE="$(CANDIDATE_IMAGE)" bash scripts/release/production_candidate_fingerprint.sh candidate candidate-post
