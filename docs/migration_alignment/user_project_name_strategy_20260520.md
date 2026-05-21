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

## Replayable Reconciliation Package

Use the package builder after the evidence probe when product/business users
need a closed review queue:

```bash
docker exec -i sc-backend-odoo-dev-odoo-1 \
  odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf \
  < scripts/migration/user_project_master_reconciliation_package.py
```

The package is read-only and emits:

- full package: `/tmp/project_master_stabilization/user_project_master_reconciliation_20260520_package.csv`
- missing-name review: `/tmp/project_master_stabilization/user_project_master_reconciliation_20260520_missing_review.csv`
- duplicate canonical review: `/tmp/project_master_stabilization/user_project_master_reconciliation_20260520_duplicate_canonical_review.csv`
- no-business-evidence review: `/tmp/project_master_stabilization/user_project_master_reconciliation_20260520_no_evidence_review.csv`
- summary: `/tmp/project_master_stabilization/user_project_master_reconciliation_20260520_result.json`

Current local package on `sc_demo`:

- `exact_with_business_evidence`: 705, proposed action `keep_confirmed`
- `duplicate_with_canonical_candidate`: 10, proposed action `confirm_canonical_project_before_write`
- `missing_no_business_evidence`: 13, proposed action `manual_alias_or_create_review`
- `missing_with_text_evidence`: 1, proposed action `manual_alias_or_create_review`
- `exact_without_business_evidence`: 5, proposed action `manual_business_evidence_review`

The package remains a review artifact. It must not be used to automatically
merge duplicate projects or relink business facts by name.

## Decision Template

After generating the review package, copy or mount the package directory to the
host and generate a fillable decision CSV:

```bash
PROJECT_MASTER_REVIEW_INPUT_DIR=/tmp/project_master_stabilization_host \
PROJECT_MASTER_REVIEW_DECISION_CSV=artifacts/project_master_stabilization/user_project_master_review_decisions_20260520.csv \
make project.master.user_review.decision_template
```

The decision template contains only unresolved rows:

- duplicate exact names: choose the canonical `project.project` carrier;
- missing names: decide whether to alias an existing project, create a project,
  exclude the row from the user baseline, or request more evidence;
- exact matches without strong business evidence: keep, exclude, or request more
  evidence.

Validate a filled decision CSV before any future write step consumes it:

```bash
PROJECT_MASTER_REVIEW_DECISION_CSV=artifacts/project_master_stabilization/user_project_master_review_decisions_20260520.csv \
make project.master.user_review.decision_validate
```

The validator is read-only. It checks decision values, required reviewer/time
metadata, and duplicate-candidate target IDs. Passing validation still does not
write projects, aliases, or business-fact links; it only establishes a bounded
input contract for a later explicit write script.

## 2026-05-21 User Decisions

The reviewed decision CSV is:

```text
migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv
```

This file is an ignored migration asset and should be treated as the local
user-reviewed input for the next explicit write step. The validated decision
counts are:

- duplicate exact names: 10 rows, use the recommended canonical project;
- exact matches without business evidence: 5 rows, exclude from the user
  baseline;
- missing names: 14 rows total, 13 rows excluded from the user baseline and
  one row aliased to an existing project.

For `周超工程（德阳二重工程项目）`, the business-fact carrier is
`project.project(360)`, `易静工程（德阳二重工程项目）`. The competing inactive
`周超零星工程` record, `project.project(694)`, has only three legacy invoice
registration lines and no contract, payment, receipt, treasury, material,
tender, or SCBS fact chain in the current `sc_demo` audit. Therefore the
approved decision is to retain the row as an alias/rename target of project
360, not to create a new project and not to use project 694 as the carrier.

Apply the reviewed decisions through the guarded write entrypoint:

```bash
PROJECT_MASTER_REVIEW_DECISION_CSV=migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv \
make project.master.user_review.decision_apply.dry_run

PROJECT_MASTER_REVIEW_DECISION_CSV=migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv \
make project.master.user_review.decision_apply
```

The write entrypoint updates only `project.project` master data. It can write
the accepted carrier's name, operation strategy, active state, and derived
project category; it can archive rejected duplicate/no-evidence project
candidates. It must not rewrite `project_id`, `legacy_project_id`, contract,
payment, SCBS, or other business-fact links.

When closing the user-visible project master baseline, also enforce that active
`project.project` rows are limited to the 716 accepted carriers:

```bash
ARCHIVE_OUT_OF_BASELINE=1 \
PROJECT_MASTER_REVIEW_DECISION_CSV=migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv \
make project.master.user_review.decision_apply.dry_run

ARCHIVE_OUT_OF_BASELINE=1 \
PROJECT_MASTER_REVIEW_DECISION_CSV=migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv \
make project.master.user_review.decision_apply
```

This archives active projects that are not in the confirmed user baseline. It
still does not delete projects or relink business facts.
