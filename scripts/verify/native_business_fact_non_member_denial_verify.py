#!/usr/bin/env python3
import json
import os
import time
import urllib.request
from http.cookiejar import CookieJar


def _env(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self._id = 0
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )

    def _post(self, path: str, payload: dict):
        req = urllib.request.Request(
            f'{self.base_url}{path}',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with self.opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode('utf-8'))
        if body.get('error'):
            raise RuntimeError(json.dumps(body['error'], ensure_ascii=False))
        return body.get('result')

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
        if not result.get('uid'):
            raise RuntimeError(f'auth failed for {login}')

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


def _assert_denied_or_empty(session: OdooSession, model: str, project_id: int):
    try:
        rows = session.call_kw(
            model,
            'search_read',
            [[('project_id', '=', project_id)]],
            {'fields': ['id'], 'limit': 1},
        )
    except Exception:
        return
    if rows:
        raise RuntimeError(f'non-member still sees records: model={model} count>0')


def main():
    base_url = _env('E2E_BASE_URL', 'http://localhost:8069')
    db_name = _env('DB_NAME', 'sc_prod_sim')
    owner_login = _env('ROLE_OWNER_LOGIN', 'wutao')
    owner_password = _env('ROLE_OWNER_PASSWORD', 'demo')
    non_member_login = _env('ROLE_NON_MEMBER_LOGIN', '')
    non_member_password = _env('ROLE_NON_MEMBER_PASSWORD', 'demo')
    non_member_candidates = [
        item.strip()
        for item in _env(
            'ROLE_NON_MEMBER_CANDIDATES',
            'yelingyue,zhangwencui,lijianfeng,lidexue,chenshuai,yangdesheng',
        ).split(',')
        if item.strip()
    ]
    admin_login = _env('ADMIN_LOGIN', 'admin')
    admin_password = _env('ADMIN_PASSWORD', 'admin')

    owner = OdooSession(base_url)
    owner.authenticate(db_name, owner_login, owner_password)
    owner_user = owner.call_kw(
        'res.users',
        'search_read',
        [[('login', '=', owner_login)]],
        {'fields': ['id', 'company_id'], 'limit': 1},
    )
    owner_uid = owner_user[0]['id']
    owner_company = owner_user[0]['company_id'][0]

    project_id = owner.call_kw(
        'project.project',
        'create',
        [{'name': f'ITER1278_DENY_{int(time.time())}', 'privacy_visibility': 'followers'}],
    )
    task_id = owner.call_kw('project.task', 'create', [{'name': 'T1278', 'project_id': project_id}])

    payment_id = None
    settlement_id = None
    try:
        payment_id = owner.call_kw(
            'payment.request',
            'create',
            [{'name': 'P1278', 'project_id': project_id, 'amount': 1.0}],
        )
    except Exception:
        pass
    try:
        settlement_id = owner.call_kw(
            'sc.settlement.order',
            'create',
            [{'name': 'S1278', 'project_id': project_id}],
        )
    except Exception:
        pass

    owner.call_kw(
        'project.project',
        'write',
        [[project_id], {'project_manager_user_id': owner_uid}],
    )

    outsider = OdooSession(base_url)
    temp_outsider_user_id = None
    if non_member_login:
        outsider.authenticate(db_name, non_member_login, non_member_password)
    else:
        selected = None
        for candidate in non_member_candidates:
            if candidate == owner_login:
                continue
            try:
                outsider.authenticate(db_name, candidate, non_member_password)
                selected = candidate
                break
            except Exception:
                continue
        if not selected:
            admin = OdooSession(base_url)
            admin.authenticate(db_name, admin_login, admin_password)
            group_user = admin.call_kw(
                'ir.model.data',
                'search_read',
                [[('module', '=', 'base'), ('name', '=', 'group_user')]],
                {'fields': ['res_id'], 'limit': 1},
            )
            group_project_read = admin.call_kw(
                'ir.model.data',
                'search_read',
                [[('module', '=', 'smart_construction_core'), ('name', '=', 'group_sc_cap_project_read')]],
                {'fields': ['res_id'], 'limit': 1},
            )
            if not group_user:
                raise RuntimeError('cannot resolve required groups for outsider bootstrap')
            non_member_login = f'iter1278_outsider_{int(time.time())}'
            temp_outsider_user_id = admin.call_kw(
                'res.users',
                'create',
                [{
                    'name': 'ITER1278 Outsider',
                    'login': non_member_login,
                    'password': non_member_password,
                    'company_id': owner_company,
                    'company_ids': [(6, 0, [owner_company])],
                    'groups_id': [(6, 0, [group_user[0]['res_id']])],
                }],
            )
            outsider.authenticate(db_name, non_member_login, non_member_password)
        else:
            non_member_login = selected

    _assert_denied_or_empty(outsider, 'project.project', project_id)
    _assert_denied_or_empty(outsider, 'project.task', project_id)
    _assert_denied_or_empty(outsider, 'project.budget', project_id)
    _assert_denied_or_empty(outsider, 'project.cost.ledger', project_id)
    _assert_denied_or_empty(outsider, 'payment.request', project_id)
    _assert_denied_or_empty(outsider, 'payment.ledger', project_id)
    _assert_denied_or_empty(outsider, 'sc.settlement.order', project_id)

    try:
        if settlement_id:
            owner.call_kw('sc.settlement.order', 'unlink', [[settlement_id]])
    except Exception:
        pass
    try:
        if payment_id:
            owner.call_kw('payment.request', 'unlink', [[payment_id]])
    except Exception:
        pass
    for model, rec_id in [('project.task', task_id), ('project.project', project_id)]:
        try:
            owner.call_kw(model, 'unlink', [[rec_id]])
        except Exception:
            pass
    if temp_outsider_user_id:
        try:
            admin = OdooSession(base_url)
            admin.authenticate(db_name, admin_login, admin_password)
            admin.call_kw('res.users', 'unlink', [[temp_outsider_user_id]])
        except Exception:
            pass

    print(
        '[native_business_fact_non_member_denial_verify] PASS '
        f'base_url={base_url} owner={owner_login} outsider={non_member_login}'
    )


if __name__ == '__main__':
    main()
