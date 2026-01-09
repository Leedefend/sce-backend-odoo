# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class InsightSummary:
    level: str               # info | warning | risk
    title: str               # short label
    message: str             # factual judgement
    suggestion: str = ""     # action suggestion
    code: str = ""           # optional rule code
    facts: Optional[Dict[str, Any]] = None  # optional explain/debug
    actions: Optional[List[Dict[str, Any]]] = None  # optional navigation hints

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # prune None to keep payload clean
        return {k: v for k, v in data.items() if v is not None and v != ""}


@dataclass
class BusinessInsight:
    object: str
    object_id: int
    scene: str
    stage: str
    summary: InsightSummary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.object,
            "object_id": self.object_id,
            "scene": self.scene,
            "stage": self.stage,
            "summary": self.summary.to_dict(),
        }
