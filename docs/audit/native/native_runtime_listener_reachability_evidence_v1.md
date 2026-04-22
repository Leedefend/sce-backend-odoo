# Native Runtime Listener Reachability Evidence v1

## Scope

- Task: `ITER-2026-04-07-1207`
- Objective: capture listener/reachability readiness signals for `/api/scenes/my`

## Runtime Listener Signals

- `ss -ltn | rg ':8069|:8070'` output includes:
  - `*:8069` in LISTEN state
- `ss` stderr also reports:
  - `Cannot open netlink socket: Operation not permitted`

## Runtime Probe Constraint

- direct TCP socket probe from Python is blocked in current environment:
  - `PermissionError: [Errno 1] Operation not permitted`
- this explains mismatch between partial listener visibility and unavailable direct reachability probing.

## Guard Matrix

- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Runtime readiness remains constrained by environment-level socket permissions.
- Next reachable-window verification for `/api/scenes/my` 401/403 should run when host/network policy allows active socket probe.
