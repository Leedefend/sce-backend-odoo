# Capability Matrix Single-File Cleanup Screen (ITER-2026-04-05-1059)

## Target

- `addons/smart_construction_core/controllers/capability_matrix_controller.py`

## Evidence

1. file content is a no-op stub:
   - defines `CapabilityMatrixController(http.Controller)` with `pass` only.
   - contains no `@http.route` decorator.
2. reference scan result:
   - `rg` across `addons/smart_core/controllers` and `addons/smart_construction_core/controllers`
   - only self-definition match found; no import/use dependency found.
3. module import wiring:
   - `addons/smart_construction_core/controllers/__init__.py` does not import this file.

## Feasibility Conclusion

- single-file cleanup is **eligible** and low-risk.
- no active route ownership, no smart_core delegation dependency, no import-wiring dependency.

## Suggested Next Batch

- open implement batch to delete `capability_matrix_controller.py` and run:
  - `make verify.controller.boundary.guard`
  - container-local `frontend_api_smoke` recovery command.
