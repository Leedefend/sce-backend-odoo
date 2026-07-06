# Form Productization Release Candidate 20260707

## 1. Candidate Identity

| Item | Value |
| --- | --- |
| Candidate ID | `form_productization_20260707` |
| Source PR | `#1007 Productize formal business form surfaces` |
| Target branch | `main` |
| Target commit | `0cffcde58cf86d48e250f820034bb19946766c6c` |
| Previous production deployment record | `docs/ops/releases/current/production_deployment_20260705_prod_closure.md` |
| Previous recorded production target | `dirty workspace incremental release package` |
| Candidate status | `deployed to production on 2026-07-07; see production_deployment_20260707_form_productization.md` |
| Local package path | `artifacts/release/form_productization_20260707/form_productization_20260707.tar.gz` |
| Local package sha256 | `5f07470fdecb9df334fb91492bf97190281329e9e42a07c13c78ca64a0854f0c` |

This document is the release candidate scope record.  The concrete production
deployment evidence is recorded in
`docs/ops/releases/current/production_deployment_20260707_form_productization.md`.

## 2. Release Scope

This candidate prepares the next incremental production package for formal
business form productization:

- Product-release form contracts for formal business entries.
- Productization audit semantics that separate risk from acceptance evidence.
- Runtime cleanup for productized form preference overlays.
- Product delivery package/readiness evidence refresh.
- Delivery readiness scoreboard refresh stabilization.

Expected deployment type: `incremental package`.

Expected module upgrade set:

```text
smart_core
smart_construction_core
smart_construction_custom
```

No production write has been performed for this candidate.

## 2.1 Local Package Build Evidence

Local package directory:

```text
artifacts/release/form_productization_20260707/package
```

Local package tarball:

```text
artifacts/release/form_productization_20260707/form_productization_20260707.tar.gz
```

Tarball sha256:

```text
5f07470fdecb9df334fb91492bf97190281329e9e42a07c13c78ca64a0854f0c  artifacts/release/form_productization_20260707/form_productization_20260707.tar.gz
```

Package contents:

```text
package/changed_files.txt
package/SHA256SUMS
package/OPERATOR_COMMANDS.sh
package/VALIDATION_MATRIX.md
package/PROD_STATUS_CURRENT.txt
package/PRODUCTION_HANDOFF_RUNBOOK.md
package/README.md
package/files/
```

Local package verification:

```text
(cd artifacts/release/form_productization_20260707/package && sha256sum -c SHA256SUMS)
result=PASS
checked_files=39
```

`PROD_STATUS_CURRENT.txt` intentionally states that production status has not
yet been fetched for this candidate.  It must be replaced or supplemented
during the production release window with live production evidence.

## 3. Changed Files

Diff range:

```text
5e6eef9488c892a209008778d3473b7d91b8efb6..0cffcde58cf86d48e250f820034bb19946766c6c
```

Tracked changed file count: `39`.

