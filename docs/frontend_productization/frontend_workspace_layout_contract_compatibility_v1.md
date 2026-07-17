# FE-PRO-04WR1 页面布局契约兼容与门禁别名修复

## 结论

FE-PRO-04WR 的视觉工作区契约保持不变。本修复只补齐历史 `layout.width_mode` 的兼容读取，并让旧公开 Make 门禁真实委托新守卫；未修改页面 CSS、页面模板、业务契约事实或数据库。

基线 main 为 `05b6097d05a10aa64c79bca6309858fa9bcfecc5`。修复前 `contractContentLayoutMode()` 只读取 root/page/presentation 的 `content_layout_mode`；旧Make目标的dry-run和实际执行均返回0，但都只输出 `Nothing to be done`。

开发历史库 `sc_demo` 只读扫描1215份 `ui.business.config.contract`：包含旧 `width_mode` 的契约0份、出现0处。该结果只描述当前开发库，不能代表其他历史数据库，也不能作为删除兼容层的依据。

## 兼容优先级

正式解释顺序为：

1. root/page/presentation 中第一个非空 `content_layout_mode`；
2. root/page/presentation 中第一个非空旧 `width_mode`；
3. 通用 page kind；
4. 安全默认 `record-grid`。

新字段即使非法也拥有优先级，但按page kind安全回退，不允许旧字段越级覆盖。旧字段只控制内部 Content Layout：`data → data-grid`、`focused → focused-form`、`fluid → data-grid`；`standard` 沿用page kind，因此detail/edit/create/list分别得到record-grid/form-grid/focused-form/data-grid。任何旧值都不能恢复不同的外框max-width。

## 兼容矩阵

| 新字段 | 旧字段/位置 | page kind | 结果 |
| --- | --- | --- | --- |
| data-grid | focused / root | create | data-grid |
| 空 | data / root | list | data-grid |
| 空 | focused / root | create | focused-form |
| 空 | standard / root | detail | record-grid |
| 空 | standard / root | edit | form-grid |
| 空 | standard / root | create | focused-form |
| 空 | fluid / root | visualization | data-grid |
| invalid | standard / root | edit | form-grid（安全回退） |
| 空 | 空 | unknown | record-grid |
| 空 | data / page | list | data-grid |
| 空 | standard / presentation | edit | form-grid |

自动测试共12项，除上表外还重复覆盖root位置并验证返回值携带新/旧来源标识。

## Make兼容入口

`verify.frontend.page_width_contract.guard` 现在依赖 `verify.frontend.workspace_content_alignment.guard`。新目标依次运行契约矩阵与Python架构守卫；旧目标不复制recipe，只在同一依赖成功后输出兼容别名PASS。因此两者使用同一失败链，不会重复运行同一guard。

修复后 `make -n verify.frontend.page_width_contract.guard` 明确显示Node矩阵、Python守卫和兼容PASS输出。CI与 `verify.frontend.quick.gate` 继续直接使用新目标，旧目标仅作为外部自动化兼容别名。

仓库生产调用统计（不含定义、PHONY、recipe输出和生成清单）：旧目标调用0处；新目标调用2处，分别为旧目标兼容依赖和`verify.frontend.quick.gate`依赖。CI实际使用新目标。文档中有2行说明兼容关系，不把旧目标当作正式API推荐。

## 当前HEAD浏览器证据

代表性矩阵为1920列表、详情、编辑、创建，以及390列表、创建，共6行。1920四页frame均为x=258/right=1898，header与primary均为x=290/right=1866；390两页frame均为x=20/right=370，header与primary均为x=36/right=354。

frame/header/primary alignment spread、document overflow、router child overflow、axe critical/serious、console/pageerror和非预期HTTP均为0。证据位于 `artifacts/frontend-professional/fe-pro-04wr1/final-report.json` 及对应截图目录。

## 合并前验证

定向契约矩阵12项、旧/新Make目标、旧目标dry-run、workspace alignment guard、frontend lint、strict typecheck、production build和`git diff --check`均通过。J02–J13、70/70导航（finance 42、project member 9、PM 14、owner 5）、action 876/menu 606拒绝和required金额探针均为PASS；`make ci.local.quick`在刷新受本次新增测试影响的复杂度生成报告后通过。

## 兼容退出条件

`width_mode` 仅作为升级兼容层保留。删除前必须同时满足：受支持历史数据库已完成迁移；跨环境只读统计连续两个发布周期为0；后端不再生成旧字段；仓库与外部CI不再调用旧Make目标；移除兼容后定向矩阵、J02–J13和Workspace Frame门禁继续通过。
