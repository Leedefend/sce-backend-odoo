# Workflow State Unification Plan

Date: 2026-06-14

## Implemented Baseline

2026-06-14 first backend/frontend baseline:

- Backend service: `sc.workflow.contract.service`
  - file: `addons/smart_construction_core/models/support/workflow_contract_service.py`
  - reads one existing record and returns a projection only; it does not mutate business data.
  - first profiles: `payment.request`, `sc.settlement.order`, `sc.expense.claim`, `construction.contract`, `sc.payment.execution`, `sc.receipt.income`, `sc.invoice.registration`, `sc.self.funding.registration`, `sc.financing.loan`, `sc.treasury.reconciliation`.
  - publishes `evidenceGate` for missing prerequisites and uses it to disable blocked workflow actions.
- Contract injection:
  - file: `addons/smart_construction_core/core_extension.py`
  - hook: `smart_core_finalize_unified_page_contract_v2`
  - only injects for form contracts with an existing `record_id`.
  - output fields:
    - `workflowContract`
    - `runtimeContract.workflowContract`
    - `statusContract.globalStatus.workflowPhase`
    - `statusContract.globalStatus.approvalPhase`
- Frontend consumption:
  - file: `frontend/apps/web/src/pages/ContractFormPage.vue`
  - header actions now prefer `workflowContract.availableActions` when present.
  - legacy/native buttons with the same backend method are suppressed, so the frontend does not show duplicate approval/submit/complete actions.
  - native form-tree buttons also call the same workflow state resolver before rendering and before execution; XML/native buttons must not bypass backend workflow gates.
  - disabled workflow actions are driven by backend `enabled=false`, `reason_code`, and `blocked_message`.
  - backend `evidenceGate` rows are rendered as a visible "办理前置条件" block near the top of the form; users should not need to hover disabled buttons to understand what is missing.
  - if no `workflowContract` exists, existing action fallback remains.
- Regression tests:
  - file: `addons/smart_construction_core/tests/test_workflow_contract_backend.py`
  - covers draft expense claim, submitted settlement, done payment request, v2 hook injection, and evidence gates for deduction lines, settlement lines, payment basis, contract close prerequisites, cashflow execution request anchors, invoice prerequisites, self-funding evidence, financing counterparty, and treasury ledger reconciliation.
  - verifies that a settlement detail gate and the backend `action_submit()` guard fail on the same invalid business fact, so frontend disabling is not the only enforcement point.

This baseline intentionally preserves existing raw `state` values. It only standardizes the projected business meaning and available action contract.

2026-06-15 coverage closeout:

- `workflowContract` profiles now cover the custom business workflow form surface inventoried in `sc_demo`.
- Current inventory reports `workflowContract covered: 71 models`.
- The only uncovered models that still expose workflow methods are standard Odoo models:
  - `account.move`
  - `purchase.order`
  - `stock.picking`
- These standard models are explicit exceptions in `scripts/verify/workflow_contract_custom_coverage_guard.py`; they are not considered hidden custom form gaps.
- If any new custom business model exposes workflow methods or workflow state fields, it must either publish a `workflowContract` profile or be deliberately added to a documented exception list with a reason.

## Problem

Business forms currently expose workflow state through several independent surfaces:

- model-specific `state` or `*_state` selections
- tier approval fields: `validation_status`, `can_review`, `review_ids`
- XML header buttons and invisible expressions
- V2 `statusContract` / `actionContract`
- frontend fallback filters in `ContractFormPage.vue`

This lets different business domains drift. A button can be correct in one entry path and wrong in another, because the frontend is forced to infer business state from mixed sources.

## Target Rule

The frontend is state-dumb.

It renders the statebar, approval status, and available actions from backend contracts. It does not infer whether a business action is allowed from labels, XML fragments, or stale route/session action context.

Native XML buttons are only display carriers. If a native button maps to a canonical workflow method such as `action_submit`, `validate_tier`, `reject_tier`, or `action_done`, the frontend must resolve its disabled/title state from `workflowContract.availableActions` and `workflowContract.evidenceGate` before it can be displayed or executed.

The backend action method remains the final authority. `workflowContract` is a projection for display, disabled state, and user guidance; it must mirror the same business checks enforced by model methods such as `action_submit`, `action_on_tier_approved`, `action_approval_decision`, and `action_done`.

