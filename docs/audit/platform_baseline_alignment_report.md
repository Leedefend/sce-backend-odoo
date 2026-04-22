# Platform Baseline Alignment Report

## 问题根因分析

- 冲突对象：
  - `scripts/verify/platform_kernel_baseline_guard.py`
  - `scripts/verify/final_slice_readiness_audit.py`
- 旧问题：
  - `platform_kernel_baseline_guard.py` 原先通过 AST 直接扫描 [scene_registry.py](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/addons/smart_construction_scene/scene_registry.py) 中字面量 `"code"`，实际只数到平台最小 fallback 里的 2 个 scene。
  - 运行时场景来源已迁移到 [scene_registry_content.py](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/addons/smart_construction_scene/profiles/scene_registry_content.py) 的动态内容装载，并由 `load_scene_configs()` 合并平台 fallback、行业内容、DB/imported scenes。
- 结果：
  - baseline guard 看到 `scene_count = 2`
  - readiness audit 不检查 scene count，因此仍返回 READY
  - 两套验证逻辑出现伪冲突

## 两套验证逻辑差异

- `platform_kernel_baseline_guard.py`
  - 旧口径：静态文件 AST 计数
  - 新口径：调用 `scene_registry.load_scene_configs(None)`，按实际动态装载结果计数
- `final_slice_readiness_audit.py`
  - 口径：平台编排文件存在性 + 禁止 token 清理
  - 不负责 scene inventory 基线判断

## 最终统一口径

- 统一选择：`B. 以动态加载结果为基线`
- 理由：
  - 与当前架构一致
  - 与 `scene_registry.py` 的真实运行机制一致
  - 能消除“静态代码已瘦身、运行时内容已外移”导致的伪回归

## 修改点说明

- [platform_kernel_baseline_guard.py](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/scripts/verify/platform_kernel_baseline_guard.py)
  - 函数：`_extract_scene_count`
  - 修改：从 AST 扫描改为动态加载 `load_scene_configs(None)` 后按 `code` 去重计数
- [platform_kernel_baseline.json](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/scripts/verify/baselines/platform_kernel_baseline.json)
  - 修改：将 baseline snapshot 更新为当前统一口径下的观测值
- [Makefile](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/Makefile)
  - 修改：增加 `verify.platform_kernel_baseline_guard` 与 `verify.product.final_slice_readiness_audit` 别名，统一 Week 1 执行命令

## 验证日志

- 已执行：
  - `make verify.platform_kernel_baseline_guard` -> `PASS`
  - `make verify.product.final_slice_readiness_audit` -> `READY_FOR_SLICE`
  - `make verify.architecture.orchestration_platform_guard` -> `PASS`
  - `make verify.architecture.five_layer_workspace_audit` -> `PASS`

## 验收结论

- 标准：
  - baseline guard PASS
  - slice readiness PASS
  - 不再出现 scene count 伪回归
- 结果：
  - 已满足
  - 最终结果见 [p0_alignment_verification.md](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/docs/audit/p0_alignment_verification.md)
