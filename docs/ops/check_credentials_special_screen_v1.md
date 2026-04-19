# Check Credentials Special Screen v1

## Goal

Determine whether the current `_check_credentials` cost is caused by an
avoidable custom inefficiency or by Odoo's native password verification policy.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: check_credentials slow-path special screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: login instrumentation already isolated `_check_credentials` as the
  dominant login hotspot

## Evidence

### 1. Real login instrumentation

Latest real login timings showed:

- `authenticate_user`: about 535 ms
- inside it, `check_credentials`: about 528 ms

So `_check_credentials` dominates the login path.

### 2. Current custom auth wrapper is thin around `_check_credentials`

Current [`auth.py`](/mnt/e/sc-backend-odoo/addons/smart_core/security/auth.py)
does:

- DB resolution
- `Registry(db)` acquisition
- user lookup
- user env creation
- `user_record.with_env(user_env)._check_credentials(password, user_env)`

Measured overhead outside `_check_credentials` is very small:

- `user_lookup`: about 3 ms
- `user_env_build`: about 0 ms

So the dominant cost is not from our wrapper logic.

### 3. Native Odoo implementation is straightforward

Container inspection of Odoo's native `_check_credentials` shows:

```python
self.env.cr.execute(
    "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
    [self.env.user.id]
)
[hashed] = self.env.cr.fetchone()
valid, replacement = self._crypt_context().verify_and_update(password, hashed)
```

This means the heavy part is native password-hash verification itself.

### 4. Native crypt context is PBKDF2 and uses default minimum rounds

Container inspection shows:

- `_crypt_context()` uses `pbkdf2_sha512`
- rounds come from `password.hashing.rounds`
- current runtime value is `0`
- Odoo fallback constant is `MIN_ROUNDS = 600000`

So the system is currently using native PBKDF2 policy with the default minimum
work factor, not a custom over-tuned rounds value.

## Conclusion

The current `_check_credentials` slowness is **not primarily caused by custom
wrapper overhead**.

It is most likely the expected cost of native Odoo password verification under:

- `pbkdf2_sha512`
- `MIN_ROUNDS = 600000`

So the claim "this is obviously far below native efficiency" is **not yet
supported** by current evidence.

Current evidence instead supports:

- we are already very close to native password-check cost
- the main hotspot is the native KDF work factor itself

## What This Means For Optimization

The realistic next options are:

1. accept current native security-cost tradeoff
2. explicitly lower password hashing rounds and treat it as a security-policy
   change
3. investigate whether Odoo/native environment or CPU profile differs from the
   baseline environment you are comparing against

What is **not** supported as the next move:

- blaming capability warmup
- blaming token generation
- blaming the auth wrapper structure as the main cause

## Recommended Next Batch

Open a bounded policy screen for password verification cost that decides:

- whether `password.hashing.rounds` should remain at native minimum policy
- whether a lower value is acceptable for this environment
- what security/performance tradeoff is acceptable before any change is made
