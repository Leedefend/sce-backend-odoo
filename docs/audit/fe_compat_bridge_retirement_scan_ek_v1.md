# FE Compat Bridge Retirement Scan EK

```json
[
  {
    "path": "frontend/apps/web/src/router/index.ts",
    "module": "router compatibility entry registration",
    "feature": "native and compat public bridge routes remain registered",
    "reason": "The router still registers `/m/:menuId`, `/a/:actionId`, `/compat/action/:actionId`, `/r/:model/:id`, `/f/:model/:id`, and `/compat/record/:model/:id` as controlled compatibility surfaces."
  },
  {
    "path": "frontend/apps/web/src/app/resolvers/sceneRegistry.ts",
    "module": "compat route recognition",
    "feature": "compat prefixes remain recognized as legacy route inputs",
    "reason": "Current runtime still treats `/compat/action/`, `/compat/form/`, and `/compat/record/` as legacy compat route inputs during scene resolution."
  },
  {
    "path": "frontend/apps/web/src/views/WorkbenchView.vue, frontend/apps/web/src/views/MyWorkView.vue, frontend/apps/web/src/views/HomeView.vue, frontend/apps/web/src/app/suggested_action/runtime.ts",
    "module": "scene-unprovable fallback producers",
    "feature": "limited compat/native fallback remains only when scene identity cannot be proven",
    "reason": "Most producer branches are now scene-first, but a small number of fallback paths still emit compat/native routes when current context cannot prove a legal scene target."
  },
  {
    "path": "frontend/apps/web/src/views/CapabilityMatrixView.vue, frontend/apps/web/src/app/action_runtime/useActionViewActionMetaRuntime.ts",
    "module": "compat consumer recognition",
    "feature": "compat URLs remain treated as valid internal targets",
    "reason": "These consumers still recognize `/compat/action/`, `/compat/record/`, or `/compat/form/` as valid internal route shapes."
  },
  {
    "path": "docs/ops/iterations/delivery_context_switch_log_v1.md",
    "module": "live ingress evidence",
    "feature": "compat-record bridge still has previously verified legacy ingress value",
    "reason": "Earlier live verification already proved that at least one real legacy compat-record URL could still enter the running frontend, so retirement safety cannot be assumed from code shape alone."
  }
]
```