## Contract Governance Rule

`workflowContract` is the workflow authority for form rendering, but it is not a new business fact store.

Rules:

- Source authority: workflow facts come from the business model and approval/tier state; `sc.workflow.contract.service` only projects them.
- Scope: every custom business form with workflow state or workflow transition methods must publish `workflowContract`.
- Exception scope: standard Odoo models may be excluded only when listed in `workflow_contract_custom_coverage_guard.py` with an explicit reason.
- Frontend scope: frontend consumers may render, disable, hide duplicates, and show evidence messages from `workflowContract`; they must not infer workflow permission from button labels, raw XML invisibility, route context, or stale session action state.
- Backend scope: backend action methods remain the enforcement point and must reject invalid transitions even if a client bypasses UI disabled state.
- Contract placement: `ui.contract.v2` exposes `workflowContract` at the top level and mirrors it under `runtimeContract.workflowContract` for compatibility; other contract blocks may reference workflow phase, but must not recalculate it.
- Statusbar rule: `workflowContract.statusbar` is the only workflow fallback source for business statusbar rendering when native XML statusbar is absent. New-record forms must not render workflow statusbar because no persisted business workflow fact exists yet.
- Coverage rule: inventory coverage is measured against custom business workflow forms, not every installed Odoo model. Standard Odoo exceptions must stay visible in the generated inventory.

Required gates:

- `ENV=dev DB_NAME=sc_demo make audit.workflow_state.inventory`
- `python3 scripts/verify/workflow_inventory_profile_method_guard.py`
- `python3 scripts/verify/workflow_contract_custom_coverage_guard.py`
- `ENV=dev DB_NAME=sc_demo make verify.workflow_contract.browser.create_statusbar.host`
- `ENV=dev DB_NAME=sc_demo make verify.workflow_contract`

## Canonical State Layers

Do not force every model to rename its existing `state` values. Instead, every workflow-enabled model must project its current record into these canonical layers.

### Business Phase

`business_phase` describes the document lifecycle.

- `draft`: editable draft, not submitted
- `submitted`: business user submitted the document
- `under_review`: tier approval is waiting or pending
- `approved`: business approval is complete, but final business posting/completion has not happened
- `effective`: business document is effective/signed/confirmed, if the domain distinguishes this from approved
- `done`: terminal successful completion
- `cancelled`: terminal cancellation
- `rejected`: returned by approval
- `legacy_confirmed`: imported historical fact accepted as already valid
- `open`: operational item remains open
- `closed`: operational item has been closed

### Approval Phase

`approval_phase` describes only approval.

- `none`: no approval flow exists or has not started
- `waiting`: approval has been requested but no active reviewer is assigned yet
- `pending`: active reviewer can act
- `approved`: tier approval validated
- `rejected`: tier approval rejected

### Editability

`editability` is derived by backend policy:

- `editable`: user may edit business fields
- `readonly`: user may view but not edit
- `locked`: record cannot be edited because of terminal state, audit lock, historical import, or downstream facts

### Evidence Gate

`evidence_gate` reports missing prerequisites for the next action.

Examples:

- missing deduction bill lines
- missing attachment
- missing settlement anchor
- missing payment request link
- amount mismatch between header and detail lines
- approval not validated

## Canonical Action Keys

Every workflow form should publish available actions using these semantic keys where applicable:

- `save_draft`
- `submit`
- `approve`
- `reject`
- `business_approve`
- `complete`
- `cancel`
- `reopen`
- `return`

The action row must include:

- `key`
- `label`
- `method`
- `visible`
- `enabled`
- `reason_code`
- `blocked_message`
- `requires_reason`
- `semantic`

Frontend display text can stay business-specific, but the semantic key must be stable.

## Backend Contract

Backend projection shape:

```json
{
  "stateField": "state",
  "rawState": "submit",
  "businessPhase": "under_review",
  "approvalPhase": "pending",
  "editability": "readonly",
  "evidenceGate": [
    {
      "reasonCode": "DEDUCTION_BILL_MISSING_LINES",
      "message": "扣款登记必须填写至少一条扣款单明细后才能提交、批准或完成。",
      "actionKeys": ["submit", "approve", "complete"],
      "blocking": true,
      "severity": "block"
    }
  ],
  "availableActions": [
    {
      "key": "approve",
      "method": "validate_tier",
      "label": "审批通过",
      "enabled": false,
      "reason_code": "DEDUCTION_BILL_MISSING_LINES",
      "blocked_message": "扣款登记必须填写至少一条扣款单明细后才能提交、批准或完成。"
    }
  ]
}
```

