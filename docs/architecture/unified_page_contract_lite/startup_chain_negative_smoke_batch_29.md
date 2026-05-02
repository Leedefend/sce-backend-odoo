# Unified Semantic Page Contract Lite - Startup Chain Negative Smoke Batch 29

Date: 2026-05-02
Status: startup-chain negative evidence only

## 1. Boundary

Layer Target: Contract Runtime Preview / Startup Chain Negative Evidence

Module:

- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

Batch-28 proved `api.onchange` Lite opt-in preview through `/api/v1/intent`. Batch-29 proves that startup-chain intents do not emit Lite preview even when Lite-shaped request fields are present.

This batch does not change runtime behavior.

## 2. Negative Cases

The smoke must validate:

- `login` with Lite-shaped params returns `ok=true`
- `login` does not include top-level `lite_preview`
- `system.init` with Lite-shaped params returns `ok=true`
- `system.init` does not include top-level `lite_preview`
- `ui.contract` with Lite-shaped params returns `ok=true`
- `ui.contract` does not include top-level `lite_preview`

## 3. Required Command

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
```

## 4. Report

The smoke writes:

```text
artifacts/backend/unified_page_contract_lite_startup_chain_negative_smoke.json
```

When running inside a container with unwritable artifact mount, it falls back to:

```text
/tmp/unified_page_contract_lite/unified_page_contract_lite_startup_chain_negative_smoke.json
```

## 5. Forbidden Expansion

Batch-29 must not:

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
Lite preview remains limited to api_onchange opt-in.
```

It is not approval to expand Lite runtime to the startup chain.
