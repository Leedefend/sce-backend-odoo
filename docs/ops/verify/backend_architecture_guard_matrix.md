# Backend Architecture Guard Matrix

This matrix maps governance checkpoints to executable verification targets.

## P0 Platform Correctness

| Guard | Target(s) | Status |
|---|---|---|
| G0.1 Intent layer must avoid business hardcoding | `make verify.intent.router.purity` | Covered |
| G0.2 Contract envelope consistency (`ok/data/meta`) | `make verify.contract.mode.smoke` + `make verify.contract.api.mode.smoke` | Covered (behavior) |
| B1.1 Business module must not assemble runtime scene/capability shape | `make verify.backend.boundary_guard` | Covered |
| B1.2 Runtime scene reads only through provider in smart_core | `make verify.scene.provider.guard` + `make verify.backend.boundary_guard` | Covered |

## P1 Boundary / Permission / Isolation

| Guard | Target(s) | Status |
|---|---|---|
| B1.3 extension hook only writes `ext_facts` namespace | `make verify.backend.boundary_guard` | Covered |
| B2.1 Model layer must not depend on scene UI registry | `make verify.boundary.import_guard` | Partially covered |
| B2.2 Controllers delegate to handler/service contract path | `make verify.backend.boundary_guard` | Covered (runtime import/route constraints) |
| P3.1 SceneProvider unified runtime entry | `make verify.scene.provider.guard` | Covered |
| P4.1 `available/reason` must not be in scene definitions | `make verify.scene.definition.semantics` | Covered |
| P4.2 Permission semantics centralized in contract governance path | `make verify.contract.governance.coverage` + `make verify.boundary.guard` | Covered |
| D1.1 Demo/seed must not leak into core provider path | `make verify.seed.demo.isolation` | Covered |
| D1.2 Demo data should not leak in user contract path | `make verify.seed.demo.isolation` + `make verify.scene.demo_leak.guard` | Covered |

## P2 Stability / HUD / Snapshot

| Guard | Target(s) | Status |
|---|---|---|
| S1.1 Contract snapshot baseline | `make verify.contract.snapshot` | Covered (scene shape baseline) |
| S1.2 Deterministic contract ordering | `make verify.contract.ordering.smoke` + `make verify.contract.snapshot` | Covered |
| H1.1 Default user mode, hud gated by flag | `make verify.mode.filter` | Covered |
| H1.2 HUD tracing fields coverage | `make verify.scene.hud.trace.smoke` + `make verify.scene.meta.trace.smoke` | Covered |

## Aggregated Targets

- `make verify.boundary.guard`
- `make verify.contract.snapshot`
- `make verify.mode.filter`
- `make verify.capability.schema`
- `make verify.scene.schema`
- `make verify.seed.demo.isolation`

## Notes

- "Partially covered" marks areas where behavior is protected but could still use stricter AST/schema assertions.
- Current baseline is non-destructive: guards are focused on boundary hardening and output governance, not architecture rewrites.
