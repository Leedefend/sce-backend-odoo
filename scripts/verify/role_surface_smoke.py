#!/usr/bin/env python3
import json
import os
import sys
import urllib.request

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8069').rstrip('/')
DB_NAME = os.getenv('DB_NAME') or os.getenv('DB') or 'sc_demo'

ROLE_USERS = [
    ('owner', os.getenv('ROLE_OWNER_LOGIN', 'demo_role_owner'), os.getenv('ROLE_OWNER_PASSWORD', 'demo')),
    ('pm', os.getenv('ROLE_PM_LOGIN', 'demo_role_pm'), os.getenv('ROLE_PM_PASSWORD', 'demo')),
    ('finance', os.getenv('ROLE_FINANCE_LOGIN', 'demo_role_finance'), os.getenv('ROLE_FINANCE_PASSWORD', 'demo')),
    ('executive', os.getenv('ROLE_EXECUTIVE_LOGIN', 'demo_role_executive'), os.getenv('ROLE_EXECUTIVE_PASSWORD', 'demo')),
]


def post_intent(intent: str, params: dict, token: str | None = None, anonymous: bool = False) -> dict:
    payload = json.dumps({'intent': intent, 'params': params}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if anonymous:
        headers['X-Anonymous-Intent'] = '1'
    req = urllib.request.Request(f'{BASE_URL}/api/v1/intent', data=payload, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode('utf-8')
    parsed = json.loads(body or '{}')
    return parsed


def ensure_ok(payload: dict, label: str):
    ok = bool(payload.get('ok'))
    if ok:
        return
    error = payload.get('error') if isinstance(payload.get('error'), dict) else {}
    message = error.get('message') or payload
    raise AssertionError(f'{label} not ok: {message}')


def main() -> int:
    summary = []
    for expected_role, login, password in ROLE_USERS:
        login_payload = post_intent('login', {'db': DB_NAME, 'login': login, 'password': password}, anonymous=True)
        ensure_ok(login_payload, f'login:{login}')
        token = ((login_payload.get('data') or {}).get('token') or '').strip()
        if not token:
            raise AssertionError(f'login:{login} missing token')

        init_payload = post_intent(
            'app.init',
            {'scene': 'web', 'with_preload': False, 'root_xmlid': 'smart_construction_core.menu_sc_root'},
            token=token,
        )
        ensure_ok(init_payload, f'app.init:{login}')
        data = init_payload.get('data') if isinstance(init_payload.get('data'), dict) else {}

        role_surface = data.get('role_surface') if isinstance(data.get('role_surface'), dict) else {}
        role_surface_map = data.get('role_surface_map') if isinstance(data.get('role_surface_map'), dict) else {}
        nav = data.get('nav') if isinstance(data.get('nav'), list) else []

        actual_role = str(role_surface.get('role_code') or '')
        if actual_role != expected_role:
            raise AssertionError(f'role mismatch for {login}: expected={expected_role} actual={actual_role}')

        landing_scene = str(role_surface.get('landing_scene_key') or '')
        landing_path = str(role_surface.get('landing_path') or '')
        if not landing_scene:
            raise AssertionError(f'landing scene missing for {login}')
        if not landing_path.startswith('/s/'):
            raise AssertionError(f'landing path invalid for {login}: {landing_path}')
        if expected_role not in role_surface_map:
            raise AssertionError(f'role map missing key {expected_role} for {login}')
        if not nav:
            raise AssertionError(f'nav empty for {login}')

        summary.append({
            'login': login,
            'role': actual_role,
            'landing_scene': landing_scene,
            'landing_path': landing_path,
            'nav_count': len(nav),
        })

    print('[role_surface_smoke] PASS')
    print(json.dumps({'db': DB_NAME, 'roles': summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'[role_surface_smoke] FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
