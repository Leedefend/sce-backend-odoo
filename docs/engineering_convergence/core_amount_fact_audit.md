# T1-A 核心金额计算事实审计

日期：2026-07-14
基线：`origin/main@58335481f39e77fea4eed991734440948feb008d`
范围：合同原始/变更后金额、付款申请、累计支付、结算可付余额。预算、税务和发票只在其作为既有输入时提及，不扩展审计。本文记录代码现状，不定义或修改业务公式。

## 结论

- 主合同 `construction.contract` 的原始含税金额来自合同明细，逐行 `qty_contract * price_contract`，先舍入未税合计和税额，再舍入两者之和。
- 主合同“最终合同价”目前恒等于原始含税金额；`amount_change` 被权威方法固定为 `0.0`。`sc.contract.event.amount_impact`、补充合同和结算调整均未写入该字段。
- 结算单累计“已付”按付款申请的 `submit/approve/approved/done` 状态占额，并非付款台账或付款执行事实；可付余额以未调整的 `amount_total` 为基数。
- 付款申请自身累计已付来自 `payment.ledger.amount`，不看付款申请状态；台账正常只能在申请 `approved` 时创建，付款执行撤销会删除台账。
- 合同累计付款来自 `sc.payment.execution.paid_amount`，只排除 `cancel/cancelled`，因此草稿和已确认但未登记付款的执行单也会计入。
- 上述三个“已付/付款金额”公式对同一业务链的状态口径不一致，已触发停止条件。T1-A 不选择权威公式、不补金额行为测试、不修改业务代码。

## 金额事实地图

### F1 合同原始金额

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | `construction.contract.line.amount_contract`；`construction.contract.line_amount_total`；`amount_untaxed`、`amount_tax`、`amount_total` |
| 权威计算方法 | `ConstructionContractLine._compute_amount_contract`：`qty_contract * price_contract`；`ConstructionContract._compute_line_amount_total`：行金额求和；`_compute_amount_total`：`untaxed = currency.round(line_amount_total)`，百分比且价外税时 `tax = currency.round(untaxed * rate / 100)`，`total = currency.round(untaxed + tax)` |
| 数据来源 | 合同明细的合同数量和合同单价；合同币种；合同税率 |
| 纳入/排除状态 | 不按合同状态过滤；草稿、确认、运行、关闭均使用同一存储计算字段。没有取消状态排除逻辑 |
| 舍入规则 | 使用 `contract.currency_id`，缺失时回退 `company_currency_id` 的 `currency.round`；行乘积本身未显式舍入 |
| 调用/写入路径 | 合同/明细 `create`、`write` 触发依赖重算；预算生成明细只是输入路径，不改变公式 |
| 当前测试 | `tests/test_contract_center.py::TestConstructionContract.test_contract_state_and_amount` 的两行求和和 9% 税断言通过，但该方法随后因审批策略下仍期待直接进入 `confirmed` 而整体失败；`test_submit_approval_does_not_require_contract_details` 覆盖零明细 |
| 缺口 | 零数量/零单价、负值约束、币种小数边界、逐行与合计舍入差异、多币种、跨公司税率/币种隔离未聚焦验证 |

辅助模型 `sc.general.contract.amount_total` 是人工/迁移写入字段，仅有非负 SQL 约束；`change_amount_total` 也是直接写入，`_compute_change_rate` 只计算比例。该模型没有“变更后合同金额”的权威计算字段，不能与主合同公式互换。

### F2 合同变更后金额

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | `construction.contract.amount_change`、`amount_final` |
| 权威计算方法 | `ConstructionContract._compute_final_amount`：`change_amount = 0.0`；`amount_final = amount_total + change_amount` |
| 数据来源 | 当前只有 `amount_total`；方法注释明确“变更模块尚未上线” |
| 纳入/排除状态 | 不查询任何变更状态；所有合同状态相同 |
| 舍入规则 | 不额外舍入，继承已舍入的 `amount_total`，变更恒为零 |
| 调用/写入路径 | 仅依赖 `amount_total` 重算；`sc.contract.event.amount_impact`、`construction.contract.original_contract_id/supplement_contract_ids`、`sc.settlement.adjustment` 没有写入路径 |
| 当前测试 | 合同金额测试间接证明 `amount_final == amount_total`，没有对 `amount_change` 的专门断言；补充合同测试只验证项目、往来方和方向一致性 |
| 缺口 | 合同事件是否应计入、哪些状态应计入、补充合同是否并入、退款/冲销影响、正负变更和舍入均尚无已实现事实，不能在 T1-B 猜测 |

