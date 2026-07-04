#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from p1_daily_business_visible_contract_audit import P1_ENTRIES, _login, _norm, _post_contract
from python_http_smoke_utils import get_base_url


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = Path(os.getenv(
    "P1_DAILY_BUSINESS_FORM_USABILITY_AUDIT_JSON",
    str(ROOT / "artifacts" / "backend" / "p1_daily_business_form_usability_audit.json"),
))
REPORT_MD = Path(os.getenv(
    "P1_DAILY_BUSINESS_FORM_USABILITY_AUDIT_MD",
    str(ROOT / "docs" / "ops" / "audit" / "p1_daily_business_form_usability_audit.md"),
))


SECTION_SIGNAL_ALIASES: dict[str, list[str]] = {
    "基本信息": ["单据号", "单据编号", "登记单号", "申请单号", "状态", "项目", "业务类型", "账户信息"],
    "申请信息": ["申请单号", "申请日期", "申请金额", "申请人", "项目"],
    "关联单据": ["合同", "结算单", "付款记录", "明细", "line_ids"],
    "收支账户信息": ["往来单位", "资金方向", "币种", "金额", "账户", "收款账户", "付款账户", "开户行", "账号"],
    "其它信息": ["备注", "说明", "用途说明", "历史录入人", "历史录入时间"],
    "还款信息": ["还款", "到期日", "资金方向", "金额"],
    "扣款信息": ["扣款", "抵扣", "发票", "金额", "税额"],
    "扣款实缴信息": ["扣款", "抵扣", "发票", "金额", "税额"],
    "扣款退回信息": ["扣款", "抵扣", "发票", "金额", "税额"],
    "工程款确认": ["收款金额", "收款账户", "收入类别", "项目"],
    "代扣代缴明细": ["代扣", "税额", "扣"],
    "施工队明细": ["施工单位", "项目"],
    "日报时段": ["日期", "报表期间", "期间"],
    "账户余额合计": ["余额", "账户"],
    "资金详情": ["收入", "支出", "账户往来", "金额"],
    "详情": ["操作原因", "事由", "业务类型", "金额", "账户"],
    "项目间借贷": ["收款账户", "付款账户", "项目", "资金方向", "转账类别"],
    "贷款账户": ["账户", "往来单位", "银行"],
    "银行": ["银行", "贷款银行", "账户", "账号"],
    "金额": ["金额"],
    "利率": ["利率", "类型"],
    "期限": ["到期日", "日期", "期限"],
    "贷款信息": ["贷款", "资金方向", "金额"],
    "发票标题": ["登记单号", "发票"],
    "开票详情": ["发票", "开票", "票"],
    "发票实开详情": ["发票", "开票", "发票号码"],
    "发票金额": ["金额", "税额", "价税合计"],
    "受票方信息": ["受票", "往来单位"],
    "开票方信息": ["开票", "经办人"],
    "本次开票信息": ["发票", "开票", "金额"],
    "相关数据": ["合同", "结算单", "项目"],
    "预缴税款详情": ["税", "发票", "金额"],
    "抵扣登记信息": ["抵扣", "发票", "金额"],
    "抵扣详情": ["抵扣", "税额", "金额"],
    "发票信息": ["发票", "税额", "金额"],
    "材料信息": ["材料", "明细", "line_ids", "申请明细", "数量", "税率", "发票"],
    "施工单位": ["施工单位", "往来单位", "劳务单位"],
    "合同信息": ["合同", "合同编号", "签订", "标题"],
    "工种信息": ["工种", "明细", "line_ids"],
    "工种/表单信息": ["工种", "明细", "line_ids", "数量", "单价", "作业内容", "工时", "用工人数"],
    "汇总信息": ["结算金额", "总金额", "已付款", "未付款", "金额"],
    "方单详情": ["方单", "明细", "line_ids", "数量", "单价"],
    "合同清单": ["合同", "清单", "line_ids"],
    "机械设备明细": ["机械", "设备", "明细", "line_ids"],
    "表单信息": ["工作时间", "数量", "单价", "金额"],
    "机械设备租赁清单": ["机械", "设备", "租赁", "明细", "line_ids"],
    "结算费用清单": ["费用", "金额", "结算"],
    "租赁材料清单": ["租赁", "材料", "明细", "line_ids"],
    "结算材料租赁清单": ["租赁", "结算", "材料", "明细"],
    "附件": ["附件", "attachment"],
}

