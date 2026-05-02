# api.onchange Lite Preview Intent Smoke - Batch 28

Date: 2026-05-02
Status: intent endpoint evidence only

## 1. Boundary

Layer Target: Contract Runtime Preview / Intent Router Evidence

Module:

- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

Batch-27 proved handler/interface behavior through Odoo shell. Batch-28 proves the same behavior through the public `/api/v1/intent` endpoint and the existing login/token flow.

This batch does not change runtime behavior.

## 2. Probe Cases

The smoke must validate:

- login through `/api/v1/intent`
- default `api.onchange` request returns `ok=true`
- default request does not include `lite_preview`
- incomplete opt-in request returns `ok=true`
- incomplete opt-in request does not include `lite_preview`
- valid opt-in request returns `ok=true`
- valid opt-in response includes top-level `lite_preview`
- valid opt-in keeps legacy `data` unchanged
- preview envelope uses `contractMode=lite_preview`
- preview envelope uses `contractVersion=2.0.0`
- preview envelope uses `entryPoint=api_onchange`
- preview envelope uses `payloadType=lite_patch`
- preview payload is `updateType=partial`
- preview payload contains `statusPatch`, `dataPatch`, and `layoutPatch`

## 3. Required Command

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_intent.container
```

## 4. Report

The smoke writes:

```text
artifacts/backend/unified_page_contract_lite_api_onchange_preview_intent_smoke.json
```

When running inside a container with unwritable artifact mount, it falls back to:

```text
/tmp/unified_page_contract_lite/unified_page_contract_lite_api_onchange_preview_intent_smoke.json
```

## 5. Forbidden Expansion

Batch-28 must not:

- change `login`
- change `system.init`
- change `ui.contract`
- change `load_contract`
- change frontend runtime
- enable Lite preview by default
- introduce `runtimeContract`
- perform data writes

## 6. Decision

Passing this smoke means only:

```text
api.onchange Lite opt-in preview has intent endpoint evidence.
```

It is not approval to expand Lite runtime beyond `api_onchange`.
