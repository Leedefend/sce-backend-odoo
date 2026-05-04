# Web Unified Page Contract v2 Gap Matrix v1

Date: 2026-05-05
Branch: `codex/mobile-contract-sync-plan`
Scope: `frontend/apps/web/src`, `scripts/verify`

## Purpose

This matrix closes the web-side v2 contract iteration explicitly. It records
which Unified Page Contract v2 surfaces are consumed by the web ActionView and
record runtime, which browser/guard gates protect the integration, and what is
intentionally out of scope.

## Current Status

Web already consumes Unified Page Contract v2 through shared runtime adapters
instead of a separate mobile-only path. The v2 contract is resolved from direct
payloads, `__unified_page_contract_v2`, or `rawBody.unified_page_contract_v2`.
ActionView and record runtime then consume v2 page info, fields, status,
selectors, actions, and primary dataSource metadata. Browser-level visual
acceptance now renders representative v2 list/form fixtures in Chromium and
captures desktop and narrow screenshots with DOM overflow checks.

## Closed Capability Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| v2 contract resolver | Closed | `unifiedPageContractV2.ts` validates `contractVersion` 2.x and resolves direct, embedded, and raw-body v2 payloads. |
| widget traversal | Closed | v2 layout `containerTree` is walked into field widgets. |
| field status | Closed | `widgetStatus` and inherited `containerStatus` drive web record field readonly/required/visibility. |
| global access | Closed | `globalStatus.pageVisible/pageAuth` feeds access policy and read rights. |
| button status | Closed | `buttonStatus` hides/disables ActionView and record runtime actions. |
| selector status | Closed | `selectorStatus` gates filter and group-by chips. |
| primary dataSource | Closed | v2 `dataSource.primary.params` contributes domain/context/order/limit to list load request and preflight. |
| action projection | Closed | v2 `actionRuleList` is normalized into ActionView action buttons with refresh policy metadata. |
| record runtime projection | Closed | v2 form widgets and actions build record runtime view fields and buttons. |
| surface mode routing | Closed | v2 `pageInfo.viewType` drives ActionView mode, surface intent, navigation, and meta runtime. |
| web v2 guard | Closed | `scripts/verify/unified_page_contract_v2_web_consumer_guard.py` locks the consumer tokens above. |
| browser screenshot acceptance | Closed | `scripts/verify/unified_page_contract_v2_web_visual_acceptance.js` renders representative v2 list/form fixtures in Chromium and writes desktop/narrow screenshots plus JSON report. |
| dedicated v2 visual regression entry | Closed | `verify.unified_page_contract.v2.web_visual_acceptance.host` checks visible v2 surfaces, fields, table, actions, client badges, dataSource summary, console/page errors, and horizontal overflow. |

## Gap Closure Matrix

| Gap ID | Priority | Status | Description | Next Batch Candidate |
| --- | --- | --- | --- | --- |
| W2-G01 | P0 before release | Closed | Browser screenshot acceptance is now artifacted for representative v2 list/form fixtures at desktop and narrow viewport. | Promote to live route smoke after a stable v2 backend action fixture is available. |
| W2-G02 | P2 | Deferred non-goal | v2 partial patch reducer is not required for the current web v2 contract closeout because web actions still use existing action/record refresh semantics. | Add a dedicated web v2 patch reducer only if backend starts returning partial web patches outside existing refresh semantics. |
| W2-G03 | P2 | Closed | Dedicated v2 visual acceptance gate now covers representative dense list/form surfaces, visible controls/actions, client/dataSource metadata, and horizontal overflow. | Extend fixture breadth when new v2 widget families are declared release blockers. |

## Deferred Scope

The following item is intentionally not claimed as part of the current closeout:

- dedicated web v2 partial patch reducer beyond existing refresh/action paths.

## Verification Gates

Every web v2 closeout batch should run:

```bash
python3 scripts/verify/unified_page_contract_v2_web_consumer_guard.py
python3 -m py_compile scripts/verify/unified_page_contract_v2_web_consumer_guard.py
make verify.unified_page_contract.v2.web_visual_acceptance.host
pnpm -C frontend/apps/web typecheck
git diff --check
make verify.unified_page_contract.v2
make verify.docs.all
```
