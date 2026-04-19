# Capability Registry Startup Warmup High-Risk Authorization v1

## Goal

Freeze the exact high-risk scope for the next startup-warmup implementation now
that the user has explicitly authorized proceeding.

## User Authorization

The user explicitly authorized:

- execute this high-risk iteration

This authorization is interpreted narrowly and only for the startup-warmup
objective already screened in the current chain.

## Frozen High-Risk Scope

The next implementation batch is authorized only for:

1. adding the minimum `smart_core` manifest/startup hook needed to trigger
   warmup
2. adding one bounded warmup entry path that seeds the existing capability
   registry artifact
3. restarting the dev runtime
4. verifying that the first real `wutao/demo -> system.init` request after
   restart shows `artifact_fallback_used = 0`

## Explicitly Out Of Scope

The next implementation batch must not expand into:

- persistence redesign
- frontend changes
- product contract changes
- business semantics
- generic bootstrap framework work
- unrelated manifest cleanup

## Target Verification Condition

Success for the next high-risk implementation batch means:

- after runtime restart, the first ordinary `system.init` request no longer
  rebuilds through fallback
- `artifact_fallback_used = 0` on that first real request

## Risk Statement

The risk is specifically:

- touching `addons/smart_core/__manifest__.py`
- introducing a startup hook into module lifecycle

The batch remains acceptable only because:

- the scope is frozen to startup warmup ownership
- the warmup target already uses the existing capability registry service
- all correctness and invalidation boundaries were proven before reaching this
  point

## Next Batch Constraint

The immediate next batch must remain a single-objective high-risk
implementation:

- manifest hook
- bounded warmup path
- restart
- first-request verification

No second objective is allowed.
