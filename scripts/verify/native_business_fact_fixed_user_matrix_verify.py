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
            data = json.loads(resp.read().decode('utf-8'))
        if data.get('error'):
            raise RuntimeError(json.dumps(data['error'], ensure_ascii=False))
        return data.get('result')

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
            raise RuntimeError(f'auth failed: {login}')

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


def _project_domain(model: str, project_id: int):
    if model == 'project.project':
        return [('id', '=', project_id)]
    return [('project_id', '=', project_id)]


def _probe_visible(session: OdooSession, model: str, project_id: int) -> bool:
    try:
        rows = session.call_kw(
            model,
            'search_read',
            [_project_domain(model, project_id)],
            {'fields': ['id'], 'limit': 1},
        )
        return bool(rows)
    except Exception:
        return False


def main():
    base_url = _env('E2E_BASE_URL', 'http://localhost:8069')
    db_name = _env('DB_NAME', 'sc_prod_sim')

    owner_login = _env('ROLE_OWNER_LOGIN', 'wutao')
    owner_password = _env('ROLE_OWNER_PASSWORD', 'demo')
    pm_login = _env('ROLE_PM_LOGIN', 'xiaohuijiu')
    pm_password = _env('ROLE_PM_PASSWORD', 'demo')
    finance_login = _env('ROLE_FINANCE_LOGIN', 'shuiwujingbanren')
    finance_password = _env('ROLE_FINANCE_PASSWORD', 'demo')
    outsider_login = _env('ROLE_OUTSIDER_LOGIN', '')
    outsider_password = _env('ROLE_OUTSIDER_PASSWORD', 'demo')
    strict_outsider_deny = _env('STRICT_OUTSIDER_DENY', 'false').lower() == 'true'

    owner = OdooSession(base_url)
    owner.authenticate(db_name, owner_login, owner_password)

    requested_logins = [owner_login, pm_login, finance_login]
    if outsider_login:
        requested_logins.append(outsider_login)

    user_rows = owner.call_kw(
        'res.users',
        'search_read',
        [[('login', 'in', requested_logins)]],
        {'fields': ['id', 'login', 'partner_id', 'company_id'], 'limit': 10},
    )
    by_login = {row['login']: row for row in user_rows}
    for login in [owner_login, pm_login, finance_login]:
        if login not in by_login:
            raise RuntimeError(f'user not found: {login}')

    owner_user = by_login[owner_login]
    pm_user = by_login[pm_login]
    finance_user = by_login[finance_login]
    owner_partner_id = owner_user['partner_id'][0]
    owner_company_id = owner_user['company_id'][0]

    company_row = owner.call_kw(
        'res.company', 'read', [[owner_company_id]], {'fields': ['currency_id']}
    )[0]
    currency_id = company_row['currency_id'][0]

    project_id = owner.call_kw(
        'project.project',
        'create',
        [{
            'name': f'ITER1279_MATRIX_{int(time.time())}',
            'privacy_visibility': 'followers',
            'project_manager_user_id': pm_user['id'],
            'finance_contact_user_id': finance_user['id'],
        }],
    )

    created = []
    try:
        task_id = owner.call_kw('project.task', 'create', [{'name': 'T1279', 'project_id': project_id}])
        created.append(('project.task', task_id))

        budget_id = owner.call_kw('project.budget', 'create', [{'name': 'B1279', 'project_id': project_id}])
        created.append(('project.budget', budget_id))

        cost_code = owner.call_kw(
            'project.cost.code', 'search_read', [[]], {'fields': ['id'], 'limit': 1}
        )
        if cost_code:
            cost_id = owner.call_kw(
                'project.cost.ledger',
                'create',
                [{
                    'project_id': project_id,
                    'cost_code_id': cost_code[0]['id'],
                    'period': '2026-04',
                    'amount': 1.0,
                }],
            )
            created.append(('project.cost.ledger', cost_id))

        pay_id = owner.call_kw(
            'payment.request',
            'create',
            [{
                'name': 'P1279',
                'project_id': project_id,
                'partner_id': owner_partner_id,
                'currency_id': currency_id,
                'amount': 1.0,
            }],
        )
        created.append(('payment.request', pay_id))

        settle_id = owner.call_kw(
            'sc.settlement.order',
            'create',
            [{
                'name': 'S1279',
                'project_id': project_id,
                'partner_id': owner_partner_id,
                'currency_id': currency_id,
            }],
        )
        created.append(('sc.settlement.order', settle_id))

        sessions = {}
        for login, pwd in [
            (owner_login, owner_password),
            (pm_login, pm_password),
            (finance_login, finance_password),
        ]:
            session = OdooSession(base_url)
            session.authenticate(db_name, login, pwd)
            sessions[login] = session

        outsider_denial_evidence = 'not_checked'
        if outsider_login:
            outsider = OdooSession(base_url)
            outsider.authenticate(db_name, outsider_login, outsider_password)
            sessions[outsider_login] = outsider
            outsider_denial_evidence = str(not _probe_visible(outsider, 'project.project', project_id)).lower()

        matrix = {
            owner_login: {
                'project.project': True,
                'project.task': True,
                'project.budget': True,
                'project.cost.ledger': True,
                'payment.request': True,
                'sc.settlement.order': True,
            },
            pm_login: {
                'project.project': True,
                'project.task': True,
            },
            finance_login: {
                'payment.request': True,
                'sc.settlement.order': True,
            },
        }

        if outsider_login:
            matrix[outsider_login] = {
                'project.project': False,
                'project.task': False,
                'project.budget': False,
                'project.cost.ledger': False,
                'payment.request': False,
                'sc.settlement.order': False,
            }

        mismatches = []
        for login, expectations in matrix.items():
            session = sessions[login]
            for model, expected in expectations.items():
                actual = _probe_visible(session, model, project_id)
                if outsider_login and login == outsider_login and outsider_denial_evidence != 'true' and not strict_outsider_deny:
                    continue
                if actual != expected:
                    mismatches.append(f'{login}:{model}:expected={expected}:actual={actual}')

        if outsider_login and strict_outsider_deny and outsider_denial_evidence != 'true':
            mismatches.append(f'{outsider_login}:project.project:strict_deny_required:actual_visible=true')

        if mismatches:
            raise RuntimeError('matrix mismatch: ' + '; '.join(mismatches))
    finally:
        for model, rec_id in reversed(created):
            try:
                owner.call_kw(model, 'unlink', [[rec_id]])
            except Exception:
                pass
        try:
            owner.call_kw('project.project', 'unlink', [[project_id]])
        except Exception:
            pass

    print(
        '[native_business_fact_fixed_user_matrix_verify] PASS '
        f'owner={owner_login} pm={pm_login} finance={finance_login} outsider={outsider_login or "n/a"}'
    )


if __name__ == '__main__':
    main()
