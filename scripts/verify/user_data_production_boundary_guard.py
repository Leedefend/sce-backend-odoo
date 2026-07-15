#!/usr/bin/env python3
"""Static guard for the user/demo production boundary."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
checks = {
    "runtime user management": ROOT / "addons/smart_construction_core/models/support/runtime_user_management.py",
    "runtime user view": ROOT / "addons/smart_construction_core/views/support/runtime_user_management_views.xml",
    "approval user wizard": ROOT / "addons/smart_construction_core/models/support/approval_scope.py",
    "role policy": ROOT / "addons/smart_construction_custom/models/security_policy.py",
    "identity resolver": ROOT / "addons/smart_core/identity/identity_resolver.py",
    "history user normalization": ROOT / "scripts/migration/history_real_user_normalize_write.py",
}
texts = {name: path.read_text(encoding="utf-8") for name, path in checks.items()}
errors = []
for name in ("runtime user management", "runtime user view", "approval user wizard", "history user normalization"):
    if "123456" in texts[name]:
        errors.append(f"shared_default_password:{name}")
for token in ("LEGACY_ROLE_LOGIN_ALIASES", "ROLE_LOGIN_GROUPS", '("login", "=", login)'):
    if token in texts["role policy"]:
        errors.append(f"login_based_role_assignment:{token}")
if 'return "restricted", {"source": "no_authoritative_role"' not in texts["identity resolver"]:
    errors.append("identity_fallback_is_not_restricted")
if '"deny_all_navigation": True' not in texts["identity resolver"]:
    errors.append("restricted_navigation_is_not_fail_closed")
if errors:
    raise SystemExit("USER_DATA_PRODUCTION_BOUNDARY_GUARD=FAIL " + ",".join(errors))
print("USER_DATA_PRODUCTION_BOUNDARY_GUARD=PASS")
