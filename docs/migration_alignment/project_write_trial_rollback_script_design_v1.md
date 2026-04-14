# Project Write Trial Rollback Script Design v1

## Purpose

Define the rollback script shape for a later task. This iteration does not
create the rollback script and does not delete records.

## Script Mode

The rollback script should support two explicit modes:

- `dry_run`: default, only emits target list and refusal diagnostics;
- `delete`: requires a separate high-risk task contract and explicit user
  authorization.

`delete` mode must not be available by default.

## Inputs

Required input:

```text
data/migration_samples/project_sample_v1.csv
```

The script must read only `legacy_project_id` from the sample. It must not use
project name, company text, `other_system_id`, `other_system_code`, or
`PROJECT_CODE` to select rollback records.

## Dry-Run Output

The dry-run output should include:

- target database;
- input row count;
- locked identity count;
- matched project count;
- missing identities;
- duplicate identities;
- matched Odoo IDs and project names;
- final decision: `ROLLBACK_READY` or `ROLLBACK_BLOCKED`.

## Delete-Mode Safeguards

Before delete-mode can call `unlink`, it must prove:

- input has exactly 30 unique `legacy_project_id` values;
- matched record count is exactly 30;
- every matched record has `legacy_project_id` in the locked list;
- no extra records are selected;
- the operator passed an explicit delete flag;
- a dry-run artifact exists for the same identity set.

## Pseudocode

```python
ids = read_legacy_project_ids(sample_csv)
assert len(ids) == 30
assert len(set(ids)) == 30

records = env["project.project"].sudo().search([
    ("legacy_project_id", "in", ids),
])
assert len(records) == 30
assert set(records.mapped("legacy_project_id")) == set(ids)

emit_dry_run_artifact(records)

if mode == "delete":
    require_explicit_authorization()
    records.unlink()
    env.cr.commit()
    verify_no_records_remain(ids)
```

## Forbidden Behavior

The script must not:

- delete by name;
- delete by company text;
- delete records with empty `legacy_project_id`;
- delete records outside the locked identity set;
- delete related company, partner, user, contract, payment, supplier, tax, bank,
  cost, settlement, or attachment records;
- combine rollback with a new import.

## Current Conclusion

The rollback script design is executable in a later batch. The current batch is
design-only and no delete was performed.
