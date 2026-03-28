# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def build_metric_sets(
    *,
    ready_count: int,
    locked_count: int,
    preview_count: int,
    scene_count: int,
    today_action_count: int,
    risk_action_count: int,
    metric_level_resolver: Callable[[int, int, int], str],
    tone_from_level_resolver: Callable[[str], str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    business_metrics = [
        {
            "key": "biz.today_actions",
            "label": "今日待处理事项",
            "value": str(today_action_count),
            "level": metric_level_resolver(today_action_count, 3, 6),
            "tone": tone_from_level_resolver(metric_level_resolver(today_action_count, 3, 6)),
            "progress": "pending" if today_action_count > 0 else "completed",
            "delta": "行动优先",
            "hint": "基于任务、待办、关键事项等动作聚合。",
        },
        {
            "key": "biz.risk_actions",
            "label": "高优先关键事项",
            "value": str(risk_action_count),
            "level": metric_level_resolver(risk_action_count, 1, 3),
            "tone": tone_from_level_resolver(metric_level_resolver(risk_action_count, 1, 3)),
            "progress": "blocked" if risk_action_count > 0 else "running",
            "delta": "事项跟进",
            "hint": "需要优先处理的关键提醒与异常事项。",
        },
        {
            "key": "biz.project_scope",
            "label": "可用业务场景数",
            "value": str(scene_count),
            "level": metric_level_resolver(scene_count, 3, 12),
            "tone": tone_from_level_resolver(metric_level_resolver(scene_count, 3, 12)),
            "progress": "running",
            "delta": "业务覆盖",
            "hint": "当前账号可直接进入的场景覆盖范围。",
        },
        {
            "key": "biz.execution_pressure",
            "label": "执行压力指数",
            "value": str(min(100, max(0, (today_action_count * 10) + (risk_action_count * 20)))),
            "level": metric_level_resolver((today_action_count * 10) + (risk_action_count * 20), 30, 70),
            "tone": tone_from_level_resolver(metric_level_resolver((today_action_count * 10) + (risk_action_count * 20), 30, 70)),
            "progress": "running",
            "delta": "综合评估",
            "hint": "根据今日行动量与高优先事项计算的运行负载指标。",
        },
    ]
    platform_metrics = [
        {"key": "platform.ready_caps", "label": "可用能力", "value": str(ready_count)},
        {"key": "platform.locked_caps", "label": "受限能力", "value": str(locked_count)},
        {"key": "platform.preview_caps", "label": "预览能力", "value": str(preview_count)},
        {"key": "platform.scene_count", "label": "场景配置数", "value": str(scene_count)},
    ]
    return business_metrics, platform_metrics
