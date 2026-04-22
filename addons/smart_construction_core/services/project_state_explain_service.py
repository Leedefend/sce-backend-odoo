# -*- coding: utf-8 -*-
from __future__ import annotations


LIFECYCLE_STATE_LABELS = {
    "draft": "筹备中",
    "in_progress": "在建",
    "paused": "暂停",
    "closing": "收口",
    "warranty": "质保",
    "done": "完工",
    "closed": "关闭",
}


def lifecycle_state_label(project_or_state, default="未设置阶段"):
    state = getattr(project_or_state, "lifecycle_state", project_or_state)
    state = str(state or "").strip().lower()
    if not state:
        return default
    return LIFECYCLE_STATE_LABELS.get(state, state)


class ProjectStateExplainService:
    def __init__(self, env):
        self.env = env

    def build(self, project):
        if not project:
            return {
                "execution_stage_label": "未选择项目",
                "stage_label": "未选择项目",
                "execution_stage_explain": "当前没有可用项目，无法进入项目驾驶舱。",
                "stage_explain": "当前没有可用项目，无法进入项目驾驶舱。",
                "project_condition_explain": "请先选择项目或创建项目。",
                "status_explain": "请先选择项目或创建项目。",
            }
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        execution_stage_label = lifecycle_state_label(lifecycle_state)
        project_condition = str(getattr(project, "health_state", "") or getattr(project, "state", "") or "").strip()
        stage_explain_map = {
            "draft": "项目已完成创建与立项准备，下一步应进入执行主线。",
            "in_progress": "项目已进入施工执行阶段，需要持续推进任务、成本与付款事实。",
            "closing": "项目处于收口阶段，重点是检查成本、付款与结算前置条件。",
            "warranty": "项目处于收尾或质保阶段，需要继续跟踪尾项和经营事实。",
            "done": "项目主线已完成，当前以结果复核与经营回看为主。",
        }
        execution_stage_explain = stage_explain_map.get(lifecycle_state, "当前项目处于已发布主线中，请按推荐动作继续推进。")
        project_condition_explain = project_condition or "整体正常"
        return {
            "execution_stage_label": execution_stage_label,
            "stage_label": execution_stage_label,
            "execution_stage_explain": execution_stage_explain,
            "stage_explain": execution_stage_explain,
            "project_condition_explain": project_condition_explain,
            "status_explain": project_condition_explain,
        }