### F3 结算金额及调整后金额

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | `sc.settlement.order.line.amount`、`sc.settlement.order.amount_total`；`adjustment_total`、`amount_after_adjustment` |
| 权威计算方法 | 行金额 `qty * price_unit`；`amount_total = sum(line.amount)`；`adjustment_total = sum(confirmed/legacy_confirmed adjustment.signed_amount)`；`amount_after_adjustment = amount_total + adjustment_total` |
| 数据来源 | 结算行；调整单 `amount`，扣款取负、增加取正 |
| 纳入/排除状态 | 调整仅纳入 `confirmed/legacy_confirmed`，排除 `draft/cancel`；结算行合计不按结算单状态过滤 |
| 舍入规则 | Monetary 字段按币种展示/存储精度；乘法、求和和调整公式未显式调用 `currency.round` |
| 调用/写入路径 | 结算行、调整单 `create/write` 触发依赖重算；调整确认/取消改变状态 |
| 当前测试 | `test_p0_state_closure.py::test_settlement_adjustment_confirm_cancel_business_flow` 覆盖 100 - 10 = 90；`test_user_feedback_business_views.py` 覆盖结算行合计与未付初值 |
| 缺口 | 取消后恢复、多个正负调整、舍入边界、调整后金额与付款占额联动未验证 |

### F4 当前申请/本次支付金额

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | 主申请 `payment.request.amount`；历史多结算明细 `payment.request.line.current_pay_amount`；实际执行 `sc.payment.execution.paid_amount`；付款台账 `payment.ledger.amount` |
| 权威计算方法 | 四者均为直接写入的 Monetary 值；新建执行单默认 `planned_amount` 和 `paid_amount` 为申请 `amount`；申请完成时 `_ensure_payment_ledger` 默认写入申请 `amount` |
| 数据来源 | 用户/迁移输入，或付款申请到执行/台账的默认复制 |
| 纳入/排除状态 | 申请金额是否进入结算累计由 F5 状态口径决定；执行 `paid_amount > 0` 在确认/付款动作校验；台账要求关联申请为 `approved` |
| 舍入规则 | 超额比较使用币种 rounding；金额复制不显式量化。中文大写另用 `Decimal(str(value)).quantize(0.01, ROUND_HALF_UP)`，只影响显示文本 |
| 调用/写入路径 | 申请 `create/write`；`action_create_payment_execution`/`_payment_request_values`；`action_done`、`sc.payment.execution.action_paid` -> `_ensure_payment_ledger` |
| 当前测试 | `test_p0_state_closure.py::test_payment_execution_values_from_payment_request`、`test_payment_execution_paid_closes_payment_request`；`test_p0_ledger_gate.py` 覆盖台账等于申请及禁止超申请 |
| 缺口 | 部分实付语义（当前执行低于申请会阻断自动完成）、多次实付（台账唯一约束）、币种不一致、半分边界、负数/零值的各入口一致性未形成矩阵 |

### F5 结算累计占额与剩余可支付金额

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | `sc.settlement.order.paid_amount/amount_paid`；`remaining_amount/amount_payable/unpaid_amount`；付款申请上的 related 镜像字段 |
| 权威计算方法 | `operating_metrics.settlement_paid_map`：主关联按 `payment.request.amount` 汇总；无主关联的历史多结算路径按 `payment.request.line.current_pay_amount` 汇总。`_compute_paid_amounts`：`remaining = settlement.amount_total - paid`，五个别名同步赋值 |
| 数据来源 | 付款申请及历史付款申请明细，不读取 `payment.ledger` 或 `sc.payment.execution` |
| 纳入状态 | `PAID_STATES = (submit, approve, approved, done)` |
| 排除状态 | `draft`、`cancel` 及所有不在上述元组的状态；退款/冲销没有负金额汇总，执行撤销通过申请退回 `approved`，该申请仍在占额状态内 |
| 舍入规则 | 汇总与减法不显式舍入；超额判断使用 `compute_payment_payable_excluding_self` 返回的公司币种 rounding（不是结算/申请币种），非正 precision 回退 `0.01` |
| 隔离 | 查询以结算单 ID 精确过滤，因此项目间通常不混入；付款申请约束校验项目/合同/往来方。未在聚合 domain 中追加 company；结算单 `company_id` 不是 project related，且 create 不强制同步，存在跨公司锚点缺口 |
| 调用/写入路径 | 结算单 `_compute_paid_amounts`；付款申请 `_check_settlement_remaining_amount`、`_check_not_overpay_settlement`、`_compute_is_overpay_risk`；validator `rule_payment_not_overpay.py` 复用同一聚合 |
| 当前测试 | `test_smoke_validator.py::test_payment_request_paid_payable_consistent` 覆盖一笔 80 后已占额 80/余额 20 和第二笔 30 风险；`test_smoke_3waymatch_flow.py` 有余额冒烟断言 |
| 缺口 | 零值、全额、三笔以上累计、取消释放、撤销后的口径、部分实付、调整后结算金额、币种 rounding、跨项目/跨公司污染均未形成聚焦测试 |

