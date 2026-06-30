# -*- coding: utf-8 -*-
import base64
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from odoo import fields


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "site_quality_safety_closure_audit.json"


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_report(payload):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _expect_error(label, func, failures):
    try:
        with env.cr.savepoint():  # noqa: F821
            func()
    except Exception:
        return True
    failures.append("%s: expected business error, got success" % label)
    return False


def _attachment(record, name):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": name,
            "datas": base64.b64encode(("site closure evidence: %s" % name).encode("utf-8")),
            "res_model": record._name,
            "res_id": record.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.sudo().write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _audit_events(model, res_id):
    return sorted(
        {
            code
            for code in env["sc.audit.log"].sudo().search(  # noqa: F821
                [("model", "=", model), ("res_id", "=", res_id)],
                order="id asc",
            ).mapped("event_code")
            if code
        }
    )


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_project_user",
        "smart_construction_core.group_sc_cap_project_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})
    env.invalidate_all()  # noqa: F821


def _project(token):
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "Site Closure Project %s" % token,
            "code": "SITE-%s" % token,
            "company_id": env.company.id,  # noqa: F821
            "manager_id": env.user.id,  # noqa: F821
        }
    )


def _photo_batch(project, field_name, record, stage):
    batch = env["sc.site.photo.batch"].sudo().create(  # noqa: F821
        {
            "name": "%s evidence %s" % (record._description, _token()),
            "project_id": project.id,
            "evidence_stage": stage,
            field_name: record.id,
            "location": "现场闭环门禁",
            "note": "现场履约闭环证据",
        }
    )
    attachment = _attachment(batch, "%s-photo.txt" % record._name.replace(".", "-"))
    batch.write({"attachment_ids": [(4, attachment.id)]})
    return batch


def _close_quality(project, failures):
    issue = env["sc.quality.issue"].sudo().create(  # noqa: F821
        {
            "name": "质量问题闭环 %s" % _token(),
            "project_id": project.id,
            "location": "1#楼二层",
            "description": "墙面平整度偏差，需要整改并复验。",
            "issue_level": "important",
            "rectification_deadline": fields.Date.context_today(env["sc.quality.issue"]),  # noqa: F821
        }
    )
    _attachment(issue, "quality-issue.txt")
    issue.action_submit()
    _expect(issue.state == "submitted", "quality.state_after_submit: expected submitted", failures)
    _expect_error("quality.close_without_rectification", issue.action_close, failures)

    rectification = env["sc.quality.rectification"].sudo().create(  # noqa: F821
        {
            "issue_id": issue.id,
            "result": "已完成打磨找平并复测。",
        }
    )
    _attachment(rectification, "quality-rectification.txt")
    issue.invalidate_recordset()
    _expect(issue.state == "rectifying", "quality.state_after_rectification: expected rectifying", failures)
    issue.action_request_recheck()
    _expect(issue.state == "rechecking", "quality.state_after_recheck_request: expected rechecking", failures)
    _expect_error("quality.close_without_passed_recheck", issue.action_close, failures)

    failed = env["sc.quality.recheck"].sudo().create(  # noqa: F821
        {
            "issue_id": issue.id,
            "result": "failed",
            "comment": "局部仍需修补。",
        }
    )
    _attachment(failed, "quality-recheck-failed.txt")
    issue.invalidate_recordset()
    _expect(issue.state == "rectifying", "quality.state_after_failed_recheck: expected rectifying", failures)
    issue.action_request_recheck()
    passed = env["sc.quality.recheck"].sudo().create(  # noqa: F821
        {
            "issue_id": issue.id,
            "result": "passed",
            "comment": "复验通过。",
        }
    )
    _attachment(passed, "quality-recheck-passed.txt")
    issue.invalidate_recordset()
    _expect(issue.state == "closed", "quality.state_after_passed_recheck: expected closed", failures)
    _expect(bool(issue.closed_date), "quality.closed_date missing", failures)

    issue_photo = _photo_batch(project, "quality_issue_id", issue, "check")
    rectification_photo = _photo_batch(project, "quality_rectification_id", rectification, "rectification")
    recheck_photo = _photo_batch(project, "quality_recheck_id", passed, "recheck")
    _expect_error("quality.closed_issue_photo_delete_blocked", issue_photo.unlink, failures)

    expected_events = {
        "quality_issue_submitted",
        "quality_rectification_started",
        "quality_recheck_requested",
        "quality_recheck_failed",
        "quality_issue_closed",
    }
    events = set(_audit_events("sc.quality.issue", issue.id))
    _expect(expected_events.issubset(events), "quality audit events missing: %s" % sorted(expected_events - events), failures)
    _expect(
        env["sc.audit.log"].sudo().search_count([("model", "=", "sc.quality.rectification"), ("res_id", "=", rectification.id), ("event_code", "=", "quality_rectification_registered")]) == 1,  # noqa: F821
        "quality rectification audit missing",
        failures,
    )
    _expect(
        env["sc.audit.log"].sudo().search_count([("model", "=", "sc.quality.recheck"), ("res_id", "=", passed.id), ("event_code", "=", "quality_recheck_registered")]) == 1,  # noqa: F821
        "quality recheck audit missing",
        failures,
    )
    return {
        "issue_id": issue.id,
        "rectification_id": rectification.id,
        "failed_recheck_id": failed.id,
        "passed_recheck_id": passed.id,
        "photo_batch_ids": [issue_photo.id, rectification_photo.id, recheck_photo.id],
        "events": sorted(events),
    }


