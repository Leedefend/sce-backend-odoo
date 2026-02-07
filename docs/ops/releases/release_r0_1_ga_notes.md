# Release r0.1 GA Notes

Status: Ready for GA
RC Reference: r0.1.0-rc1

## Release Scope
This release finalizes the core navigation, scene orchestration,
and portal bridge architecture for Smart Construction Platform.

## Verification
- Canonical RC smoke user: demo_pm
- Portal bridge E2E verified
- Scene list profile and default sort verified
- SPA API strictly token-based (no cookies)

## Known Constraints
- Dual UI planes (SPA + Odoo portal) remain in this release
- act_url is transitional and partially retained
- Service accounts (svc_*) are not intended for UI-level smokes