### F6 付款申请自身累计已支付与未支付

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | `payment.request.paid_amount_total`、`unpaid_amount`、`is_fully_paid` |
| 权威计算方法 | `_compute_payment_totals` 对该申请全部 `payment.ledger.amount` 求和；`unpaid = request.amount - paid_total`；币种 rounding 下 `unpaid <= 0` 即结清，不截断负余额 |
| 数据来源 | `payment.ledger`；每申请有唯一台账 SQL 约束 |
| 纳入/排除状态 | 台账无状态字段，全部纳入；不按付款申请状态过滤。正常创建要求申请 `approved`；撤销已付执行会删除台账并把 `done` 申请退回 `approved` |
| 舍入规则 | 求和/减法不显式舍入；结清判断使用申请币种 rounding，缺失回退 `0.01` |
| 调用/写入路径 | 申请完成或付款执行登记付款生成台账；付款执行取消 `_reverse_paid_execution` 删除台账 |
| 当前测试 | `test_p0_ledger_gate.py` 覆盖创建、唯一性、金额等于申请和超额阻断；`test_p0_state_closure.py::test_payment_execution_paid_closes_payment_request` 覆盖执行到台账 |
| 缺口 | 计算字段的零/部分/全额/负余额直接断言、舍入边界、撤销后累计回零、跨项目/公司隔离未覆盖 |

### F7 合同累计实付与未付

| 项目 | 代码事实 |
| --- | --- |
| 模型和字段 | `construction.contract.paid_amount`、`unpaid_amount` |
| 权威计算方法 | `_compute_execution_amounts` -> `_sum_amount_by_contract("sc.payment.execution", "paid_amount", excluded_states=("cancel", "cancelled"))`；`unpaid = max(amount_final - paid, 0)` |
| 数据来源 | 与合同直接关联的付款执行单，不读取付款申请或付款台账 |
| 纳入状态 | 除取消外所有状态，包括 `draft`、`confirmed`、`paid`、`legacy_confirmed` |
| 排除状态 | `cancel/cancelled`；执行撤销将单据置 `cancel`，随后应从累计移除 |
| 舍入规则 | 聚合、减法不显式舍入；未付截断为零，因而超付金额不会体现在 `unpaid_amount` |
| 隔离 | domain 只按 `contract_id`；合同 ID 天然隔离项目。执行模型公司 related 到项目，但聚合不显式核验执行项目/公司与合同一致；业务动作会校验执行与申请，却不直接校验执行与合同项目 |
| 调用/写入路径 | 付款执行 `create/write/state` 触发合同非存储计算；`action_paid` 登记付款；`action_cancel/_reverse_paid_execution` 取消/撤销 |
| 当前测试 | `test_user_feedback_business_views.py::test_contract_execution_amounts_come_from_business_documents` 意图覆盖默认草稿执行计入合同已付，但当前先在未登记发票仍期待计入的断言失败，无法到达付款断言；状态闭环测试覆盖执行 `paid` 和撤销路径，但未同时断言合同累计 |
| 缺口 | 草稿是否应计入的语义测试、confirmed/paid/legacy 状态矩阵、累计多笔、取消/撤销回退、超付、舍入和跨公司错误锚点未覆盖 |

## 公式冲突与最小复现

### C1 “累计已付”存在三套不一致状态公式

具体差异：

1. `models/support/operating_metrics.py::PAID_STATES/settlement_paid_map` 把已提交但未实际付款的申请金额计为结算单 `paid_amount/amount_paid`。
2. `models/core/payment_request.py::_compute_payment_totals` 只有付款台账才计为申请 `paid_amount_total`。
3. `models/support/contract_center.py::_compute_execution_amounts` 把除取消外的付款执行（包括草稿）计为合同 `paid_amount`。

最小复现（同一项目、合同、100 元结算单）：

1. 新建 80 元付款申请并提交，不生成台账或付款执行：结算单已付为 80，申请自身已付为 0，合同已付为 0。
2. 再新建一张关联同合同的 50 元草稿付款执行：合同已付变为 50，但申请自身仍为 0；结算单仍按申请占额为 80。
3. 将执行单取消：合同已付回到 0；已提交申请未取消时结算单仍为 80。

