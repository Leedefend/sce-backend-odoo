# Contract Form Behavior Regression Runbook

Date: 2026-07-13
Scope: post-split ContractForm behavior validation
Baseline: `ContractFormPage.vue <= 6000`

## Purpose

This runbook is the release-facing regression baseline for ContractForm after the
P4-P0 split. It complements the code-level guards in `ci.local.quick`; it does
not authorize moving `saveRecord`, `runAction`, or `runOnchangeRoundtrip` out of
their current transaction boundaries.

## Required Gates

| Gate | Command | Purpose |
| --- | --- | --- |
| Local quick | `make ci.local.quick` | PR inner-loop guard for split evidence, runtime protocol, side-effect boundary, helper purity, lint, and strict typecheck. |
| Full PR gate | `make ci` | Required PR gate covering generated inventories, architecture reports, syntax, frontend lint/typecheck/build, contract checks, and E2E preflight. |
| Release browser/container sweep | `make test.e2e` or mapped browser acceptance target | Release-only user-path validation with browser artifacts. |

## Required Evidence

Each release sweep must keep artifacts for failed and fixed runs:

| Evidence | Required content |
| --- | --- |
| Screenshot | Final visible page state for the scenario. |
| Browser log | Console errors, failed requests, and route state. |
| Server/API log | Failed save/action/onchange/config requests and response payloads. |
| Request trace | Relevant create/write/action/onchange/config request and response bodies. |
| Result summary | Scenario id, action id or route, record id when available, expected result, actual result, and pass/fail. |

## Scenario Matrix

| ID | Scenario | Entry | Expected behavior | PR guard | Release validation |
| --- | --- | --- | --- | --- | --- |
| CF-BHV-01 | Edit existing record save | Existing ContractForm route | Dirty editable values are persisted; dirty state clears only after confirmed write; projection refresh follows policy. | `contract_form_save_payload_builder_guard.py`; `contract_form_side_effect_regression_guard.py` | Browser/container save path with persisted readback. |
| CF-BHV-02 | Create record | New ContractForm route | Normalized values are created; pending attachments upload after create; autosave clears; navigation uses created-record runtime. | `contract_form_save_payload_builder_guard.py`; `contract_form_side_effect_regression_guard.py` | Browser/container create path with created record id and navigation evidence. |
| CF-BHV-03 | Save validation failure | Save with invalid required/policy field | Validation returns before `busyKind = 'save'`; errors remain visible; no API write occurs. | `contract_form_side_effect_regression_guard.py` | Browser/container validation path with no write request. |
| CF-BHV-04 | Save API failure | Save with API/network failure | `busyKind` clears in `finally`; feedback is visible; caller receives failure without uncaught throw. | `contract_form_runtime_state_behavior_guard.sh`; `contract_form_side_effect_regression_guard.py` | Browser/container failure injection or captured failed write path. |
| CF-BHV-05 | Normal object/server action | Enabled record action | Save-before-action boundary is respected; action busy clears in `finally`; response navigation or refresh follows action result. | `contract_form_action_plan_builder_guard.py`; `contract_form_side_effect_regression_guard.py` | Browser/container action run with response evidence. |
| CF-BHV-06 | Tier or prompt action | Prompt/tier action | Prompt validation returns before execution; remote failure writes status through runtime state protocol. | `contract_form_runtime_state_protocol_guard.py`; `contract_form_action_plan_builder_guard.py` | Browser/container prompt/tier action path. |
| CF-BHV-07 | Config save | Field order/config operation | `formConfig` begin/end wraps API work; reload and feedback ordering remains in runtime. | `contract_form_runtime_state_behavior_guard.sh`; `contract_form_side_effect_regression_guard.py` | Browser/container config save path. |
| CF-BHV-08 | Inline field policy | Inline policy toggle/update | Busy precheck blocks duplicate writes; `inlinePolicy` clears busy in `finally`. | `contract_form_runtime_state_behavior_guard.sh`; `contract_form_side_effect_regression_guard.py` | Browser/container duplicate-click policy path. |
| CF-BHV-09 | Contract mode action | Contract mode operation | Shared busy/status events are used without changing navigation semantics. | `contract_form_runtime_state_protocol_guard.py`; `contract_form_runtime_state_behavior_guard.sh` | Browser/container contract mode path. |
| CF-BHV-10 | Field onchange | Field value change | Request payload and response patch normalization stay pure; failed onchange is best-effort and silent. | `contract_form_onchange_normalization_guard.py`; `contract_form_side_effect_regression_guard.py` | Browser/container onchange patch path. |
| CF-BHV-11 | Relation onchange | Relation field change | Relation display/id normalization stays in helper; cache/query side effects remain in page transaction. | `contract_form_onchange_normalization_guard.py`; `contract_form_side_effect_regression_guard.py` | Browser/container relation dependency path. |
| CF-BHV-12 | Native structures | group, notebook, statusbar, x2many | Native structure rendering and x2many updates remain governed by contract/runtime guards. | `frontend_page_contract_boundary_guard.py`; `frontend_page_contract_orchestration_consumption_guard.py` | Browser/container native form path. |
| CF-BHV-13 | Collaboration panel | Native collaboration/chatter panel | Panel renders expected copy and does not block save/action/onchange paths. | `frontend_page_contract_boundary_guard.py`; `frontend_contract_consumer_intrusion_guard.py` | Browser/container collaboration path. |
| CF-BHV-14 | Duplicate click | Repeat save/action/config click while busy | Existing global busy guard remains the concurrency boundary; no parallel transaction state is introduced. | `contract_form_runtime_state_behavior_guard.sh`; `contract_form_side_effect_regression_guard.py` | Browser/container duplicate-click path. |
| CF-BHV-15 | Network/action error recovery | Failed save/action/config/reload | Busy/status do not remain stuck after failure; visible error/feedback remains actionable. | `contract_form_runtime_state_behavior_guard.sh`; `contract_form_side_effect_regression_guard.py` | Browser/container failure recovery path. |

## Execution Rules

1. Run `make ci.local.quick` before opening a ContractForm PR.
2. Run `make ci` before marking a ContractForm PR ready.
3. Do not count this runbook as release-complete without browser or container artifacts for the release sweep.
4. Do not migrate `saveRecord`, `runAction`, or `runOnchangeRoundtrip` as part of a regression-only PR.
5. Add new ContractForm behavior to this matrix before adding or changing the user-visible flow.
