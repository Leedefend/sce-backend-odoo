# Delivery Playbook v1

## Goal
Run one reproducible customer onboarding flow from company setup to role-based acceptance evidence.

## Scope

This playbook is used by implementation, customer success, and engineering. It covers company onboarding, role setup, product package activation, acceptance, rollback, and evidence collection.

## Customer Onboarding Steps

1. Confirm customer company profile:
   - company name
   - unified social credit code when available
   - timezone and currency
   - target product package and tier
2. Install `smart_core`.
3. Install one product bundle:
   - `smart_construction_bundle` or `smart_owner_bundle`.
4. Optionally install `smart_license_core` and set `sc.license.level`.
5. Configure extension modules in `sc.core.extension_modules`.
6. Select onboarding mode:
   - blank company setup
   - demo/training setup
   - historical data migration setup
7. Create or prepare users for each role:
   - PM
   - Finance
   - Executive
   - Purchase manager
   - Business configuration admin
   - Owner (optional)
8. Initialize base dictionaries:
   - organizations
   - project types
   - tax rates
   - approval roles
   - material and supplier basics when applicable
9. Execute key journey:
   - login
   - system.init
   - ui.contract
   - execute_button/payment flow
10. Verify platform gates:
   - `make verify.platform.governance.ready`
   - `make verify.product.delivery.productization.readiness`

## Acceptance

Customer acceptance must include:

- company profile exists and opens correctly
- role users can log in
- each role lands on the expected home scene
- standard package menus are visible according to role
- payment request, project ledger, project cockpit, and finance ledger golden paths are verified
- unavailable capabilities explain product tier or permission reason
- implementation evidence is attached to the delivery package
- customer confirms known limitations

Engineering acceptance must include:

- Payload envelope stable.
- Role surface matches bundle + tier policy.
- No smart_core source mutation.
- Core flow passes without 5xx.

## Rollback

Rollback must be planned before customer handoff:

- keep the previous database backup or snapshot
- record installed modules and product tier before change
- record activated product policy and release snapshot
- if onboarding fails, restore backup or deactivate the new product policy
- if historical data migration fails, keep failed rows as review assets and do not silently drop records

## Evidence

Evidence must be readable by both customer and implementation team:

- product package and tier
- company setup summary
- role account matrix
- enabled capability list
- browser acceptance screenshots or smoke logs
- migration summary when applicable
- known limitations
- rollback target and support contact path

## Evidence Board

- Delivery manager one-page evidence board:
  - `docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md`
- Default strict evidence command:
  - `make verify.scene.delivery.readiness.role_company_matrix`
