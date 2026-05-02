# api.onchange Lite Preview Interface Probe - Batch 27

Date: 2026-05-02
Status: handler/interface evidence only

## 1. Boundary

Layer Target: Contract Runtime Preview / api.onchange Interface Evidence

Module:

- `addons/smart_core/handlers/api_onchange.py`
- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

Batch-20 proved Lite preview behavior with a side-effect-free helper. Batch-27 adds an Odoo shell probe that calls `ApiOnchangeHandler` through the handler boundary with a real Odoo `env`.

This batch does not change runtime behavior.

## 2. Probe Cases

The probe must validate:

- default `api.onchange` params return `ok=true`
- default params do not include `lite_preview`
- incomplete opt-in params return `ok=true`
- incomplete opt-in params do not include `lite_preview`
- valid opt-in params return `ok=true`
- valid opt-in params include top-level `lite_preview`
- valid opt-in keeps legacy `data` unchanged
- preview envelope uses `contractMode=lite_preview`
- preview envelope uses `contractVersion=2.0.0`
- preview envelope uses `entryPoint=api_onchange`
- preview envelope uses `payloadType=lite_patch`
- preview payload is `updateType=partial`
- preview payload contains `statusPatch`, `dataPatch`, and `layoutPatch`

## 3. Required Command

```bash
DB_NAME=sc_demo make verify.unified_page_contract.lite.api_onchange_interface
```

## 4. Report

The Odoo shell probe first tries to write:

```text
/mnt/artifacts/backend/unified_page_contract_lite_api_onchange_preview_interface.json
```

If the container user cannot write that mount, the probe falls back to:

```text
/tmp/unified_page_contract_lite/unified_page_contract_lite_api_onchange_preview_interface.json
```

The report is also printed to stdout, so a mount permission issue must not mask handler behavior.

## 5. Forbidden Expansion

Batch-27 must not:

- change `login`
- change `system.init`
- change `ui.contract`
- change `load_contract`
- change frontend runtime
- enable Lite preview by default
- introduce `runtimeContract`
- perform data writes

## 6. Decision

Passing this probe means only:

```text
api.onchange Lite opt-in preview has handler/interface evidence.
```

It is not approval to expand Lite runtime beyond `api_onchange`.
