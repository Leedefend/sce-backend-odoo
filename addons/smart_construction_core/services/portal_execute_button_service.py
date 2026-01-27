# -*- coding: utf-8 -*-
from __future__ import annotations


class PortalExecuteButtonService:
    def __init__(self, env):
        self.env = env

    def build_contract(self, model=None, res_id=None, method=None):
        entry = self._resolve_entry(model, method)
        record = self._resolve_record(entry.get("model"), res_id)
        error = None

        if not entry.get("allowed"):
            error = entry.get("error")
        elif not record:
            error = _error("missing_record", "record not found")
        else:
            error = self._check_method(record, entry.get("method"))
            if not error:
                error = self._check_access(record)

        allowed = error is None
        return {
            "action": {
                "label": entry.get("label"),
                "desc": entry.get("desc"),
                "code": entry.get("code"),
            },
            "target": {
                "model": entry.get("model"),
                "res_id": record.id if record else (res_id or None),
                "method": entry.get("method"),
            },
            "allowed": allowed,
            "error": error,
        }

    def assert_allowed(self, model, method):
        entry = self._resolve_entry(model, method)
        if not entry.get("allowed"):
            raise ValueError(entry.get("error", {}).get("message") or "not allowed")
        return entry

    def _resolve_entry(self, model=None, method=None):
        model = model or "project.project"
        method = method or "action_portal_demo_ping"
        registry = _registry()
        entry = registry.get(model, {}).get(method)
        if not entry:
            return {
                "model": model,
                "method": method,
                "allowed": False,
                "error": _error("not_allowed", "method not allowed"),
            }
        return {
            "model": model,
            "method": method,
            "label": entry.get("label"),
            "desc": entry.get("desc"),
            "code": entry.get("code"),
            "allowed": True,
        }

    def _resolve_record(self, model, res_id):
        if not model or model not in self.env:
            return None
        if res_id:
            return self.env[model].browse(int(res_id)).exists()
        return self.env[model].search([], order="id", limit=1)

    def _check_method(self, record, method):
        fn = getattr(record, method, None)
        if fn is None or not callable(fn):
            return _error("missing_method", "method not callable")
        return None

    def _check_access(self, record):
        try:
            record.check_access_rights("write")
            record.check_access_rule("write")
        except Exception as exc:
            return _error("not_allowed", str(exc))
        return None


def _registry():
    return {
        "project.project": {
            "action_portal_demo_ping": {
                "code": "portal_demo_ping",
                "label": "执行演示动作",
                "desc": "触发一次安全的演示动作",
            }
        }
    }


def _error(code, message):
    return {
        "code": code,
        "message": message,
    }
