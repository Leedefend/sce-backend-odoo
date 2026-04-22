# Non-Auth Boundary Residue Screen After 1057 (ITER-2026-04-05-1058)

## Baseline

- `smart_construction_core/controllers/__init__.py` currently imports only:
  - `auth_signup`
  - `meta_controller`
- four dormant legacy non-auth route files were deleted in `ITER-2026-04-05-1057`.

## Residue Classification

| file | route decorator in file | smart_core wrapper dependency | classification | next action |
| --- | --- | --- | --- | --- |
| `capability_catalog_controller.py` | no | yes (`platform_capability_catalog_api.py`) | active logic provider | keep |
| `insight_controller.py` | no | yes (`platform_preference_insight_api.py`) | active logic provider | keep |
| `ops_controller.py` | no | yes (`platform_ops_api.py`) | active logic provider | keep |
| `pack_controller.py` | no | yes (`platform_packs_api.py`) | active logic provider | keep |
| `preference_controller.py` | no | yes (`platform_preference_insight_api.py`) | active logic provider | keep |
| `scene_controller.py` | no | yes (`platform_scenes_api.py`) | active logic provider | keep |
| `scene_template_controller.py` | no | yes (`platform_scene_template_api.py`) | active logic provider | keep |
| `portal_dashboard_controller.py` | no | yes (`platform_contract_portal_dashboard_api.py`) | active logic provider | keep |
| `capability_matrix_controller.py` | no | no (no active reference found) | dormant logic stub | candidate for dedicated cleanup screen |

## Findings

1. Remaining non-auth files are mostly **logic-provider carriers** consumed by smart_core route-owner wrappers, not direct route-definition surfaces.
2. Immediate additional deletion would risk breaking smart_core delegated execution paths.
3. Only `capability_matrix_controller.py` appears as a dormant non-auth residue candidate under current evidence.

## Suggested Next Batch

- open a dedicated low-risk screen for `capability_matrix_controller.py` ownership and usage proof.
- if still unreferenced after screen, perform bounded single-file cleanup in a separate implement batch.
