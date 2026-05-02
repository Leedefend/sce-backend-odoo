# Unified Semantic Page Contract Lite - Opt-in Negative Cases Batch 17

Date: 2026-05-02
Status: opt-in negative cases

## 1. Boundary

Layer Target: Contract Governance / Opt-in Negative Cases

Module:

- `docs/architecture/unified_page_contract_lite/fixtures`
- `scripts/verify`
- `Makefile`

Reason:

Batch-15 and Batch-16 froze the opt-in request/response envelopes. Batch-17 adds negative request fixtures proving that default or incomplete requests do not qualify as Lite preview.

## 2. Negative Fixtures

Fixtures:

```text
docs/architecture/unified_page_contract_lite/fixtures/default_load_contract_request_v1.json
docs/architecture/unified_page_contract_lite/fixtures/default_ui_contract_request_v1.json
docs/architecture/unified_page_contract_lite/fixtures/default_onchange_request_v1.json
docs/architecture/unified_page_contract_lite/fixtures/invalid_lite_preview_missing_version_request_v1.json
```

These must all evaluate as:

```text
not lite preview
```

## 3. Positive Fixture

The existing request example remains the only positive fixture:

```text
docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.example.json
```

It must evaluate as:

```text
lite preview
```

## 4. Still Not Connected

This batch still does not:

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

Default requests remain legacy by construction.

Future runtime implementation must use the same strict predicate:

```text
contractMode == lite_preview
contractVersion == 2.0.0
entryPoint in allowed entry points
clientType in allowed client types
```
