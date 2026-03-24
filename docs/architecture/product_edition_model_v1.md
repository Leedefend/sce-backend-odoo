# Product Edition Model v1

## Goal

Introduce a minimal `product + edition` stratification layer without replacing the existing product policy model.

## Model Strategy

Keep:

- `product_key`

Add:

- `base_product_key`
- `edition_key`

This preserves current runtime compatibility while allowing edition-aware policy resolution.

## First Editions

- `construction.standard`
- `construction.preview`

Resolved as:

```text
base_product_key = construction
edition_key = standard / preview
product_key = construction.standard / construction.preview
```

## Runtime Rule

Delivery runtime resolves policy by:

```text
product_key
or
base_product_key + edition_key
```

## Scene Binding Rule

Edition policy owns its own `scene_version_bindings`.

This allows:

- standard edition -> stable v1
- preview edition -> stable v2

for the same released scene key, without cross-edition pollution.
