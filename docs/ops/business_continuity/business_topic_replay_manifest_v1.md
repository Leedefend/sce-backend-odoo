# Business Topic Replay Manifest v1

## Topic
`imported_business_continuity_v1`

## Purpose
Replay the imported-business continuity topic after legacy data is loaded.

The topic does not create a new approval workflow and does not infer ambiguous
business facts. It only orchestrates existing deterministic sync scripts.

## Step Order

| Step | Kind | Script | Purpose |
| --- | --- | --- | --- |
| `project_continuity` | `odoo_sync` | `project_continuity_downstream_fact_state_sync.py` | Align imported projects with downstream facts to execution state. |
| `contract_continuity` | `odoo_sync` | `contract_continuity_downstream_fact_state_sync.py` | Align imported contracts to confirmed/running states. |
| `payment_downstream_fact_screen` | `host_python` | `legacy_payment_approval_downstream_fact_screen.py` | Regenerate downstream approval evidence rows. |
| `payment_done_fact` | `odoo_sync` | `legacy_payment_approval_downstream_fact_state_sync.py` | Align downstream-approved payment requests to done/validated. |
| `payment_linkage_fact` | `odoo_sync` | `payment_linkage_fact_sync.py` | Align deterministic payment company and contract links. |
| `operational_verify` | `odoo_verify` | built-in SQL | Verify project, contract, and payment continuity metrics. |

## Modes
- `plan`: print the topic plan and create a result artifact; no step execution.
- `check`: execute all sync steps in `SYNC_MODE=check`; no business writes.
- `write`: for each write-capable step, run `SYNC_MODE=check` before `SYNC_MODE=write`.

## Write Boundary
- Write mode is explicit.
- Check-before-write is mandatory.
- Replay stops on the first failed step.
- Ambiguous records remain excluded by the underlying sync scripts.
- Settlement, accounting, ACL, manifest, and frontend behavior are outside this topic.
