# Capability Registry Live-Toggle Boundary Screen v1

## Goal

Explain precisely why the running worker did not emit stale fallback after the
verification-only salt was changed and committed, so the next seam can target
the real runtime boundary.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: capability registry live-toggle runtime-boundary screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: live verification already proved that the parameter can be written and
  committed, but the running worker still behaved as if the salt had not
  changed

## Evidence Already Collected

### 1. Registry service read path

`CapabilityRegistryService._verification_salt()` currently does:

1. read `ir.config_parameter.get_param("smart_core.capability_registry.verify_salt")`
2. if empty, fall back to `SMART_CORE_CAPABILITY_REGISTRY_VERIFY_SALT`

So the live-toggle seam depends on Odoo's config-parameter runtime semantics.

### 2. Parameter write path is real

Live verification proved:

- `odoo shell` can set the parameter
- `env.cr.commit()` persists the new value
- direct DB read then shows the new value
- reset back to empty also works

So the failure is not "write did not happen".

### 3. Running worker still ignores the changed value

After:

- empty salt baseline
- change to `live-toggle-a`
- reset to empty

the same running `localhost:8069` worker still returned:

- `runtime_query_registry.artifact_fallback_used = 0`
- no fallback-reason marker
- no stale-fallback behavior

So the failure is "running worker did not re-observe the changed verification
input".

## Root-Cause Screen

### Odoo config-parameter read path is process-cached

Container inspection shows:

```python
@api.model
@ormcache('key')
def _get_param(self, key):
    self.flush_model(['key', 'value'])
    self.env.cr.execute("SELECT value FROM ir_config_parameter WHERE key = %s", [key])
    result = self.env.cr.fetchone()
    return result and result[0]
```

And `get_param()` simply returns `_get_param(key) or default`.

This means:

- the read path is cached per process by key
- a running worker may continue to serve the old parameter value
- DB commit alone is not sufficient to guarantee same-process reread

### `set_param()` does not itself prove cross-process cache invalidation

Container inspection of `set_param()` shows normal ORM write/create/unlink
behavior, but no direct cache-clear call for `_get_param()` inside the method
body.

That is sufficient for this screen's conclusion:

- the chosen live-toggle seam is blocked by config-parameter cache semantics
- the live verification failed because the running worker was not forced to
  bypass or invalidate that cached read path

## Architectural Conclusion

The failure is not:

- capability-registry invalidation logic
- artifact trust-check logic
- database commit behavior
- performance regression

The failure is specifically:

- using `ir.config_parameter.get_param()` as a verification-only runtime toggle
  assumes same-worker freshness that the current process-cached read path does
  not guarantee

Therefore the current live-toggle seam is architecturally misaligned for
"change input on one process, expect another already-running process to notice
immediately".

## Design Consequence

If the product requirement is:

- verify stale mismatch on an already running worker without restart

then the verification seam must be one of:

1. an uncached, service-owned diagnostic input source
2. a direct SQL read path used only for verification-mode salt lookup
3. an explicit cache-bypass/invalidation mechanism that is guaranteed to affect
   the running worker before the probe

What should not happen next:

- keep stacking more `ir.config_parameter` toggles
- misclassify this as a capability-registry performance issue
- patch the frontend or consumer contract

## Recommended Next Batch

Open a bounded design/implementation task that replaces the verification-only
live-toggle source with the smallest service-owned uncached input.

Preferred direction:

- keep `ir.config_parameter` out of the live-toggle hot path
- add an explicit verification-only uncached read in the registry service
- keep ordinary runtime behavior unchanged when verification mode is absent
