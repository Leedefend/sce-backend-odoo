#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "artifacts" / "menu"


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if isinstance(headers, dict):
        for key, value in headers.items():
            req.add_header(str(key), str(value))
    opener = build_opener()
    try:
        with opener.open(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "{}")
            return int(resp.status), payload if isinstance(payload, dict) else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(raw or "{}")
        except Exception:
            payload = {}
        return int(exc.code), payload if isinstance(payload, dict) else {}


def _login_token(base_url: str, db: str, login: str, password: str) -> str:
    params = urlencode({"db": db})
    status, payload = _post_json(
        f"{base_url}/api/v1/intent?{params}",
        {
            "intent": "login",
            "params": {
                "db": db,
                "login": login,
                "password": password,
                "contract_mode": "default",
            },
        },
        headers={"X-Anonymous-Intent": "true"},
    )
    token = ""
    if isinstance(payload.get("data"), dict):
        token = str(payload.get("data", {}).get("token") or payload.get("data", {}).get("session", {}).get("token") or "").strip()
    if status >= 400 or not bool(payload.get("ok")) or not token:
        raise RuntimeError(f"login failed: {login}@{db} status={status}")
    return token


def _fetch_navigation(base_url: str, db: str, token: str) -> dict[str, Any]:
    params = urlencode({"db": db})
    status, payload = _post_json(
        f"{base_url}/api/menu/navigation?{params}",
        {},
        headers={"Authorization": f"Bearer {token}", "X-Odoo-DB": db},
    )
    if status >= 400 or not bool(payload.get("ok")):
        raise RuntimeError(f"menu navigation failed: status={status}")
    return payload


def _iter_leaves(nodes: list[dict[str, Any]], path: list[str] | None = None):
    stack = list(path or [])
    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name") or node.get("label") or "").strip()
        next_path = [*stack, name] if name else list(stack)
        children = node.get("children") if isinstance(node.get("children"), list) else []
        if children:
            yield from _iter_leaves(children, next_path)
            continue
        yield {
            "menu_id": node.get("menu_id"),
            "name": name,
            "path": "/".join([item for item in next_path if item]),
            "target_type": str(node.get("target_type") or ""),
            "delivery_mode": str(node.get("delivery_mode") or ""),
            "delivery_bucket": str(node.get("delivery_bucket") or ""),
            "route": str(node.get("route") or ""),
        }


def _leaf_count(tree: list[dict[str, Any]]) -> int:
    return len(list(_iter_leaves(tree)))


