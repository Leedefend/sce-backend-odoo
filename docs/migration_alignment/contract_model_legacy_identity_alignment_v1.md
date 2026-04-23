# Contract Model Legacy Identity Alignment v1

Iteration: `ITER-2026-04-13-1840`

Status: `PASS`

## Scope

This batch adds only migration identity and reference fields to `construction.contract`.

It does not import contract data, create partner data, change workflow, change tax logic, change payment or settlement logic, change ACL, change menus, or change frontend code.

## Reason

`ITER-2026-04-13-1839` blocked contract writes because the target model had no confirmed legacy contract identity field for exact rollback/upsert. Contract import needs a stable old-system key before any create-only trial.

## Added Fields

| Field | Legacy source | Purpose |
|---|---|---|
| `legacy_contract_id` | `Id` | primary old-system contract identity for migration traceability, rollback targeting, and future upsert decisions |
| `legacy_project_id` | `XMID` | old project identity copied for audit; formal relation remains `project_id` |
| `legacy_document_no` | `DJBH` | old document number reference |
| `legacy_contract_no` | `HTBH` | old contract number reference; formal `name` remains system-generated |
| `legacy_external_contract_no` | `f_WBHTBH` / `PID` candidate | external/legacy reference number |
| `legacy_status` | `DJZT` | old status marker; not used to replay workflow in first slice |
| `legacy_deleted_flag` | `DEL` | old deletion marker; `DEL=1` remains excluded from first safe import |
| `legacy_counterparty_text` | inferred `FBF` / `CBF` | counterparty text used for partner matching audit |

## View Alignment

The contract form view now exposes these fields as read-only migration references:

- inline `legacy_contract_id` near the system contract number
- a `迁移对照` notebook page containing all eight fields

No menu or action was changed.

## Validation

Runtime validation in `sc_demo`:

- missing model fields: none
- missing `ir.model.fields`: none
- missing form view refs: none
- existing contract count: 71
- contracts with non-empty `legacy_contract_id`: 0

The last point confirms this batch did not import or mutate old contract data.

## Remaining Blockers

This batch resolves only the legacy identity/model coverage blocker.

Still blocked before contract write:

- partner matching for `FBF` / `CBF`
- project coverage beyond the current 146 known-written project matches
- tax/default tax policy
- computed amount and contract line policy
- state replay policy
- `DEL=1` filtering policy implementation in future dry-run/importer
