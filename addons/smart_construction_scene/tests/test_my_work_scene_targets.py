# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


SCENE_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


target = _load_module(
    "smart_construction_scene.services.my_work_scene_targets",
    SCENE_DIR / "services" / "my_work_scene_targets.py",
)


class TestMyWorkSceneTargets(unittest.TestCase):
    def test_project_task_records_resolve_to_task_center(self):
        self.assertEqual(
            target.resolve_my_work_scene_key(model_name="project.task"),
            "task.center",
        )
        self.assertEqual(
            target.resolve_my_work_scene_key(source_key="project.task"),
            "task.center",
        )

    def test_project_project_records_resolve_to_projects_detail(self):
        self.assertEqual(
            target.resolve_my_work_scene_key(model_name="project.project"),
            "projects.detail",
        )
        self.assertEqual(
            target.resolve_my_work_scene_key(source_key="project.project"),
            "projects.detail",
        )

    def test_build_my_work_target_keeps_record_context_for_projects_detail(self):
        payload = target.build_my_work_target(
            model_name="project.project",
            record_id=42,
            action_id=502,
            menu_id=202,
        )

        self.assertEqual(payload.get("kind"), "record")
        self.assertEqual(payload.get("scene_key"), "projects.detail")
        self.assertEqual(payload.get("model"), "project.project")
        self.assertEqual(payload.get("record_id"), 42)
        self.assertEqual(payload.get("action_id"), 502)
        self.assertEqual(payload.get("menu_id"), 202)

    def test_build_my_work_target_keeps_record_context_for_task_center(self):
        payload = target.build_my_work_target(
            model_name="project.task",
            record_id=88,
            action_id=601,
            menu_id=0,
        )

        self.assertEqual(payload.get("kind"), "record")
        self.assertEqual(payload.get("scene_key"), "task.center")
        self.assertEqual(payload.get("model"), "project.task")
        self.assertEqual(payload.get("record_id"), 88)
        self.assertEqual(payload.get("action_id"), 601)


if __name__ == "__main__":
    unittest.main()
