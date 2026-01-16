# Dev Environment (DevContainer + Odoo Runtime)

## 目标

将当前已验证可用的 DevContainer + Odoo Runtime 正确配置方式，固化为团队可复制的开发环境标准，确保：

- 新人 30 分钟内跑起来
- 不再出现 conf 漂移 / socket 误连 / default@default 等典型 Odoo Docker 误用问题
- Dev 与 Runtime 职责边界清晰

## 一、开发环境整体架构

开发环境包含多个容器，各自职责如下（文字逻辑表）：

- `sc-dev`
  - VS Code DevContainer
  - 用于：git / 编辑 / 调试 / 执行 make
  - 不跑 Odoo 服务
- `sc-odoo`
  - 真正的 Odoo Runtime
  - 由 entrypoint 渲染 conf 并启动
  - 不作为开发环境使用（不编辑代码、不执行 git）
- `sc-db / sc-redis / sc-nginx`
  - 基础设施

验收要点：读完这一节，新人知道自己在哪个容器干活。

## 二、DevContainer 使用方式

按以下顺序操作：

1. 克隆仓库
2. VS Code 打开目录
3. `Reopen in Container`
4. 容器名应为 `sc-dev`
5. 进入后验证：

   ```bash
   git status
   docker ps
   ```

如果上述任一命令失败，请停止后续操作，先排查 DevContainer 是否连接到了正确的服务。

重要提示（请牢记）：

> ❗ 不要在 sc-odoo 容器内写代码  
> ❗ 所有开发行为只发生在 sc-dev

验收要点：新人照着复制，不会进错容器。

## 三、Odoo 配置渲染与启动机制（关键）

这一节是核心链路，必须明确唯一事实源：

1. 模板文件

   ```
   /etc/odoo/odoo.conf.template
   ```
2. 渲染工具

   ```
   scripts/render_odoo_conf.py
   ```
3. 输出路径（唯一事实源）

   ```
   /var/lib/odoo/odoo.conf
   ```
4. 入口脚本

   ```
   scripts/odoo-entrypoint.sh
   ```

两个关键环境变量：

```env
ODOO_CONF_OUT=/var/lib/odoo/odoo.conf
ODOO_DB=${DB_NAME}
```

禁止事项（非常重要）：

> 🚫 禁止直接使用 `/etc/odoo/odoo.conf` 启动  
> 🚫 禁止 docker exec 不带 `-c` 的 odoo 命令

因果关系声明（重要）：

- 所有 Odoo 运行时行为 ← 由 `/var/lib/odoo/odoo.conf` 决定
- `/var/lib/odoo/odoo.conf` ← 仅由 entrypoint 渲染生成
- entrypoint ← 仅从环境变量与模板推导

任何绕过该链路的行为，都会导致运行结果不可预测。

验收要点：任何人看完都知道 Odoo 永远只认 `/var/lib/odoo/odoo.conf`。

## 四、常用开发与维护命令

```bash
# 查看当前使用的配置
docker compose exec -T odoo grep dbfilter /var/lib/odoo/odoo.conf

# 升级模块（正确方式）
docker compose exec -T odoo \
  odoo -c /var/lib/odoo/odoo.conf -d ${DB_NAME} -u smart_construction_core --stop-after-init

# 重启 Odoo
docker compose restart odoo

# 看日志
docker logs -f sc-odoo
```

如果你看到 `default@default`，说明你用错了配置。

常见错误示例（不要这样做）：

```bash
docker compose exec -T odoo odoo -d ${DB_NAME} -u smart_construction_core
```

## 五、多环境运行（dev/test/prod）

建议使用独立的 env 文件与项目名，避免端口和数据冲突：

```bash
# dev
ENV=dev make up

# test
ENV=test make up

# prod
ENV=prod make up
```

也可以直接指定文件：

```bash
ENV_FILE=.env.dev make up
```

原因：该命令未指定 `-c`，会回退到默认配置路径。

验收要点：这页能当值班手册用。

## 五、常见问题与排查思路

- 现象：`psycopg2 socket /var/run/postgresql`  
  根因：没用正确 conf  
  正解：使用 `/var/lib/odoo/odoo.conf` 启动，并确认 entrypoint 渲染链路生效
- 现象：DevContainer 里没有 git / sudo  
  根因：连错服务  
  正解：确认容器名为 `sc-dev`，并通过 VS Code Reopen in Container 进入
- 现象：重启后配置被覆盖  
  根因：绕过 entrypoint  
  正解：只通过 `scripts/odoo-entrypoint.sh` 生成和启动，避免手动改 `/etc/odoo/odoo.conf`

验收要点：半年后自己看了都不骂过去的自己。

## 六、环境验收清单（Checklist）

- [ ] sc-dev 中可正常 `git status`
- [ ] `docker ps` 显示 `sc-dev` 与 `sc-odoo`
- [ ] sc-odoo 中存在 `/var/lib/odoo/odoo.conf`
- [ ] Odoo 日志显示 `database: odoo@db:5432`
- [ ] `odoo -c /var/lib/odoo/odoo.conf` 可正常启动
- [ ] `default@default` 不存在
- [ ] `psycopg2 socket /var/run/postgresql` 不再出现
- [ ] 重启后配置仍来自 entrypoint 渲染结果
- [ ] 任意成员按本文档从零启动，30 分钟内完成上述所有检查项

## Makefile Guarantee

所有 Makefile 中调用 Odoo 的 target 必须经由 `$(ODOO_EXEC)`，任何直接调用 `odoo` 的行为一律视为缺陷。

## 架构师真心话

你今天做的不是写文档，而是把昂贵的踩坑经验转化成可规模化复用的工程资产。这一步，是团队从能跑到可复制的分水岭。

## 附录 A：15 分钟快速启动（TL;DR）

1. VS Code 打开仓库 → Reopen in Container
   - 确认容器名为 `sc-dev`
2. 不在 sc-odoo 写代码，只用于运行时
3. Odoo 唯一配置文件：
   `/var/lib/odoo/odoo.conf`
4. 正确升级模块：
   ```bash
   docker compose exec -T odoo \
     odoo -c /var/lib/odoo/odoo.conf -d ${DB_NAME} -u smart_construction_core --stop-after-init
   ```
5. 如果看到 `default@default` 或 socket 错误：
   → 回到正文第三、五章排查
