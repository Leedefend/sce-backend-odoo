# Capability Warmup Session Chain Screen v1

## Goal

Choose the narrowest session-chain hook that can move user-scoped capability
warmup ahead of ordinary `system.init`.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: user-scoped capability warmup session-chain screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: the user explicitly accepts company/user-scoped semantics and first
  user warmup, so the next optimization is to move that warmup earlier in the
  session chain instead of redesigning global artifact ownership

## Relevant Current Facts

### 1. `system.init` currently pays the warmup cost

Current `system.init` still calls `load_capabilities_for_user_with_timings()`,
so the first page-init request is where user-scoped artifact warmup happens.

### 2. `session.bootstrap` v2 is too thin

Current [`session_bootstrap_service.py`](/mnt/e/sc-backend-odoo/addons/smart_core/v2/services/session_bootstrap_service.py)
only reports bootstrap metadata and does not own the authenticated user
materialization path needed for capability warmup.

So using it as the primary first move would require extra session-chain wiring
first.

### 3. `login` already owns the exact user context we need

Current [`login.py`](/mnt/e/sc-backend-odoo/addons/smart_core/handlers/login.py)
already:

- authenticates the real user
- loads user profile from the authenticated DB
- decides `bootstrap.next_intent = system.init`

So it is the earliest existing hook that:

- has the real user identity
- is already on the accepted first-session path
- can warm user-scoped capability artifact without touching page-init logic

## Candidates Screened

### 1. Keep warmup in `system.init`

Decision: reject

Reason:

- leaves page-init carrying the first-user build cost

### 2. Move warmup into `session.bootstrap` first

Decision: reject as the immediate next move

Reason:

- current implementation is too thin
- would add an extra refactor hop before solving the real user-visible issue

### 3. Warm directly in `login`

Decision: accept as the preferred next bounded move

Reason:

- earliest existing hook with authenticated user context
- already leads immediately into `system.init`
- smallest code movement to shift cost earlier without changing public flow

## Chosen Next Step

The next implementation batch should:

- add a bounded capability warmup call in `LoginHandler` after authentication
  and profile resolution, before returning the login response

The warmup should:

- seed the existing user-scoped registry artifact for that authenticated user
- avoid changing login contract shape
- keep `system.init` as the canonical consumer

## Recommended Verification

After implementation:

1. restart runtime
2. real `wutao/demo` login
3. first real `system.init` request should show `artifact_fallback_used = 0`

That verifies the first-user warmup has been moved off the page-init path and
into the login chain.
