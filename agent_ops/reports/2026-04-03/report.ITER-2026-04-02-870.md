# ITER-2026-04-02-870

- status: FAIL
- mode: verify
- layer_target: Product Usability Closure
- module: host-browser reachability diagnostics
- risk: low

## Verification Result

- `curl -I http://localhost:8070/login?db=sc_demo`: FAIL (connect error)
- `curl -I http://127.0.0.1:8070/login?db=sc_demo`: FAIL (connect error)
- `make verify.portal.second_slice_browser_smoke.host`: FAIL (`page.goto` timeout on `/login`)

## Decision

- FAIL
- host-browser route remains unreachable in current runtime, full freeze gate cannot be restored yet.

## Next Iteration Suggestion

- keep constrained-runtime aggregate/surrogate gates as active baseline until host route is reachable.