def _close_safety(project, failures):
    issue = env["sc.safety.issue"].sudo().create(  # noqa: F821
        {
            "name": "安全问题闭环 %s" % _token(),
            "project_id": project.id,
            "location": "基坑临边",
            "description": "临边防护缺失，需要整改并复验。",
            "issue_level": "critical",
            "rectification_deadline": fields.Date.context_today(env["sc.safety.issue"]),  # noqa: F821
        }
    )
    _attachment(issue, "safety-issue.txt")
    issue.action_submit()
    _expect(issue.state == "submitted", "safety.state_after_submit: expected submitted", failures)
    _expect_error("safety.close_without_rectification", issue.action_close, failures)

    rectification = env["sc.safety.rectification"].sudo().create(  # noqa: F821
        {
            "issue_id": issue.id,
            "result": "已设置防护栏杆和警示标识。",
        }
    )
    _attachment(rectification, "safety-rectification.txt")
    issue.invalidate_recordset()
    _expect(issue.state == "rectifying", "safety.state_after_rectification: expected rectifying", failures)
    issue.action_request_recheck()
    _expect(issue.state == "rechecking", "safety.state_after_recheck_request: expected rechecking", failures)
    _expect_error("safety.close_without_passed_recheck", issue.action_close, failures)

    failed = env["sc.safety.recheck"].sudo().create(  # noqa: F821
        {
            "issue_id": issue.id,
            "result": "failed",
            "comment": "警示标识仍不足。",
        }
    )
    _attachment(failed, "safety-recheck-failed.txt")
    issue.invalidate_recordset()
    _expect(issue.state == "rectifying", "safety.state_after_failed_recheck: expected rectifying", failures)
    issue.action_request_recheck()
    passed = env["sc.safety.recheck"].sudo().create(  # noqa: F821
        {
            "issue_id": issue.id,
            "result": "passed",
            "comment": "复验通过。",
        }
    )
    _attachment(passed, "safety-recheck-passed.txt")
    issue.invalidate_recordset()
    _expect(issue.state == "closed", "safety.state_after_passed_recheck: expected closed", failures)
    _expect(bool(issue.closed_date), "safety.closed_date missing", failures)

    issue_photo = _photo_batch(project, "safety_issue_id", issue, "check")
    rectification_photo = _photo_batch(project, "safety_rectification_id", rectification, "rectification")
    recheck_photo = _photo_batch(project, "safety_recheck_id", passed, "recheck")
    _expect_error("safety.closed_issue_photo_delete_blocked", issue_photo.unlink, failures)

    expected_events = {
        "safety_issue_submitted",
        "safety_rectification_started",
        "safety_recheck_requested",
        "safety_recheck_failed",
        "safety_issue_closed",
    }
    events = set(_audit_events("sc.safety.issue", issue.id))
    _expect(expected_events.issubset(events), "safety audit events missing: %s" % sorted(expected_events - events), failures)
    _expect(
        env["sc.audit.log"].sudo().search_count([("model", "=", "sc.safety.rectification"), ("res_id", "=", rectification.id), ("event_code", "=", "safety_rectification_registered")]) == 1,  # noqa: F821
        "safety rectification audit missing",
        failures,
    )
    _expect(
        env["sc.audit.log"].sudo().search_count([("model", "=", "sc.safety.recheck"), ("res_id", "=", passed.id), ("event_code", "=", "safety_recheck_registered")]) == 1,  # noqa: F821
        "safety recheck audit missing",
        failures,
    )
    return {
        "issue_id": issue.id,
        "rectification_id": rectification.id,
        "failed_recheck_id": failed.id,
        "passed_recheck_id": passed.id,
        "photo_batch_ids": [issue_photo.id, rectification_photo.id, recheck_photo.id],
        "events": sorted(events),
    }


failures = []
evidence = {}

try:
    _ensure_groups()
    token = _token()
    project = _project(token)
    evidence["project_id"] = project.id
    evidence["quality"] = _close_quality(project, failures)
    evidence["safety"] = _close_safety(project, failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "site_quality_safety_closure_audit",
    "generated_at_utc": _utc_now(),
    "ok": not failures,
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
    "report_path": str(REPORT_PATH.relative_to(ROOT)),
}
_write_report(result)
print(REPORT_PATH)
print("SITE_QUALITY_SAFETY_CLOSURE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)
    raise SystemExit(1)
