# Product Edition Lifecycle Model v1

## Goal

Upgrade edition delivery from a parseable stratification layer to a governed release channel.

## Scope

This model governs:

- `construction.standard`
- `construction.preview`

within `sc.product.policy`.

It does not reopen FR-1 to FR-5 and does not replace Delivery Engine v1.

## Core Fields

Edition lifecycle is stored on `sc.product.policy`:

- `base_product_key`
- `edition_key`
- `state`
- `access_level`
- `allowed_role_codes`
- `activated_at`
- `deprecated_at`
- `state_reason`
- `promotion_note`
- `promoted_from_policy_id`

## Lifecycle States

- `draft`
- `ready`
- `preview`
- `stable`
- `deprecated`

## Allowed Transitions

- `draft -> ready`
- `ready -> preview`
- `ready -> stable`
- `preview -> stable`
- `preview -> deprecated`
- `stable -> deprecated`

Forbidden:

- `draft -> preview`
- `draft -> stable`
- `deprecated -> *`

## Access Levels

- `public`
  - runtime can resolve for any released role
- `role_restricted`
  - runtime resolves only for explicitly allowed role codes
- `internal`
  - runtime never releases to external delivery surface

## Runtime Resolution Rules

Delivery runtime resolves edition policy in this order:

1. requested `product_key` / `edition_key`
2. validate lifecycle state is releaseable
3. validate access level against `role_surface.role_code`
4. if invalid, fallback to public stable edition under the same `base_product_key`
5. if no released stable edition exists, fallback to default `construction.standard`

## Releaseable States

For runtime delivery:

- `preview`
- `stable`

Non-releaseable:

- `draft`
- `ready`
- `deprecated`

## Stable Uniqueness

For one `base_product_key`, only one public active stable edition should be treated as runtime fallback target.

Current governance uses service-level control instead of SQL-level partial uniqueness.

## Promotion and Rollback

Promotion is handled by `ProductEditionPromotionService`.

Supported operations:

- promote to `ready`
- promote to `preview`
- promote to `stable`
- deprecate
- rollback to previous stable edition within the same `base_product_key`

Rollback strategy:

- current stable edition is deprecated
- previous deprecated stable edition is reactivated as stable

## First Released Mapping

- `construction.standard`
  - state: `stable`
  - access: `public`
- `construction.preview`
  - state: `preview`
  - access: `role_restricted`
  - allowed roles: `pm`, `executive`
