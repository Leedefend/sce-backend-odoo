# Capability Registry User-Scoping Block Screen v1

## Goal

Explain why the currently planned startup warmup cannot yet guarantee
first-request `artifact_fallback_used = 0` for a real user such as `wutao`.

## Verified Blocking Facts

### 1. Artifact cache key is user-scoped

Current [`capability_registry_service.py`](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/capability/services/capability_registry_service.py)
builds the cache key from:

- db
- platform owner
- mode
- user_id

So materialization is not just runtime-scoped. It is user-scoped.

### 2. Registry build path also consumes user context

Current [`registry.py`](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/capability/core/registry.py)
passes `user` into contribution loading.

Current [`contribution_loader.py`](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/capability/core/contribution_loader.py)
passes `user` into:

- native projection
- extension providers

And native adapters such as menu/model adapters resolve group visibility from
`user` or `env.user`.

So the current artifact is not merely cached per user by accident. Its source
rows are user-shaped.

## Architectural Consequence

Because the artifact is currently user-scoped:

- warming once at startup without a user does not guarantee a hit for `wutao`
- warming once with root/admin does not guarantee semantic equivalence for
  ordinary users
- adding a startup manifest hook right now would not truthfully satisfy the
  previously frozen verification target

Therefore the startup-warmup implementation is blocked by an earlier design
problem:

- capability registry currently mixes user-dependent filtering with artifact
  materialization

## What This Means

The next most important issue is no longer startup hook ownership by itself.
It is:

- separating user-neutral registry facts from user-specific projection or
  access filtering

Until that split exists, startup warmup can only prebuild a user-specific
artifact for some chosen identity, which does not solve the first real-user
steady-state objective.

## Rejected Immediate Move

Reject:

- proceeding directly to manifest/startup warmup implementation now

Reason:

- it would create a technically real warmup path
- but it would not reliably achieve the promised `wutao` first-request
  no-fallback outcome

That would be a misleading batch.

## Recommended Next Batch

Open a bounded architecture screen or implementation task that decides the
smallest split between:

1. user-neutral capability registry artifact
2. user-specific runtime projection/filtering layer

Only after that split is defined should startup warmup be resumed as the next
steady-state move.
