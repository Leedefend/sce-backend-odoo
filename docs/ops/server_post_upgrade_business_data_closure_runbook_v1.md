# Server Post-Upgrade Business Data Closure Runbook v1

Status: READY

## Purpose

This runbook defines what must happen on a server after code deployment and
module upgrade.  A module upgrade only updates schema, views, access rules, and
data XML.  It does not by itself prove that historical business data is carried
by the new system or that users can continue daily work.

Use this runbook for:

- production first launch after historical replay
- production upgrade that includes migration/projection changes
- acceptance server refresh before user sign-off
- final merge/release closure when the branch changes business data carriers,
  projections, or visible business-field rules

## Boundary

The server closure has four separate responsibilities:

| Layer | Responsibility | Not Allowed |
| --- | --- | --- |
| Module upgrade | load Python/XML/schema/security changes | claim data continuity |
| Historical replay/init | materialize old facts into formal runtime carriers | invent missing business facts |
| Projection/backfill | fill formal new-system fields from existing source facts | expose legacy-only fields as user workflow fields |
| Verification | prove formal fields, visible surfaces, and user workflows are usable | accept backend-only PASS as final user acceptance |

If a visible field is empty, do not blindly backfill.  First decide whether the
source fact actually carries that value.  If no source fact exists, classify it
as source/scene scope instead of creating false data.

## Preconditions

- Deployed commit or release branch is fixed and recorded.
- Target DB is explicit, for example `DB_NAME=sc_prod` or `DB_NAME=sc_demo`.
- `.env.prod` or `.env.dev` has been reviewed.
- A current DB and filestore backup exists before any write step.
- Migration assets under `artifacts/migration` are present when historical
  replay or projection depends on packaged payloads.
- The operator has decided whether this is:
  - new production historical initialization
  - existing production module upgrade
  - acceptance server rehearsal

## Required Server Sequence

### 1. Deploy and upgrade modules

For production:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make prod.upgrade.core
```

If using the explicit module list:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make mod.upgrade MODULE=smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom
```

For an acceptance server, use the matching environment and DB:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  make mod.upgrade MODULE=smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom
```

### 2. Run user-usable historical initialization

If this is a fresh production historical rebuild, use the production one-click
entry.  It includes module install/upgrade, phase-1 historical replay, phase-2
user-usable initialization, and smoke checks:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  RUN_ID=prod_history_init_$(date +%Y%m%dT%H%M%S) \
  BASE_URL=https://<production-host> \
  FRONTEND_BASE_URL=https://<production-host> \
  make history.production.fresh_init
```

If modules are already upgraded and the DB already contains replayed historical
facts, run phase-2 user-usable initialization directly:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  MIGRATION_REPLAY_DB_ALLOWLIST=sc_prod \
  make history.business.usable.init
```

Acceptance server equivalent:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
  make history.business.usable.init
```

This step is mandatory when the release changes:

- project master-data continuity
- construction contract projections
- income/receipt/payment/expense runtime carriers
- material/budget/cost projections
- formal entry metadata
- visible business field coverage rules
- form/list/search orchestration for user workflow pages

### 3. Run value-level and formal-data gates

Run these after initialization/projection.  They check exact business continuity,
not only table existence.

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make verify.project_migration_field_continuity_gap.probe

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make verify.construction_contract_history_value_gap.probe

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make verify.formal_business_backfill.audit

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make verify.formal_entry_metadata.audit
```

Acceptance server equivalent replaces `ENV`, `ENV_FILE`, and `DB_NAME`.

Expected result:

- project migration field continuity: `PASS`
- construction contract history value gap: `PASS`
- formal business backfill audit: `PASS`
- formal entry metadata audit: `PASS`

### 4. Run visible-surface matrix and warning classification

The visible matrix proves that the configured user can see usable business
surfaces.  The classification step then separates true business gaps from
metadata, source-scope, or scene-scope warnings.

For production:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  AUDIT_LOGIN=wutao \
  MIGRATION_ARTIFACT_ROOT=/mnt/artifacts/migration/post_upgrade_visible_matrix \
  bash scripts/ops/odoo_shell_exec.sh < scripts/verify/visible_data_usability_matrix_probe.py

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  SYSTEMIC_FIELD_GAP_ARTIFACT_BASE=artifacts/migration \
  MIGRATION_ARTIFACT_ROOT=artifacts/migration/post_upgrade_visible_classification \
  make verify.visible_data_usability_warning.classify
```

