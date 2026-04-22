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
        "user_id",
        "partner_id",
        "stage_id",
        "lifecycle_state",
        "date_start",
        "date",
    ]
    assert (list_profile.get("column_labels") or {}) == {
        "name": "名称",
        "user_id": "项目管理员",
        "partner_id": "客户",
        "stage_id": "阶段",
        "lifecycle_state": "项目状态",
        "date_start": "开始日期",
        "date": "有效期",
    }
