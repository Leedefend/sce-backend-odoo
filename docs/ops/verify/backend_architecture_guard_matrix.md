# Backend Architecture Guard Matrix

This matrix maps governance checkpoints to executable verification targets.

## P0 Platform Correctness

| Guard | Target(s) | Status |
|---|---|---|
| G0.1 Intent layer must avoid business hardcoding | `make verify.intent.router.purity` | Covered |
| G0.2 Contract envelope consistency (`ok/data/meta`) | `make verify.contract.envelope` + `make verify.contract.envelope.guard` | Covered |
| G0.3 Baseline policy integrity for governance guards | `make verify.baseline.policy_integrity.guard` | Covered |
| B1.1 Business module must not assemble runtime scene/capability shape | `make verify.backend.boundary_guard` + `make verify.business.shape.guard` | Covered |
| B1.2 Runtime scene reads only through provider in smart_core | `make verify.scene.provider.guard` + `make verify.backend.boundary_guard` | Covered (baseline policy: `scene_provider_guard.json`) |
| B1.2.a Backend boundary policy must remain baseline-governed | `make verify.backend.boundary_guard` + `make verify.baseline.policy_integrity.guard` | Covered (`backend_boundary_guard.json`) |

## P1 Boundary / Permission / Isolation

| Guard | Target(s) | Status |
|---|---|---|
| B1.3 extension hook only writes `ext_facts` namespace | `make verify.backend.boundary_guard` | Covered |
| B2.1 Model layer must not depend on scene UI registry | `make verify.boundary.import_guard` | Covered |
| B2.2 Controllers delegate to handler/service contract path | `make verify.backend.boundary_guard` + `make verify.controller.boundary.guard` | Covered |
| P3.1 SceneProvider unified runtime entry | `make verify.scene.provider.guard` | Covered |
| P3.2 CapabilityProvider unified runtime entry | `make verify.capability.provider.guard` | Covered |
| P4.1 `available/reason` must not be in scene definitions | `make verify.scene.definition.semantics` | Covered |
| P4.2 Permission semantics centralized in contract governance path | `make verify.contract.governance.coverage` + `make verify.boundary.guard` | Covered |
| C1.1 Business core journey intent coverage baseline | `make verify.business.core_journey.guard` + `make verify.business.capability_baseline.guard` | Covered |
| C1.2 Role capability floor baseline | `make verify.role.capability_floor.guard` + `make verify.business.capability_baseline.guard` | Covered |
| C1.3 Prod-like role fixture floor (non-demo) | `make verify.role.capability_floor.prod_like` | Covered |
| C1.4 Prod-like role evidence schema stability | `make verify.role.capability_floor.prod_like.schema.guard` | Covered |
| D1.1 Demo/seed must not leak into core provider path | `make verify.seed.demo.isolation` | Covered |
| D1.1.a Runtime modules must not import demo/seed addons | `make verify.seed.demo.import_boundary.guard` + `make verify.seed.demo.isolation` | Covered |
| D1.2 Demo data should not leak in user contract path | `make verify.seed.demo.isolation` + `make verify.scene.demo_leak.guard` | Covered |

## P2 Stability / HUD / Snapshot

| Guard | Target(s) | Status |
|---|---|---|
| S1.1 Contract snapshot baseline | `make verify.contract.snapshot` | Covered (scene shape baseline) |
| S1.2 Deterministic contract ordering | `make verify.contract.ordering.smoke` + `make verify.contract.catalog.determinism` + `make verify.contract.snapshot` | Covered |
| A1.1 Catalog/runtime scene surface alignment | `make verify.scene.catalog.runtime_alignment.guard` + `make verify.scene.catalog.governance.guard` | Covered |
| A1.2 Scene catalog source semantics invariants | `make verify.scene.catalog.source.guard` + `make verify.scene.catalog.governance.guard` | Covered |
| E1.1 Contract evidence bundle includes alignment/baseline signals | `make verify.contract.evidence.guard` (with `contract_evidence_guard_baseline.json`) | Covered |
| E1.2 Contract assembler semantic smoke (pm/executive, user/hud) | `make verify.contract.assembler.semantic.smoke` | Covered |
| E1.2.a Contract assembler semantic evidence schema stability | `make verify.contract.assembler.semantic.schema.guard` | Covered |
| E1.3 Runtime surface dashboard report (warning-only thresholds) | `make verify.runtime.surface.dashboard.report` | Covered |
| E1.3.a Runtime surface dashboard evidence schema stability | `make verify.runtime.surface.dashboard.schema.guard` | Covered |
| E1.3.b Runtime surface dashboard strict warning gate (optional) | `make verify.runtime.surface.dashboard.strict.guard` | Covered (enabled by `SC_RUNTIME_SURFACE_STRICT=1`) |
| E1.4 Backend architecture full summary report | `make verify.backend.architecture.full.report` | Covered |
| E1.4.a Backend architecture full summary schema stability | `make verify.backend.architecture.full.report.schema.guard` | Covered |
| E1.4.b Backend architecture full summary baseline policy guard | `make verify.backend.architecture.full.report.guard` | Covered |
| E1.5 Backend evidence manifest integrity guard | `make verify.backend.evidence.manifest.guard` | Covered |
| H1.1 Default user mode, hud gated by flag | `make verify.mode.filter` | Covered |
| H1.2 HUD tracing fields coverage | `make verify.scene.hud.trace.smoke` + `make verify.scene.meta.trace.smoke` | Covered |

## Aggregated Targets

- `make verify.boundary.guard`
- `make verify.contract.envelope`
- `make verify.contract.envelope.guard`
- `make verify.contract.snapshot`
- `make verify.mode.filter`
- `make verify.capability.schema`
- `make verify.scene.schema`
- `make verify.seed.demo.isolation`
- `make verify.seed.demo.import_boundary.guard`
- `make verify.backend.architecture.full`
- `make verify.backend.architecture.full.report`
- `make verify.phase_next.evidence.bundle`
- `make verify.controller.boundary.guard`
- `make verify.scene.catalog.runtime_alignment.guard`
- `make verify.scene.catalog.source.guard`
- `make verify.scene.catalog.governance.guard`
- `make verify.capability.provider.guard`
- `make verify.role.capability_floor.prod_like`
- `make verify.role.capability_floor.prod_like.schema.guard`
- `make verify.contract.assembler.semantic.smoke`
- `make verify.contract.assembler.semantic.schema.guard`
- `make verify.runtime.surface.dashboard.report`
- `make verify.runtime.surface.dashboard.schema.guard`
- `make verify.runtime.surface.dashboard.strict.guard`
- `make verify.backend.architecture.full.report`
- `make verify.backend.architecture.full.report.schema.guard`
- `make verify.backend.architecture.full.report.guard`
- `make verify.backend.evidence.manifest`
- `make verify.backend.evidence.manifest.guard`
- `make verify.phase_next.evidence.bundle.strict`
- `make verify.business.core_journey.guard`
- `make verify.role.capability_floor.guard`
- `make verify.business.capability_baseline.guard`
- `make verify.contract.evidence.guard`

## Notes

- Current baseline is non-destructive: guards are focused on boundary hardening and output governance, not architecture rewrites.
