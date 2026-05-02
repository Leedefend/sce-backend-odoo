# Unified Semantic Page Contract Lite - Phase 2 load_contract Preview Batch 39

Date: 2026-05-02
Status: implemented

## 1. Boundary

Layer Target: Contract Runtime / Lite load_contract Opt-In Preview

Module:

- `addons/smart_core/core/unified_page_contract_lite_preview.py`
- `addons/smart_core/handlers/load_contract.py`
- `scripts/verify`
- `Makefile`

Reason:

Batch 38 defined the implementation gate. This batch implements the smallest
approved runtime expansion: `load_contract` may return a top-level
`lite_preview` only when the request is a complete explicit opt-in.

## 2. Implemented Scope

Allowed runtime entries now:

```text
api_onchange opt-in preview
load_contract opt-in preview
```

The `load_contract` preview is:

```text
backend-only preview
```

Frontend consumption remains blocked.

## 3. Request Shape

Valid opt-in requires:

```json
{
  "contractMode": "lite_preview",
  "contractVersion": "2.0.0",
  "entryPoint": "load_contract",
  "clientType": "web_pc",
  "fallbackMode": "legacy_default"
}
```

Any missing or invalid field keeps legacy behavior.

## 4. Response Shape

Valid opt-in may add:

```text
top-level lite_preview
```

with:

```text
payloadType=lite_contract
```

Legacy `data` remains unchanged.

## 5. Still Blocked

Still blocked:

```text
ui.contract
login
system.init
frontend runtime
runtimeContract
```

The frontend still must not contain:

```text
lite_preview
payloadType
lite_patch
lite_contract
runtimeContract
UnifiedPageContractLite
unified_page_contract_lite
```

## 6. Verification

Required positive guards:

```bash
DB_NAME=sc_demo make verify.unified_page_contract.lite.load_contract_preview_interface
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_preview_intent.container
```

Required negative guards:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
make verify.unified_page_contract.lite.frontend_runtime_negative
```

Required live scope aggregate guard:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_live_scope.container
```

Required aggregate guard:

```bash
make verify.unified_page_contract.lite
```

## 7. Rollback

Rollback:

```text
remove or disable load_contract with_lite_preview_if_requested branch
```

Rollback does not require:

- database migration
- frontend deployment
- public intent rename
- user data cleanup
