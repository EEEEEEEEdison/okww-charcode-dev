# MCP 自动实测指引

本指引让 Agent 通过 ok-ww MCP 自动完成一局实测：进场、开战、录像、取证和分析。
测试脚本是本仓库 `templates/mcp/` 下的 Task 模板，用 MCP 的 `run_task` 提交。
ok-ww 的 MCP 不需要额外安装脚本。
已实测的场景只有终焉矩阵。其他场景按 §9 补模板。

## 1 前提

| 项 | 要求 |
|---|---|
| ok-ww | 正式版 v3.7.12 及以上，设置里已开启 MCP |
| 启动方式 | 必须经 `ok-ww.exe` 以管理员身份启动 |
| 宿主 | 已配置 ok-ww MCP 连接，能调用 `run_task`、`get_run_status` |
| 游戏 | 分辨率 16:9；矩阵已解锁，目标队伍已有挑战记录 |
| 本机路径 | 工作区 `okwwcharcode.local.md` 里的 `working` 目录和 Python |

非管理员实例在游戏未运行时不能启动游戏。
这时 `run_task` 在 `preparing` 阶段失败，报 `Target device could not be started`。
桌面快捷方式启动的实例没有管理员权限。
遇到该错误时，必须请用户关闭 ok-ww，再右键 `ok-ww.exe` 以管理员身份运行。

连接配置教程不在本指引范围内。

## 2 连接检查与内置技能

1. 调用 `list_skills()`。能返回技能列表，说明 MCP 已连通。
2. 调用 `get_skill(skill_id="develop")`，读 Task 契约与框架用法。技能 ID 以 `list_skills()` 的返回为准。
3. 修改 ok-ww 已注册任务的源码后，按 `reload-tasks` 技能重载。本指引的模板是独立文件，不必重载。

`screenshot()` 报错不表示 MCP 断开。游戏未运行时它也会报错。
连通性必须用 `list_skills()` 判断。

执行器同一时间只运行一个任务。
提交下一个任务前，必须等上一个任务进入 `succeeded`、`failed` 或 `cancelled`。
`stopping` 状态仍占用执行器。

## 3 模板与配置

使用前把 `templates/mcp/` 下的 5 个文件复制到 `<工作区>/<队名>/media/mcp/`，再改 `mcp_test.json`。
`run_task` 必须传该副本的绝对路径。
模板按自身所在目录读取 `mcp_test.json`。

| 模板 | 起点 | 终点 | 产物 | 消耗 |
|---|---|---|---|---|
| `preflight.py` | 登录页、公告、菜单、矩阵区域 | 大世界 | `steps.json`、各步截图 | 无 |
| `team_import.py` | 任意 | 不变 | `import.json`、旧队伍目录备份 | 覆盖已装的队伍代码 |
| `matrix_nav.py` | 大世界、指南、矩阵主页、结算页 | 矩阵编队详情页 | `nav.json`、各步截图 | 无 |
| `matrix_run.py` | 矩阵编队详情页 | 矩阵结算页 | `summary.json`、`steps.json`、`record.mp4`、节点截图 | 每局 1 点结晶单质（“前往”旁的 ⚡1） |

分析脚本是 `scripts/mcp_report.py`，用 ok-ww 的 Python 运行，见 §6。

`mcp_test.json` 字段：

| 字段 | 含义 | 用于 |
|---|---|---|
| `team` | 3 个角色类名，顺序不限 | 全部 |
| `opener` | 开场角色类名；空字符串表示不切人 | `matrix_run.py` |
| `zip` | 待导入工坊 zip 的绝对路径 | `team_import.py` |
| `mode` | `奇点扩张` 或 `稳态协议` | `matrix_nav.py` |
| `slot_label` | 队伍槽位，两位数字，如 `"04"` | `matrix_nav.py`、`matrix_run.py` |
| `save_result` | 是否保存本局成绩，默认 `false` | `matrix_nav.py` |
| `switch_delay` | 按 F 后到按开场角色槽位键的秒数 | `matrix_run.py` |
| `walk_time_out` | 走向回音之钥的上限秒数 | `matrix_run.py` |
| `fight_cap` | 从任务开始算的战斗上限秒数 | `matrix_run.py` |
| `end_out_of_team` | 队伍 HUD 连续消失多少秒判为结算 | `matrix_run.py` |
| `record` | 录像帧率与尺寸 | `matrix_run.py` |