`ui.contract.v2` exposes this projection as `workflowContract`. The frontend must treat this projection as the authority for:

- statusbar visible steps
- header buttons
- button disabled/visible state
- action execution refresh policy

Statusbar acceptance boundary:

- Existing-record forms may render native XML statusbar first, then `workflowContract.statusbar` as the governed workflow fallback.
- New-record forms must not render workflow statusbar. The create path can show create/save actions, but it must not invent a business workflow phase before a record id exists.
- Frontend code may only choose the display source and enforce this persisted-record boundary; it must not define workflow phase sequences or terminal labels locally.

Every blocking `evidenceGate` row should have a matching model-level guard before the state transition mutates data. Current first-batch hard guards:

- `sc.expense.claim`: `_check_business_ready()` is called by `action_submit`, `action_approve`, `action_on_tier_approved`, and `action_done`.
- `payment.request`: payment basis and settlement/material-settlement balance checks are called by submit, approval, approval-decision, and done paths.
- `sc.settlement.order`: `_check_business_anchor_or_raise()` and related consistency checks are called by submit, approve, tier-approved callback, and done paths.
- `sc.payment.execution`: `_check_business_anchor_or_raise()` and request scope checks are called by confirm and paid paths.
- `sc.receipt.income`: `_check_business_anchor_or_raise()` and request scope checks are called by confirm and received paths.
- `sc.invoice.registration`: `_check_business_anchor()` is called by confirm, register, and tier-approved callback paths.
- `sc.self.funding.registration`: `_check_done_ready()` is called by confirm and done paths.
- `sc.financing.loan`: `_check_done_ready()` is called by confirm and done paths.
- `sc.treasury.reconciliation`: `_check_reconcile_ready()` is called by confirm and reconcile paths.

## Implementation Order

1. Inventory all workflow surfaces with `scripts/audit/workflow_state_inventory.py`.
2. Add a backend workflow adapter service that can describe one record without mutating it.
3. Implement profiles for the first covered high-risk models:
   - `payment.request`
   - `sc.settlement.order`
   - `sc.expense.claim`
   - `construction.contract`
   - `sc.payment.execution`
   - `sc.receipt.income`
   - `sc.invoice.registration`
   - `sc.self.funding.registration`
   - `sc.financing.loan`
   - `sc.treasury.reconciliation`
4. Wire `ui.contract.v2` to expose `workflowState` and `availableActions`.
5. Change `ContractFormPage.vue` to render workflow buttons only from backend available actions when present.
6. Add regression tests for:
   - create route may inherit menu action context
   - edit route must not inherit stale `session.currentAction`
   - draft/submitted/pending/approved/done button sets
   - approval rejection path
   - evidence gate messages
7. Migrate remaining domains by profile, not by frontend conditionals.
8. Keep the custom business form coverage guard green before declaring workflow form coverage complete.

## Local Verification Notes

The dev nginx service mounts `frontend/apps/web/dist-dev`, not the default Vite `dist`.

Use this command when rebuilding the static frontend served on `http://127.0.0.1:18081`:

```bash
VITE_BUILD_OUT_DIR=dist-dev pnpm --dir frontend/apps/web exec vite build --mode development
docker compose restart nginx
```

Do not copy the default production `dist` into `dist-dev`: production mode reads `frontend/apps/web/.env.production` and locks the app to `sc_prod`, which breaks local `sc_demo` acceptance.

Last verified commands:

