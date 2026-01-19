# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional

from odoo import _
from odoo.exceptions import AccessError

from .dto import BusinessInsight, InsightSummary


MISSING = object()


def _get_schedule_dates(project, safe_getattr):
    # Prefer system daterange fields (date_start/date) used by Odoo form view.
    primary_start = safe_getattr(project, "date_start")
    primary_end = safe_getattr(project, "date")
    alt_start = safe_getattr(project, "start_date")
    alt_end = safe_getattr(project, "end_date")

    start = primary_start if primary_start is not MISSING else alt_start
    end = primary_end if primary_end is not MISSING else alt_end

    # If primary exists but empty, allow alt fields to fill in.
    if not start and alt_start is not MISSING:
        start = alt_start
    if not end and alt_end is not MISSING:
        end = alt_end
    return start, end


def _check_missing_schedule(project, safe_getattr) -> bool:
    start, end = _get_schedule_dates(project, safe_getattr)
    if start is MISSING or end is MISSING:
        return False
    return not (start and end)


def _check_missing_manager(project, safe_getattr) -> bool:
    manager = safe_getattr(project, "manager_id")
    if manager is MISSING:
        return False
    return not manager


def _check_missing_wbs(project, safe_getattr) -> bool:
    ready = safe_getattr(project, "wbs_ready")
    if ready is MISSING:
        return False
    return not ready


def _check_missing_boq(project, safe_getattr) -> bool:
    imported = safe_getattr(project, "boq_imported")
    if imported is MISSING:
        return False
    return not imported


PROJECT_ENTRY_RULES = [
    {
        "key": "schedule_missing",
        "priority": 0,
        "level": "warning",
        "missing": _("项目周期（开始/结束日期）"),
        "check": _check_missing_schedule,
        "impact": _("无法形成施工周期计划，进度与资金预测将失准"),
        "will_block_at": _("进度计划与里程碑制定"),
        "recommended_action": {"label": _("补全周期"), "target": "schedule"},
    },
    {
        "key": "manager_missing",
        "priority": 1,
        "level": "warning",
        "missing": _("项目负责人"),
        "check": _check_missing_manager,
        "impact": _("责任归属不清，协作与审批流程将低效"),
        "will_block_at": _("任务分派与责任确认"),
        "recommended_action": {"label": _("指定负责人"), "target": "manager"},
    },
    {
        "key": "wbs_missing",
        "priority": 2,
        "level": "warning",
        "missing": _("工程结构（WBS）"),
        "check": _check_missing_wbs,
        "impact": _("无法拆解任务，成本与进度难以落地"),
        "will_block_at": _("任务拆解与成本归集"),
        "recommended_action": {"label": _("完善工程结构"), "target": "wbs"},
    },
    {
        "key": "boq_missing",
        "priority": 3,
        "level": "warning",
        "missing": _("工程量清单（BOQ）"),
        "check": _check_missing_boq,
        "impact": _("无法核算合同与成本，结算分析将受阻"),
        "will_block_at": _("成本测算与结算分析"),
        "recommended_action": {"label": _("导入工程量清单"), "target": "boq"},
    },
]


