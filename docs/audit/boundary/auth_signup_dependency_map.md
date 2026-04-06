# auth_signup Dependency Map (ITER-2026-04-05-1035)

## Scan Scope

- controller: `addons/smart_construction_core/controllers/auth_signup.py`
- related assets:
  - `addons/smart_construction_core/views/web_login_views.xml`
  - `addons/smart_construction_core/views/signup_templates.xml`
  - `addons/smart_construction_core/models/support/signup_throttle.py`
  - `addons/smart_construction_core/hooks.py`

## Route Entry Map

| route | method | exposure | direct upstream anchor | evidence |
| --- | --- | --- | --- | --- |
| `/web/signup` | `web_auth_signup` | public website | login page link (`signup_enabled`) | `web_login_views.xml:71`, `auth_signup.py:162` |
| `/sc/auth/activate/<string:token>` | `sc_activate_account` | public callback URL | activation mail link generated in controller | `auth_signup.py:149`, `auth_signup.py:238` |

## Downstream Dependency Map

| dependency type | target | usage | evidence |
| --- | --- | --- | --- |
| base auth controller | `AuthSignupHome` | inherit signup base flow | `auth_signup.py:12` |
| model/service | `res.users.signup` | create user during signup | `auth_signup.py` (via `request.env["res.users"].sudo().signup`) |
| model/service | `res.partner._signup_retrieve_partner` | activation token resolve | `auth_signup.py` (activate method) |
| model/service | `sc.signup.throttle` | rate-limit check and bump | `auth_signup.py:83`, `signup_throttle.py:8` |
| model/service | `mail.mail` | send activation mail | `auth_signup.py` (`_send_activation_email`) |
| platform helper | `ir.http._verify_request_recaptcha_token` | captcha validation | `auth_signup.py:175` |

## Config Dependency Map (`sc.signup.*`)

| key | consumed in controller | seeded in hooks | purpose |
| --- | --- | --- | --- |
| `sc.signup.mode` | yes | yes | open/invite/off gate |
| `sc.signup.require_email_verify` | yes | yes | activation required policy |
| `sc.signup.domain_whitelist` | yes | yes | email domain allowlist |
| `sc.signup.default_group_xmlids` | yes | yes | default group grant |
| `sc.signup.recaptcha.mode` | yes | yes | captcha policy |
| `sc.signup.token_expiration_hours` | yes | yes | activation token ttl |
| `sc.signup.ratelimit.window_sec` | yes | yes | rate-limit window |
| `sc.signup.ratelimit.max_per_ip` | yes | yes | ip quota |
| `sc.signup.ratelimit.max_per_email` | yes | yes | email quota |
| `sc.signup.ratelimit.gc_days` | throttle gc | yes | throttle retention |

Evidence: `hooks.py:168-193`, `auth_signup.py:20-68`, `signup_throttle.py:56`.

## Template/UI Coupling

| surface | coupling | evidence |
| --- | --- | --- |
| login page | exposes signup entry link | `web_login_views.xml:70-71` |
| signup template | inherits `auth_signup.signup` and custom styles/labels | `signup_templates.xml:36` |

## Boundary Notes (Scan Stage)

- dependency cluster is concentrated in auth lifecycle (signup + activation + anti-abuse).
- no scene/capability/ops/pack registry coupling found in scanned files.
- migration planning must keep compatibility anchors stable:
  - `/web/signup` entry from login page
  - activation URL format `/sc/auth/activate/<token>`
  - `sc.signup.*` config key continuity
