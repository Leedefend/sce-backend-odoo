# Product Edition Context Log v1

## 2026-03-24

- batch: `Product Edition Stratification v1`
- status: `in_progress`
- scope:
  - product + edition layering
  - edition-aware policy resolution
  - edition-specific scene version binding
  - standard/preview release isolation

## Frozen Facts

- `product_key` remains the compatibility identifier
- `base_product_key + edition_key` is the new edition stratification layer
- preview must never overwrite standard binding behavior
