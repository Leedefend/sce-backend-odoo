# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _ensure_dict(env, *, dict_type, name, code=None, sequence=10):
    Dict = env["sc.dictionary"].sudo().with_context(active_test=False)
    domain = [("type", "=", dict_type)]
    if code:
        domain.append(("code", "=", code))
    else:
        domain.append(("name", "=", name))
    rec = Dict.search(domain, limit=1)
    if rec:
        if not rec.active:
            rec.write({"active": True})
        return rec
    vals = {
        "type": dict_type,
        "name": name,
        "sequence": sequence,
        "active": True,
    }
    if code:
        vals["code"] = code
    return Dict.create(vals)


def _run(env):
    items = [
        ("project_type", "施工项目", "PT01", 10),
        ("project_type", "设计项目", "PT02", 20),
        ("project_type", "运维项目", "PT03", 30),
        ("project_category", "房建", "PC01", 10),
        ("project_category", "市政", "PC02", 20),
        ("project_category", "机电", "PC03", 30),
        ("contract_category", "主合同", "CC01", 10),
        ("contract_category", "分包合同", "CC02", 20),
        ("contract_category", "采购合同", "CC03", 30),
        ("contract_type", "收入合同", "CT_OUT", 10),
        ("contract_type", "支出合同", "CT_IN", 20),
        ("doc_type", "立项资料", "DT01", 10),
        ("doc_type", "合同资料", "DT02", 20),
        ("doc_type", "签证资料", "DT03", 30),
        ("doc_type", "结算资料", "DT04", 40),
        ("doc_type", "验收资料", "DT05", 50),
        ("doc_subtype", "其他", "DST00", 10),
        ("fee_type", "人工", "FEE01", 10),
        ("fee_type", "材料", "FEE02", 20),
        ("fee_type", "机械", "FEE03", 30),
        ("fee_type", "分包", "FEE04", 40),
        ("fee_type", "措施", "FEE05", 50),
        ("fee_type", "管理费", "FEE06", 60),
        ("fee_type", "税金", "FEE07", 70),
        ("fee_type", "其他", "FEE99", 80),
        ("tax_type", "13%", "TAX13", 10),
        ("tax_type", "9%", "TAX09", 20),
        ("tax_type", "3%", "TAX03", 30),
        ("tax_type", "1%", "TAX01", 40),
        ("cost_item", "人工", "CI01", 10),
        ("cost_item", "材料", "CI02", 20),
        ("cost_item", "机械", "CI03", 30),
    ]
    for dict_type, name, code, sequence in items:
        _ensure_dict(env, dict_type=dict_type, name=name, code=code, sequence=sequence)


register(
    SeedStep(
        name="dictionary_min",
        description="Seed minimal sc.dictionary values for base usability.",
        run=_run,
    )
)