def _latest_smoke_leaf_count() -> int:
    pinned = int(os.environ.get("MENU_BASELINE_LEAF_COUNT", "66") or 66)
    root = ROOT / "artifacts" / "codex" / "unified-system-menu-click-usability-smoke"
    if not root.exists():
        return pinned
    summaries = sorted(root.glob("*/summary.json"), key=lambda item: item.parent.name)
    for summary in reversed(summaries):
        try:
            payload = json.loads(summary.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(payload.get("status") or "").upper() != "PASS":
            continue
        count = int(payload.get("leaf_count") or 0)
        if count > 0:
            return max(count, pinned)
    return pinned


def _assert_user_navigation(leaves: list[dict[str, Any]], *, baseline_leaf_count: int) -> list[str]:
    errors: list[str] = []
    prohibited_tokens = [
        "演示",
        "试点",
        "窗口动作",
        "菜单项",
        "IAP",
        "场景与能力",
        "能力目录",
        "场景编排",
        "订阅实例",
        "交付包注册表",
        "生命周期驾驶舱",
        "工作台",
        "能力矩阵",
    ]
    user_leaf_count = len(leaves)
    if user_leaf_count >= baseline_leaf_count:
        errors.append(f"leaf_count_not_reduced: baseline={baseline_leaf_count}, current={user_leaf_count}")
    if baseline_leaf_count - user_leaf_count < 8:
        errors.append(f"leaf_count_reduction_too_small: baseline={baseline_leaf_count}, current={user_leaf_count}")

    for row in leaves:
        path_text = str(row.get("path") or "")
        for token in prohibited_tokens:
            if token in path_text:
                errors.append(f"prohibited_token_visible: token={token}, path={path_text}")
                break
    return errors


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    base_url = str(os.environ.get("MENU_AUDIT_BASE_URL", "http://127.0.0.1:8069")).rstrip("/")
    db = str(os.environ.get("DB_NAME", "sc_demo")).strip() or "sc_demo"

    user_login = str(os.environ.get("MENU_USER_LOGIN", os.environ.get("FRONTEND_API_LOGIN", "wutao"))).strip() or "wutao"
    user_password = str(os.environ.get("MENU_USER_PASSWORD", os.environ.get("FRONTEND_API_PASSWORD", "demo"))).strip() or "demo"
    admin_login = str(os.environ.get("MENU_ADMIN_LOGIN", "admin")).strip() or "admin"
    admin_password = str(os.environ.get("MENU_ADMIN_PASSWORD", "admin")).strip() or "admin"

    user_token = _login_token(base_url, db, user_login, user_password)
    user_payload = _fetch_navigation(base_url, db, user_token)
    user_nav_explained = user_payload.get("nav_explained") if isinstance(user_payload.get("nav_explained"), dict) else {}
    user_tree = user_nav_explained.get("tree") if isinstance(user_nav_explained.get("tree"), list) else []
    user_leaves = list(_iter_leaves(user_tree))

    admin_fallback_to_user = False
    try:
        admin_token = _login_token(base_url, db, admin_login, admin_password)
        admin_payload = _fetch_navigation(base_url, db, admin_token)
    except Exception:
        admin_fallback_to_user = True
        admin_payload = user_payload
        admin_login = user_login
    admin_nav_explained = admin_payload.get("nav_explained") if isinstance(admin_payload.get("nav_explained"), dict) else {}
    admin_tree = admin_nav_explained.get("tree") if isinstance(admin_nav_explained.get("tree"), list) else []

    baseline_leaf_count = _latest_smoke_leaf_count()
    errors = _assert_user_navigation(user_leaves, baseline_leaf_count=baseline_leaf_count)

    user_snapshot = {
        "profile": "delivery_user",
        "login": user_login,
        "db": db,
        "leaf_count": _leaf_count(user_tree),
        "tree": user_tree,
        "meta": user_payload.get("meta") if isinstance(user_payload.get("meta"), dict) else {},
    }
    admin_snapshot = {
        "profile": "delivery_admin",
        "login": admin_login,
        "db": db,
        "leaf_count": _leaf_count(admin_tree),
        "tree": admin_tree,
        "meta": admin_payload.get("meta") if isinstance(admin_payload.get("meta"), dict) else {},
        "fallback_to_user": admin_fallback_to_user,
    }
    diff_payload = {
        "baseline_leaf_count": baseline_leaf_count,
        "delivery_user_leaf_count": user_snapshot["leaf_count"],
        "delivery_admin_leaf_count": admin_snapshot["leaf_count"],
        "leaf_reduction": baseline_leaf_count - int(user_snapshot["leaf_count"]),
        "delivery_user_convergence": (user_snapshot.get("meta") or {}).get("delivery_convergence") if isinstance(user_snapshot.get("meta"), dict) else {},
        "delivery_admin_convergence": (admin_snapshot.get("meta") or {}).get("delivery_convergence") if isinstance(admin_snapshot.get("meta"), dict) else {},
        "errors": errors,
    }

    _write_json(ARTIFACT_DIR / "delivery_user_navigation_v1.json", user_snapshot)
    _write_json(ARTIFACT_DIR / "delivery_admin_navigation_v1.json", admin_snapshot)
    _write_json(ARTIFACT_DIR / "menu_convergence_diff_v1.json", diff_payload)

    if errors:
        for row in errors:
            print(f"[menu_delivery_convergence_audit] FAIL: {row}")
        return 2

    print("[menu_delivery_convergence_audit] PASS")
    print(f"- baseline_leaf_count: {baseline_leaf_count}")
    print(f"- delivery_user_leaf_count: {user_snapshot['leaf_count']}")
    print(f"- delivery_admin_leaf_count: {admin_snapshot['leaf_count']}")
    print("- artifacts:")
    print("  - artifacts/menu/delivery_user_navigation_v1.json")
    print("  - artifacts/menu/delivery_admin_navigation_v1.json")
    print("  - artifacts/menu/menu_convergence_diff_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
