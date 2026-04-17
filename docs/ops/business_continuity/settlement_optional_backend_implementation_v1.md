# Settlement Optional Backend Implementation v1

## Status

Implemented after explicit user authorization for this high-risk business
semantics batch.

## Intended Implementation

The implementation changed only these surfaces:

- `addons/smart_construction_core/models/core/payment_request.py`
- `addons/smart_construction_core/models/core/payment_ledger.py`
- `addons/smart_construction_core/models/core/settlement_order.py`
- `addons/smart_construction_core/tools/validator/rule_3way_link_integrity.py`

## Implemented Semantics

Payment request without settlement:

- can submit when contract, funding, attachment, project lifecycle, and approval
  requirements pass
- can approve through tier validation
- can register ledger after approval
- can complete after ledger registration

Payment request with settlement:

- must keep current settlement state checks
- must keep consistency checks
- must keep settlement compliance checks
- must keep settlement payable balance and overpay checks

Settlement submit/approve:

- must validate the target settlement order and its linked records
- must not scan all historical payment requests and fail because old imported
  payments have no `settlement_id`

## Implementation Notes

- `SC.VAL.3WAY.001` no longer treats missing `settlement_id` as an error.
- `SC.VAL.3WAY.001` still reports settlement records without required purchase
  sources when settlement is selected and the settlement is in an approved/done
  state.
- Settlement submit/approve now passes a scoped validator payload for the target
  settlement order records.
- Payment ledger creation still requires an approved payment request. If a
  settlement is selected, the settlement must still be approved or done.
- Smoke validator tests were updated to assert that no-settlement payment
  requests are valid payment facts.

## Verification

Passed:

- task contract validation
- Python compile using a temp pyc output directory
- rollback-only no-settlement payment: create, submit, approve, ledger, done
- rollback-only settlement-linked payment: settlement submit/approve, payment
  submit, approve, ledger, done
- strict check: payment linked to draft settlement is still blocked by
  `P0_PAYMENT_SETTLEMENT_NOT_READY`
- smoke validator Python compile

Conditional / environment-limited:

- `python3 -m py_compile ...` writing into source `__pycache__` failed because
  an existing pycache path is not writable. The same files compiled successfully
  when pyc output was redirected to `/tmp/codex_py_compile_optional_settlement`.
- `DB_NAME=sc_demo make mod.upgrade MODULE=smart_construction_core` was blocked
  by the repository fast upgrade guard because this batch did not touch views,
  security, data, or schema.
- `make verify.restricted` is not defined in the current Makefile.
- `DB_NAME=sc_demo make verify.payment_fact_consistency.v1` failed on existing
  missing demo projects:
  - `展厅-智慧园区运营中心`
  - `展厅-装配式住宅试点`
  - `展厅-产线升级改造工程`
- `DB_NAME=sc_demo make verify.settlement_evidence_guard` failed on the same
  existing missing demo projects.
- `DB_NAME=sc_demo MODULE=smart_construction_core TEST_TAGS=smoke_validator
  scripts/test/test_safe.sh` did not start Odoo tests because the script
  environment is missing `DOCS_MOUNT_HOST`.

These conditional failures are not caused by the optional settlement code path
validated in the rollback-only Odoo shell flow.