def _build_initiation_v0_3(risks, risk_count):
    def priority(risk):
        return risk.get("priority", 999)

    def is_actionable(risk):
        return bool((risk.get("recommended_action") or {}).get("target"))

    sorted_risks = sorted(risks, key=priority)
    primary = next((r for r in sorted_risks if is_actionable(r)), None) or (sorted_risks[0] if sorted_risks else None)
    secondary = [r for r in sorted_risks if r is not primary]

    if risk_count <= 0:
        return {
            "can_continue": True,
            "tone": "neutral",
            "headline": _("项目已具备执行条件"),
            "recommendation": _("可以开始组织任务、进度和成本工作。"),
            "reason": "",
            "primary_suggestion": None,
            "secondary_items": [],
        }

    headline = _("项目已创建，可以继续推进。")
    recommendation = _("建议先完成：%s") % (primary.get("missing") or _("一项关键准备")) if primary else _("建议先完成一项关键准备。")
    reason = ""
    if primary:
        impact = primary.get("impact") or ""
        block = primary.get("will_block_at") or ""
        if impact and block:
            reason = _("否则在【%s】会受阻：%s") % (block, impact)
        elif impact:
            reason = impact
        elif block:
            reason = _("在【%s】将受到影响") % block

    def map_item(risk):
        return {
            "rule_key": risk.get("rule_key"),
            "headline": risk.get("missing") or "",
            "recommendation": (risk.get("recommended_action") or {}).get("label") or "",
            "reason": risk.get("impact") or "",
            "block_stage": risk.get("will_block_at") or "",
            "recommended_action": risk.get("recommended_action") or {},
        }

    return {
        "can_continue": True,
        "tone": "gentle",
        "headline": headline,
        "recommendation": recommendation,
        "reason": reason,
        "primary_suggestion": map_item(primary) if primary else None,
        "secondary_items": [map_item(risk) for risk in secondary],
    }


def _build_ui_model(initiation: Dict[str, Any]) -> Dict[str, Any]:
    risks = initiation.get("risks") or []
    risk_count = initiation.get("risk_count", len(risks))
    if risk_count <= 0:
        return {
            "variant": "initiation_v0_3",
            "hero": {
                "tone": "ready",
                "title": _("项目已具备执行条件"),
                "subtitle": _("可以开始组织任务、进度和成本工作。"),
                "hint": "",
            },
            "next_best": None,
            "more": None,
            "footer": {"text": ""},
        }

    def risk_priority(risk):
        return risk.get("priority", 999)

    sorted_risks = sorted(risks, key=risk_priority)
    best = sorted_risks[0] if sorted_risks else None
    rest = sorted_risks[1:] if len(sorted_risks) > 1 else []

    cta_map = {
        "schedule": {"label": _("先设置项目周期"), "target": "schedule"},
        "manager": {"label": _("现在指定负责人"), "target": "manager"},
        "wbs": {"label": _("现在拆一下"), "target": "wbs"},
        "boq": {"label": _("导入清单"), "target": "boq"},
    }

    headline_map = {
        "schedule": _("把项目周期设清楚（开始/结束日期）"),
        "manager": _("把负责人定下来（责任与审批才能跑起来）"),
        "wbs": _("把工程拆到可执行（工程结构 / WBS）"),
        "boq": _("把工程量清单导进来（BOQ）"),
    }

    label_map = {
        "schedule": _("设置周期"),
        "manager": _("指定负责人"),
        "wbs": _("完善结构"),
        "boq": _("导入清单"),
    }

    def map_best(risk):
        target = (risk.get("recommended_action") or {}).get("target") or ""
        cta = cta_map.get(target) or {
            "label": (risk.get("recommended_action") or {}).get("label") or _("去完善"),
            "target": target,
        }
        headline = headline_map.get(target)
        if not headline:
            missing = risk.get("missing")
            headline = _("完善：%s") % missing if missing else _("建议优先补齐一项关键准备")
        return {
            "key": risk.get("rule_key"),
            "headline": headline,
            "because": risk.get("impact") or "",
            "cta_primary": cta,
            "cta_secondary": {"label": _("我先干别的"), "target": ""},
        }

    def map_more(risk):
        target = (risk.get("recommended_action") or {}).get("target") or ""
        label = label_map.get(target) or (risk.get("recommended_action") or {}).get("label") or _("去完善")
        missing = risk.get("missing")
        headline = _("%s 尚未完善") % missing if missing else _("尚有一项准备未完善")
        block_stage = risk.get("will_block_at") or ""
        return {
            "key": risk.get("rule_key"),
            "headline": headline,
            "consequence": risk.get("impact") or "",
            "block_stage": _("在【%s】需要补齐") % block_stage if block_stage else "",
            "cta": {"label": label, "target": target},
        }

    return {
        "variant": "initiation_v0_3",
        "hero": {
            "tone": "ok_to_continue",
            "title": _("项目已创建，可以继续推进。"),
            "subtitle": _("在进入执行前，建议你先完成下面 1 件关键准备。"),
            "hint": _("其余准备可以稍后补齐，不会影响当前操作。"),
        },
        "next_best": {"title": _("建议现在先做这一件："), "item": map_best(best)} if best else None,
        "more": {
            "collapsed_title": _("还有 %s 项准备会在后续阶段影响执行（可稍后处理）") % len(rest),
            "items": [map_more(risk) for risk in rest],
        }
        if rest
        else None,
        "footer": {"text": _("提示：你可以按自己的节奏逐步完善，系统会在合适的时候再提醒你。")},
    }

