"""Probe migrated real-user company assignments in prod-sim."""

from collections import Counter, defaultdict
import json


def _text(value):
    return str(value or "").strip()


def _is_runtime_user(user):
    login = _text(user.login)
    if not user.active:
        return False
    if not login or login in {"admin", "default"}:
        return False
    if login in {"admin_10000000", "history_system_user_10000000"}:
        return False
    if login.startswith(("demo_", "svc_", "sc_test", "sc_fx_")):
        return False
    return True


Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
Company = env["res.company"].sudo()  # noqa: F821

companies = [
    {
        "id": company.id,
        "name": company.name,
        "partner": company.partner_id.display_name,
    }
    for company in Company.search([], order="id")
]

users = []
company_counts = Counter()
allowed_company_patterns = Counter()
role_company_by_user = defaultdict(Counter)
scope_company_by_user = defaultdict(Counter)

if "sc.legacy.user.role" in env:  # noqa: F821
    for role in env["sc.legacy.user.role"].sudo().with_context(active_test=False).search([]):  # noqa: F821
        if role.user_id and _text(role.company_legacy_id):
            role_company_by_user[role.user_id.id][_text(role.company_legacy_id)] += 1

if "sc.legacy.user.project.scope" in env:  # noqa: F821
    for scope in env["sc.legacy.user.project.scope"].sudo().with_context(active_test=False).search([]):  # noqa: F821
        if scope.user_id and _text(scope.company_legacy_id):
            scope_company_by_user[scope.user_id.id][_text(scope.company_legacy_id)] += 1

for user in Users.search([], order="login"):
    if not _is_runtime_user(user):
        continue
    allowed = [{"id": company.id, "name": company.name} for company in user.company_ids]
    main_company = {"id": user.company_id.id, "name": user.company_id.name}
    company_counts[main_company["name"] or ""] += 1
    allowed_company_patterns[tuple(company["name"] for company in allowed)] += 1
    users.append(
        {
            "id": user.id,
            "login": user.login,
            "name": user.name,
            "active": bool(user.active),
            "main_company": main_company,
            "allowed_companies": allowed,
            "legacy_user_profile": bool(
                env["sc.legacy.user.profile"].sudo().search_count([("user_id", "=", user.id)])  # noqa: F821
                if "sc.legacy.user.profile" in env  # noqa: F821
                else False
            ),
            "role_company_legacy_ids": dict(role_company_by_user.get(user.id, {})),
            "scope_company_legacy_ids": dict(scope_company_by_user.get(user.id, {})),
        }
    )

result = {
    "database": env.cr.dbname,  # noqa: F821
    "companies": companies,
    "user_count": len(users),
    "company_counts": dict(company_counts),
    "allowed_company_patterns": {
        " | ".join(pattern): count for pattern, count in allowed_company_patterns.items()
    },
    "role_company_legacy_id_counts": dict(sum((Counter(v) for v in role_company_by_user.values()), Counter())),
    "scope_company_legacy_id_counts": dict(sum((Counter(v) for v in scope_company_by_user.values()), Counter())),
    "users": users,
    "db_writes": 0,
}

print("HISTORY_REAL_USER_COMPANY_PROBE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
