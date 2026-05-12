# System Capability Baseline v1 Batch 20260512

## 1. 本轮变更

- 目标：设立前后端功能迭代后的系统能力基线，作为后续持续迭代的统一参照。
- 完成：
  - 新增 `docs/product/system_capability_baseline_v1.md`。
  - 新增 `scripts/verify/baselines/system_capability_baseline_v1.json`。
  - 新增 `scripts/verify/system_capability_baseline_report.py`。
  - 新增 `make verify.system.capability_baseline.report`。
- 未完成：不提升或降低业务能力基线数字；本批只冻结当前已验收口径。

## 2. 影响范围

- 模块：`docs/product`、`scripts/verify`、`Makefile`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险

- P0：无，本批不改运行时代码。
- P1：如果后续批次新增能力但忘记提升 baseline，会导致治理账滞后。
- P2：当前基线引用部分前序交付改动，合并时需一起审阅工作区已有变更。

## 4. 验证

- 命令：
  - `python3 -m py_compile scripts/verify/system_capability_baseline_report.py`
  - `make verify.system.capability_baseline.report`
  - `git diff --check`
- 结果：
  - `python3 -m py_compile scripts/verify/system_capability_baseline_report.py`：PASS
  - `make verify.system.capability_baseline.report`：PASS
    - `check_count=17`
    - `failed_check_count=0`
    - `module_count=9`
    - `delivery_scope_scene_count=22`
    - `business_required_intent_count=10`
    - `business_required_role_count=4`
  - `git diff --check`：PASS

## 5. 产物

- snapshot：`scripts/verify/baselines/system_capability_baseline_v1.json`
- report：`artifacts/backend/system_capability_baseline_report.json`
- docs：`docs/product/system_capability_baseline_v1.md`

## 6. 回滚

- commit：回退本批次新增文档、baseline JSON、report 脚本和 Makefile target。
- 方法：删除 `verify.system.capability_baseline.report` target 后继续使用既有局部 baseline。

## 7. 下一批次

- 目标：如需继续，按模块或角色提升具体能力基线，并同步对应 guard。
- 前置条件：Owner 确认新增能力属于 baseline 提升，而不是临时试验。
