# Navigation Smoke Gap Analysis 2026-03-23

## Problem Statement

Manual review exposed two release-facing problems:
- the `项目立项` sidebar entry could land on a legacy form shell instead of the intended product page
- the PM sidebar exposed only one visible entry, creating a misleading release surface

Existing browser smoke and guards passed, but they did not detect either problem.

## Root Causes

### 1. Slice browser smoke bypassed the published navigation surface

The FR-1 to FR-5 browser smoke scripts do not start from the real sidebar entry path.

They log in and then navigate directly to:

```text
/f/project.project/new?scene_key=projects.intake&intake_mode=quick
```

This validates the slice chain itself, but it does not validate:
- sidebar discoverability
- menu-click routing correctness
- release navigation information architecture

Affected scripts include:
- `scripts/verify/first_release_slice_browser_smoke.mjs`
- `scripts/verify/second_slice_browser_smoke.mjs`
- `scripts/verify/cost_slice_browser_smoke.mjs`
- `scripts/verify/payment_slice_browser_smoke.mjs`
- `scripts/verify/settlement_slice_browser_smoke.mjs`

### 2. Existing menu guards verify metadata, not user-visible routing outcome

Current menu smoke mainly checks:
- whether a menu node exposes `scene_key`
- whether menu-scene metadata is structurally resolvable

It does not check:
- whether clicking the actual sidebar entry lands on the intended product page
- whether the user still falls into a legacy action/form shell
- whether the sidebar composition is appropriate for release

Relevant guards:
- `scripts/verify/fe_menu_scene_key_smoke.js`
- `scripts/verify/fe_menu_scene_resolve_smoke.js`

### 3. Role-surface verification only asserts non-empty nav

Current role-surface smoke verifies:
- role code
- landing scene key
- landing path format
- nav is non-empty

It does not verify:
- the minimum required release entries for a role
- sidebar grouping quality
- whether navigation is too thin for a released product surface

Relevant guard:
- `scripts/verify/role_surface_smoke.py`

### 4. Browser smoke uses a service account rather than the reviewed demo role

Most release browser smoke uses:
- `svc_e2e_smoke`

Manual review used:
- `demo_pm`

That means role-specific sidebar and release-navigation behavior for the demo PM surface was not directly covered by the released browser path.

### 5. Console and page errors are collected, but not treated as hard failures

The release browser smoke scripts append:
- `console_errors`
- `page_errors`

But they do not fail merely because those arrays are non-empty.

So a route/runtime defect can exist on a release-facing surface and still pass if the main scripted chain continues successfully.

## Why The Problem Escaped Release Gates

The released gates were optimized for:
- slice functional continuity
- product chain block presence
- end-to-end creation and progression

They were not optimized for:
- release entry correctness
- published sidebar quality
- role-specific navigation completeness

The current gap is therefore a release-navigation governance gap, not a single-script bug.

## Required Fix Direction

The fix must be handled as a release-navigation batch, not as a casual UI tweak.

The new coverage must add:
- a browser smoke that starts from login and enters through the real sidebar
- a role-nav guard that asserts minimum release entries for the demo PM role
- a release contract that defines what the sidebar must expose for released slices

## Non-Fix Directions

Do not treat this issue as:
- an isolated CSS/sidebar styling problem
- a one-off hardcoded frontend menu patch
- a reason to reopen FR-1 to FR-5 business scope

## Conclusion

The current release verification stack proves that the slices work when entered directly.

It does not yet prove that users can discover and enter those slices through the published sidebar surface.

This gap is now formally elevated into the release-navigation batch.
