# ITER-2026-04-03-944

- status: PASS
- mode: scan
- layer_target: Product Release Usability Proof
- module: edition route fallback guard timeout scan
- risk: low
- publishability: scan_only

## Candidate List (Scan Only)

- candidate-1: guard still uses UI login flow (`submitLogin`) with strict 20s navigation timeout.
- candidate-2: failure artifact indicates 401 on login resource path before fallback checks.
- candidate-3: intercepted intents contain only `login`; expected `system.init/my.work.summary` never appears.
- candidate-4: guard default account in artifact is `demo_finance`, unlike mainline `admin` run, suggesting credential-path sensitivity.
- candidate-5: `networkidle` + `waitForURL` combo may be too strict under current runtime conditions.

## Decision

- PASS (scan complete)
- next: `945(screen)`.
