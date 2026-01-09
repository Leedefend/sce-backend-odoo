# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional

from odoo.exceptions import AccessError

from .dto import BusinessInsight, InsightSummary


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

        missing = []
        if not self._safe_getattr(project, "partner_id"):
            missing.append("客户")

        # Odoo project.project default manager field: user_id
        manager = self._safe_getattr(project, "user_id") or self._safe_getattr(project, "project_manager_id")
        if not manager:
            missing.append("项目经理")

        if missing:
            return BusinessInsight(
                object="project.project",
                object_id=project.id,
                scene=self.SCENE_PROJECT_ENTRY,
                stage=stage,
                summary=InsightSummary(
                    level="info",
                    title="项目已立项",
                    message=f"项目基础信息尚未完善（缺少：{'、'.join(missing)}）。",
                    suggestion="建议先完善基础信息，以便后续开展投标、合同、施工与结算管理。",
                    code="PROJ_ENTRY_MISSING_BASE",
                    facts={"missing": missing},
                    actions=[
                        {"type": "tab", "name": "项目概览"},
                        {"type": "field", "name": "partner_id"},
                        {"type": "field", "name": "user_id"},
                    ],
                ),
            )

        # 这里先不去读合同/施工结构等可能牵扯权限的模型，保守给“下一步建议”
        return BusinessInsight(
            object="project.project",
            object_id=project.id,
            scene=self.SCENE_PROJECT_ENTRY,
            stage=stage,
            summary=InsightSummary(
                level="info",
                title="准备就绪",
                message="项目基础信息已完善。",
                suggestion="建议进入投标管理或合同管理，并尽快建立施工结构，以便系统开始评估进度与资金风险。",
                code="PROJ_ENTRY_READY",
                facts={"partner_id": bool(project.partner_id), "manager": bool(manager)},
                actions=[
                    {"type": "tab", "name": "投标管理"},
                    {"type": "tab", "name": "合同"},
                    {"type": "tab", "name": "施工信息"},
                ],
            ),
        )

    # -----------------------------
    # Helpers
    # -----------------------------
    def _get_stage(self, project) -> str:
        # Prefer explicit stage name if present
        stage_id = self._safe_getattr(project, "stage_id")
        if stage_id:
            return stage_id.display_name or stage_id.name

        # fallback to state if any
        state = self._safe_getattr(project, "state")
        if state:
            return str(state)

        return "unknown"

    def _safe_getattr(self, record, name):
        try:
            return getattr(record, name)
        except (AccessError, AttributeError):
            return False
