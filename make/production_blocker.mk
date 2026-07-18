BLOCKER_RUNTIME_IMAGE ?= sce-blocker-runtime:test
BLOCKER_MATRIX_ARTIFACTS ?= artifacts/production-blocker/migration-matrix

.PHONY: verify.production_blocker.capture_daily_dev_history verify.production_blocker.migration_unit verify.production_blocker.migration_matrix verify.production_blocker.history_upgrade verify.production_blocker.fresh_and_rollback verify.production_blocker.runtime_assets verify.production_blocker.image

verify.production_blocker.capture_daily_dev_history: guard.prod.forbid
	@bash scripts/verify/capture_daily_dev_history_snapshot.sh

verify.production_blocker.migration_unit:
	@python3 addons/smart_construction_seed/tests/test_demo_ownership_migration_safety.py
	@python3 -m py_compile \
		addons/smart_construction_seed/migrations/17.0.0.2.0/post-migration.py \
		addons/smart_construction_seed/migrations/17.0.0.2.1/post-migration.py \
		addons/smart_construction_seed/tests/test_demo_ownership_migration_safety.py \
		scripts/ops/demo_ownership_cleanup.py \
		scripts/verify/migration_safety_fingerprint.py

verify.production_blocker.migration_matrix: guard.prod.forbid verify.production_blocker.migration_unit
	@BLOCKER_RUNTIME_IMAGE="$(BLOCKER_RUNTIME_IMAGE)" BLOCKER_MATRIX_ARTIFACTS="$(BLOCKER_MATRIX_ARTIFACTS)" \
		bash scripts/verify/production_blocker_migration_matrix.sh

verify.production_blocker.history_upgrade: guard.prod.forbid
	@BLOCKER_RUNTIME_IMAGE="$(BLOCKER_RUNTIME_IMAGE)" bash scripts/verify/production_blocker_history_upgrade.sh

verify.production_blocker.fresh_and_rollback: guard.prod.forbid
	@BLOCKER_RUNTIME_IMAGE="$(BLOCKER_RUNTIME_IMAGE)" bash scripts/verify/production_blocker_fresh_and_rollback.sh

verify.production_blocker.runtime_assets: guard.prod.forbid
	@BLOCKER_RUNTIME_IMAGE="$(BLOCKER_RUNTIME_IMAGE)" bash scripts/verify/production_blocker_runtime_assets.sh

verify.production_blocker.image: guard.prod.forbid
	@BLOCKER_RUNTIME_IMAGE="$(BLOCKER_RUNTIME_IMAGE)" bash scripts/verify/production_blocker_image.sh
