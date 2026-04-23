# Project Ontology First Assetization Plan v1

Status: Frozen Migration Governance
Decision: project ontology first
Purpose: correct the migration assetization entry point from master-data-first to business-ontology-first.

## 1. Decision

The first complete assetization sample must start from the project business ontology and the project model.

Partner assetization remains necessary, but it is not the first business sample. It is a dependency lane that supplies stable enterprise references for project, contract, and receipt facts.

The corrected migration axis is:

```text
project ontology
  -> project core facts
  -> project dependent master references
  -> project relations
  -> project-adjacent business facts
  -> rebuild validation
```

## 2. Why project comes first

The project model is the business body of this system:

- It is the main operating object for construction enterprise management.
- It connects partner, contract, member, cost, receipt, payment, settlement, and lifecycle facts.
- It provides the natural validation surface for whether migrated data is useful.
- It owns the stage / milestone / data relationship that gives migrated facts business meaning.

Starting from partner would produce technically valid master data, but it would not prove that the migrated data can reconstruct the business operating body.

## 3. Project ontology boundary

The project ontology is not just `project.project` rows. It includes the minimum facts needed to make a project recognizable and reconstructable:

| Layer | Meaning | Assetization stance |
| --- | --- | --- |
| Project identity | stable legacy project key and target model identity | required |
| Project descriptive facts | name, short name, environment, nature, address, profile, overview | required when available |
| Project lifecycle skeleton | stage, milestone, lifecycle state, deleted/archive stance | staged, conservative |
| Project organization references | company, owner, supervision, manager, technical lead | dependency or deferred |
| Project relation facts | members, contracts, receipts, later cost/payment/settlement | separate dependent lanes |
| Project evidence | original fields, deferred fields, discard/archive reasons | manifest and validation evidence |

## 4. stage / milestone / data rule

The project ontology follows the product business closure model:

```text
stage -> milestone -> data
```

Rules:

- `stage` is the main business skeleton.
- `milestone` is medium-grain progress within a stage.
- `data` provides factual evidence: contract, member, receipt, cost, payment, settlement.
- Migration must not fabricate stage or milestone from incomplete facts.
- If lifecycle meaning is unclear, preserve legacy state and defer normalized lifecycle.
- Reading or importing data must not imply workflow advancement.

Initial assetization should load the project skeleton first, then attach dependent facts.

## 5. Project source facts

Current known project source:

| Source | Rows | Target |
| --- | ---: | --- |
| `tmp/raw/project/project.csv` | 755 | `project.project` |

Known identity facts:

- `ID` -> `legacy_project_id`: 755/755 non-empty and unique.
- `OTHER_SYSTEM_ID`: fallback only.
- `OTHER_SYSTEM_CODE`: fallback only.
- `PROJECT_CODE`: manual reference only until code policy is settled.

Primary idempotency key:

```text
legacy_project_id
```

Stable external id:

```text
legacy_project_sc_<legacy_project_id>
```

Example:

```text
legacy_project_sc_1001
```

## 6. Project core asset package

The first business asset package should be:

```text
migration_assets/
  10_master/
    project/
      project_master_v1.csv
      project_deferred_fields_v1.csv
      project_discard_summary_v1.csv
  manifest/
    project_asset_manifest_v1.json
    project_external_id_manifest_v1.json
    project_validation_manifest_v1.json
```

`project_master_v1.csv` is the first business-body asset. It must be generated before partner becomes the first promoted baseline sample.

## 7. Project master fields

Initial target asset fields:

```text
external_id,legacy_identity_key,legacy_project_id,name,short_name,project_environment,business_nature,detail_address,project_profile,project_area,project_overview,legacy_parent_id,other_system_id,other_system_code
```

Rules:

- `external_id`: `legacy_project_sc_<legacy_project_id>`.
- `legacy_identity_key`: `project:sc:<legacy_project_id>`.
- `name`: from `XMMC`, required.
- `legacy_project_id`: from `ID`, required.
- Optional text fields may be empty.
- `PROJECT_CODE` is not used as idempotency key in v1.
- Hierarchy from `PID` is preserved as `legacy_parent_id`, not used to build parent-child structure in the first package.
- Deleted/archive handling from `DEL` is deferred unless policy is frozen.

## 8. Partner dependency

partner dependency is required but secondary.

Partner assetization supplies:

- owner unit references.
- supervision unit references.
- contract counterparty references.
- receipt party references.

However, project skeleton asset generation must not block on unresolved partner matching when project facts are otherwise loadable.

Policy:

- Project skeleton loads with direct project facts.
- Partner references are emitted as deferred dependencies if unresolved.
- Partner lane can run before loader execution as a dependency package, but the business ontology sample remains project-first.
- partner asset generator design remains useful, but its priority becomes dependency support for project ontology.

## 9. Relation lane ordering

Corrected assetization order:

1. `10_master/project` project ontology skeleton.
2. `10_master/partner` dependency master data.
3. `30_relation/project_partner_reference` owner/supervision/counterparty references.
4. `30_relation/project_member_neutral`.
5. `10_master/contract_header` scoped to project references.
6. `20_business/receipt_core` scoped to project/contract references.
7. `40_post/project_lifecycle_projection` only after facts support it.

This order is logical, not necessarily file loading order. Loader may load partner before resolving references, but the migration design and validation remain project-centered.

## 10. Manifest implications

`asset_manifest.json` for the first business package must use:

```json
{
  "asset_manifest_version": "1.0",
  "asset_package_id": "project_sc_v1",
  "lane": {
    "lane_id": "project",
    "layer": "10_master",
    "business_priority": "core_business_body",
    "risk_class": "normal"
  },
  "target": {
    "model": "project.project",
    "identity_field": "legacy_project_id",
    "load_strategy": "upsert_by_external_id"
  }
}
```

`project_external_id_manifest_v1.json` record shape:

```json
{
  "external_id": "legacy_project_sc_1001",
  "legacy_key": "1001",
  "legacy_key_type": "single_pk",
  "source_table": "project",
  "target_model": "project.project",
  "target_lookup": {
    "field": "legacy_project_id",
    "value": "1001"
  },
  "status": "loadable"
}
```

## 11. Validation gates

The project ontology first package must validate:

- source project file exists.
- required source headers exist.
- `legacy_project_id` is non-empty and unique.
- `name` is non-empty for loadable rows.
- `external_id` is unique.
- `legacy_identity_key` is unique.
- optional fields are allowed to be blank.
- deferred fields are recorded.
- project lifecycle is not fabricated.
- partner dependency is recorded as deferred, not invented.
- no payment, settlement, accounting, ACL, record rule, or module manifest leakage.

## 12. Impact on existing partner generator design

The partner generator design is not discarded.

It is reclassified:

```text
from: first assetization sample
to: first dependency master-data generator supporting project ontology
```

No immediate rewrite is required. The next implementation should not implement partner generator first unless it is explicitly scoped as project dependency support.

## 13. next batch

next batch:

```text
ITER-MIGRATION-PROJECT-ASSET-GENERATOR-DESIGN
```

Goal:

- Define no-DB project asset generator inputs, outputs, fields, external id rule, deferred dependency handling, and validation gates.

Not doing:

- No DB writes.
- No partner generator implementation.
- No project loader.
- No lifecycle state normalization beyond preserving raw values.
- No payment, settlement, or accounting.
