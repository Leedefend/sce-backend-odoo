# Business Capability Acceptance Audit - 2026-06-09

Environment: development server, database `sc_demo`

Branch: `feature/business-capability-acceptance-audit`

## Result

Status: PASS with one product-review boundary.

## Checks

1. User-confirmed formal form data alignment
   - Script: `scripts/verify/user_confirmed_form_data_alignment_audit.py`
   - Menus: 62
   - Models: 36
   - Records checked: 260357
   - Fields checked: 862
   - Mismatch fields: 0
   - Readonly source-only fields: 1
   - Status: PASS

2. User-confirmed form capability audit
   - Script: `scripts/verify/user_confirmed_form_capability_audit.py`
   - Menus: 62
   - Models: 36
   - Severity: 61 ok, 1 needs_review
   - Status: PASS

3. P2 runtime business smoke
   - Script: `scripts/ops/validate_p2_runtime.sh`
   - Task flow: PASS
   - Progress flow: PASS
   - Ledger lock: PASS
   - Contract binding: PASS
   - Payment submit/approve/pay flow: PASS
   - Audit events:
     - `task_ready`, `task_started`, `task_done`, `task_cancelled`
     - `progress_submitted`, `progress_reverted`
     - `period_locked`, `period_unlocked`
     - `contract_bound`, `contract_unbound`
     - `payment_submitted`, `payment_approved`, `payment_paid`
   - Status: PASS

## Boundary

The only review item is `sc.material.inbound` / 入库单: the formal list includes a legacy source-only field for old-system line tax-included amount. This field remains aligned for visible data, but is not promoted to a header-level editable form field because it is line-level source data, not an inbound document header total.

## Conclusion

The user-confirmed formal menu data surface is aligned with the acceptance surface, and the core business processing chain is executable on the development server. The next product decision is whether the inbound legacy line amount should remain source-only or be modeled as a dedicated line-level editable field.
