# Unified Semantic Page Contract Lite - api.onchange Preview Acceptance Batch 18

Date: 2026-05-02
Status: runtime acceptance checklist only

## 1. Boundary

Layer Target: Contract Governance / Runtime Acceptance Checklist

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Phase 1 readiness, opt-in request envelope, opt-in response envelope, and negative cases are in place. Batch-18 freezes the acceptance checklist for the first runtime validation batch.

This document is not a runtime implementation.

## 2. First Entry Point

The first runtime validation entry point is:

```text
api.onchange
```

Reason:

- validates Lite patch path first
- avoids full page delivery changes
- avoids `login -> system.init -> ui.contract` default chain changes
- is reversible by disabling opt-in

## 3. Required Opt-in Request

The future request must include:

```json
{
  "contractMode": "lite_preview",
  "contractVersion": "2.0.0",
  "entryPoint": "api_onchange",
  "clientType": "web_pc",
  "fallbackMode": "legacy_default"
}
```

Any missing or different value must keep the legacy default response.

## 4. Required Opt-in Response

The future response must be wrapped as:

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

## 5. Acceptance Requirements

The future runtime validation batch must prove:

- default `api.onchange` request returns unchanged legacy response
- incomplete Lite preview request returns unchanged legacy response
- valid Lite preview request returns opt-in response envelope
- opt-in response `payloadType` is `lite_patch`
- opt-in response payload follows Lite patch shape
- legacy onchange data semantics remain unchanged
- no frontend behavior change is required
- no `ui.contract` output changes
- no `login` output changes
- no `system.init` output changes
- rollback is `disable opt-in flag`

## 6. Required Verification

Future implementation must pass:

```bash
make verify.unified_page_contract.lite
make verify.frontend.onchange_contract_schema.guard
make verify.frontend.onchange_roundtrip.guard
make verify.frontend.x2many_command_semantic.guard
make verify.native_view.semantic_page
```

If any handler default output is touched, the batch must stop and be re-scoped.

## 7. Forbidden In First Runtime Batch

The first runtime batch must not:

- change `login`
- change `system.init`
- change `ui.contract`
- change frontend runtime
- introduce `runtimeContract`
- enable Lite preview by default
- change public intent names
- change default route semantics

## 8. Decision

The next allowed implementation batch is:

```text
Batch-19: api.onchange Lite opt-in preview runtime validation
```

Batch-19 remains optional and must be explicitly started.
