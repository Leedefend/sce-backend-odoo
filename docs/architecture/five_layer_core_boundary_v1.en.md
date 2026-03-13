# Five-Layer Core Boundary v1

## Goal
Freeze the five-layer boundary so future iterations stay on the "backend orchestration, frontend consumption" path.

## Five Layers
1. **Business Truth Layer**
   - Owns: models, state machines, constraints, business methods, permission facts.
   - Must not: output UI structures or rendering strategies.

2. **Native Expression Layer**
   - Owns: Odoo form/tree/kanban/search declarations, modifiers, button declarations.
   - Must not: role-based product orchestration.

3. **Native Parse Layer**
   - Owns: lossless parsing from native definitions to structured native outputs.
   - Must not: inject role strategy, scene special-cases, frontend display policy.

4. **Contract Governance Layer**
   - Owns: unified contract egress, policy shaping, traceable mapping evidence.
   - Must not: create business truth or own scene UX decisions.

5. **Scene Orchestration Layer**
   - Owns: role/task page orchestration (page/zone/block/action composition).
   - Must not: parse XML directly or consume parser-private internals.

## Frontend Consumption Rules
- Frontend consumes **scene orchestration result contracts** directly (e.g. `page_orchestration_v1` and action/data schema).
- `native_view/semantic_page` are orchestration inputs, not direct frontend decision sources.
- Frontend must not hardcode page structure by `sceneKey/model`.

## Delivery Chain
`Business Truth -> Native Expression -> Native Parse -> Contract Governance -> Scene Orchestration -> Frontend`

## Hard Prohibitions
1. Frontend page-structure branching by `sceneKey`.
2. Frontend product-semantic branching by specific `model` (except generic capability probing).
3. Scene layer consuming parser-private structures directly.
4. Governance layer mutating business truth.

## Iteration Entry Criteria
Each frontend iteration must declare:
- `Layer Target: Frontend Layer`
- contract input fields from scene orchestration result
- no newly introduced scene/model hardcoded branches