`switch_delay` 0.15 秒来自今弗坎队的实测。其他队伍必须先按录屏核对。

## 4 一局测试流程

每一步都用 `run_task(<副本绝对路径>)` 提交，再等终态。
`get_run_status(run_id)` 和运行目录下的 `status.json` 都能读到状态。
运行目录是返回值里的 `artifact_directory`，位于 `<working>/logs/mcp/<run_id>/`。

1. 首局或游戏状态不明时，运行 `preflight.py`。
2. 待测代码与已装代码不同时，运行 `team_import.py`。
3. 运行 `matrix_nav.py`，停在编队详情页。
4. 运行 `matrix_run.py`。一局约 220 秒，宜后台等待终态。
5. 运行 `python -I -B scripts/mcp_report.py <运行目录> --frames`。
6. 按 §6 判读结果。
7. 下一局从第 2 步开始。`matrix_nav.py` 会从结算页取消保存并回到详情页。

各模板的 `verify_start_state()` 不通过时，任务不会执行任何操作，也不消耗结晶单质。
`matrix_run.py` 失败时，先看 `steps.json` 的最后一个节点，再决定重跑哪一步。

### 4.1 前置：preflight.py

- 游戏未运行时，`run_task` 的准备阶段会先启动游戏。
- 登录、公告、月卡和“开始游戏”由 `AutoLoginTask.wait_login()` 逐帧推进。
- 已登录但停在菜单时，按 ESC 返回，最多 5 次。
- 加载画面只等待，不按 ESC。
- 从矩阵区域 ESC 到底会弹“是否确认返回大世界”，模板点“确认”。

### 4.2 导入：team_import.py

1. 校验 zip 里的队伍与 `team` 一致。
2. 把已装的队伍目录复制到运行目录的 `backup_<队名>/`。
3. 调用 `CustomCharLoader.import_custom_team()` 导入。
4. 按文本读回，核对每个角色文件与 zip 一致，`code_mode` 为 `import`。

队伍目录旁已有 `<队名>.backup` 时，模板停止导入。
原因：该目录说明上次导入中断，加载器导入时会删除它。

`team_import.py` 只能导入本轮生成的版本，或用户指定的 zip。
已装代码含用户未打包的修改时，必须先问用户。

### 4.3 开战：matrix_run.py

1. 点“前往”，等加载完成、队伍 HUD 出现。
2. 清空旧角色对象，调用 `load_chars()` 重新识别，记录 3 个类、源码路径和 sha256。
3. 队伍与 `team` 不符时停止，不开战。
4. 向前走到出现 F 提示，按 F 交互回音之钥。
5. 在场角色不是 `opener` 时，等 `switch_delay` 秒，按开场角色的槽位键。
6. 调用 `wait_combat(target=True)` 进入战斗并锁定目标。
7. 循环调用 `AutoCombatTask.run()`，直到队伍 HUD 消失超过 `end_out_of_team` 秒。
8. 在结算页读队伍得分，不点任何按钮。

MCP 运行期间，ok-ww 的触发任务暂停。
因此第 7 步必须显式调用自动战斗。

`AutoCombatTask` 的“战斗前后切治疗”配置会调用 `switch_healer()`。
开场角色不是治疗时，必须用 `steps.json` 的 `switched` 节点和录像核对实际首位。

## 5 矩阵页面与安全规则

