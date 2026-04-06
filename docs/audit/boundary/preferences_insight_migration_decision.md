# Preferences & Insight Migration Decision (Screen)

- Target endpoints:
  - `/api/preferences/get`
  - `/api/preferences/set`
  - `/api/insight`

## Decision

- migration mode: **single bounded implement batch** with route-shell ownership transfer.
- target ownership: **smart_core route shell**.
- semantic handling: **delegate to existing scenario controllers**.

## Hard Constraints

1. Keep current auth and access-check behavior unchanged.
2. Keep payload shape and error codes compatible.
3. No ACL/security/manifest/financial domain changes.

## Stop Signals

- modifying scene preference business semantics.
- rewriting insight service logic or ACL checks.
- any frontend-specific fallback insertion.

## Next Implement Slice

- migrate these three routes to smart_core delegation controller and verify.