FIELD_SIGNAL_ALIASES: dict[str, list[str]] = {
    "账号类型": ["账户类型"],
    "开户账号": ["账号", "银行账号"],
    "是否默认账号": ["默认账户"],
    "是否过渡账户": ["固定账户"],
    "日期": ["日志日期", "单据日期"],
    "施工部位": ["施工部位", "标题"],
    "出勤人数": ["现场人数", "人数"],
    "出勤机械": ["机械", "设备"],
    "温度": ["天气"],
    "上午气候": ["天气"],
    "下午气候": ["天气"],
    "当日施工内容": ["日志内容", "单据说明", "说明"],
    "操作负责人": ["经办人", "项目经理"],
    "质量情况": ["质量/事项", "质量"],
    "施工员": ["经办人", "项目经理"],
}


def _post_form_contract(intent_url: str, token: str, model: str, render_profile: str = "") -> tuple[int, dict[str, Any]]:
    params: dict[str, Any] = {"op": "model", "model": model, "view_type": "form"}
    if render_profile:
        params["render_profile"] = render_profile
    status, payload = _post_contract(intent_url, token, model, "form")
    if render_profile:
        from python_http_smoke_utils import http_post_json

        status, payload = http_post_json(
            intent_url,
            {"intent": "ui.contract", "params": params},
            headers={"Authorization": f"Bearer {token}"},
        )
    return int(status), payload if isinstance(payload, dict) else {}


def _contract_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _field_labels(data: dict[str, Any]) -> list[str]:
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    labels: list[str] = []
    for name, meta in fields.items():
        label = _norm((meta or {}).get("string") if isinstance(meta, dict) else "") or _norm(name)
        if label and label not in labels:
            labels.append(label)
    return labels


def _form_json(data: dict[str, Any]) -> str:
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    return json.dumps(form, ensure_ascii=False, sort_keys=True)


def _has_attachment_signal(data: dict[str, Any]) -> bool:
    text = _form_json(data)
    return any(token in text for token in ("attachment", "附件", "message_main_attachment_id"))


def _has_chatter_signal(data: dict[str, Any]) -> bool:
    text = _form_json(data)
    return any(token in text for token in ("chatter", "日志", "message_ids", "activity_ids"))


def _missing_tokens(expected: list[str], data: dict[str, Any], aliases: dict[str, list[str]] | None = None) -> list[str]:
    text = _form_json(data)
    labels = set(_field_labels(data))
    missing: list[str] = []
    for item in expected:
        token = _norm(item)
        if not token:
            continue
        compatible = [token] + list((aliases or {}).get(token, []))
        if not any(candidate in labels or candidate in text for candidate in compatible):
            missing.append(token)
    return missing


def _permission(data: dict[str, Any], key: str) -> bool:
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    permissions = head.get("permissions") if isinstance(head.get("permissions"), dict) else {}
    if key in permissions:
        return bool(permissions.get(key))
    top = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
    effective = top.get("effective") if isinstance(top.get("effective"), dict) else {}
    rights = effective.get("rights") if isinstance(effective.get("rights"), dict) else {}
    return bool(rights.get(key))


def _required_fields(data: dict[str, Any]) -> list[dict[str, str]]:
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    rows: list[dict[str, str]] = []
    for name, meta in fields.items():
        if not isinstance(meta, dict) or not meta.get("required"):
            continue
        if meta.get("readonly") or meta.get("compute"):
            continue
        rows.append({"name": _norm(name), "label": _norm(meta.get("string") or meta.get("label") or name)})
    return rows


