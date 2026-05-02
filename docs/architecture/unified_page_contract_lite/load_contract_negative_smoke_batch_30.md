# Unified Semantic Page Contract Lite - load_contract Negative Smoke Batch 30

Date: 2026-05-02
Status: load_contract negative evidence only

## 1. Boundary

Layer Target: Contract Runtime Preview / Load Contract Negative Evidence

Module:

- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

Batch-29 proved startup-chain intents do not emit Lite preview. Batch-30 proves `load_contract` also remains outside Lite preview runtime even when Lite-shaped request fields are present.

This batch does not change runtime behavior.

## 2. Negative Case

The smoke must validate:

- `load_contract` with Lite-shaped params returns `ok=true`
- `load_contract` does not include top-level `lite_preview`
- `load_contract.data` does not include `lite_preview`

## 3. Required Command

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container
```

## 4. Report

The smoke writes:

```text
artifacts/backend/unified_page_contract_lite_load_contract_negative_smoke.json
```

When running inside a container with unwritable artifact mount, it falls back to:

```text
/tmp/unified_page_contract_lite/unified_page_contract_lite_load_contract_negative_smoke.json
```

## 5. Forbidden Expansion

Batch-30 must not:

- change `login`
- change `system.init`
- change `ui.contract`
- change `load_contract`
- change frontend runtime
- enable Lite preview by default
- introduce `runtimeContract`
- perform data writes

## 6. Decision

Passing this smoke means:

```text
load_contract remains outside Lite preview runtime.
```

It is not approval to expand Lite runtime to page-load contracts.
