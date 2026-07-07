# Project Showcase Governance

Purpose: keep project showcase selection as a product capability instead of a
demo-only filter leaking into core business entry points.

Policy
- Core entry points must use `sc_project_showcase` and
  `sc_project_showcase_ready`.
- `sc_demo_showcase` and `sc_demo_showcase_ready` are compatibility aliases only.
- Demo-only menus/actions live in `smart_construction_demo`.
- Seed/verify scripts should write the product fields first.

Allowed locations
- smart_construction_core/models/core/project_core.py (compatibility aliases)
- smart_construction_core/migrations/17.0.0.60/post-migration.py (legacy data backfill)
- smart_construction_demo/data/demo/sc_demo_showcase_actions.xml (demo actions)
- smart_construction_demo/models/project_demo_cockpit_seed.py (demo data generation)

Gate
- Test: smart_construction_demo/tests/test_demo_showcase_gate.py
- Tag: sc_gate

Audit evidence
- docs/audit/sc_demo_showcase_ready_refs.txt (rg output)
