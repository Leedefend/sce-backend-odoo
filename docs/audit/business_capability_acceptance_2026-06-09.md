# Business Capability Acceptance Audit - 2026-06-09

Environment: development server, database `sc_demo`

Branch: `feature/business-capability-acceptance-audit`

## Result

Status: PASS.

## Checks

1. User-confirmed formal form data alignment
   - Script: `scripts/verify/user_confirmed_form_data_alignment_audit.py`
   - Menus: 62
   - Models: 36
   - Records checked: 260357
   - Fields checked: 863
   - Mismatch fields: 0
   - Readonly source-only fields: 0
   - Severity: 62 ok
   - Status: PASS

2. User-confirmed form capability audit
   - Script: `scripts/verify/user_confirmed_form_capability_audit.py`
   - Menus: 62
   - Models: 36
   - Severity: 62 ok
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

## Notes

`sc.material.inbound` / 入库单 now carries the user-confirmed "含税金额" surface as a formal computed field. Historical records use the accepted legacy value when present; new business records fall back to the current inbound amount total.

## Conclusion

The user-confirmed formal menu data surface is fully aligned with the acceptance surface, and the core business processing chain is executable on the development server. The current conclusion can be given to the user: the confirmed formal menus are data-aligned and support the core business processing flow.