```bash
python3 -m py_compile addons/smart_construction_core/models/support/workflow_contract_service.py addons/smart_construction_core/tests/test_workflow_contract_backend.py scripts/audit/workflow_state_inventory.py
ENV=dev DB_NAME=sc_demo make audit.workflow_state.inventory
python3 scripts/verify/workflow_inventory_profile_method_guard.py
python3 scripts/verify/workflow_contract_custom_coverage_guard.py
pnpm --dir frontend/apps/web run typecheck:strict
VITE_BUILD_OUT_DIR=dist-dev pnpm --dir frontend/apps/web exec vite build --mode development
DOCS_MOUNT_HOST=./docs DOCS_MOUNT_CONT=/mnt/docs ADDONS_EXTERNAL_MOUNT=/mnt/addons_external/oca_server_ux DB_NAME=sc_demo MODULE=smart_construction_core TEST_TAGS='/smart_construction_core:TestWorkflowContractBackend' bash scripts/test/test_safe.sh
DOCS_MOUNT_HOST=./docs DOCS_MOUNT_CONT=/mnt/docs ADDONS_EXTERNAL_MOUNT=/mnt/addons_external/oca_server_ux DB_NAME=sc_demo MODULE=smart_construction_core TEST_TAGS='/smart_construction_core:TestUserFeedbackBusinessViews.test_deduction_registration_action_creates_deduction_bill_lines' bash scripts/test/test_safe.sh
ENV=dev DB_NAME=sc_demo make restart
ENV=dev DB_NAME=sc_demo make verify.workflow_contract
```

Browser evidence:

- Deduction evidence: `artifacts/workflow-evidence-gate-browser-workflow-contract-required/workflow-evidence-gate.json` and `workflow-evidence-gate.png`.
- Contract close evidence: `artifacts/workflow-evidence-gate-browser-contract-close-workflow-contract-required/workflow-evidence-gate.json` and `workflow-evidence-gate.png`.

Make target knobs: `WORKFLOW_CONTRACT_FRONTEND_URL`, `WORKFLOW_CONTRACT_DB_NAME`, `WORKFLOW_CONTRACT_EXPENSE_RECORD_ID`, and `WORKFLOW_CONTRACT_CLOSE_RECORD_ID`.

## First Profile Mapping

### `sc.expense.claim`

- raw `draft` + `validation_status=no`: `draft`, approval `none`
- raw `submit` + `validation_status in waiting,pending`: `under_review`, approval same as validation
- raw `submit` + `validation_status=validated`: `approved`, approval `approved`
- raw `approve`: `approved`
- raw `done`: `done`
- raw `cancel`: `cancelled`
- raw `legacy_confirmed`: `legacy_confirmed`

Evidence gates:

- noncash deduction bill requires at least one `deduction_line_ids`
- deduction bill header amount must equal line total
- categories requiring attachment must have attachment before submit/approve/done

### `payment.request`

- raw `draft`: `draft`
- raw `submit`: `under_review` until tier validated
- raw `approve`: `approved`
- raw `done`: `done`
- raw `cancel`: `cancelled`

Evidence gates:

- payment request must link to settlement where the business category requires settlement anchor
- amount must not exceed settlement payable balance
- approval must be validated before business approval/final payment execution

Business boundary:

- `payment.request` is the application/approval basis.
- `sc.payment.execution` and `sc.receipt.income` are actual cashflow facts.
- A new-system actual cashflow fact must point back to an approved payment/receipt request; otherwise the workflow must block before confirmation or actual paid/received registration.

### `sc.settlement.order`

- raw `draft`: `draft`
- raw `submit`: `under_review` until tier validated
- raw `approve`: `approved`
- raw `done`: `done`
- raw `cancel`: `cancelled`
- raw `legacy_confirmed`: `legacy_confirmed`

Evidence gates:

- settlement detail/material/labor facts must exist where the business category requires them
- settlement amount must be internally consistent
- payment request links are downstream and must not drive settlement state

### `construction.contract`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending; do not mutate the business state while tier approval is running
- raw `confirmed`: `approved`
- raw `running`: `effective`
- raw `closed`: `done`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `activate`: `action_set_running`
- `complete`: `action_close`
- `cancel`: `action_cancel`
- `reopen`: `action_reset_draft`

Evidence gates:

- project and contract party must exist
- duplicate submit is blocked while unified approval is already waiting/pending
- close/complete requires contract lines
- downstream payment/settlement references lock cancel and reset-to-draft

### `sc.payment.execution`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending; do not mutate the business state while tier approval is running
- raw `confirmed`: `approved`
- raw `paid`: `done`
- raw `legacy_confirmed`: `legacy_confirmed`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `complete`: `action_paid` displayed as `已付款`
- `cancel`: `action_cancel`

Evidence gates:

- actual payment must link an approved payment request
- actual payment must have project, counterparty, contract or settlement basis, positive paid amount, payer account, and payee account
- duplicate submit is blocked while unified approval is already waiting/pending

