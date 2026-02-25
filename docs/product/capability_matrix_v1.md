# Capability Matrix v1.0

Source of truth: `docs/product/capability_matrix_v1.json`

## Scope
- Product capability items: 16
- Audience: PM / Finance / Executive / Owner / Admin
- Intent abstraction: product-facing capability names mapped to internal intents

## Rules
- Every product capability must map to at least one internal intent.
- Every product capability must map to at least one scene.
- Product capability count must remain <= 20 for v1.
- Product capability is business-facing, not technical.

## Delivery Notes
- Core delivery uses `smart_construction_bundle`.
- Owner delivery uses `smart_owner_bundle`.
- Tier gating uses `smart_license_core`.
