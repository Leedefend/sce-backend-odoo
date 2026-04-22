# Scene Route Boundary Alignment Screen V1

## Scope

This screen evaluates the current system against one frozen rule:

- frontend may consume only backend-orchestrated scene-ready delivery
- backend may reuse native menu/action/model/view/data only as internal input
- even list/form pages must still be delivered as scene-orchestration output

This screen does not propose code changes. It classifies only the currently
visible misalignment families.

## Evidence Base

Bounded inputs:

1. `docs/architecture/frontend_scene_ready_only_contract_governance_topic_v1.md`
2. `docs/architecture/ui_base_vs_scene_ready_contract_v1.md`
3. `docs/architecture/backend_contract_layer_responsibility_freeze_v1.md`
4. `docs/architecture/runtime_entrypoint_inventory_v1.md`
5. `frontend/apps/web/src/api/contract.ts`
6. `frontend/apps/web/src/views/MenuView.vue`
7. `frontend/apps/web/src/views/WorkbenchView.vue`
8. `addons/smart_core/handlers/ui_contract.py`

## Boundary Restatement

The required public chain is:

```text
native menu/action/model/view/data
  -> backend translation / scene orchestration
  -> scene-ready contract
  -> frontend generic consumer
```

Forbidden public chain:

```text
native menu/action/model/view/data
  -> frontend route/bootstrap/render decision
```

Important clarification:

- list pages are not an exception
- form pages are not an exception
- direct structure alignment with backend view facts is still valid only after
  backend orchestration emits a scene-ready surface for frontend consumption

## Current Misalignment Families

### Family A: Multiple public route shapes still carry frontend authority

Current fact:

- frontend still actively uses scene route `/s/:sceneKey`
- frontend also still routes through menu/action/record forms such as `/m`,
  `/a`, and `/r`
- `MenuView.vue` and `WorkbenchView.vue` both branch across these route forms

Why this is misaligned:

- route authority is still split between scene identity and native/intermediate
  identifiers
- frontend therefore still decides whether the next page is addressed by scene,
  menu, action, route string, or record tuple

Classification:

- `route-shape authority leakage`

Owner layer for recovery:

- `scene-orchestration layer`

Required closure:

- backend must expose one canonical scene-facing navigation surface
- frontend must stop treating menu/action/model/record identifiers as parallel
  public route families

### Family B: Frontend navigation still consumes menu/action metadata directly

Current fact:

- `MenuView.vue` resolves leaf and redirect nodes from navigation trees
- it reads and forwards `menu_id`, `menu_xmlid`, `action_id`, `scene_key`, and
  arbitrary `target.route`
- `WorkbenchView.vue` also pushes by tile `route`, `action_id`, `model`, and
  `record_id`

Why this is misaligned:

- frontend shell/workbench still receives and acts on native or transitional
  navigation metadata instead of a single scene-oriented navigation contract
- arbitrary `target.route` remains a public escape hatch

Classification:

- `native navigation metadata leakage`

Owner layer for recovery:

- `scene-orchestration layer`

Required closure:

- backend navigation output must expose scene-target semantics, not mixed raw
  menu/action/model/route instructions
- frontend should execute only declared scene-oriented navigation actions

### Family C: Native `ui.contract` remains a frontend-facing fallback protocol

Current fact:

- `frontend/apps/web/src/api/contract.ts` still builds `ui.contract` requests
  for `action_open` and `model`
- request params still include `model`, `view_type`, `menu_id`, `menu_xmlid`,
  `action_id`, and `scene_key`
- the frontend error message itself tells callers to switch to `/s/:sceneKey`

Why this is misaligned:

- the policy is frozen as "frontend must not use native contract delivery"
- but the frontend codebase still carries a first-class native contract client
  protocol

Classification:

- `native contract consumer residual`

Owner layer for recovery:

- `route and contract delivery boundary`, with backend ownership unchanged and
  frontend cleanup following once replacement entry surfaces are complete

Required closure:

- openability/bootstrap must be satisfied through scene-ready entry paths
- frontend should not keep native contract fetch APIs as ordinary page entry
  tools

### Family D: Backend transitional handler still exposes native operation grammar

Current fact:

- `addons/smart_core/handlers/ui_contract.py` still parses `menu`,
  `action_open`, `model`, and `view`
- it blocks frontend-native delivery with HTTP 410, but the transitional
  operation grammar is still present at the handler boundary

Why this is misaligned:

- current backend runtime is better than frontend because it blocks direct
  native delivery
- however the public boundary is still transitional, not fully converged

Classification:

- `transitional backend delivery boundary`

Owner layer for recovery:

- `scene-orchestration / delivery boundary`

Required closure:

- keep native grammar internal or compatibility-only
- continue converging frontend-visible runtime onto scene-ready scene entry
  paths

### Family E: List/Form consumption is not yet fully scene-entry-only

Current fact:

- there is an active batch to unify `ActionView` list semantics to scene-ready
  only
- there is a blocked batch to recover direct record route bootstrap
- current route and bootstrap paths still imply that list/form work surfaces
  may be entered through action or record identifiers before scene-only closure

Why this is misaligned:

- even when list/form structure is aligned with backend view facts, frontend is
  still not supposed to own the final entry grammar
- list/form pages must be scene-orchestration outputs, not native route
  exceptions

Classification:

- `scene-entry incompleteness for list/form`

Owner layer for recovery:

- `scene-orchestration layer`

Required closure:

- backend must provide complete scene-ready entry semantics for list/form work
  surfaces
- frontend must consume those surfaces without parallel action/model/record
  entry authority

## Screen Conclusion

The current main contradiction is no longer "frontend styling" or "single page
fallback text". The contradiction is:

- frontend routing and bootstrap still retain parallel native/transitional
  authority
- backend has not yet reduced public delivery to one canonical scene-ready
  scene-entry family

Therefore the next closure work must be ordered around route and entry
authority, not around isolated micro UI cleanup.

## Next Candidate Family

`scene-entry authority closure`

## Family Scope

- canonical frontend-visible route family
- scene-oriented navigation target surface
- removal order for public menu/action/model/record route authority
- list/form entry alignment under scene-ready orchestration

## Reason

This family closes the highest-value contradiction directly:

- it attacks the coexistence of scene route and native/transitional route
  families
- it reduces frontend navigation complexity at the boundary, not only inside a
  single page
- it aligns with the frozen product rule that all frontend-visible page
  rendering, including list/form pages, must arrive through backend
  orchestration output
