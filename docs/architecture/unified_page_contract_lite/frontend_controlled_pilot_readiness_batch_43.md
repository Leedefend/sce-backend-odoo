# Unified Semantic Page Contract Lite - Frontend Controlled Pilot Readiness Batch 43

Date: 2026-05-02
Status: readiness design only

## 1. Boundary

Layer Target: Frontend Governance / Lite Controlled Pilot Readiness

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

`api_onchange` and `load_contract` now have opt-in Lite preview coverage.
The next question is not whether frontend can consume Lite globally. The next
question is what exact gate must exist before a single controlled frontend
pilot can be implemented.

This document is not approved for implementation.

## 2. Decision

Decision:

```text
frontend_pilot_readiness_designed_implementation_not_approved
```

The frontend pilot is allowed to be designed, but not implemented by this
batch.

## 3. Pilot Candidate

Initial candidate:

```text
project.project:tree
```

Allowed source entry:

```text
load_contract opt-in preview
```

Required opt-in envelope:

```json
{
  "contractMode": "lite_preview",
  "contractVersion": "2.0.0",
  "entryPoint": "load_contract",
  "clientType": "web_pc",
  "fallbackMode": "legacy_default"
}
```

The pilot must consume the existing top-level `lite_preview` envelope from
`load_contract`. It must not use `ui.contract`.

## 4. Feature Flag

Required frontend flag:

```text
VITE_LITE_CONTRACT_PILOT=0
```

Required semantics:

- `VITE_LITE_CONTRACT_PILOT=0`: default-off
- `VITE_LITE_CONTRACT_PILOT=1`: allow the pilot route only
- no flag or invalid flag: default-off

Required allowlist:

```text
project.project:tree
```

The implementation batch may define the exact allowlist variable, but it must
not enable more than the single pilot candidate above.

## 5. Frontend Pilot Gate

Before any implementation can begin, the next batch must keep these gates:

```bash
make verify.unified_page_contract.lite
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_live_scope.container
make verify.unified_page_contract.lite.frontend_runtime_negative
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
make verify.frontend.quick.gate
```

The future implementation batch must also add a browser smoke target for the
single pilot page before declaring the pilot usable.

Expected future target name:

```text
verify.unified_page_contract.lite.frontend_pilot_browser.container
```

## 6. Required Runtime Behavior

The future pilot implementation must satisfy:

- default-off
- legacy fallback
- single model/view allowlist
- no `ui.contract`
- no `login`
- no `system.init`
- no `runtimeContract`
- no selector status
- no dependency graph
- no realtime or streaming runtime

Legacy fallback means:

- if `lite_preview` is absent, render existing legacy contract
- if `lite_preview` is invalid, render existing legacy contract
- if the feature flag is off, do not request or consume Lite
- if the model/view is not allowlisted, do not request or consume Lite

## 7. Frontend Runtime Negative Guard Transition

Current rule:

```text
frontend runtime must not contain Lite consumption tokens.
```

This remains true until the implementation batch starts.

Future rule after a pilot implementation exists:

```text
Lite consumption tokens may exist only inside the pilot adapter and pilot route guard.
All non-pilot frontend paths must remain Lite-free.
```

The implementation batch must update the negative guard in the same commit
that introduces the pilot code.

## 8. Stop Conditions

Stop immediately if a plan requires:

- consuming `ui.contract`
- touching `login`
- touching `system.init`
- enabling Lite by default
- removing legacy fallback
- broad frontend runtime consumption
- adding `runtimeContract`
- adding selector status or dependency graph
- introducing realtime, streaming, hydration, scheduler, or UI kernel behavior

## 9. Rollback

This batch makes no runtime change.

Rollback:

```text
remove this readiness document, guard, and Makefile target
```

Future pilot rollback must be:

```text
set VITE_LITE_CONTRACT_PILOT=0 and redeploy frontend
```

No database migration may be required for rollback.