class ProjectInsightService:
    """
    Generate deterministic 'system voice' insight for project.project.

    Design goals:
    - deterministic first (rules), AI later
    - no cross-model reads that may trigger AccessError (especially accounting)
    - scene-driven output
    """

    SCENE_PROJECT_ENTRY = "project.entry"

    def __init__(self, env):
        self.env = env

    def get_insight(self, project, scene: Optional[str] = None) -> Dict[str, Any]:
        scene = scene or self.SCENE_PROJECT_ENTRY
        if scene == self.SCENE_PROJECT_ENTRY:
            bi = self._insight_project_entry(project)
            return bi.to_dict()

        # fallback: unknown scene
        bi = BusinessInsight(
            object="project.project",
            object_id=project.id,
            scene=scene,
            stage=self._get_stage(project),
            summary=InsightSummary(
                level="info",
                title="系统提示",
                message="当前场景暂无洞察规则。",
                suggestion="请联系系统管理员配置洞察规则。",
                code="INSIGHT_SCENE_NOT_SUPPORTED",
            ),
        )
        return bi.to_dict()

    # -----------------------------
    # Scene rules
    # -----------------------------
    def _insight_project_entry(self, project) -> BusinessInsight:
        stage = self._get_stage(project)

        risks = []
        for rule in PROJECT_ENTRY_RULES:
            if rule["check"](project, self._safe_getattr):
                risks.append(
                    {
                        "rule_key": rule["key"],
                        "priority": rule.get("priority", 999),
                        "level": rule["level"],
                        "missing": rule.get("missing"),
                        "impact": rule["impact"],
                        "will_block_at": rule["will_block_at"],
                        "recommended_action": rule["recommended_action"],
                        "confidence": 1.0,
                    }
                )

        risk_count = len(risks)
        if risk_count == 0:
            summary_text = _("项目已具备基本执行条件，可开始组织任务与结构")
            summary_level = "info"
            title = _("项目准备就绪")
        else:
            summary_text = _("项目已创建，但存在 %s 项可执行性风险（可继续，但建议尽快补齐）") % risk_count
            summary_level = "warning"
            title = _("可执行性风险")

        initiation = {
            "can_continue": True,
            "risk_count": risk_count,
            "risks": risks,
            "summary": summary_text,
        }
        initiation.update(_build_initiation_v0_3(risks, risk_count))
        initiation["ui_model"] = _build_ui_model(initiation)

        return BusinessInsight(
            object="project.project",
            object_id=project.id,
            scene=self.SCENE_PROJECT_ENTRY,
            stage=stage,
            summary=InsightSummary(
                level=summary_level,
                title=title,
                message=summary_text,
                suggestion="",
                code="PROJ_ENTRY_INITIATION_RISKS",
                facts={"risk_count": risk_count},
            ),
            initiation=initiation,
        )

    # -----------------------------
    # Helpers
    # -----------------------------
    def _get_stage(self, project) -> str:
        # Prefer explicit stage name if present
        stage_id = self._safe_getattr(project, "stage_id")
        if stage_id and stage_id is not MISSING:
            try:
                return stage_id.display_name or stage_id.name
            except AccessError:
                return "stage"

        # fallback to state if any
        state = self._safe_getattr(project, "state")
        if state:
            return str(state)

        return "unknown"

    def _safe_getattr(self, record, name):
        try:
            if name not in record._fields:
                return MISSING
            return record[name]
        except (AccessError, AttributeError, KeyError):
            return MISSING
