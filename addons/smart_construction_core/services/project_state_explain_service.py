# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectStateExplainService:
    def __init__(self, env):
        self.env = env

    def build(self, project):
        if not project:
            return {
                "stage_label": "未选择项目",
                "stage_explain": "当前没有可用项目，无法进入项目驾驶舱。",
                "status_explain": "请先选择项目或创建项目。",
            }
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        stage_label = str(getattr(getattr(project, "stage_id", None), "display_name", "") or "").strip() or "未设置阶段"
        status = str(getattr(project, "health_state", "") or getattr(project, "state", "") or "").strip()
        stage_explain_map = {
            "draft": "项目已完成创建与立项准备，下一步应进入执行主线。",
            "in_progress": "项目已进入施工执行阶段，需要持续推进任务、成本与付款事实。",
            "closing": "项目处于收口阶段，重点是检查成本、付款与结算前置条件。",
            "warranty": "项目处于收尾或质保阶段，需要继续跟踪尾项和经营事实。",
            "done": "项目主线已完成，当前以结果复核与经营回看为主。",
        }
        return {
            "stage_label": stage_label,
            "stage_explain": stage_explain_map.get(lifecycle_state, "当前项目处于已发布主线中，请按推荐动作继续推进。"),
            "status_explain": status or "整体正常",
        }
