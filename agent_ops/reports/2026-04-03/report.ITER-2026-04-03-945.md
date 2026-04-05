# ITER-2026-04-03-945

- status: PASS
- mode: screen
- layer_target: Product Release Usability Proof
- module: edition route fallback guard timeout screen
- risk: low
- publishability: screen_only

## Screening Classification (No Rescan)

- P0: UI form-login path (`submitLogin`) is brittle and times out before fallback assertions.
- P1: credential path sensitivity exists (`demo_finance` + 401 in failed artifact).
- P2: strict `networkidle`/`waitForURL` windows increase timeout risk.
- P3: fallback semantic assertions are never reached when login path fails.

## Selected Verify Path

- rerun only declared `verify.edition.route_fallback_guard` under explicit `DB_NAME=sc_demo` and explicit credentials.
- objective: confirm deterministic timeout reproduction as implementation input.

## Decision

- PASS (screen complete)
- next: `946(verify)`.