`matrix_nav.py` 每步取新帧，按全屏 OCR 判定页面，最多 20 步，未知页面最多按 2 次 ESC。

| 页面 | 判定文字 | 动作 |
|---|---|---|
| 大世界 | 队伍 HUD 可见 | 按指南键（默认 F2） |
| 指南 | 刚按指南键或刚切分页，左上有标题 | 依次点左侧分页图标，找“周期挑战” |
| 周期挑战 | 左上标题“周期挑战” | 点“终焉矩阵”，再点所选模式下方的“前往” |
| 矩阵主页 | 左上“终焉矩阵”，有“当前累计积分” | 读各队记录，选队，点“重新挑战” |
| 提示 | “提示”“重新挑战并保存” | 点“确认” |
| 编队详情页 | 左上“终焉矩阵”，有“角色编队” | 裁剪 OCR 核对槽位编号后结束 |
| 结算页 | “队伍得分”“战绩详情” | 点“返回” |
| 成绩确认 | “成绩确认”“是否覆盖” | `save_result` 为 false 时点“取消” |

安全规则：

- `matrix_nav.py` 只重测最后一个有记录的队伍。槽位在它之前或没有记录时，任务失败。
- 保存成绩会覆盖本队记录，并清空其后所有队伍的记录。
- 结算页的“当前总积分”只是预览。点“返回”后弹“成绩确认”，点“取消”保留原记录。
- `save_result` 必须保持 `false`，用户要求保存成绩时除外。
- 每次 `matrix_run.py` 点“前往”消耗 1 点结晶单质。运行局数按 [iterate.md §4.1](../guides/iterate.md#41-自主迭代上限) 的上限计算。

OCR 识别要点：

- 模式标题可能把“扩”读成“护”，模板只比较前 2 个字。
- 编队详情页的槽位编号全屏 OCR 读不出。模板裁剪 (0.44, 0.64)–(0.56, 0.76) 后能读出“(04)”。
- 矩阵主页的队伍记录行读作 `+8488`，位于右侧 x > 0.85。行 01 的 y 为 0.27，行距 0.107。
- 截图里的“特征码”属于账号信息。模板写入的文字已过滤，截图不得公开。

## 6 结果判读

`mcp_report.py` 读 `<working>/logs/ok-script.log` 中本次运行时段的行。
该日志有毫秒时间戳，不含控制台噪声。
运行目录里的 `run.log` 每行业务日志后都跟 2 段 `--- Logging error ---` 回溯，是 pythonw 没有控制台导致的，宜不读。

脚本输出 `report/report.md`、`report/events.json`、`report/run.log`，`--frames` 另输出 `report/frames/`。
`report.md` 包括：

- 运行状态、队伍、版本、各角色代码 sha256 前 16 位、队伍得分；
- 每个角色每种技能的 `ok` / `fail` 次数；
- 问题行：`fail`、`fallback`、`interrupt`、warning 及以上级别、脱战；
- 每个问题行的录像秒数与 4 帧拼图；
- 启动轴耗时和各循环轮墙钟耗时。

判读顺序：

1. `status.json` 为 `succeeded` 只说明任务没有报错，不等于战斗通过。
2. `steps.json` 必须依次有 `click_go`、`lobby`、`f_found`、`switched` 或 `f_pressed`、`lock`、`fight1_start`、`fight1_end`、`end`。
3. `summary.json` 的 `team` 必须与 `mcp_test.json` 一致。
4. `summary.json` 的 `code[].sha256_16` 必须等于 `import.json` 中 `new.files` 的 `<类名>.py`。不相等说明新代码没有生效，见 §7。
5. 逐条查看问题行的拼图，区分代码判据错误和游戏状态。
6. 队伍得分只能辅助比较，不能替代动作和耗时检查。
   `summary.json` 的 `result_texts` 含挑战进度，如“第1轮（5/5）”，可比较打到第几轮。

录像是实时的：视频秒数 = 日志时刻 − `summary.json` 的 `recorder.video_start`。
任务长时间不取帧时，录像模板向采集后端补帧；后端忙时用上一帧补齐。
`recorder.gaps_over_0_5s` 列出采集空档；问题行落在空档里时，报告标“旧帧”。
2560×1440 下 1 局录像约 220 MB。录像只存运行目录，不得提交到本仓库。

## 7 代码怎样生效

- `team_import.py` 导入后，加载器清空该队的类缓存。
- `matrix_run.py` 清空旧角色对象后重新识别，下一局即加载新代码，不必重启 ok-ww。
- 加载器按文件修改时间缓存类。模块名末尾的数字是文件的 `mtime_ns`，可用于核对。
- `reload_tasks()` 不刷新角色代码。
- 改了 ok-ww 内置的 `src/char/` 文件时，必须重启 ok-ww。

重启步骤：调用 `exit_process`，等返回的 PID 退出，再请用户以管理员身份启动 `ok-ww.exe`。
重启需要用户操作，Agent 必须停下说明，不得自行用非管理员方式拉起。

shell 读 `working/configs/custom_teams/` 会被拒绝访问。
需要读已装文件时，看 `team_import.py` 的备份目录，或在 Task 里复制到运行目录。

## 8 故障与处理

| 现象 | 原因 | 处理 |
|---|---|---|
| `preparing` 阶段报 `Target device could not be started` | ok-ww 不是管理员实例，游戏未运行 | 请用户以管理员身份重启 ok-ww |
| `verify_start_state` 失败 | 起点页面不对 | 先运行 `matrix_nav.py` 或 `preflight.py` |
| `slot N is before last recorded M` | 目标队伍之后还有记录 | 停止，问用户改测哪一队 |
| `team mismatch` | 编队与配置不符 | 停止，不开战；请用户确认编队 |
| `lock-on failed` | F 交互或进入战斗失败 | 看 `f_found`、`lock` 截图后再重跑 |
| `fight cap reached` | 战斗超过 `fight_cap` | 看录像末段，确认是否卡住 |
| 代码 sha 与导入不符 | 加载失败退回内置类，或缓存未清 | 查 `report/run.log` 的加载错误 |

同一步骤连续失败 2 次时，必须停止并向用户报告，不得换方法反复重试。

## 9 扩展到其他场景

新场景宜照 `matrix_nav.py` 写导航模板：

- 每步取新帧，用标题位置和关键字判定页面；
- 每个页面只做一个动作，步数和 ESC 次数有上限；
- 每步截图，写 `nav.json`；
- 会改记录的弹窗默认选不保存。

新场景的开战和战斗宜复用 `matrix_run.py` 的 `Recorder`、`_mark`、`_code_info` 和战斗循环。
新模板在本机实测通过前，不得写成已验证。

## 10 验证记录

2026-10-28，ok-ww v3.7.12，游戏 2560×1440，今弗坎队 2.0.6.3：

| 项 | 结果 |
|---|---|
| `preflight.py` | 从矩阵编队详情页回到大世界，用时 11 秒 |
| `matrix_nav.py` | 从大世界到编队详情页 7 步；从结算页取消保存回到详情页，原记录 8488 保留 |
| `team_import.py` | 导入同版 zip，读回一致，旧目录已备份 |
| `matrix_run.py` | 连续 3 局都从详情页打到结算页，得分 7941、7467、5073 |
| 代码生效 | 第 3 局 3 个角色的 sha256 与 `import.json` 一致，模块名带导入后的 `mtime_ns` |
| 记录保护 | 3 局都点“取消”，总积分 27209 和队伍 4 的 8488 未变 |
| 录像 | 第 3 局 3062 帧对应 204.1 秒，同时段墙钟 204.3 秒，最大采集空档 1.59 秒 |
| 发现的问题 | 第 3 局第 2–4 轮今汐 E 链连续失败，第 1、2 局没有；同一代码版本 |
