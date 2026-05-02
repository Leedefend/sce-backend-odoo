# Unified Semantic Page Contract Lite - Opt-in Envelope Batch 15

Date: 2026-05-02
Status: opt-in envelope spec only

## 1. Boundary

Layer Target: Contract Governance / Opt-in Envelope Spec

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Batch-14 defines runtime integration as opt-in only. Batch-15 freezes the opt-in envelope shape before any runtime code can consume it.

## 2. Envelope

Schema:

```text
docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.schema.json
```

Example:

```text
docs/architecture/unified_page_contract_lite/lite_runtime_opt_in_envelope.example.json
```

Required fields:

- `contractMode`
- `contractVersion`
- `entryPoint`
- `clientType`

Required values:

```text
contractMode = lite_preview
contractVersion = 2.0.0
fallbackMode = legacy_default
```

Allowed entry points:

- `load_contract`
- `ui_contract`
- `api_onchange`

## 3. Default Behavior Rule

No request may enter Lite mode without:

```text
contractMode = lite_preview
contractVersion = 2.0.0
```

Absence of this envelope must mean:

```text
legacy_default
```

## 4. Still Not Connected

This batch still does not:

- parse this envelope in handlers
- import normalizers from handlers
- import adapter from handlers
- change `api.onchange`
- change `ui.contract`
- change `login`
- change `system.init`
- modify frontend runtime
- introduce `runtimeContract`

## 5. Decision

The opt-in envelope is now frozen as a contract artifact.

Runtime consumption remains blocked until a future explicit integration batch.
