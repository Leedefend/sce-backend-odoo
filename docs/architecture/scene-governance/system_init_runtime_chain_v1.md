# System Init Runtime Chain v1

## 1. Goal

Freeze the logical responsibility boundaries of `system.init` before any deeper
physical refactor.

## 2. Current Problem

`system.init` currently assembles:

- scene runtime
- navigation
- capability
- startup shell payload
- diagnostics
- release / extension facts

This makes it powerful but hard to inspect without a fixed runtime vocabulary.

## 3. Logical Segments

### 3.1 Identity Bootstrap

- owner: identity resolver / role surface logic
- input: user/company/role/menu candidates
- output: role surface, landing entry candidate, default route base facts

### 3.2 Scene Bootstrap

- owner: scene runtime orchestrator / registry / provider stack
- input: scene candidates, context, runtime hints
- output: scene target, scene-ready contract inputs, normalize/degrade results

### 3.3 Navigation Bootstrap

- owner: nav adapter / payload builder
- input: menu facts, resolved scene semantics, entry target metadata
- output: startup nav, nav meta, default route entry_target

### 3.4 Capability Bootstrap

- owner: capability provider / capability target resolution
- input: role scope, capability map, explicit target hints
- output: capability groups, capability entry targets, visibility facts

### 3.5 Diagnostics Bootstrap

- owner: diagnostics collectors/builders
- input: trace, drift, resolve errors, timing
- output: diagnostics payload, warnings, timing surfaces

### 3.6 Release / Extension Facts Bootstrap

- owner: extension fact merge layer
- input: industry/enterprise release facts
- output: extension payload, released scene semantic surface

## 4. Current Governance Strategy

- freeze logical segments first
- add observability by segment
- keep the runtime chain readable before considering file splits

## 5. Future Refactor Rule

Physical splitting should only be considered after:

- authority hierarchy is frozen
- entry semantics are frozen
- family governance is stable
- verify guards are trusted
