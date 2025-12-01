# -*- coding: utf-8 -*-
# contract_service.py
#
# 说明：
# 1）本文件在原有生成契约的基础上，增加“最后一公里”保险丝（ContractNormalizer）
# 2）保险丝仅在返回前进行“只读”清洗，不改变业务含义，只做结构兜底、类型纠偏、空值处理与安全裁剪
# 3）如需临时关闭保险丝，可将环境变量 CONTRACT_NORMALIZER_ENABLED 设为 "0"

import os
import copy
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

JsonDict = Dict[str, Any]
JsonList = List[Any]

# =========================
# ========== P0 ===========
# =========================
# P0 目标（最小必要集）：
# - 结构兜底：确保返回包含 2.0 规范的顶层区块（head/permissions/rules/search/views/fields/buttons/workflow/collab/reports/ui/data/meta）
# - 类型一致：核心字段类型统一；将 tuple 转 list；将 None 置为安全默认值
# - 数据安全：裁剪过大字段（如 data.records 超限）、移除明显无效项（如空字符串键）
# - 兼容性：不“推理”业务含义，不重排字段，仅在缺失或类型错误时做最小更正
# - 可观测性：将清洗告警写入 meta.warn，便于排查

# ========== 工具函数 ==========

def _is_sequence(x) -> bool:
    """判断是否可当作序列（不含字符串与字节）"""
    return isinstance(x, (list, tuple))

def _coerce_list(x: Any, field_name: str, warns: List[str]) -> List[Any]:
    """将值强制转为 list；None -> []；tuple -> list；其他非序列 -> [x] 并告警"""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, tuple):
        return list(x)
    warns.append(f"[{field_name}] 非列表，已强制转为单元素列表")
    return [x]

def _safe_bool(x: Any, default: bool) -> bool:
    """安全布尔化"""
    if isinstance(x, bool):
        return x
    if x in (0, 1):
        return bool(x)
    if isinstance(x, str):
        return x.lower() in ("1", "true", "yes", "y", "t")
    return default

def _safe_int(x: Any, default: int) -> int:
    """安全整型化"""
    try:
        return int(x)
    except Exception:
        return default

def _safe_str(x: Any, default: str = "") -> str:
    """安全字符串化"""
    if x is None:
        return default
    if isinstance(x, str):
        return x
    return str(x)

def _strip_nones(d: JsonDict) -> JsonDict:
    """浅层清除 None 值键"""
    return {k: v for k, v in d.items() if v is not None}

def _cap_list(lst: List[Any], cap: int, field_name: str, warns: List[str]) -> List[Any]:
    """裁剪列表到上限"""
    if cap is not None and isinstance(cap, int) and len(lst) > cap:
        warns.append(f"[{field_name}] 数量 {len(lst)} 超过上限 {cap}，已裁剪")
        return lst[:cap]
    return lst

def _ensure_dict(x: Any, field_name: str, warns: List[str]) -> JsonDict:
    """确保为 dict，否者给空 dict 并告警"""
    if isinstance(x, dict):
        return x
    if x is None:
        return {}
    warns.append(f"[{field_name}] 非 dict，已置为空对象")
    return {}

def _ensure_str_list(x: Any, field_name: str, warns: List[str]) -> List[str]:
    """确保为字符串列表"""
    seq = _coerce_list(x, field_name, warns)
    out = []
    for i, item in enumerate(seq):
        if item is None:
            continue
        if not isinstance(item, str):
            warns.append(f"[{field_name}[{i}]] 非字符串，已转字符串")
            out.append(str(item))
        else:
            out.append(item)
    return out

def _now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

# ========== 保险丝实现 ==========

