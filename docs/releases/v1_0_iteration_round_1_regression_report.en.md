# v1.0 Iteration Round 1 Minimum Regression Report

## 1. Scope

Executed required commands:

1. `make verify.frontend.build`
2. `make verify.frontend.typecheck.strict`
3. `make verify.project.dashboard.contract`
4. `make verify.phase_next.evidence.bundle`

Release-grade demo seed closure commands (new fixed items):

5. `make demo.load.release DB_NAME=sc_demo`
6. `make verify.demo.release.seed DB_NAME=sc_demo`

## 2. Results

- `make verify.frontend.build`: PASS
- `make verify.frontend.typecheck.strict`: PASS
- `make verify.project.dashboard.contract`: PASS
- `make verify.phase_next.evidence.bundle`: FAIL (environment timeout)
- `make demo.load.release DB_NAME=sc_demo`: PASS (release seed load succeeded)
- `make verify.demo.release.seed DB_NAME=sc_demo`: PASS (release seed acceptance passed)

Failure output:

- `[role_capability_floor_prod_like] FAIL`
- `admin session setup failed: <urlopen error timed out>`

Re-run once with same result.

## 3. Impact Assessment

- Product-expression changes do not break frontend build/typecheck/dashboard contract verification.
- Evidence bundle failure is tied to environment/session bootstrap timeout, not directly caused by current display-layer changes.

## 4. Recommendation

1. Re-run `make verify.phase_next.evidence.bundle` in a stable environment.
2. If still failing, inspect admin session bootstrap and URL timeout/network path.
3. Keep this round in “expression validation” stage; do not release yet.

## 5. Release Demo Seed Acceptance (Fixed Section)

- Goal: ensure demo data is a repeatable + verifiable release baseline.
- Load command: `make demo.load.release DB_NAME=sc_demo`
- Verify command: `make verify.demo.release.seed DB_NAME=sc_demo`
- Minimum pass criteria:
  - showroom project coverage is present;
  - `project_id=20` has non-empty contract/cost/finance data;
  - release role users (including `svc_e2e_smoke`) are present.
