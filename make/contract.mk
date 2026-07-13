# ======================================================
# ================== Contract ==========================
# ======================================================
.PHONY: contract.export contract.export_all contract.catalog.export contract.evidence.export verify.contract.catalog verify.scene.contract.shape verify.contract.evidence gate.contract gate.contract.bootstrap gate.contract.bootstrap-pass

INTENT_SURFACE_MD ?= artifacts/intent_surface_report.md
INTENT_SURFACE_JSON ?= artifacts/intent_surface_report.json
CONTRACT_PREFLIGHT_INTENT_SURFACE_MD ?= artifacts/intent_surface_report.md
CONTRACT_PREFLIGHT_INTENT_SURFACE_JSON ?= artifacts/intent_surface_report.json
CONTRACT_PREFLIGHT_CONTINUE_FROM_FAILURE ?= 0

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
