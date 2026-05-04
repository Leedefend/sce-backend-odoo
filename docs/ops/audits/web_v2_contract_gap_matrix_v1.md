# Web Unified Page Contract v2 Gap Matrix v1

Date: 2026-05-05
Branch: `codex/mobile-contract-sync-plan`
Scope: `frontend/apps/web/src`

## Purpose

This matrix closes the web-side v2 contract iteration explicitly. It records
which Unified Page Contract v2 surfaces are consumed by the web ActionView and
record runtime, which gates protect the integration, and what remains deferred.

## Current Status

Web already consumes Unified Page Contract v2 through shared runtime adapters
instead of a separate mobile-only path. The v2 contract is resolved from direct
payloads, `__unified_page_contract_v2`, or `rawBody.unified_page_contract_v2`.
ActionView and record runtime then consume v2 page info, fields, status,
selectors, actions, and primary dataSource metadata.

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

## Remaining Gap Matrix

| Gap ID | Priority | Status | Description | Next Batch Candidate |
| --- | --- | --- | --- | --- |
| W2-G01 | P0 before release | Partial | Browser runtime screenshot acceptance for v2 web ActionView is not yet artifacted in this branch. | Add Playwright acceptance against a representative v2 contract route when a stable test fixture is available. |
| W2-G02 | P2 | Deferred | v2 patch application in web ActionView remains routed through existing action/record refresh paths rather than a dedicated patch reducer. | Add a web-specific v2 patch reducer only if backend starts returning partial web patches outside existing refresh semantics. |
| W2-G03 | P2 | Deferred | Advanced visual regression coverage for dense v2 form/list states is not a dedicated gate. | Extend existing form visual acceptance to include a v2 contract fixture. |

## Deferred Scope

The following items are intentionally not claimed closed:

- browser screenshot acceptance for a live representative v2 route;
- dedicated web v2 partial patch reducer beyond existing refresh/action paths;
- exhaustive visual regression for every v2 widget family.

## Verification Gates

Every web v2 closeout batch should run:

```bash
python3 scripts/verify/unified_page_contract_v2_web_consumer_guard.py
python3 -m py_compile scripts/verify/unified_page_contract_v2_web_consumer_guard.py
pnpm -C frontend/apps/web typecheck
git diff --check
make verify.unified_page_contract.v2
make verify.docs.all
```
