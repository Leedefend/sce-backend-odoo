#!/usr/bin/env python3
import json
import os
import time
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


def _base_url() -> str:
    return os.getenv('E2E_BASE_URL', 'http://localhost:8069').rstrip('/')


def _db_name() -> str:
    return os.getenv('DB_NAME', 'sc_prod_sim')


def _login() -> str:
    return os.getenv('ROLE_OWNER_LOGIN', os.getenv('E2E_LOGIN', 'admin'))


def _password() -> str:
    return os.getenv('ROLE_OWNER_PASSWORD', os.getenv('E2E_PASSWORD', 'admin'))


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._id = 0
        cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    def _post(self, path: str, payload: dict):
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f'{self.base_url}{path}',
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with self.opener.open(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
        result = json.loads(body)
        if result.get('error'):
            raise RuntimeError(json.dumps(result['error'], ensure_ascii=False))
        return result.get('result')

    def authenticate(self, db: str, login: str, password: str):
        self._id += 1
        result = self._post(
            '/web/session/authenticate',
            {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {'db': db, 'login': login, 'password': password},
                'id': self._id,
            },
        )
        uid = result.get('uid')
        if not uid:
            raise RuntimeError('authenticate failed: missing uid')
        return uid

    def call_kw(self, model: str, method: str, args=None, kwargs=None):
        self._id += 1
        return self._post(
            f'/web/dataset/call_kw/{model}/{method}',
            {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'model': model,
                    'method': method,
                    'args': args or [],
                    'kwargs': kwargs or {},
                },
                'id': self._id,
            },
        )


def main():
    view_file = Path('addons/smart_construction_core/views/core/project_views.xml')
    view_xml = view_file.read_text(encoding='utf-8')
    expected_fields = [
        'project_manager_user_id',
        'technical_lead_user_id',
        'business_lead_user_id',
        'cost_lead_user_id',
        'finance_contact_user_id',
        'project_member_ids',
    ]
    for field_name in expected_fields:
        if f'name="{field_name}"' not in view_xml:
            raise SystemExit(
                '[native_business_fact_project_org_native_form_persistence_verify] FAIL '
                f'native project form missing field/entry: {field_name}'
            )

    base_url = _base_url()
    db_name = _db_name()
    login = _login()
    password = _password()

    session = OdooSession(base_url)
    session.authenticate(db_name, login, password)

    users = session.call_kw(
        'res.users',
        'search_read',
        [[('login', '=', login)]],
        {'fields': ['id', 'login'], 'limit': 1},
    )
    if not users:
        raise SystemExit(
            '[native_business_fact_project_org_native_form_persistence_verify] FAIL login user not found'
        )
    user_id = users[0]['id']

    project_name = f'ITER1275_PROJECT_ORG_{int(time.time())}'
    project_id = session.call_kw('project.project', 'create', [{'name': project_name}])

    member_id = None
    try:
        role_values = {
            'project_manager_user_id': user_id,
            'technical_lead_user_id': user_id,
            'business_lead_user_id': user_id,
            'cost_lead_user_id': user_id,
            'finance_contact_user_id': user_id,
        }
        session.call_kw('project.project', 'write', [[project_id], role_values])

        member_id = session.call_kw(
            'project.responsibility',
            'create',
            [{'project_id': project_id, 'user_id': user_id, 'role_key': 'manager', 'is_primary': True}],
        )

        read_data = session.call_kw(
            'project.project',
            'read',
            [[project_id]],
            {'fields': list(role_values.keys()) + ['project_member_ids']},
        )
        if not read_data:
            raise SystemExit(
                '[native_business_fact_project_org_native_form_persistence_verify] FAIL project read returned empty'
            )

        record = read_data[0]
        for key, expected in role_values.items():
            value = record.get(key)
            actual = value[0] if isinstance(value, list) and value else value
            if actual != expected:
                raise SystemExit(
                    '[native_business_fact_project_org_native_form_persistence_verify] FAIL '
                    f'field not persisted: {key} expected={expected} actual={actual}'
                )

        member_ids = set(record.get('project_member_ids') or [])
        if member_id not in member_ids:
            raise SystemExit(
                '[native_business_fact_project_org_native_form_persistence_verify] FAIL '
                'project member carrier not persisted on project'
            )
    finally:
        if member_id:
            try:
                session.call_kw('project.responsibility', 'unlink', [[member_id]])
            except Exception:
                pass
        if project_id:
            try:
                session.call_kw('project.project', 'unlink', [[project_id]])
            except Exception:
                pass

    print(
        '[native_business_fact_project_org_native_form_persistence_verify] PASS '
        f'base_url={base_url} db={db_name} login={login}'
    )


if __name__ == '__main__':
    main()
