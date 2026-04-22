# BE Project Management Target Action Supply Implement CA

## Goal

Repair the backend `project.management` scene target so the generic frontend
consumer receives an executable scene target without depending on menu-node
reverse inference.

## Boundary

- Layer target: backend scene-orchestration runtime
- Module: `project.management` target semantic supply
- Ownership: `smart_construction_scene` registry fallback + scene version payload
- Reason: real `wutao/demo` verification proved the scene route is now correct,
  but the scene target still lacks explicit action semantics.

## Planned Change

1. Add `action_xmlid=smart_construction_core.action_project_dashboard` to the
   fallback registry entry for `project.management`.
2. Add the same action target to the published scene version payload in
   `project_management_scene.xml`.
3. Add a regression test that freezes this target contract.

## Acceptance

- `validate_task` passes
- targeted `py_compile` passes
- `python3 addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py` passes
- after restart, live browser smoke no longer stalls on missing render target
