# Material RFQ Source Coverage

Date: 2026-06-10
Database: `sc_demo`
Scope: user-confirmed formal menu `报价单` / formal business menu `询比价`

## Decision

Historical `报价单` rows are projected to formal `sc.material.rfq`.

For formal source fields:

- `source_material_plan_id`: backfill only when the legacy `GLYWID` plus material name plus spec matches exactly one formal material plan.
- `purchase_request_id`: keep empty for accepted legacy rows because the accepted source does not carry a stable purchase-request reference.
- `due_date`: keep empty for accepted legacy rows because the accepted source does not carry a distinct quote deadline. Do not copy `rfq_date` into `due_date`.

This preserves accepted user-visible quote data and avoids inventing upstream process data.

## Evidence

`DB_NAME=sc_demo scripts/ops/backfill_material_rfq_source_plan.sh`

- Linked unique source-plan matches: 24
- Rows without plan source: 95
- Rows with plan source but no unique material/spec match: 7
- Status: PASS

`DB_NAME=sc_demo scripts/ops/validate_material_rfq_source_coverage.sh`

- Source quote facts: 126
- Formal RFQs: 126
- Source deadline count: 0
- Source purchase-request reference count: 0
- Unique material-plan matches: 24
- Linked material-plan matches: 24
- Linked material-plan line matches: 24
- Failures: 0
- Status: PASS

`DB_NAME=sc_demo scripts/ops/validate_formal_business_release_gate.sh`

- User-confirmed menus: 62
- Checked records: 256844
- Checked fields: 862
- Mismatch fields: 0
- Material RFQ source coverage gate: PASS
- Business capability gate: PASS
- Status: PASS

## Classification Impact

`python3 scripts/verify/visible_data_usability_warning_classification.py`

- `covered_by_material_rfq_source_coverage_gate`: 1
- Remaining model-specific business value gates: 1
  - `sc.construction.diary`: `legacy_visible_07`, `legacy_visible_08`

This removes `sc.material.rfq.due_date`, `sc.material.rfq.purchase_request_id`,
and `sc.material.rfq.source_material_plan_id` from the unresolved
model-specific business gap list. Only source-proven relationships are written.
