# History Business Usable Gap Report v1

Status: CLOSED

Task: `ITER-2026-04-25-HISTORY-CONTINUITY-PROMOTION-001`

## Probe Summary

Command:

```bash
DB_NAME=sc_demo make history.business.usable.probe
```

Result:

- `status = PASS`
- `decision = history_business_usable_visible_but_promotion_gaps`
- `gap_count = 1`

## Frozen Conclusion

The replay baseline has already crossed into user-visible runtime surfaces:

- projects list/form sample exists
- contracts list/form sample exists
- payment requests list/form sample exists
- project ownership links exist
- contract partner links exist
- actionable todo surface exists through `mail.activity`

The former singular promotion blocker:

- `payment_request_no_pending_runtime_states = true`

is now closed.

## Live Evidence

Selected counts in `sc_demo`:

- `project_runtime_records = 755`
- `project_records_with_owner_link = 755`
- `contract_runtime_records = 6793`
- `contract_records_with_partner_link = 6793`
- `payment_request_runtime_records = 27802`
- `payment_request_with_project_link = 27802`
- `payment_request_with_contract_link = 1683`
- `mail_activity_total = 26`
- `legacy_workflow_audit_facts = 79702`
- `tier_review_total = 0`

Sample runtime records:

- `project_project_id = 39`
- `construction_contract_id = 96`
- `payment_request_id = 183`
- `payment_request_line_id = 1`
- `receipt_invoice_line_id = 1`
- `legacy_workflow_audit_id = 1`
- `mail_activity_id = 1`

Original payment request state distribution:

```json
{
  "draft": 27802
}
```

## Resolution

`Batch-History-Continuity-Promotion-A` activated historical `outflow_request_core`
rows with workflow audit evidence from `draft` to `submit` through a dedicated
historical promotion lane.

Current probe result:

- `decision = history_business_usable_ready`
- `gap_count = 0`

Current payment request state distribution:

```json
{
  "draft": 15555,
  "submit": 12247
}
```

## Interpretation

This means the current replay chain already provides:

- runtime-visible lists and forms
- ownership/partner links
- at least one actionable my-work surface

The replay + promotion chain now provides:

- runtime-visible lists and forms
- ownership/partner links
- actionable my-work surface
- non-draft historical payment request states for outflow approval continuity

## Next Batch

The next valid batch is no longer `Promotion-A`.

Replay + first promotion baseline is now ready for targeted continuation work,
rather than generic historical replay repair.
