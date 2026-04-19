# Login Session Performance Screen v1

## Goal

Determine whether current login/session establishment has meaningful
optimization headroom and identify the real hotspot before changing runtime
behavior again.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: login/session performance screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: after moving user-scoped capability warmup into the login chain, the
  user reports that login/session establishment still feels slow

## Real Runtime Evidence

### Login-only live samples

Real `wutao/demo` login probes on the current runtime produced:

- 626.3 ms
- 731.1 ms
- 667.8 ms
- 653.3 ms
- 678.3 ms

Average:

- about 671.4 ms

So the current login chain is materially slower than a lightweight auth-only
path.

### First page-init after login

The latest verified chain already showed:

- first real `system.init` after login has `artifact_fallback_used = 0`

So the moved warmup is working as intended: page-init is no longer paying that
first-user capability build cost.

## Code-Path Assessment

Current `LoginHandler` does these major steps in sequence:

1. `authenticate_user(...)`
2. `_load_user_profile(...)`
3. `_warm_capability_artifact(...)`
4. `generate_token(...)`
5. build login response payload

By code inspection:

- `authenticate_user(...)` is a focused DB lookup plus credential check
- `_load_user_profile(...)` is a focused profile read
- `generate_token(...)` is cheap compared with DB-bound work
- `_warm_capability_artifact(...)` invokes the full capability-registry artifact
  path for that authenticated user

And that artifact path is exactly the one that previously cost the first
`system.init` request a noticeable fallback build.

## Conclusion

Yes, there is still optimization headroom in the login/session establishment
chain.

But the hotspot is not mysterious:

- the dominant new cost is very likely the synchronous user-scoped capability
  warmup now executed inside login

That means current behavior is a deliberate trade:

- faster first page-init
- slower login

## Decision Implication

If the product prefers:

- "login faster, first page may warm"

then warmup should move later again.

If the product prefers:

- "login slower, first page always ready"

then current structure is directionally correct, and optimization should focus
on reducing the warmup path itself rather than relocating it.

## Most Likely Optimization Targets

The next bounded optimization opportunities are:

1. add login-chain substage timing so auth/profile/warmup are measured
   separately
2. optimize user-scoped capability warmup itself
3. optionally move warmup from login response path into a dedicated
   post-login/session-bootstrap follow-up request if product experience favors
   shorter perceived login time

## Recommendation

The next best step is not blind optimization.

It is:

- add fine-grained timing around `authenticate_user`, `_load_user_profile`, and
  `_warm_capability_artifact` inside login

That will confirm the exact share of warmup cost before deciding whether to:

- keep warmup in login and optimize it
- or move it into a follow-up session/bootstrap stage
