# Project Create-Only Write Gate v1

## Gate Decision

This gate allows preparing a later create-only project skeleton write batch for
`sc_demo`. It does not authorize execution in this batch.

The admissible write mode is:

- create-only
- 30-row sample only
- safe-slice fields only
- `legacy_project_id` required
- no upsert/update

## Evidence

| Evidence | Value |
| --- | ---: |
| source dry-run sample | `data/migration_samples/project_sample_v1.csv` |
| sample rows | 30 |
| safe fields | 22 |
| target database | `sc_demo` |
| target identity rows | 0 |
| target dry-run create | 30 |
| target dry-run update | 0 |
| target dry-run error | 0 |

## Allowed Write Fields

The later write batch may only write the 22 safe-slice fields already present in
`data/migration_samples/project_sample_v1.csv`:

| Field | Write rule |
| --- | --- |
| `legacy_project_id` | required, primary identity, must be unique |
| `legacy_parent_id` | optional raw legacy reference |
| `name` | required project name |
| `short_name` | optional text |
| `project_environment` | optional raw text |
| `legacy_company_id` | optional raw legacy reference |
| `legacy_company_name` | optional raw text |
| `legacy_specialty_type_id` | optional raw legacy reference |
| `specialty_type_name` | optional raw text |
| `legacy_price_method` | optional raw legacy marker |
| `business_nature` | optional raw text |
| `detail_address` | optional text |
| `project_profile` | optional text |
| `project_area` | optional raw text |
| `legacy_is_shared_base` | optional raw legacy marker |
| `legacy_sort` | optional raw legacy marker |
| `legacy_attachment_ref` | optional raw legacy reference only |
| `project_overview` | optional text |
| `legacy_project_nature` | optional raw legacy marker |
| `legacy_is_material_library` | optional raw legacy marker |
| `other_system_id` | optional raw identity reference |
| `other_system_code` | optional raw identity reference |

## Forbidden Writes

The later write batch must not write:

- `company_id`
- `project_type_id`
- `project_category_id`
- `stage_id`
- `lifecycle_state`
- `active`
- user relation fields
- partner relation fields
- contract, payment, supplier, tax, bank, account, cost, settlement, or
  attachment records
- official `project_code` from legacy `PROJECT_CODE`

## Preconditions

Before a later write batch starts, all checks must pass:

1. Re-export target identity snapshot from `sc_demo`.
2. Confirm target identity rows remain `0`.
3. Re-run dry-run and confirm `create=30`, `update=0`, `error=0`.
4. Confirm the sample CSV still has exactly 30 rows and no unsafe fields.
5. Confirm `legacy_project_id` and `name` are present for 30/30 rows.
6. Confirm no duplicate `legacy_project_id` exists in the sample.
7. Confirm `sc_demo` is intentionally the empty target for this import.

If any check fails, the write batch must not start.

## Stop Conditions

Stop immediately if:

- target identity rows are greater than 0;
- dry-run returns any update row;
- dry-run returns any error row;
- any unsafe field appears in the sample;
- a field expansion is required;
- upsert/update behavior is requested;
- company, specialty, lifecycle/state, user, partner, contract, payment,
  supplier, tax, bank, cost, settlement, or attachment writes are requested.

## Gate Conclusion

This gate is PASS for create-only design readiness, conditional on confirming
that `sc_demo` is intentionally empty for project skeleton import.

It is NO-GO for upsert/update import.