def _select_model(intent_url: str, token: str, entry: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for model in entry["candidates"]:
        status, payload = _post_contract(intent_url, token, model, "tree")
        ok = bool(200 <= status < 300 and isinstance(payload, dict) and payload.get("ok") is True)
        attempts.append({"model": model, "status": status, "ok": ok})
        if ok:
            return model, attempts
    return "", attempts


def _audit_entry(intent_url: str, token: str, entry: dict[str, Any]) -> dict[str, Any]:
    selected_model, attempts = _select_model(intent_url, token, entry)
    if not selected_model:
        return {
            "id": entry["id"],
            "name": entry["name"],
            "domain": entry["domain"],
            "selected_model": "",
            "status": "no_contract",
            "attempts": attempts,
            "gaps": ["no_readable_model_contract"],
        }

    form_status, form_payload = _post_form_contract(intent_url, token, selected_model)
    form_ok = bool(200 <= form_status < 300 and form_payload.get("ok") is True)
    form_data = _contract_data(form_payload) if form_ok else {}
    create_status, create_payload = _post_form_contract(intent_url, token, selected_model, "create")
    create_ok = bool(200 <= create_status < 300 and create_payload.get("ok") is True)
    create_data = _contract_data(create_payload) if create_ok else {}
    edit_status, edit_payload = _post_form_contract(intent_url, token, selected_model, "edit")
    edit_ok = bool(200 <= edit_status < 300 and edit_payload.get("ok") is True)
    edit_data = _contract_data(edit_payload) if edit_ok else {}

    missing_sections = _missing_tokens(
        list(entry.get("expected_form_sections") or []),
        form_data,
        SECTION_SIGNAL_ALIASES,
    )
    missing_fields = _missing_tokens(
        list(entry.get("expected_form_fields") or []),
        form_data,
        FIELD_SIGNAL_ALIASES,
    )
    attachment = _has_attachment_signal(form_data)
    chatter = _has_chatter_signal(form_data)
    create_allowed = create_ok and _permission(create_data, "create")
    edit_allowed = edit_ok and _permission(edit_data, "write")
    required_fields = _required_fields(create_data)

    gaps: list[str] = []
    if not form_ok:
        gaps.append("form_contract_error")
    if not create_ok:
        gaps.append("create_contract_error")
    if not edit_ok:
        gaps.append("edit_contract_error")
    if not create_allowed:
        gaps.append("create_not_allowed_for_audit_user")
    if not edit_allowed:
        gaps.append("edit_not_allowed_for_audit_user")
    if not attachment:
        gaps.append("missing_attachment_signal")
    if not chatter:
        gaps.append("missing_chatter_signal")
    if missing_sections:
        gaps.append("missing_expected_sections")
    if missing_fields:
        gaps.append("missing_expected_form_fields")

    return {
        "id": entry["id"],
        "name": entry["name"],
        "domain": entry["domain"],
        "selected_model": selected_model,
        "status": "usable_contract_ready" if not gaps else "needs_usability_attention",
        "attempts": attempts,
        "form_contract_ok": form_ok,
        "create_contract_ok": create_ok,
        "edit_contract_ok": edit_ok,
        "create_allowed": create_allowed,
        "edit_allowed": edit_allowed,
        "has_attachment_signal": attachment,
        "has_chatter_signal": chatter,
        "expected_form_sections": list(entry.get("expected_form_sections") or []),
        "missing_form_sections": missing_sections,
        "expected_form_fields": list(entry.get("expected_form_fields") or []),
        "missing_form_fields": missing_fields,
        "required_create_fields": required_fields,
        "required_create_field_count": len(required_fields),
        "gaps": gaps,
    }


def _write_reports(payload: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# P1 Daily Business Form Usability Audit",
        "",
        f"- audit_login: {payload.get('audit_login') or '-'}",
        f"- entry_count: {payload['summary']['entry_count']}",
        f"- usable_contract_ready_count: {payload['summary']['usable_contract_ready_count']}",
        f"- needs_usability_attention_count: {payload['summary']['needs_usability_attention_count']}",
        f"- no_contract_count: {payload['summary']['no_contract_count']}",
        f"- create_contract_ok_count: {payload['summary']['create_contract_ok_count']}",
        f"- create_allowed_count: {payload['summary']['create_allowed_count']}",
        f"- edit_contract_ok_count: {payload['summary']['edit_contract_ok_count']}",
        f"- edit_allowed_count: {payload['summary']['edit_allowed_count']}",
        f"- attachment_signal_count: {payload['summary']['attachment_signal_count']}",
        f"- chatter_signal_count: {payload['summary']['chatter_signal_count']}",
        f"- role_authorization_gap_count: {payload['summary']['role_authorization_gap_count']}",
        f"- form_field_gap_count: {payload['summary']['form_field_gap_count']}",
        "",
        "| id | old entry | model | status | create | edit | attachment | chatter | missing sections | missing fields | required fields | gaps |",
        "|---|---|---|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {id} | {name} | {model} | {status} | {create} | {edit} | {attach} | {chatter} | {sections} | {fields} | {required} | {gaps} |".format(
                id=row["id"],
                name=row["name"],
                model=row.get("selected_model") or "-",
                status=row["status"],
                create="Y" if row.get("create_contract_ok") and row.get("create_allowed") else "N",
                edit="Y" if row.get("edit_contract_ok") and row.get("edit_allowed") else "N",
                attach="Y" if row.get("has_attachment_signal") else "N",
                chatter="Y" if row.get("has_chatter_signal") else "N",
                sections=len(row.get("missing_form_sections") or []),
                fields=len(row.get("missing_form_fields") or []),
                required=row.get("required_create_field_count", 0),
                gaps=", ".join(row.get("gaps") or []),
            )
        )

    attention = [row for row in payload["rows"] if row["status"] != "usable_contract_ready"]
    if attention:
        lines.extend(["", "## Attention Details", ""])
        for row in attention:
            lines.append(f"### {row['id']} {row['name']}")
            lines.append(f"- selected_model: `{row.get('selected_model') or '-'}`")
            if row.get("missing_form_sections"):
                lines.append(f"- missing_form_sections: {', '.join(row['missing_form_sections'])}")
            if row.get("missing_form_fields"):
                lines.append(f"- missing_form_fields: {', '.join(row['missing_form_fields'])}")
            if row.get("gaps"):
                lines.append(f"- gaps: {', '.join(row['gaps'])}")
            if _has_role_authorization_gap(row):
                lines.append("- permission_note: audit user can read this contract but lacks create/write rights for this role profile")
            if row.get("required_create_fields"):
                labels = [item["label"] for item in row["required_create_fields"][:12]]
                lines.append(f"- required_create_fields: {', '.join(labels)}")
            lines.append("")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _has_role_authorization_gap(row: dict[str, Any]) -> bool:
    gaps = set(row.get("gaps") or [])
    return bool({"create_not_allowed_for_audit_user", "edit_not_allowed_for_audit_user"} & gaps)


def main() -> int:
    intent_url = f"{get_base_url()}/api/v1/intent"
    token, audit_login = _login(intent_url)
    rows = [_audit_entry(intent_url, token, entry) for entry in P1_ENTRIES]
    attention_rows = [row for row in rows if row["status"] != "usable_contract_ready"]
    summary = {
        "entry_count": len(rows),
        "usable_contract_ready_count": len([row for row in rows if row["status"] == "usable_contract_ready"]),
        "needs_usability_attention_count": len([row for row in rows if row["status"] == "needs_usability_attention"]),
        "no_contract_count": len([row for row in rows if row["status"] == "no_contract"]),
        "create_contract_ok_count": len([row for row in rows if row.get("create_contract_ok")]),
        "create_allowed_count": len([row for row in rows if row.get("create_allowed")]),
        "edit_contract_ok_count": len([row for row in rows if row.get("edit_contract_ok")]),
        "edit_allowed_count": len([row for row in rows if row.get("edit_allowed")]),
        "attachment_signal_count": len([row for row in rows if row.get("has_attachment_signal")]),
        "chatter_signal_count": len([row for row in rows if row.get("has_chatter_signal")]),
        "role_authorization_gap_count": len([row for row in rows if _has_role_authorization_gap(row)]),
        "form_field_gap_count": len(
            [row for row in rows if "missing_expected_form_fields" in set(row.get("gaps") or [])]
        ),
    }
    errors = [
        {
            "id": row["id"],
            "name": row["name"],
            "selected_model": row.get("selected_model") or "",
            "gaps": list(row.get("gaps") or []),
        }
        for row in attention_rows
    ]
    payload = {
        "ok": not errors,
        "scope": "P1 old-system daily-business form usability audit",
        "source_doc": "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx",
        "audit_login": audit_login,
        "summary": summary,
        "rows": rows,
        "errors": errors,
    }
    _write_reports(payload)
    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[p1_daily_business_form_usability_audit] FAIL")
        print(json.dumps({"error_count": len(errors), "errors": errors[:10]}, ensure_ascii=False, indent=2))
        return 1
    print("[p1_daily_business_form_usability_audit] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
