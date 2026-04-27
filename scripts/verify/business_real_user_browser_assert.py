# -*- coding: utf-8 -*-
"""Assert browser-approved business records reached final backend states."""

import json
from pathlib import Path


ARTIFACT_DIR = Path("/mnt/artifacts/browser-real-user-business-closure/current")
SETUP_JSON = ARTIFACT_DIR / "setup.json"


def _env():
    return globals()["env"]


def main():
    setup = json.loads(SETUP_JSON.read_text(encoding="utf-8"))
    rows = []
    for row in setup.get("cases") or []:
        record = _env()[row["model"]].sudo().browse(int(row["record_id"])).exists()
        if not record:
            raise AssertionError("%s/%s missing before cleanup" % (row["model"], row["record_id"]))
        reviews = _env()["tier.review"].sudo().search([("model", "=", record._name), ("res_id", "=", record.id)])
        state = getattr(record, "state", "")
        validation_status = getattr(record, "validation_status", "")
        review_statuses = reviews.mapped("status")
        if state != row["expected_state"]:
            raise AssertionError("%s expected state %s, got %s" % (record._name, row["expected_state"], state))
        if validation_status != "validated":
            raise AssertionError("%s expected validated, got %s" % (record._name, validation_status))
        if not review_statuses or any(status != "approved" for status in review_statuses):
            raise AssertionError("%s review not approved: %s" % (record._name, review_statuses))
        rows.append(
            {
                "model": record._name,
                "record_id": record.id,
                "state": state,
                "validation_status": validation_status,
                "review_statuses": review_statuses,
            }
        )
    (ARTIFACT_DIR / "backend_assert.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("BUSINESS_REAL_USER_BROWSER_BACKEND_ASSERT=PASS")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


main()
