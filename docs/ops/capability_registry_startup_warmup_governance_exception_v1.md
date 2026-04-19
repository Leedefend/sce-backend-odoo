# Capability Registry Startup Warmup Governance Exception v1

## Goal

Create a narrow governance exception so the next authorized batch may touch
`addons/smart_core/__manifest__.py` only for capability-registry startup
warmup ownership.

## Why The Exception Is Needed

Current AGENTS rules stop on any `__manifest__.py` change by default.
Existing manifest exceptions cover other scenarios, but not:

- `smart_core` startup hook introduction
- capability-registry warmup ownership
- first-request fallback removal from ordinary `system.init`

So the implementation is currently blocked by governance, not by uncertainty.

## Frozen Exception Scope

The exception must allow only:

1. `addons/smart_core/__manifest__.py`
2. one bounded startup warmup hook file or directly related warmup helper file
3. directly related capability-registry service wiring
4. restart and first-request verification work

## Explicitly Excluded

This exception does not authorize:

- generic bootstrap refactors
- persistence redesign
- frontend changes
- ACL/security work
- payment/settlement/account changes
- unrelated manifest cleanup or module dependency reshaping

## Verification Target For The Follow-Up Batch

The next implementation batch must prove:

- after runtime restart, the first real `wutao/demo -> system.init` request
  shows `artifact_fallback_used = 0`

## Rationale

This is the narrowest exception that matches the already completed screens:

- steady-state screen selected startup warmup
- startup-warmup screen proved a manifest-declared startup hook is the only
  true startup-owned attachment point
- user explicitly authorized proceeding with this high-risk line

So the governance layer should now allow one focused implementation batch and
no more.