class ContractNormalizer:
    """
    契约 2.0 最后一公里保险丝
    - 仅做结构兜底、类型一致化与裁剪；不改变业务语义
    - 关键字段缺失时补安全默认，类型错误时纠偏
    - 所有修正规则均记录到 meta.warn 中
    """

    # 可配置上限（根据需要调整）
    MAX_RECORDS = int(os.getenv("CONTRACT_NORMALIZER_MAX_RECORDS", "200"))
    MAX_COLUMNS = int(os.getenv("CONTRACT_NORMALIZER_MAX_COLUMNS", "200"))
    ENABLED = _safe_bool(os.getenv("CONTRACT_NORMALIZER_ENABLED", "1"), True)

    TOP_KEYS = [
        "head", "permissions", "rules", "search", "views", "fields",
        "buttons", "workflow", "collab", "reports", "ui", "data", "meta"
    ]

    def normalize(self, payload: JsonDict) -> JsonDict:
        """主入口：对 {ok, data, meta} 或直接契约对象进行兜底清洗"""
        if not self.ENABLED:
            return payload

        payload = copy.deepcopy(payload) if isinstance(payload, dict) else {}

        # 兼容：既可能是 { ok, data, meta }，也可能直接就是契约主体
        if "ok" in payload and "data" in payload:
            # 标准包裹形式
            wrapper = payload
            data = wrapper.get("data") or {}
            meta = wrapper.get("meta") or {}
            warns: List[str] = []

            data = self._normalize_contract_body(data, warns)
            meta = self._normalize_meta(meta, warns)

            # 将告警注入 meta
            if warns:
                meta.setdefault("warn", [])
                meta["warn"] = list(set(meta["warn"] + warns))  # 去重
            wrapper["data"] = data
            wrapper["meta"] = meta
            return wrapper

        # 直接返回契约体（非常见；为健壮性保留）
        warns: List[str] = []
        data = self._normalize_contract_body(payload, warns)
        meta = self._normalize_meta({}, warns)
        ret = {"ok": True, "data": data, "meta": meta}
        if warns:
            ret["meta"]["warn"] = list(set(ret["meta"].get("warn", []) + warns))
        return ret

    # ---------- 子块清洗 ----------

    def _normalize_contract_body(self, data: JsonDict, warns: List[str]) -> JsonDict:
        """对契约主体做结构兜底与类型一致化"""
        data = _ensure_dict(data, "data", warns)

        # 1）顶层区块兜底
        for key in self.TOP_KEYS:
            if key not in data or data[key] is None:
                data[key] = {}
                warns.append(f"[{key}] 缺失，已补空对象")

        # 2）各分块校正
        data["head"] = self._normalize_head(data["head"], warns)
        data["permissions"] = self._normalize_permissions(data["permissions"], warns)
        data["rules"] = self._normalize_rules(data["rules"], warns)
        data["search"] = self._normalize_search(data["search"], warns)
        data["views"] = self._normalize_views(data["views"], warns)
        data["fields"] = self._normalize_fields(data["fields"], warns)
        data["buttons"] = self._normalize_buttons(data["buttons"], warns)
        data["workflow"] = self._normalize_workflow(data["workflow"], warns)
        data["collab"] = self._normalize_collab(data["collab"], warns)
        data["reports"] = self._normalize_reports(data["reports"], warns)
        data["ui"] = self._normalize_ui(data["ui"], warns)
        data["data"] = self._normalize_data_block(data["data"], data, warns)  # 依赖 views/head

        # 3）浅层去 None，避免前端渲染异常
        return _strip_nones(data)

    def _normalize_meta(self, meta: JsonDict, warns: List[str]) -> JsonDict:
        """meta 兜底：时间戳、版本、etag 字符串化"""
        meta = _ensure_dict(meta, "meta", warns)
        meta.setdefault("ts", _now_iso())
        if "version" in meta and not isinstance(meta["version"], str):
            meta["version"] = _safe_str(meta["version"])
            warns.append("[meta.version] 非字符串，已转字符串")
        if "etag" in meta and not isinstance(meta["etag"], str):
            meta["etag"] = _safe_str(meta["etag"])
            warns.append("[meta.etag] 非字符串，已转字符串")
        if "subject" in meta and not isinstance(meta["subject"], str):
            meta["subject"] = _safe_str(meta["subject"])
            warns.append("[meta.subject] 非字符串，已转字符串")
        return meta

    # ---------- 分块规则 ----------

    def _normalize_head(self, head: Any, warns: List[str]) -> JsonDict:
        head = _ensure_dict(head, "head", warns)
        head.setdefault("model", "")
        head["model"] = _safe_str(head["model"])
        head.setdefault("title", "")
        head["title"] = _safe_str(head["title"])
        head.setdefault("view_modes", ["tree", "form"])
        head["view_modes"] = self._ensure_unique_str_list(head["view_modes"], "head.view_modes", warns)
        head.setdefault("default_view", head["view_modes"][0] if head["view_modes"] else "tree")
        head["default_view"] = _safe_str(head["default_view"], "tree")
        head.setdefault("identity", {"pk": "id", "display": "name"})
        head["identity"] = _ensure_dict(head["identity"], "head.identity", warns)
        head.setdefault("context", {})
        head["context"] = _ensure_dict(head["context"], "head.context", warns)
        return head

    def _normalize_permissions(self, perm: Any, warns: List[str]) -> JsonDict:
        perm = _ensure_dict(perm, "permissions", warns)
        perm["read"] = _safe_bool(perm.get("read", True), True)
        perm["create"] = _safe_bool(perm.get("create", True), True)
        perm["write"] = _safe_bool(perm.get("write", True), True)
        perm["unlink"] = _safe_bool(perm.get("unlink", False), False)
        return perm

    def _normalize_rules(self, rules: Any, warns: List[str]) -> JsonDict:
        rules = _ensure_dict(rules, "rules", warns)
        rules.setdefault("record_rules", [])
        rules["record_rules"] = _coerce_list(rules["record_rules"], "rules.record_rules", warns)
        rules.setdefault("domain_default", [])
        rules.setdefault("order_default", "id desc")
        rules["order_default"] = _safe_str(rules["order_default"], "id desc")
        return rules

    def _normalize_search(self, search: Any, warns: List[str]) -> JsonDict:
        search = _ensure_dict(search, "search", warns)
        search.setdefault("filters", [])
        search["filters"] = _coerce_list(search["filters"], "search.filters", warns)
        search.setdefault("group_by", [])
        search["group_by"] = _ensure_str_list(search["group_by"], "search.group_by", warns)
        # facets 可选
        if "facets" in search and not isinstance(search["facets"], dict):
            search["facets"] = {}
            warns.append("[search.facets] 非 dict，已置空对象")
        return search

    def _normalize_views(self, views: Any, warns: List[str]) -> JsonDict:
        views = _ensure_dict(views, "views", warns)

        # 统一将 tuple -> list；对常见子键做基本兜底
        for vt in ["tree", "form", "kanban", "pivot", "graph", "calendar", "gantt"]:
            if vt in views and views[vt] is not None:
                cfg = _ensure_dict(views[vt], f"views.{vt}", warns)
                if vt == "tree":
                    cfg.setdefault("columns", [])
                    cfg["columns"] = _ensure_str_list(cfg["columns"], "views.tree.columns", warns)
                    cfg["columns"] = _cap_list(cfg["columns"], self.MAX_COLUMNS, "views.tree.columns", warns)
                    cfg.setdefault("row_actions", [])
                    cfg["row_actions"] = _coerce_list(cfg["row_actions"], "views.tree.row_actions", warns)
                    cfg.setdefault("page_size", 50)
                    cfg["page_size"] = _safe_int(cfg["page_size"], 50)
                elif vt == "form":
                    cfg.setdefault("layout", [])
                    cfg["layout"] = _coerce_list(cfg["layout"], "views.form.layout", warns)
                    cfg.setdefault("statusbar", {})
                    cfg["statusbar"] = _ensure_dict(cfg["statusbar"], "views.form.statusbar", warns)
                elif vt == "pivot":
                    cfg.setdefault("measures", [])
                    cfg["measures"] = _ensure_str_list(cfg["measures"], "views.pivot.measures", warns)
                    cfg.setdefault("dimensions", [])
                    cfg["dimensions"] = _ensure_str_list(cfg["dimensions"], "views.pivot.dimensions", warns)
                elif vt == "graph":
                    cfg.setdefault("type", "bar")
                    cfg["type"] = _safe_str(cfg["type"], "bar")
                    cfg.setdefault("measure", "")
                    cfg["measure"] = _safe_str(cfg["measure"])
                    cfg.setdefault("dimension", "")
                    cfg["dimension"] = _safe_str(cfg["dimension"])
                elif vt in ("calendar", "gantt"):
                    # 只兜底关键字段名，不做校验
                    cfg.setdefault("date_start", "date_start")
                    cfg.setdefault("date_stop", "date_end")
                views[vt] = cfg

        return views

    def _normalize_fields(self, fields: Any, warns: List[str]) -> JsonDict:
        """字段字典：确保为 {name: {type, string, ...}}"""
        fields = _ensure_dict(fields, "fields", warns)
        out = {}
        for k, v in fields.items():
            if not isinstance(k, str):
                warns.append("[fields] 存在非字符串的字段名，已跳过")
                continue
            fv = _ensure_dict(v, f"fields.{k}", warns)
            fv.setdefault("string", k)
            fv["string"] = _safe_str(fv["string"], k)
            if "type" in fv and not isinstance(fv["type"], str):
                fv["type"] = _safe_str(fv["type"], "")
                warns.append(f"[fields.{k}.type] 非字符串，已转字符串")
            out[k] = fv
        return out

    def _normalize_buttons(self, buttons: Any, warns: List[str]) -> List[Dict[str, Any]]:
        buttons = _coerce_list(buttons, "buttons", warns)
        out = []
        for i, btn in enumerate(buttons):
            b = _ensure_dict(btn, f"buttons[{i}]", warns)
            b.setdefault("name", "")
            b["name"] = _safe_str(b["name"])
            b.setdefault("label", b["name"])
            b["label"] = _safe_str(b["label"], b["name"])
            b.setdefault("place", "header")
            b.setdefault("intent", "button.execute")
            out.append(b)
        return out

    def _normalize_workflow(self, wf: Any, warns: List[str]) -> JsonDict:
        wf = _ensure_dict(wf, "workflow", warns)
        wf.setdefault("states", [])
        wf["states"] = self._ensure_unique_str_list(wf["states"], "workflow.states", warns)
        wf.setdefault("transitions", [])
        wf["transitions"] = _coerce_list(wf["transitions"], "workflow.transitions", warns)
        return wf

    def _normalize_collab(self, collab: Any, warns: List[str]) -> JsonDict:
        collab = _ensure_dict(collab, "collab", warns)
        for k in ("chatter", "activity", "attachments"):
            if k in collab and not isinstance(collab[k], dict):
                collab[k] = {}
                warns.append(f"[collab.{k}] 非 dict，已置空对象")
        return collab

    def _normalize_reports(self, reports: Any, warns: List[str]) -> List[Dict[str, Any]]:
        reports = _coerce_list(reports, "reports", warns)
        out = []
        for i, r in enumerate(reports):
            rr = _ensure_dict(r, f"reports[{i}]", warns)
            rr.setdefault("name", "")
            rr.setdefault("label", rr["name"])
            rr.setdefault("type", "qweb-pdf")
            out.append(rr)
        return out

    def _normalize_ui(self, ui: Any, warns: List[str]) -> JsonDict:
        ui = _ensure_dict(ui, "ui", warns)
        # i18n、shortcuts、responsive 可选，按需兜底
        if "i18n" in ui and not isinstance(ui["i18n"], dict):
            ui["i18n"] = {}
            warns.append("[ui.i18n] 非 dict，已置空对象")
        if "shortcuts" in ui and not isinstance(ui["shortcuts"], list):
            ui["shortcuts"] = []
            warns.append("[ui.shortcuts] 非 list，已置空列表")
        if "responsive" in ui and not isinstance(ui["responsive"], dict):
            ui["responsive"] = {}
            warns.append("[ui.responsive] 非 dict，已置空对象")
        return ui

    def _normalize_data_block(self, datablock: Any, root: JsonDict, warns: List[str]) -> JsonDict:
        """data 区域兜底；根据当前默认视图类型给出最安全形态"""
        datablock = _ensure_dict(datablock, "data", warns)
        vt = root.get("head", {}).get("default_view", "tree")

        # 统一顶层键
        dtype = _safe_str(datablock.get("type", ""), "")
        if not dtype:
            # 未显式声明时，根据视图推测最保守类型
            dtype = "records" if vt in ("tree", "kanban") else (
                "record" if vt == "form" else vt
            )
        datablock["type"] = dtype

        # records/record 兜底
        if dtype in ("records", "groups"):
            records = datablock.get("records", [])
            records = _coerce_list(records, "data.records", warns)
            records = _cap_list(records, self.MAX_RECORDS, "data.records", warns)
            # 统一将 tuple -> list；浅层去 None
            fixed = []
            for i, r in enumerate(records):
                if r is None:
                    continue
                if isinstance(r, dict):
                    fixed.append(_strip_nones(r))
                else:
                    warns.append(f"[data.records[{i}]] 非 dict，已跳过")
            datablock["records"] = fixed
            datablock["total"] = _safe_int(datablock.get("total", len(fixed)), len(fixed))
            if "next_offset" in datablock and not isinstance(datablock["next_offset"], int):
                datablock["next_offset"] = _safe_int(datablock["next_offset"], 0)

        elif dtype == "record":
            rec = datablock.get("record", {})
            if not isinstance(rec, dict):
                warns.append("[data.record] 非 dict，已置空对象")
                rec = {}
            datablock["record"] = _strip_nones(rec)

        # 其他视图（pivot/graph/calendar/gantt/kpis）不在 P0 做深度校验，仅兜底键存在性
        # （避免对上游聚合逻辑产生误伤）

        return datablock

    # ---------- 辅助 ----------

    def _ensure_unique_str_list(self, x: Any, field_name: str, warns: List[str]) -> List[str]:
        lst = _ensure_str_list(x, field_name, warns)
        # 保持原有顺序去重
        seen = set()
        out = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                out.append(item)
        if len(out) < len(lst):
            warns.append(f"[{field_name}] 含重复项，已去重")
        return out