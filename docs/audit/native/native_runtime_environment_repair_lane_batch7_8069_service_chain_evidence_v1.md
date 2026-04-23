# Native Runtime Environment Repair Lane Batch7 8069 Service-Chain Evidence v1

## Scope

- Task: `ITER-2026-04-07-1220`
- Objective: capture 8069 handshake-level behavior for RemoteDisconnected

## Captured Evidence

- Listener snapshot (`ss -ltnp | rg :8069`):
  - `LISTEN ... *:8069`

- Direct HTTP handshake test (Python `http.client`):
  - request: `GET /api/scenes/my` on `localhost:8069`
  - result: `RemoteDisconnected: Remote end closed connection without response`

- Runtime probe aggregate still shows:
  - `8069 -> RemoteDisconnected`
  - `8070 -> timeout`

## Interpretation

- 8069 listener accepts connection but closes before sending HTTP response.
- This indicates runtime service chain/application entry behavior issue, not a simple port-unreachable case.

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Batch7 PASS with stronger service-chain evidence for 8069 RemoteDisconnected.
- Next step should target runtime service entry diagnostics (process health / proxy/app handshake boundary).

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
