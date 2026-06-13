# -*- coding: utf-8 -*-

import ast
from pathlib import Path
from xml.etree import ElementTree as ET


def _projects_list_payload():
    xml_path = Path(__file__).resolve().parents[1] / "data" / "sc_scene_list_profile.xml"
    tree = ET.parse(str(xml_path))
    for record in tree.findall(".//record"):
        if str(record.get("id") or "").strip() != "sc_scene_version_projects_list_v2":
            continue
        field = record.find("./field[@name='payload_json']")
        if field is None:
            raise AssertionError("payload_json field missing for projects.list scene profile")
        payload_eval = str(field.get("eval") or "").strip()
        if not payload_eval:
            raise AssertionError("payload_json eval missing for projects.list scene profile")
        return ast.literal_eval(payload_eval)
    raise AssertionError("projects.list scene version record not found")


def test_projects_list_profile_keeps_canonical_column_order_and_labels():
    payload = _projects_list_payload()
    list_profile = (payload.get("list_profile") or {})

    assert (list_profile.get("columns") or []) == [
        "name",
        "project_code",
        "owner_id",
        "sc_partner_display_name",
        "operation_strategy",
        "lifecycle_state",
        "user_id",
        "contract_amount",
        "dashboard_progress_rate",
        "write_date",
    ]
    assert (list_profile.get("column_labels") or {}) == {
        "name": "名称",
        "project_code": "项目编号",
        "owner_id": "业主单位",
        "sc_partner_display_name": "关联单位",
        "operation_strategy": "经营方式",
        "lifecycle_state": "项目状态",
        "user_id": "项目负责人",
        "contract_amount": "合同总额",
        "dashboard_progress_rate": "进度(%)",
        "write_date": "更新时间",
    }