```text
Makefile
addons/smart_construction_core/__manifest__.py
addons/smart_construction_core/data/construction_plan_form_productization_contract.xml
addons/smart_construction_core/data/document_admin_form_productization_contract.xml
addons/smart_construction_core/data/equipment_request_settlement_form_productization_contract.xml
addons/smart_construction_core/data/equipment_usage_form_productization_contract.xml
addons/smart_construction_core/data/expense_claim_form_productization_contract.xml
addons/smart_construction_core/data/financing_loan_form_productization_contract.xml
addons/smart_construction_core/data/hr_payroll_form_productization_contract.xml
addons/smart_construction_core/data/invoice_input_form_productization_contract.xml
addons/smart_construction_core/data/invoice_output_tax_form_productization_contract.xml
addons/smart_construction_core/data/labor_equipment_plan_attendance_form_productization_contract.xml
addons/smart_construction_core/data/labor_request_settlement_form_productization_contract.xml
addons/smart_construction_core/data/labor_usage_form_productization_contract.xml
addons/smart_construction_core/data/office_admin_form_productization_contract.xml
addons/smart_construction_core/data/payment_execution_actual_outflow_form_productization_contract.xml
addons/smart_construction_core/data/payment_request_form_productization_contract.xml
addons/smart_construction_core/data/purchase_order_form_productization_contract.xml
addons/smart_construction_core/data/receipt_income_form_productization_contract.xml
addons/smart_construction_core/data/remaining_p2_form_productization_contract.xml
addons/smart_construction_core/data/remaining_p3_form_productization_contract.xml
addons/smart_construction_core/data/settlement_adjustment_form_productization_contract.xml
addons/smart_construction_core/data/settlement_order_form_productization_contract.xml
addons/smart_construction_core/data/subcontract_register_settlement_form_productization_contract.xml
addons/smart_construction_core/data/subcontract_request_form_productization_contract.xml
addons/smart_construction_core/data/tax_deduction_certificate_form_productization_contract.xml
addons/smart_construction_core/data/tender_bid_form_productization_contract.xml
addons/smart_construction_core/tests/test_approval_policy_configuration_handler.py
addons/smart_construction_custom/__manifest__.py
addons/smart_construction_custom/data/productized_form_runtime_cleanup.xml
addons/smart_construction_custom/models/user_preferences.py
addons/smart_core/tests/test_backend_contract_boundaries.py
addons/smart_core/utils/backend_contract_boundaries.py
docs/ops/audit/product_delivery_package_manifest.md
docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md
docs/product/formal_business_form_productization_standard_v1.md
scripts/verify/business_form_productization_audit.py
scripts/verify/delivery_readiness_scoreboard_refresh.py
scripts/verify/python_http_smoke_utils.py
```

## 4. Local Main Validation Evidence

Executed after PR merge on local `main`:

```text
make verify.business_form.productization.audit
python3 scripts/verify/product_delivery_scoreboard_final_closeout_guard.py
make verify.product.delivery.productization.readiness.strict
make verify.production_release.flow.guard
git diff --check
```

Latest form productization audit:

```text
formal_business_entries=81
by_severity={"PASS": 81}
risk_entry_count=0
p1_entry_count=0
productized_entry_count=78
productized_pass_count=78
productized_status_context_count=78
productized_contract_structure_evidence_count=78
source_trace_sectioned_count=68
```

Additional pre-merge evidence from PR #1007:

```text
make verify.backend.contract.closure.mainline PASS
make verify.restricted PASS
make verify.product.delivery.productization.readiness PASS
make verify.product.delivery.productization.readiness.strict PASS
make verify.product.delivery.gap PASS
make verify.product.delivery.v1.map PASS
make export.product.delivery.package PASS
make verify.production_deployment.record.guard PASS
```

## 5. Production Release Requirements

Before this candidate can be deployed to production, execute the standard
production release chain:

1. Verify the local incremental release package sha256 and `SHA256SUMS`.
2. Confirm the package includes at minimum:
   - `changed_files.txt`
   - `SHA256SUMS`
   - `OPERATOR_COMMANDS.sh`
   - `VALIDATION_MATRIX.md`
   - `PROD_STATUS_CURRENT.txt`
   - `PRODUCTION_HANDOFF_RUNBOOK.md`
3. Restore the latest production database and filestore backup into prod-sim.
4. Apply the candidate package in prod-sim.
5. Upgrade `smart_core`, `smart_construction_core`, and `smart_construction_custom`.
6. Run the prod-sim validation matrix.
7. Create a concrete production deployment record from
   `docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md`.
8. Only after prod-sim PASS, execute production package application with a fresh
   production backup.

## 6. Required Production Validation Matrix

Minimum production post-deploy commands:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.baseline
SC_LOGIN_ENV_EXPECTED=prod ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.p0
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.business_full
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.role_matrix
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod make verify.non_demo_data_contamination
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.business_system.usability_readiness.prod
```

Then confirm:

```text
smart_construction_demo XMLID count=0
smart_construction_demo|uninstalled|
service state=running healthy
```

## 7. Explicit Non-Claims

- This candidate does not mean production has been upgraded.
- This candidate does not mean production and local `main` are full-tree aligned.
- This candidate does not replace prod-sim replay.
- This candidate does not replace a concrete production deployment record.

## 8. Next Action

Proceed with release package construction and prod-sim replay from the latest
production backup.  If prod-sim passes, create the concrete production
deployment record and execute the production window according to
`docs/ops/production_release_flow_standard_v1.md`.
