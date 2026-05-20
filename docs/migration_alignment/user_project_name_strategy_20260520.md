# User Project Name Strategy Baseline 2026-05-20

## Scope

The user-provided workbook `副本项目名称统计表直营41条，联营693条(1).xlsx`
is treated as the confirmed baseline for two user-facing project fields:

- project name
- operation strategy: `公司直营 -> direct`, `公司联营 -> joint`

It is not a business-fact linkage source. The workbook has no legacy project id,
contract id, customer, project code, or other stable business identity.

## Boundary

`scripts/migration/user_project_name_strategy_sync.py` enforces this boundary:

- exact normalized project-name matches only;
- update only `project.project.name` and `project.project.operation_strategy`;
- never rewrite `project_id`, `legacy_project_id`, contract links, payment links,
  SCBS mappings, or other business-fact relationships;
- missing source names and duplicate project-name matches are exported for manual
  review instead of being auto-created or merged.

Stored user-visible `operation_strategy` projections can be synchronized after
the project baseline with:

```bash
ARTIFACT_ROOT=/tmp/visible_data_usability_closure \
docker exec -i sc-backend-odoo-dev-odoo-1 \
  odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf \
  < scripts/migration/visible_surface_operation_strategy_sync_write.py
```

This projection step aligns displayed strategy values on existing business
records; it does not change their project linkage.

## Current Local Evidence

On `sc_demo`, the first application produced:

- source rows: 734
- source counts: `direct=41`, `joint=693`
- exact project-name matches: 710
- missing source names: 14
- duplicate project-name review rows: 22
- existing projects outside the user source: 187
- project baseline writes: 1
- post-apply dry-run writes: 0

The one automatic write was:

- `2023年高标准农田改造提升-东美村`: `joint -> direct`

Project counts after apply:

- total: 897
- active: 714
- direct: 47
- joint: 850

## Business Evidence Probe

Use the read-only probe to verify whether the user-confirmed names have
business-fact backing:

```bash
docker exec -i sc-backend-odoo-dev-odoo-1 \
  odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf \
  < scripts/migration/user_project_business_evidence_probe.py
```

The probe checks project ids against strong business-fact tables, including
contract, payment, receipt, treasury, material, settlement, tender, and SCBS
staging tables. It also searches common legacy project-name fields for source
names that do not match `project.project`.

Current local evidence on `sc_demo`:

- matched source names: 720
- source names with business evidence: 715
- source names matched but without strong business evidence: 5
- source names missing from `project.project`: 14
- missing source names with exact legacy text evidence: 1
- missing source names without exact legacy text evidence: 13
- duplicate source names requiring canonical-project review: 10

This means the workbook is mostly backed by business facts after joining
through existing `project.project` records, but the missing 14 names still
cannot be treated as business-linked projects without another identifier or
manual alias decision. The one missing name with text evidence is backed only
by a legacy tender-registration project-name field, not by a resolved
`project.project` id.
