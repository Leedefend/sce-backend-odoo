# Capability Registry Startup Warmup Screen v1

## Goal

Select the narrowest real startup hook that can seed the current capability
registry artifact before ordinary `system.init` traffic.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: capability registry startup warmup screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: steady-state screening already decided that startup/bootstrap warmup
  is the next bounded move; this screen only decides where that warmup should
  attach

## Current Runtime Facts

### 1. `smart_core.__init__` is module-load only

Current [`addons/smart_core/__init__.py`](/mnt/e/sc-backend-odoo/addons/smart_core/__init__.py)
only imports submodules and writes a log line.

It does not provide:

- database selection
- environment/context
- user-independent registry warmup execution path

So plain module import is not enough to seed the artifact.

### 2. `session.bootstrap` is still request-chain work

Current [`addons/smart_core/v2/handlers/system/session_bootstrap.py`](/mnt/e/sc-backend-odoo/addons/smart_core/v2/handlers/system/session_bootstrap.py)
is an intent handler executed on demand.

That means:

- it still runs because a user/request arrived
- it does not remove first-user startup cost

So it is not a true startup warmup hook.

### 3. Existing cron is not suitable

Current [`addons/smart_core/data/ui_base_contract_asset_cron.xml`](/mnt/e/sc-backend-odoo/addons/smart_core/data/ui_base_contract_asset_cron.xml)
is:

- inactive
- unrelated to capability registry
- time-scheduled, not startup-triggered

So cron does not satisfy the requirement either.

### 4. Manifest currently exposes no startup hook

Current [`addons/smart_core/__manifest__.py`](/mnt/e/sc-backend-odoo/addons/smart_core/__manifest__.py)
does not declare:

- `post_load`
- `pre_init_hook`
- `post_init_hook`

So there is currently no module-owned startup warmup hook in place.

## Candidates Screened

### 1. Warm in `system.init`

Decision: reject

Reason:

- keeps fallback on the ordinary user path
- fails the steady-state objective directly

### 2. Warm in `session.bootstrap`

Decision: reject

Reason:

- still first-user request work
- only shifts the cost earlier in the same chain

### 3. Warm by cron

Decision: reject

Reason:

- not deterministic at process start
- may run too late or not at all before first request

### 4. Warm by external operational script only

Decision: reject as the kernel-owned next step

Reason:

- useful for ops, but not a platform-kernel lifecycle owner
- would leave correctness depending on deployment discipline instead of module
  lifecycle

### 5. Warm through a dedicated module startup hook

Decision: accept as the preferred next hook

Preferred form:

- a manifest-declared startup hook, most likely `post_load`, that delegates into
  a bounded kernel warmup path

Reason:

- this is the first point that is truly startup-owned rather than request-owned
- it keeps warmup inside backend/kernel ownership
- it allows the current in-process artifact store to be seeded before ordinary
  request traffic
- it matches the steady-state objective without requiring persistence first

## Chosen Design

The next implementation batch should target:

- a dedicated module startup hook for `smart_core`

Not:

- request handlers
- cron
- ad hoc operational scripts as the primary owner

## Important Constraint

Because current manifest lacks startup hook declarations, this next batch will
necessarily touch `__manifest__.py`.

That means:

- it is no longer an ordinary low-risk batch
- it needs a dedicated high-risk manifest-scoped task line
- implementation should stay strictly bounded to startup warmup ownership and
  must not expand into unrelated bootstrap refactors

## Recommended Next Batch

Open a dedicated startup-warmup implementation task that:

1. adds the minimal manifest/startup hook needed for `smart_core`
2. delegates into a bounded capability-registry warmup path
3. restarts the runtime
4. verifies that the first real `wutao/demo -> system.init` request after
   restart shows `artifact_fallback_used = 0`

That is the narrowest path that actually removes first-request fallback from the
ordinary user chain.
