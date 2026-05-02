# Unified Semantic Page Contract Lite - Opt-in Response Envelope Batch 16

Date: 2026-05-02
Status: opt-in response envelope spec only

## 1. Boundary

Layer Target: Contract Governance / Opt-in Response Envelope Spec

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Batch-15 freezes the request envelope. Batch-16 freezes the response envelope for future Lite preview output.

## 2. Response Envelope

Schema:

```text
docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_response.schema.json
```

Example:

```text
docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_response.example.json
```

Required values:

```text
contractMode = lite_preview
contractVersion = 2.0.0
fallbackMode = legacy_default
meta.previewOnly = true
meta.defaultUnchanged = true
```

Allowed payload types:

- `lite_contract`
- `lite_patch`

## 3. Default Behavior Rule

The response envelope is only valid for explicit Lite preview requests.

Default legacy responses must not be wrapped, replaced, or reshaped by this envelope.

## 4. Still Not Connected

This batch still does not:

- emit this envelope from handlers
- parse opt-in requests in handlers
- import normalizers from handlers
- import adapter from handlers
- change `api.onchange`
- change `ui.contract`
- change `login`
- change `system.init`
- modify frontend runtime
- introduce `runtimeContract`

## 5. Decision

The opt-in response envelope is now frozen as a contract artifact.

Runtime emission remains blocked until a future explicit integration batch.