### `sc.receipt.income`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending; do not mutate the business state while tier approval is running
- raw `confirmed`: `approved`
- raw `received`: `done`
- raw `legacy_confirmed`: `legacy_confirmed`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `complete`: `action_received` displayed as `已收款`
- `cancel`: `action_cancel`

Evidence gates:

- actual receipt must link an approved receipt request
- actual receipt must have project, contract, counterparty, positive receipt amount, and receiving account
- duplicate submit is blocked while unified approval is already waiting/pending

### `sc.invoice.registration`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending
- raw `confirmed`: `approved`
- raw `registered`: `done`
- raw `legacy_confirmed`: `legacy_confirmed`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `complete`: `action_register` displayed as `已登记`
- `cancel`: `action_cancel`

Evidence gates:

- invoice registration must have invoice date and valid amount
- regular invoice registration must have invoice number
- prepaid tax registration must have tax certificate number
- contract, settlement, project, and counterparty must be internally consistent
- duplicate submit is blocked while unified approval is already waiting/pending

Business boundary:

- invoice registration is a tax/票据 fact.
- It can reference contract and settlement facts, but it is not a payment request and must not drive settlement or cashflow state by itself.

### `sc.self.funding.registration`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending
- raw `confirmed`: `approved`
- raw `done`: `done`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `complete`: `action_done`
- `cancel`: `action_cancel`

Evidence gates:

- self-funding must have project, contractor, date, and positive amount
- manual self-funding must have attachment, company account, and contractor account
- refund amount must not exceed company-contractor self-funding balance; this remains enforced by backend model guard
- duplicate submit is blocked while unified approval is already waiting/pending

Business boundary:

- self-funding is a company-contractor responsibility and cash responsibility fact.
- It should be separated from ordinary payment requests and from noncash deduction bill details.

### `sc.financing.loan`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending
- raw `confirmed`: `approved`
- raw `done`: `done`
- raw `legacy_confirmed`: `legacy_confirmed`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `complete`: `action_done`
- `cancel`: `action_cancel`

Evidence gates:

- financing/loan must have project, counterparty, date, and positive amount
- borrowed-fund handling must use the specific contractor-project or project-company borrowing categories
- duplicate submit is blocked while unified approval is already waiting/pending

Business boundary:

- financing/loan registration is a funding responsibility fact.
- Borrowing between company, project, and contractor is separate from ordinary payment request settlement flow.

### `sc.treasury.reconciliation`

- raw `draft`: `draft`
- raw `draft` + `validation_status in waiting,pending`: business `draft`, approval waiting/pending
- raw `confirmed`: `approved`
- raw `reconciled`: `done`
- raw `legacy_confirmed`: `legacy_confirmed`
- raw `cancel`: `cancelled`

Action mapping:

- `submit`: `action_confirm`
- `approve`: `validate_tier`
- `reject`: `reject_tier`
- `complete`: `action_reconcile` displayed as `对账完成`
- `cancel`: `action_cancel`

Evidence gates:

- treasury reconciliation must link a posted treasury ledger
- ledger project must match reconciliation project
- bank-enterprise difference must be zero
- duplicate submit is blocked while unified approval is already waiting/pending

Business boundary:

- treasury reconciliation is an internal cash ledger control fact.
- It verifies posted treasury ledger data; it should not create payment application facts or settlement facts.

## Boundary Decisions

- Existing model `state` values are preserved initially.
- No frontend hard-coded business workflow rules are added.
- XML invisible expressions remain as compatibility input, but backend workflow projection becomes the higher authority.
- Historical data gets explicit `legacy_confirmed`, not silently mapped to `done`.
- Cashflow and noncash business processes must have separate evidence gates.

## 2026-06-14 Validation Snapshot

