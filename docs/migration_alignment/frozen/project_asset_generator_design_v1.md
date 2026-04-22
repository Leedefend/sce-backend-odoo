# Project Asset Generator Design v1

Status: Frozen Migration Governance
Depends on:

- `docs/migration_alignment/frozen/project_ontology_first_assetization_plan_v1.md`
- `docs/migration_alignment/frozen/migration_asset_manifest_schema_v1.md`
- `docs/migration_alignment/project_mapping_dry_run_master_v1.md`
- `docs/migration_alignment/project_import_identity_policy_v1.md`

Objective: define the no-DB project asset generator contract as the first business ontology assetization sample.

## 1. Position

The project generator is the first business-body generator in the assetized migration bus.

```text
legacy project facts
  -> normalized project facts
  -> project_master_v1.csv
  -> project deferred/discard evidence
  -> project manifests
  -> later loader/rebuild verification
```

The generator must be deterministic. The same source snapshot and rules must produce the same records, the same stable external ids, and the same manifest counts.

## 2. Generator boundary

Script to implement in the next batch:

```text
scripts/migration/project_asset_generator.py
```

Allowed behavior:

- Read `tmp/raw/project/project.csv`.
- Normalize project facts from frozen mapping rules.
- Generate project asset files under `.runtime_artifacts/`.
- Generate manifest files.
- Generate deferred field evidence.
- Run no-DB validation.

Forbidden behavior:

- No Odoo shell.
- No database write.
- No `project.project` create/update/unlink.
- No parent-child project relation build in v1.
- No lifecycle stage/milestone fabrication.
- No partner, contract, receipt, payment, settlement, accounting, ACL, record rule, or module manifest changes.
- No mutation of source CSV.

## 3. Input

Required input:

| Input | Role | Known rows |
| --- | --- | ---: |
| `tmp/raw/project/project.csv` | project business ontology source | 755 |

CLI proposal:

```bash
python3 scripts/migration/project_asset_generator.py \
  --project tmp/raw/project/project.csv \
  --out .runtime_artifacts/migration_assets/project_sc_v1 \
  --source sc \
  --asset-version v1 \
  --check
```

`--check` must generate and validate local files without connecting to Odoo.

## 4. Outputs

The next implementation must produce:

```text
.runtime_artifacts/migration_assets/project_sc_v1/
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

Generated files are runtime evidence by default and must not be committed unless a later baseline promotion task explicitly allows it.

## 5. Required source headers

Minimum required headers:

```text
ID,XMMC
```

Optional direct headers used when present:

```text
PID,SHORT_NAME,PROJECT_ENV,NATURE,DETAIL_ADDRESS,PROFILE,AREA,PROJECTOVERVIEW,OTHER_SYSTEM_ID,OTHER_SYSTEM_CODE
```

Deferred headers tracked when present:

```text
PROJECT_CODE,SPECIALTY_TYPE_ID,SPECIALTY_TYPE_NAME,PRICE_METHOD,CONTRACT_STATUS,IS_COMPLETE_PROJECT,COMPANYID,COMPANYNAME,TAX_ORGANIZATION_ID,TAX_ORGANIZATION_NAME,ACCOUNT_NAME,ACCOUNT_NUMBER,ACCOUNT_BANK,COST,MANAGE_FEE_RATIO,IS_SHARED_BASE,SORT,NOTE,FJ,LRR,LRRID,LRSJ,XGR,XGRID,XGSJ,DEL,PROJECTMANAGER,TECHNICALRESPONSIBILITY,OWNERSUNIT,OWNERSCONTACT,OWNERSCONTACTPHONE,SUPERVISIONUNIT,SUPERVISORYENGINEER,SUPERVISOPHONE,CONTRACTAGREEMENT,PROJECTFILE,CONTRACTINGMETHOD,PROJECT_NATURE,IS_MACHINTERIAL_LIBRARY,WBHTID,ZSLX,XMJDID,XMJD,SSDQID,SSDQ,STATE,XQRGZ,XQRGZR,XQRGZRID,XQRGZXZRID,XQRGZXZR
```

Header policy:

- Missing required headers block the package.
- Missing optional headers do not block.
- Missing deferred headers do not block, but the validation manifest must record absence.

## 6. Normalized project facts

The generator must produce this normalized in-memory shape:

| Field | Source | Required | Rule |
| --- | --- | --- | --- |
| `legacy_project_id` | `ID` | yes | trim, non-empty, unique |
| `project_name` | `XMMC` | yes | trim, non-empty |
| `legacy_parent_id` | `PID` | no | preserve only |
| `short_name` | `SHORT_NAME` | no | copy as text |
| `project_environment` | `PROJECT_ENV` | no | copy raw value |
| `business_nature` | `NATURE` | no | copy raw value |
| `detail_address` | `DETAIL_ADDRESS` | no | copy as text |
| `project_profile` | `PROFILE` | no | copy as text |
| `project_area` | `AREA` | no | copy raw value |
| `project_overview` | `PROJECTOVERVIEW` | no | copy as text |
| `other_system_id` | `OTHER_SYSTEM_ID` | no | copy as reference |
| `other_system_code` | `OTHER_SYSTEM_CODE` | no | copy as reference |
| `discard_reason` | derived | conditional | required for discarded rows |

Discard rules:

- Missing `ID`: discard.
- Duplicate `ID`: block package unless exact duplicate row policy is later frozen.
- Missing `XMMC`: discard.

Do not discard for missing optional fields.

## 7. Target asset columns

`project_master_v1.csv` columns:

```text
external_id,legacy_identity_key,legacy_project_id,name,short_name,project_environment,business_nature,detail_address,project_profile,project_area,project_overview,legacy_parent_id,other_system_id,other_system_code
```

Mapping:

| Asset column | Source |
| --- | --- |
| `external_id` | generated |
| `legacy_identity_key` | `project:sc:<legacy_project_id>` |
| `legacy_project_id` | `ID` |
| `name` | `XMMC` |
| `short_name` | `SHORT_NAME` |
| `project_environment` | `PROJECT_ENV` |
| `business_nature` | `NATURE` |
| `detail_address` | `DETAIL_ADDRESS` |
| `project_profile` | `PROFILE` |
| `project_area` | `AREA` |
| `project_overview` | `PROJECTOVERVIEW` |
| `legacy_parent_id` | `PID` |
| `other_system_id` | `OTHER_SYSTEM_ID` |
| `other_system_code` | `OTHER_SYSTEM_CODE` |

`PROJECT_CODE` is deliberately excluded from `project_master_v1.csv` v1 because project-code write policy is not approved.

## 8. Stable external id

Pattern:

```text
legacy_project_sc_<legacy_project_id>
```

Example:

```text
legacy_project_sc_1001
```

Rules:

- `legacy_project_id` must come from source `ID`.
- Do not use new database ids.
- Duplicate external ids block the package.
- Discarded rows do not enter `project_master_v1.csv`, but their counts and reasons enter `project_discard_summary_v1.csv`.

## 9. deferred_fields

`project_deferred_fields_v1.csv` captures business facts that are intentionally not in the first project skeleton package.

Columns:

```text
legacy_project_id,legacy_field,legacy_value,defer_reason,target_candidate
```

Required deferred classes:

| Legacy field group | defer_reason |
| --- | --- |
| `PROJECT_CODE` | project_code_write_policy_not_frozen |
| `SPECIALTY_TYPE_*` | dictionary_mapping_not_frozen |
| `CONTRACT_STATUS`, `CONTRACTAGREEMENT`, `CONTRACTINGMETHOD`, `WBHTID` | contract_adjacent_lane |
| `COMPANY*`, `OWNERS*`, `SUPERVISION*`, `PROJECTMANAGER`, `TECHNICALRESPONSIBILITY` | partner_or_user_dependency |
| `ACCOUNT_*`, `TAX_ORGANIZATION_*` | tax_bank_account_out_of_scope |
| `COST`, `MANAGE_FEE_RATIO` | cost_financial_semantics_deferred |
| `STATE`, `XMJD*`, `IS_COMPLETE_PROJECT` | lifecycle_policy_deferred |
| `LR*`, `XG*` | legacy_audit_metadata_policy_deferred |
| `DEL` | archive_delete_policy_deferred |
| `PROJECTFILE`, `FJ` | attachment_import_deferred |
| `XQRGZ*` | requirement_confirmation_workflow_deferred |

Deferred values are evidence, not target facts. They must not create target field values in v1.

## 10. project_discard_summary_v1.csv

Columns:

```text
discard_reason,count
```

Minimum reasons:

- `missing_legacy_project_id`
- `duplicate_legacy_project_id`
- `missing_project_name`

If all 755 source rows are loadable, the file still exists with zero counts.

## 11. project_asset_manifest_v1.json

Required manifest values:

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

Required assets:

- `project_master_csv_v1`
- `project_deferred_fields_csv_v1`
- `project_discard_summary_csv_v1`
- `project_external_id_manifest_v1`
- `project_validation_manifest_v1`

## 12. project_external_id_manifest_v1.json

Record shape:

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

Summary must include:

- `total`
- `loadable`
- `discarded`
- `deferred`
- `conflict_blocked`

## 13. project_validation_manifest_v1.json

Must include validation_gates:

- `source_project_file_exists`
- `required_source_headers_present`
- `legacy_project_id_non_empty`
- `legacy_project_id_unique`
- `project_name_present`
- `external_id_unique`
- `legacy_identity_key_unique`
- `deferred_fields_written`
- `discard_summary_written`
- `asset_hashes_match`
- `manifest_counts_match`
- `no_lifecycle_fabrication`
- `no_partner_dependency_fabrication`
- `no_high_risk_lane_leakage`

Failure policy:

| Failure | Policy |
| --- | --- |
| missing source file | block_package |
| missing required header | block_package |
| duplicate legacy project id | block_package |
| missing project name | discard_record |
| external id duplicate | block_package |
| lifecycle normalization attempted | block_package |
| high risk lane leakage | block_package |

## 14. no-DB validation_gates

The next implementation must validate without Odoo:

1. Source file exists and is readable.
2. Required headers `ID` and `XMMC` exist.
3. Output directory is under the requested `--out`.
4. `project_master_v1.csv` has the required header.
5. `legacy_project_id` is non-empty for loadable rows.
6. `name` is non-empty for loadable rows.
7. `external_id` is unique.
8. `legacy_identity_key` is unique.
9. Deferred fields file is generated.
10. Discard summary file is generated.
11. Manifest `record_count` matches CSV rows.
12. Manifest hashes match generated files.
13. No target field is generated for payment, settlement, accounting, ACL, record rules, or module manifests.

## 15. Next implementation

next implementation file:

```text
scripts/migration/project_asset_generator.py
```

Expected commands:

```bash
python3 -m py_compile scripts/migration/project_asset_generator.py
python3 scripts/migration/project_asset_generator.py \
  --project tmp/raw/project/project.csv \
  --out .runtime_artifacts/migration_assets/project_sc_v1 \
  --source sc \
  --asset-version v1 \
  --check
python3 -m json.tool .runtime_artifacts/migration_assets/project_sc_v1/manifest/project_asset_manifest_v1.json
python3 -m json.tool .runtime_artifacts/migration_assets/project_sc_v1/manifest/project_external_id_manifest_v1.json
python3 -m json.tool .runtime_artifacts/migration_assets/project_sc_v1/manifest/project_validation_manifest_v1.json
make verify.native.business_fact.static
git diff --check
```

## 16. Stop conditions for implementation

Stop if:

- `ID` or `XMMC` headers are absent.
- `ID` uniqueness is not guaranteed.
- The generator needs Odoo ORM to decide business facts.
- Lifecycle normalization becomes necessary to generate v1.
- The implementation attempts to write `project.project`.
- The implementation touches partner, contract, receipt, payment, settlement, accounting, ACL, record rules, or module manifests.

## 17. Output policy

Commit in the implementation batch:

- `scripts/migration/project_asset_generator.py`
- formal docs only if the design needs a correction

Do not commit generated `.runtime_artifacts/` files.
