# Legacy Workflow Fact Screen v1

Status: `PASS`

This is a read-only screen for legacy approval facts from
`S_Execute_Approval`. It does not replay workflow runtime state.

## Result

- raw rows: `163245`
- loadable historical approval facts: `79702`
- blocked rows: `83543`
- matched target records: `29932`
- ambiguous rows: `0`
- carrier decision: `new_historical_workflow_audit_carrier_required`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
| blocked_target_not_assetized_or_not_loadable | 83543 |
| loadable_historical_approval_fact | 79702 |

## Target Lane Coverage

| Lane | Approval rows |
|---|---:|
| actual_outflow | 6088 |
| contract | 6084 |
| outflow_request | 45693 |
| receipt | 8556 |
| supplier_contract | 13281 |

## Action Classification

| Action | Rows |
|---|---:|
| approve | 947 |
| unknown | 162298 |

## Source Table Top Counts

| SJBMC | Rows |
|---|---:|
| missing_source_table | 86154 |
| 审批意见信息表 | 77091 |

## Rejected Existing Carriers

- `sc.workflow.instance`: runtime current workflow state; would fabricate active process truth.
- `sc.workflow.workitem`: runtime todo/completion carrier; not historical audit-safe.
- `sc.workflow.log`: requires runtime instance and node references; cannot preserve source rows independently.
- `sc.business.evidence`: requires runtime integer business_id and restricted evidence types; not safe as XML carrier.

## Decision

`new_historical_workflow_audit_carrier_required`
