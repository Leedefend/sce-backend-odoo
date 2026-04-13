# Form Contract Render Profile v1

## Purpose

Freeze the consumption contract for `ui.contract` form render profiles so backend and frontend use the same truth-source and priority rules.

## Canonical Data Model

- `views.form.layout` is the only form layout truth source.
- `semantic_page.form_semantics.layout_source` must be `views.form.layout`.
- `semantic_page.form_semantics` is semantic-only, not a duplicated layout tree.
- `fields` is the canonical field metadata source.
- `layout.fieldInfo` is layout-only projection (`name/label/widget/colspan/modifiers`).

## Render Surfaces

The contract must expose:

- `render_surfaces.create`
- `render_surfaces.edit`
- `render_surfaces.readonly`

Each surface provides:

- `field_names`
- `readonly`
- `actions.header_buttons`
- `actions.button_box`
- `actions.stat_buttons`
- `subviews`

## Consumption Rules

- `render_profile` indicates the currently effective runtime mode.
- Frontend must consume the matching `render_surfaces.<profile>` first.
- If `render_surfaces` is missing, fallback to `views.form` with conservative defaults.

## Modifiers Priority

`modifiers priority` order:

1. surface-level readonly (`render_surfaces.<profile>.readonly`)
2. field-level canonical flags from `fields`
3. layout-level `fieldInfo.modifiers`

When conflicts exist, stricter constraint wins (`readonly/invisible/required` safety-first).

## Actions Priority

`actions priority` order:

1. `render_surfaces.<profile>.actions.*`
2. `views.form.header_buttons/button_box/stat_buttons`
3. `action_groups` (grouped projection only)

Action identity must use composite key (`name/method/action_id/ref`) to avoid name-only merge errors.

## Subview Rules

- `render_surfaces.<profile>.subviews` is the profile-level behavior projection.
- Subview structural truth comes from `views.form.subviews`.
- x2many subviews must include:
  - `relation_model`
  - `tree.columns`
  - `fields` metadata aligned with columns
  - `policies` (`inline_edit/can_create/can_unlink/can_open`)

## Compatibility Policy

- Additive only for current phase.
- No frontend inferred business semantics outside contract.
- Any new profile field must be backward-compatible and documented in this file before consumption switch.
