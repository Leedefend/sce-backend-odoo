#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from http.cookiejar import CookieJar


REQUIRED_FIELDS = {"scope_type", "scope_ref", "value_text", "value_json"}


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._id = 0
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def _post(self, path: str, payload: dict):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Anonymous-Intent": "1"},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        return int(response.status), body

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        status, body = self._post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": 1,
            },
        )
        if status != 200:
            return 0
        result = body.get("result") if isinstance(body, dict) else {}
        return int((result or {}).get("uid") or 0)

    def intent(self, intent: str, params: dict) -> tuple[int, dict]:
        return self._post("/api/v1/intent", {"intent": intent, "params": params})

    def call_kw(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None):
        status, body = self._post(
            f"/web/dataset/call_kw/{model}/{method}",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args or [],
                    "kwargs": kwargs or {},
                },
                "id": 2,
            },
        )
        if status != 200 or body.get("error"):
            raise RuntimeError(json.dumps(body.get("error") or body, ensure_ascii=False))
        return body.get("result")


def _login(base_url: str, db_name: str, login: str, passwords: list[str]) -> tuple[OdooSession | None, str]:
    for pwd in passwords:
        session = OdooSession(base_url)
        uid = session.authenticate(db_name, login, pwd)
        if uid > 0:
            return session, pwd
    return None, ""


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "sc_fx_pure_outsider")

    roles = [
        ("admin", "admin", ["admin"]),
        ("pm", "sc_fx_pm", ["demo", "prod_like", "admin"]),
        ("finance", "sc_fx_finance", ["demo", "prod_like", "admin"]),
        ("outsider", outsider_login, ["demo", "prod_like", "admin"]),
    ]

    failures: list[str] = []
    details: list[str] = []
    parity_rows: list[dict] = []

    for role, login, pwds in roles:
        session, used = _login(base_url, db_name, login, pwds)
        if not session:
            failures.append(f"{role}: session bootstrap auth failed")
            continue

        # Batch A rule: session bootstrap first, then intent.
        status_form, body_form = session.intent(
            "ui.contract",
            {"op": "model", "model": "sc.dictionary", "view_type": "form", "contract_mode": "user"},
        )
        status_tree, body_tree = session.intent(
            "ui.contract",
            {"op": "model", "model": "sc.dictionary", "view_type": "tree", "contract_mode": "user"},
        )

        if status_form != 200 or status_tree != 200:
            failures.append(f"{role}: intent status form={status_form} tree={status_tree}")
            continue
        if not (isinstance(body_form, dict) and body_form.get("ok") is True):
            failures.append(f"{role}: form intent not ok")
            continue
        if not (isinstance(body_tree, dict) and body_tree.get("ok") is True):
            failures.append(f"{role}: tree intent not ok")
            continue

        form_payload = (body_form.get("data") or {}) if isinstance(body_form.get("data"), dict) else {}
        tree_payload = (body_tree.get("data") or {}) if isinstance(body_tree.get("data"), dict) else {}
        form_fields = set((form_payload.get("fields") or {}).keys())
        tree_fields = set((tree_payload.get("fields") or {}).keys())
        if not REQUIRED_FIELDS.issubset(form_fields):
            failures.append(f"{role}: form missing required fields")
        if not REQUIRED_FIELDS.issubset(tree_fields):
            failures.append(f"{role}: tree missing required fields")

        # Batch B parity: compare with runtime-equivalent surfaces
        eq_fields = session.call_kw("sc.dictionary", "fields_get", [], {"attributes": ["type", "readonly", "required"]})
        eq_field_keys = set((eq_fields or {}).keys()) if isinstance(eq_fields, dict) else set()
        if not REQUIRED_FIELDS.issubset(eq_field_keys):
            failures.append(f"{role}: equivalent fields_get missing required fields")

        rights = {
            mode: bool(session.call_kw("sc.dictionary", "check_access_rights", [mode], {"raise_exception": False}))
            for mode in ("read", "write", "create", "unlink")
        }
        permissions = (form_payload.get("permissions") or {}) if isinstance(form_payload, dict) else {}
        perms_by_group = permissions.get("perms_by_group") if isinstance(permissions, dict) else None
        if not isinstance(perms_by_group, dict) or not perms_by_group:
            failures.append(f"{role}: intent permissions.perms_by_group missing")

        parity_rows.append(
            {
                "role": role,
                "password_used": used,
                "intent_form_field_count": len(form_fields),
                "intent_tree_field_count": len(tree_fields),
                "equivalent_field_count": len(eq_field_keys),
                "required_fields_present": REQUIRED_FIELDS.issubset(form_fields)
                and REQUIRED_FIELDS.issubset(tree_fields)
                and REQUIRED_FIELDS.issubset(eq_field_keys),
                "equivalent_rights": rights,
            }
        )
        details.append(f"{role}:parity-ok")

    parity_doc = {
        "base_url": base_url,
        "db": db_name,
        "model": "sc.dictionary",
        "batch": "ITER-2026-04-08-1338",
        "rows": parity_rows,
        "result": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    with open("docs/ops/business_admin_config_center_intent_parity_v1.md", "w", encoding="utf-8") as fp:
        fp.write("# Business Admin Config Center Intent Parity v1\n\n")
        fp.write(f"- result: `{parity_doc['result']}`\n")
        fp.write(f"- base_url: `{base_url}`\n")
        fp.write(f"- db: `{db_name}`\n")
        fp.write("- session-bootstrap: required and applied for all role probes\n\n")
        fp.write("## Rows\n")
        for row in parity_rows:
            fp.write(
                f"- role={row['role']} intent_form={row['intent_form_field_count']} "
                f"intent_tree={row['intent_tree_field_count']} eq_fields={row['equivalent_field_count']} "
                f"required_fields_present={row['required_fields_present']} rights={row['equivalent_rights']}\n"
            )
        if failures:
            fp.write("\n## Failures\n")
            for item in failures:
                fp.write(f"- {item}\n")

    if failures:
        raise SystemExit("[native_business_admin_config_center_intent_parity_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_center_intent_parity_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
