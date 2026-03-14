# Legacy Path Resolver → Provider Registry 迁移计划 v1

## 1. 背景
现状中 `resolve_*_path` 通过路径候选判断 provider，属于迁移期兼容方案；
目标架构要求“平台机制 + 行业内容”分层，需切换为 registry 驱动。

## 2. 迁移目标
- 目标：按 `scene_key` 解析 provider，不再按文件路径猜测 provider。
- 保持兼容：旧 `resolve_*_path` 暂保留为外壳，内部转 registry-first。

## 3. 分阶段方案

### Phase 1（已完成）
- 新增平台注册核心：`scene_provider_registry.py`
- 新增行业注册入口：`smart_construction_scene/bootstrap/register_scene_providers.py`
- `provider_locator.py` 改为 registry-first + fallback
- 增加守卫：`verify.scene.provider.registry.guard`

### Phase 2（进行中，已完成 consumer 首批切换）
- 逐步替换各 consumer 的 `resolve_*_path` 直接依赖：
  - ✅ workspace home builder
  - ✅ project dashboard service
  - ✅ scene registry engine
- 统一输出 provider diagnostics（来源/版本/命中 key）

本轮新增守卫：
- `verify.scene.provider.registry.consumer.guard`
  - 防止核心 consumer 回退到 `provider_locator.py`。

### Phase 3（计划）
- 删除路径候选列表逻辑
- 删除 legacy provider fallback（按 scene 分批）
- 仅保留 registry 驱动链路

当前进展：
- ✅ `provider_locator.py` 已收口为 deprecated shim（仅转发 registry，不再保留路径候选 fallback）
- ✅ 新增 `verify.scene.provider_locator.deprecated_shim.guard` 防止回退
- ✅ `smart_scene.core` 对外 API 已移除 path-resolver 导出，仅保留 registry 能力出口

## 4. 验收标准
- A. registry 能返回三个核心 scene 的行业 provider
- B. consumer 在不改主协议前提下正常运行
- C. 平台 verify 链包含 registry 守卫
- D. 行业内容新增时不再新增 `resolve_xxx_path` 函数

## 5. 风险与对策
- 风险：注册模块加载失败导致 provider 缺失
  - 对策：保留 fallback，守卫报告具体 scene 缺口
- 风险：多 provider 冲突
  - 对策：统一 `priority` 规则与 provider_key 去重

## 6. 关键原则
- 平台层不固化行业策略，只提供注册机制与约束。
- 行业层不改平台 contract shape，只注册内容 provider。
- fallback 只作为迁移保障，不作为长期机制。
