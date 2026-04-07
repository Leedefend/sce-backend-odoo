#!/usr/bin/env python3
import json
import os
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
        request = urllib.request.Request(
            f'{self.base_url}{path}',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with self.opener.open(request, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        if data.get('error'):
            raise RuntimeError(json.dumps(data['error'], ensure_ascii=False))
        return data.get('result')

    def authenticate(self, db_name: str, login: str, password: str):
        self._id += 1
        result = self._post(
            '/web/session/authenticate',
            {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {'db': db_name, 'login': login, 'password': password},
                'id': self._id,
            },
        )
        if not result.get('uid'):
            raise RuntimeError('authentication failed')

    def search_count(self, model: str, domain: list):
        self._id += 1
        return self._post(
            f'/web/dataset/call_kw/{model}/search_count',
            {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'model': model,
                    'method': 'search_count',
                    'args': [domain],
                    'kwargs': {},
                },
                'id': self._id,
            },
        )


def main():
    base_url = _env('E2E_BASE_URL', 'http://localhost:8069')
    db_name = _env('DB_NAME', 'sc_prod_sim')
    login = _env('ROLE_OWNER_LOGIN', _env('E2E_LOGIN', 'wutao'))
    password = _env('ROLE_OWNER_PASSWORD', _env('E2E_PASSWORD', 'demo'))

    session = OdooSession(base_url)
    session.authenticate(db_name, login, password)

    checks = {
        'payment.ledger.project_based_missing_project_anchor': (
            'payment.ledger',
            [('payment_request_id.project_id', '!=', False), ('project_id', '=', False)],
        ),
        'payment.ledger.project_based_project_without_company': (
            'payment.ledger',
            [('project_id', '!=', False), ('project_id.company_id', '=', False)],
        ),
        'payment.request.company_id_null_for_project_records': (
            'payment.request',
            [('project_id.company_id', '!=', False), ('company_id', '=', False)],
        ),
        'payment.request.project_without_company': (
            'payment.request',
            [('project_id', '!=', False), ('project_id.company_id', '=', False)],
        ),
        'sc.settlement.order.company_id_null_for_project_records': (
            'sc.settlement.order',
            [('project_id.company_id', '!=', False), ('company_id', '=', False)],
        ),
        'sc.settlement.order.project_without_company': (
            'sc.settlement.order',
            [('project_id', '!=', False), ('project_id.company_id', '=', False)],
        ),
    }

    failures = []
    details = []
    for key, (model, domain) in checks.items():
        count = session.search_count(model, domain)
        details.append(f'{key}={count}')
        if count:
            failures.append(f'{key}:{count}')

    if failures:
        raise SystemExit(
            '[native_business_fact_payment_settlement_anchor_data_verify] FAIL '
            + '; '.join(failures)
        )

    print(
        '[native_business_fact_payment_settlement_anchor_data_verify] PASS '
        + ' '.join(details)
    )


if __name__ == '__main__':
    main()
