# Material Plan Visible Note Coverage

Date: 2026-06-10
Database: `sc_demo`
Scope: user-confirmed formal menu `材料计划`

## Decision

`project.material.plan.legacy_visible_10` is covered by a targeted source-value gate.

The source field is the user-confirmed `备注` column from direct acceptance `材料计划`.
Non-empty source notes must be projected into:

- `project.material.plan.legacy_visible_10`
- `project.material.plan.line.note`
- `project.material.plan.line_note_summary`

Empty source notes remain empty. No synthetic backfill is allowed.

## Evidence

`DB_NAME=sc_demo scripts/ops/validate_material_plan_visible_note.sh`

- Source material-plan facts: 686
- Formal material plans: 686
- Source rows with non-empty notes: 133
- Source rows with empty notes: 553
- Projected source notes: 133
- Missing formal visible notes: 0
- Missing line notes: 0
- Missing line-note summaries: 0
- Status: PASS

`DB_NAME=sc_demo scripts/ops/validate_formal_business_release_gate.sh`

- User-confirmed menus: 62
- Checked records: 256844
- Checked fields: 862
- Mismatch fields: 0
- Material plan visible note gate: PASS
- Business capability gate: PASS
- Status: PASS

## Classification Impact

`python3 scripts/verify/visible_data_usability_warning_classification.py`

- `covered_by_material_plan_visible_note_gate`: 1
- Remaining model-specific business value gates: 2
  - `sc.construction.diary`: `legacy_visible_07`, `legacy_visible_08`
  - `sc.material.rfq`: `due_date`, `purchase_request_id`, `source_material_plan_id`

This removes `project.material.plan.legacy_visible_10` from the unresolved
model-specific business gap list without changing accepted user-visible data.
