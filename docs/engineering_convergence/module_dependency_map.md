# Module Dependency Map

Generated from addon manifests.

## Summary

- Addon modules: `13`
- Internal dependency edges: `19`
- External Odoo dependency references: `20`
- Circular internal dependencies: `0`
- Missing internal-like dependencies: `0`

## Modules

| Module | Version | Installable | Application | Internal Depends | External Depends | Reverse Internal Depends |
| --- | --- | --- | --- | --- | --- | --- |
| `sc_norm_engine` | 17.0.1.0.0 | yes | no | smart_construction_core | uom | - |
| `smart_construction_bootstrap` | 17.0.0.1.0 | yes | no | - | base | smart_construction_seed |
| `smart_construction_bundle` | 0.1.0 | yes | no | smart_construction_core, smart_construction_portal, smart_construction_scene, smart_core, smart_license_core, smart_scene | - | smart_construction_demo |
| `smart_construction_core` | 17.0.0.61 | yes | yes | smart_core | account, auth_signup, base_tier_validation, base_tier_validation_server_action, hr, mail, product, project, purchase, stock, uom, web | sc_norm_engine, smart_construction_bundle, smart_construction_portal, smart_construction_scene, smart_construction_seed |
| `smart_construction_demo` | 0.2.0 | yes | no | smart_construction_bundle | account | - |
| `smart_construction_portal` | 17.0.1.1 | yes | no | smart_construction_core | web | smart_construction_bundle |
| `smart_construction_scene` | 17.0.0.3 | yes | no | smart_construction_core, smart_scene | - | smart_construction_bundle |
| `smart_construction_seed` | 17.0.0.2.1 | yes | no | smart_construction_bootstrap, smart_construction_core | account | - |
| `smart_core` | 17.0.1.0 | yes | no | - | base, web | smart_construction_bundle, smart_construction_core, smart_license_core, smart_owner_bundle, smart_owner_core, smart_scene |
| `smart_license_core` | 0.1.0 | yes | no | smart_core | - | smart_construction_bundle |
| `smart_owner_bundle` | 0.1.0 | yes | no | smart_core, smart_owner_core | - | - |
| `smart_owner_core` | 0.1.0 | yes | no | smart_core | - | smart_owner_bundle |
| `smart_scene` | 1.0.0 | yes | no | smart_core | base | smart_construction_bundle, smart_construction_scene |

## Internal Edges

| From | To |
| --- | --- |
| `sc_norm_engine` | `smart_construction_core` |
| `smart_construction_bundle` | `smart_construction_core` |
| `smart_construction_bundle` | `smart_construction_portal` |
| `smart_construction_bundle` | `smart_construction_scene` |
| `smart_construction_bundle` | `smart_core` |
| `smart_construction_bundle` | `smart_license_core` |
| `smart_construction_bundle` | `smart_scene` |
| `smart_construction_core` | `smart_core` |
| `smart_construction_demo` | `smart_construction_bundle` |
| `smart_construction_portal` | `smart_construction_core` |
| `smart_construction_scene` | `smart_construction_core` |
| `smart_construction_scene` | `smart_scene` |
| `smart_construction_seed` | `smart_construction_bootstrap` |
| `smart_construction_seed` | `smart_construction_core` |
| `smart_license_core` | `smart_core` |
| `smart_owner_bundle` | `smart_core` |
| `smart_owner_bundle` | `smart_owner_core` |
| `smart_owner_core` | `smart_core` |
| `smart_scene` | `smart_core` |

## Circular Dependencies

No circular internal dependencies detected.

## Missing Internal-Like Dependencies

No missing internal-like dependencies detected.

## Boundary Notes

- `smart_core` should remain the platform core and avoid depending on construction business modules.
- Construction modules may depend on platform modules, but platform modules must not depend back on construction domains.
- Bundle, seed, demo, and portal modules should stay at the outer edge of the dependency graph.
- Any new cross-domain dependency requires an ADR before becoming part of the release baseline.
