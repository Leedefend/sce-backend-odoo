# Delivery Playbook v1

## Goal
Run one reproducible delivery simulation from installation to role-based usage.

## Steps
1. Install `smart_core`.
2. Install one bundle:
   - `smart_construction_bundle` or `smart_owner_bundle`.
3. Optionally install `smart_license_core` and set `sc.license.level`.
4. Configure extension modules in `sc.core.extension_modules`.
5. Create/prepare users for roles:
   - PM
   - Finance
   - Executive
   - Owner (optional)
6. Seed demo data.
7. Execute key journey:
   - login
   - system.init
   - ui.contract
   - execute_button/payment flow
8. Verify platform gates:
   - `make verify.platform.governance.ready`

## Acceptance
- Payload envelope stable.
- Role surface matches bundle + tier policy.
- No smart_core source mutation.
- Core flow passes without 5xx.

## Evidence Board

- Delivery manager one-page evidence board:
  - `docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md`
- Default strict evidence command:
  - `make verify.scene.delivery.readiness.role_company_matrix`
