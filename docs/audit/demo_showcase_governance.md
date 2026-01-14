# Demo Showcase Governance

Purpose: prevent demo-only filters (sc_demo_showcase_ready) from leaking into
core business entry points.

Policy
- Core entry points must not hardcode demo filters.
- Demo-only filters live in demo/seed modules and demo menus/actions only.
- Core may define the field and nothing else.

Allowed locations
- smart_construction_core/models/core/project_core.py (field definition)
- smart_construction_seed/data/sc_demo_showcase_actions.xml (demo actions)
- smart_construction_seed/seed/steps/step_90_verify_demo.py (seed verification)

Gate
- Test: smart_construction_core/tests/test_demo_showcase_gate.py
- Tag: sc_gate

Audit evidence
- docs/audit/sc_demo_showcase_ready_refs.txt (rg output)
