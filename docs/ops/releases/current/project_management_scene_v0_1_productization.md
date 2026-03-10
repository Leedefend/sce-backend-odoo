# project.management Productization Flow v0.1

## Objective
- Deliver a repeatable, auditable productization flow for `project.management` scene.
- Ensure contract/runtime/evidence remain stable under continuous iteration.

## Single Entry
- Command:
  - `make verify.project.management.productization`
- This command includes:
  - `make verify.project.dashboard.contract`
  - `make verify.project.dashboard.snapshot`
  - `python3 scripts/verify/project_management_productization_flow_guard.py`

## Acceptance Entry
- Command:
  - `make verify.project.management.acceptance`
- This command includes:
  - `make verify.project.management.productization`
  - `python3 scripts/verify/project_management_productization_acceptance_export.py`

## Evidence Outputs
- Snapshot:
  - `tmp/project_dashboard_contract_snapshot_v1.json`
- Verification evidence:
  - `tmp/project_dashboard_verification_evidence_v1.json`
- Productization flow report:
  - `tmp/project_management_productization_flow_report.json`
  - `tmp/project_management_productization_flow_report.md`
- Acceptance report:
  - `tmp/project_management_scene_v0_1_acceptance_report.json`
  - `tmp/project_management_scene_v0_1_acceptance_report.md`

## Release Gate (v0.1)
- Scene and contract docs exist:
  - scene XML, route doc, contract doc, block contract doc, mapping v2 JSON
- Runtime chain exists:
  - intent handler, service, 7 block builders
- Snapshot and evidence are exported and consistent
- Zone/block cardinality remains stable:
  - 7 zones, 7 builders, 7 mapping rows

## Current Scope
- Backend orchestration + guard suite + evidence chain.
- Frontend page rendering migration is out of this v0.1 flow scope.
