# Unified Semantic Page Contract Lite - api.onchange Preview Runtime Batch 19

Date: 2026-05-02
Status: api.onchange opt-in preview runtime validation

## 1. Boundary

Layer Target: Contract Runtime Preview / api.onchange Opt-in

Module:

- `addons/smart_core/handlers/api_onchange.py`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

Batch-18 froze the api.onchange Lite preview acceptance checklist. Batch-19 implements only that first opt-in preview path.

## 2. Runtime Behavior

Default request:

```text
unchanged legacy api.onchange response
```

Incomplete Lite preview request:

```text
unchanged legacy api.onchange response
```

Valid Lite preview request:

```text
legacy api.onchange response
+ top-level lite_preview envelope
```

The existing `data` payload remains unchanged so current frontend consumers do not need any change.

## 3. Exact Opt-in Predicate

The handler only enables Lite preview when all conditions match:

```text
contractMode == lite_preview
contractVersion == 2.0.0
entryPoint == api_onchange
clientType in web_pc/wx_mini/harmony_h5
fallbackMode == legacy_default
```

## 4. Preview Envelope

The preview envelope is returned under:

```text
lite_preview
```

Shape:

```json
{
  "contractMode": "lite_preview",
  "contractVersion": "2.0.0",
  "entryPoint": "api_onchange",
  "payloadType": "lite_patch",
  "fallbackMode": "legacy_default",
  "payload": {},
  "meta": {
    "previewOnly": true,
    "defaultUnchanged": true
  }
}
```

## 5. Not Changed

This batch does not:

- change `login`
- change `system.init`
- change `ui.contract`
- change frontend runtime
- introduce `runtimeContract`
- enable Lite preview by default
- change public intent names
- change default route semantics

## 6. Rollback

Rollback is one step:

```text
remove or disable _with_lite_preview_if_requested call
```

Default legacy api.onchange behavior remains available because the legacy response is still built first.