这不是浮点误差，而是数据源和状态集合不同。现有测试分别固化了结算“提交/审批即已付”和合同“草稿执行即已付”，但没有测试明确说明二者应代表不同业务事实。

### C2 调整后结算金额未进入可付余额公式

`settlement_adjustment.py::_compute_adjustment_totals` 产出 `amount_after_adjustment`，但 `settlement_order.py::_compute_paid_amounts`、`operating_metrics.compute_payment_payable_excluding_self` 和 validator 均以原始 `amount_total` 为基数。

最小复现：100 元结算单确认 10 元扣款且无付款申请时，`amount_after_adjustment = 90`，但 `amount_payable/remaining_amount = 100`。两字段是否本应代表同一可付款基数没有权威说明，因此停止并交由业务所有者裁决。

## 现有覆盖矩阵

| 场景 | 合同原始/最终 | 结算占额/余额 | 申请台账累计 | 合同执行累计 | 结论 |
| --- | --- | --- | --- | --- | --- |
| 零值 | 零明细间接覆盖 | 仅初始未付展示 | 未直接断言 | 未直接断言 | 缺 |
| 部分支付 | 无 | 80/100 覆盖，但实际是申请占额 | 创建台账等于整笔申请 | 单笔 50 覆盖但为草稿 | 口径割裂 |
| 全额支付 | 无 | 无聚焦断言 | 业务完成路径间接覆盖 | 无累计断言 | 缺 |
| 超额申请 | 无 | 100 后申请 30 的风险/validator 覆盖；另有软提示继续审批测试 | 台账超申请阻断 | 未覆盖合同超付展示 | 部分覆盖 |
| 已取消/已冲销 | 无 | 未断言取消申请释放占额 | 执行撤销删台账有路径，累计未断言 | 取消过滤未断言 | 缺 |
| 多次累计 | 两合同明细求和 | 两笔申请场景 | 唯一台账禁止多条 | 多执行未覆盖 | 缺 |
| 舍入边界 | 普通 9% 税 | 无 | 无 | 无 | 缺 |
| 跨项目/公司 | 合同项目锚点有约束测试 | unrelated 项目 validator 冒烟；无 company 错配 | record rule 侧重可见性 | 无金额污染断言 | 缺 |

## 建议的 T1-B 最小测试范围

公式冲突裁决前，只建议准备用例，不实施：

1. 合同金额：空明细、两行普通值、币种半舍入边界；断言 `line_amount_total/amount_untaxed/amount_tax/amount_total/amount_final`。
2. 对“结算累计”先由业务选择名称和数据源：若是申请占额，测试 `submit/approve/approved/done` 纳入、`draft/cancel` 排除；若是实际已付，改以台账或已付款执行为事实后再写测试。
3. 零、部分、全额、三次累计和超额各一例；当前申请必须排除自身后再比较。
4. 申请取消释放；已付执行撤销删除台账并回退累计；不得用负数模拟退款，除非先定义正式退款/冲销模型。
5. 以币种 rounding 构造“差半个最小单位”的边界，分别验证等额、低一单位和高一单位。
6. 两项目同金额同往来方、两个公司各一项目；断言只聚合目标合同/结算单，并新增结算单公司必须与项目公司的明确约束测试（若业务裁决要求）。
7. 对调整后可付基数先裁决使用 `amount_total` 还是 `amount_after_adjustment`；裁决前不新增会固化任一公式的行为测试。

## T1-B 前置裁决

- 将结算字段改名/定义为“已申请占额”，还是改为真实“已支付”？
- 合同 `paid_amount` 应纳入哪些付款执行状态？草稿是否只是当前被测试固化的历史行为？
- 结算扣款/增加是否改变付款上限？若改变，以哪个调整状态生效？
- 额度比较的 rounding 应使用申请公司币种、申请币种还是结算币种？多币种是否允许？
- `sc.general.contract` 与 `construction.contract` 哪一个是本域合同金额权威载体，或二者明确服务不同业务面？

## 本次定向验证注记

在独立测试库组合运行 6 个现有金额相关方法，4 个通过，2 个失败：

- 通过：结算 80/20 占额一致性、付款台账等于申请、付款执行生成台账并完成申请、结算扣款 100 - 10 = 90。
- 失败：`TestConstructionContract.test_contract_state_and_amount` 的金额断言均已通过，随后状态期望失败（实际 `draft`，期望 `confirmed`）；`TestUserFeedbackBusinessViews.test_contract_execution_amounts_come_from_business_documents` 在发票累计断言先失败（实际 `0`，期望 `120`），未运行到付款累计断言。

两项均为现有测试与当前状态/过滤公式不一致，不由本批文档改动造成；按只读原则未修复。
