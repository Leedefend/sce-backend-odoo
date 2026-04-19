# Login Slow Special Screen v1

## Goal

Freeze the current evidence about slow login into a standalone research line and
identify the most defensible next optimization target.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: login slow special screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: the user explicitly requested a dedicated study line for slow login

## Objective Evidence

### 1. Successful login remains materially slow

Latest successful real `wutao/demo` login samples:

- 762.5 ms
- 629.7 ms
- 629.5 ms
- 663.7 ms
- 633.1 ms

Average:

- about 663.7 ms

This is the current login-only cost, before adding user-visible page-init
timings.

### 2. Failed login is almost as expensive as successful login

Latest failed-login samples with wrong password:

- 570.9 ms
- 577.3 ms
- 687.7 ms
- 583.2 ms
- 625.2 ms

Average:

- about 608.9 ms

The gap between successful and failed login is only about:

- 54.8 ms on average

This is the most important evidence in the current chain.

## Why This Matters

Failed login does not execute the success-only steps:

- `_load_user_profile(...)`
- `_warm_capability_artifact(...)`
- `generate_token(...)`
- login success response assembly

Yet it still costs roughly the same as successful login.

Therefore the dominant cost is not the success-only tail of the login chain.

## Code-Path Interpretation

Current `authenticate_user(...)` performs:

1. database resolution
2. `Registry(db)` acquisition
3. superuser environment creation
4. `res.users` search by login
5. per-user environment creation
6. `_check_credentials(...)`

This path is executed for both failed and successful login.

By contrast, the success-only additions are relatively smaller:

- `_load_user_profile(...)`
- `_warm_capability_artifact(...)`
- `generate_token(...)`

## Additional Evidence From Adjacent Requests

The latest chained probe also showed:

- login average around 1956.4 ms under a combined `login -> heavy system.init`
  probe
- first `system.init` total around 4.6s to 6.3s
- capability registry build subtiming only around 50 ms to 144 ms with
  `artifact_fallback_used = 0`

This supports the same interpretation:

- capability warmup has cost
- but it is not the dominant explanation for slow login

## Special-Line Conclusion

The current slow-login hotspot is most defensibly located in the shared
authentication path, especially:

- registry acquisition / DB-bound auth setup
- user lookup
- `_check_credentials(...)`

Not primarily in:

- capability warmup
- token generation
- success response assembly

## Recommended Next Batch

Open a bounded login-auth instrumentation batch that adds substage timings for:

1. database resolution / registry acquisition
2. user lookup
3. `_check_credentials(...)`
4. `_load_user_profile(...)`
5. `_warm_capability_artifact(...)`
6. `generate_token(...)`

Only after that should we decide whether the first optimization should target:

- authentication path itself
- profile read path
- warmup path

At this point, the evidence does **not** support blaming warmup as the primary
cause of slow login.