- Backend workflow projection test suite passed: `TEST_TAGS='/smart_construction_core:TestWorkflowContractBackend' bash scripts/test/test_safe.sh`, 19 tests, 0 failures. This includes profile method integrity, which verifies every non-empty workflow action method declared by the backend profiles exists on the target Odoo model, frontend-stable workflow contract schema coverage for every supported model profile, and no-email contract cancellation coverage.
- Deduction registration regression passed: `TEST_TAGS='/smart_construction_core:TestUserFeedbackBusinessViews.test_deduction_registration_action_creates_deduction_bill_lines' bash scripts/test/test_safe.sh`, 1 test, 0 failures.
- Frontend strict typecheck and development build passed: `pnpm --dir frontend/apps/web run typecheck:strict`; `VITE_BUILD_OUT_DIR=dist-dev pnpm --dir frontend/apps/web exec vite build --mode development`.
- Browser evidence gate passed for `sc.expense.claim#273134`: evidence reasons `DEDUCTION_BILL_MISSING_LINES` and `EXPENSE_ATTACHMENT_REQUIRED`, `提交审批` disabled with backend message. The browser script now also requires the target `ui.contract.v2` response to include `workflowContract` for `sc.expense.claim#273134`.
- Browser evidence gate passed for `construction.contract#13159`: evidence reason `CONTRACT_MISSING_LINES_FOR_CLOSE`, `完成` disabled with backend message, and stale native workflow buttons `提交审批|审批通过|审批驳回|重置为草稿` hidden. The browser script now also requires the target `ui.contract.v2` response to include `workflowContract` for `construction.contract#13159`.
- Frontend workflow action execution now treats `cancel` as a local navigation action only when it has no backend method; workflow contract `cancel` actions with `action_cancel` continue to execute through the normal server/object button path.
- Browser click evidence for `construction.contract#13210` confirmed that the visible native cancel button `作废` emits `execute_button` with `button.name=action_cancel`; direct backend shell execution of `action_cancel` on the same sample succeeded and moved the record to `cancel`.
- Contract state transitions now treat chatter posting as best-effort for permission/business validation failures only: missing sender email no longer rolls back `action_confirm`, `action_set_running`, `action_close`, `action_cancel`, or `action_reset_draft`, while non-business/system exceptions still surface. Backend coverage includes a no-email business user cancelling a contract, and browser evidence for `construction.contract#13249` confirms `execute_button/action_cancel` returns HTTP 200 with `reasonCode=OK` and record state `cancel`.
- After the contract message side-effect fix, frontend strict typecheck, Vite development build, deduction evidence gate browser acceptance, and contract close evidence gate browser acceptance all passed again. A first browser rerun hit a transient served static asset mismatch on `18081`; direct asset checks later returned HTTP 200 and sequential browser reruns passed.
- Web Contract V2 architecture guard now locks `workflowContract` propagation through `unifiedPageContractV2CompatProjection.ts` and `ContractFormPage.vue`: raw V2 `workflowContract`, `runtimeContract.workflowContract`, legacy projection `workflowContract`, and form evidence/action consumers are all covered by static tokens. `make verify.unified_page_contract.v2.web_architecture` passed.
- Browser acceptance artifacts now include `targetWorkflowResponses`, `workflowModel`, `workflowRecordId`, and `availableActionKeys`, making workflow contract presence a direct acceptance requirement rather than an inferred UI-only condition.
- Workflow contract acceptance is now exposed as `make verify.workflow_contract`, chaining backend workflow tests, the deduction registration regression, frontend strict typecheck, Web Contract V2 frontend architecture guards, frontend static build, and browser evidence samples. Browser-only acceptance remains available as `make verify.workflow_contract.browser.host`, with separate deduction and contract-close sub-targets plus overridable sample knobs.
- Browser workflow samples assert backend evidence codes and action dedupe directly: deduction registration must expose `DEDUCTION_BILL_MISSING_LINES` and render exactly one `提交审批` button; contract close must expose `CONTRACT_MISSING_LINES_FOR_CLOSE`, render exactly one `完成` button, and keep stale native workflow buttons hidden.
- Workflow inventory refresh is exposed as `make audit.workflow_state.inventory`; the method scan now includes the business terminal and approval methods used by first-batch profiles, including `action_confirm`, `action_approval_decision`, `action_close`, `action_paid`, `action_received`, `action_register`, and `action_reconcile`. `verify.workflow_contract.backend` also runs `workflow_inventory_profile_method_guard.py` so inventory method coverage stays aligned with backend profiles.
- Static gates passed: Python compile for workflow service/tests/audit script, Node syntax check for browser acceptance script, and `git diff --check`.
- Known limitation: no existing frontend unit harness is present in `frontend/apps/web`; workflow action alias dedupe is covered through typecheck/build plus browser contract-close alias behavior, not by a dedicated frontend unit test.