For acceptance:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  AUDIT_LOGIN=wutao \
  MIGRATION_ARTIFACT_ROOT=/mnt/artifacts/migration/post_upgrade_visible_matrix \
  bash scripts/ops/odoo_shell_exec.sh < scripts/verify/visible_data_usability_matrix_probe.py

ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  SYSTEMIC_FIELD_GAP_ARTIFACT_BASE=artifacts/migration \
  MIGRATION_ARTIFACT_ROOT=artifacts/migration/post_upgrade_visible_classification \
  make verify.visible_data_usability_warning.classify
```

Expected result:

- visible matrix: `ok=true`, `error_count=0`
- warning classification: `status=PASS`
- `unresolved_business_warning_count=0`

Warnings are allowed only when classified as:

- covered by formal entry metadata gate
- covered by contract history value gate
- covered by source-scope rule
- covered by scene-scope rule

Warnings are not acceptable when classification reports:

- `requires_model_specific_business_value_gate`
- `metadata_gate_required`
- `contract_value_gate_required`
- `unclassified_visible_warning`

### 5. Rebuild and verify served frontend when frontend files changed

If the release changes `frontend/apps/web`, rebuild and publish the static
bundle before user acceptance:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make prod.frontend.build
```

Then verify the real served browser path for the acceptance user.  Backend
contract success is not enough when the user-visible list/form/search page is
part of the change.

Minimum real-user checks:

- login as the named acceptance user, usually `wutao`
- open project list and project form
- open income contract list and form
- open the pages touched by the release
- check field labels, order, search controls, relationship fields, attachments,
  and save/edit workflow

## Evidence To Keep

Archive the following artifact directories with the deployment record:

- project continuity probe result
- construction contract history value probe result
- formal business backfill audit result
- formal entry metadata audit result
- visible data usability matrix result
- visible data usability warning classification result
- frontend build or browser acceptance artifact when applicable

For this class of release, the minimum final evidence must include:

```text
visible_data_usability_warning_classification_result_v1.json
visible_data_usability_matrix_probe_result_v1.json
formal_business_backfill_audit_probe_result_v1.json
formal_entry_metadata_audit_result_v1.json
project_migration_field_continuity_gap_probe_result_v1.json
construction_contract_history_value_gap_probe_result_v1.json
```

## Stop Conditions

Stop the server rollout and do not hand over to users when any of the following
is true:

- module upgrade fails
- `history.business.usable.init` fails
- any value-level or formal-data gate is not `PASS`
- visible matrix has `error_count > 0`
- warning classification is not `PASS`
- classification has `unresolved_business_warning_count > 0`
- frontend was changed but the served bundle was not rebuilt
- the real acceptance user cannot continuously open, edit, and save the target
  business forms

## Failure Handling

When a gate fails:

1. Do not hide the field to make the warning disappear.
2. Identify the source model and source field first.
3. If the source carries the fact, add or fix a projection/backfill and rerun
   the gate.
4. If the source does not carry the fact, add a source-scope or scene-scope
   rule with evidence.
5. If the field is only historical/provenance metadata, keep it out of the
   business handling area and prove it through the formal metadata gate.
6. Rerun the visible matrix and classification before continuing.

## Final Merge Closure

Before merging a branch that changes migration, projection, contract, or user
visible business fields, the branch owner must record:

- final commit SHA
- target DB used for validation
- exact commands run
- artifact paths
- `PASS`/`FAIL` status for every gate above
- any source-scope or scene-scope exclusions added in the branch
- confirmation that no unresolved business warning remains

Only after this record exists should the branch proceed to PR, merge, and
server deployment.
