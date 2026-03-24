# -*- coding: utf-8 -*-
from __future__ import annotations

from .scene_snapshot_service import SceneSnapshotService


class SceneReplicationService:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = SceneSnapshotService(env)

    def clone(self, **kwargs):
        return self.snapshot_service.clone_snapshot(**kwargs)
