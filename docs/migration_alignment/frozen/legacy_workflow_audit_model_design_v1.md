# Legacy Workflow Audit Model Design v1

Status: `PASS`

## Scope

This batch adds the neutral historical approval audit carrier:

```text
sc.legacy.workflow.audit
```

The model is designed for old `S_Execute_Approval` facts that are loadable
through stable business asset anchors. It is not a new approval runtime and it
does not replay workflow state.

## Architecture

| Item | Value |
|---|---|
| Layer Target | Domain business-fact layer |
| Module | `smart_construction_core` support model |
| Ownership | construction workflow/audit domain |
| Kernel or Scenario | scenario |
| Runtime approval dependency | none |

## Boundary

The carrier stores historical facts only:

- source row identity
- target business model and external id
- target asset lane
- actor id/name
- approval/receive timestamps
- approval note
- old source status and step/template identifiers

The carrier does not:

- inherit `tier.validation`
- create or update `tier.review`
- link to `sc.workflow.instance`, `sc.workflow.workitem`, or `sc.workflow.log`
- change `payment.request.validation_status`
- trigger approval callbacks
- write target business document state

## Key Fields

| Field | Meaning |
|---|---|
| `legacy_workflow_id` | old `S_Execute_Approval.Id` |
| `legacy_djid` | old target business document id |
| `legacy_business_id` | old workflow/setup context id |
| `target_model` | target Odoo model |
| `target_external_id` | deterministic target external id for XML replay |
| `target_lane` | target business asset lane |
| `actor_legacy_user_id` | old actor user id |
| `actor_name` | old actor display name |
| `approved_at` | old processing timestamp |
| `approval_note` | old approval opinion/comment |
| `legacy_status` | raw `f_SPZT` value |
| `legacy_back_type` | raw `f_Back_YJLX` value |
| `action_classification` | screening classification only, not runtime state |

## Idempotency

SQL uniqueness:

```text
unique(legacy_workflow_id, import_batch)
```

This lets XML assets replay deterministically without merging unrelated source
rows.

## Next Gate

Next implementation batch should generate the XML asset package for the
currently loadable `79702` approval audit rows, split by lane or batch if needed.
That batch must verify:

- generated records point to stable target external ids
- no `tier.review` rows are created
- no target business state is changed
- no database integer ids are required in XML
