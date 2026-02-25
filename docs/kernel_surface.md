# Kernel Public Surface (R7)

## Scope
This document defines Smart Core L0 kernel boundaries and extension contracts.

## L0 Protected Paths (Do Not Touch by Default)
- `addons/smart_core/core/`
- `addons/smart_core/governance/`
- `addons/smart_core/runtime/`
- `addons/smart_core/controllers/intent_dispatcher.py`
- `addons/smart_core/handlers/system_init.py`
- `addons/smart_core/core/base_handler.py`
- `addons/smart_core/core/intent_router.py`

## Approved Extension Entry Points
- Extension module registration:
  - `smart_core_register(registry)`
- `system.init` payload extension hook:
  - `smart_core_extend_system_init(data, env, user)`
- Extension module config switch:
  - `ir.config_parameter: sc.core.extension_modules`

## Hook Safety Rules
- Extensions may add/replace **domain payload** only.
- Extensions must not mutate Smart Core source files at runtime.
- Extensions must not bypass intent permission checks in `BaseIntentHandler`.
- Extensions must not break contract envelope (`ok/data/meta`).

## Change Control
- Protected-path changes require freeze override:
  - CI env `KERNEL_FREEZE_LABEL=kernel-approved` or `KERNEL_FREEZE_ALLOW=1`
- All protected-path changes must include:
  - rationale
  - risk assessment
  - rollback plan

## Public Compatibility Commitments
- `system.init` and `ui.contract` keep envelope stability.
- Public intent surface evolves additively first.
- Backward incompatible changes require documented version migration.
