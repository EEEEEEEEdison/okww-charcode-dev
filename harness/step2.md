# 步骤 2：实现、验证与交付

整队生成的前提是 [G2](timeline.md#3-关口-g2) 通过。
局部修改的输入见 [代码实现 Skill](../skills/okww-implementation/SKILL.md)。
代码遵守 [rules.md](../rules.md)。
骨架见 [workshop.md](../references/workshop.md)，日志见 [logging.md](../references/logging.md)。
API 查 [basechar-api.md](../references/basechar-api.md) 和 [task-api.md](../references/task-api.md)。

## 1 目标代码形式

- 工坊循环轴使用 3 个直接继承 `BaseChar` 的类。
- f/s 节点按 rules.md 第 6 组组织。
- 共用协议和日志 helper 按 workshop.md 保持一致。
- 优先调用框架函数，新增实现按 rules.md 的决策阶梯判断。
- 不引入 DSL（自定义领域语言）。

## 2 节点映射

一个节点对应薄包装 `perform_<f或s><序号>()` 和动作体 `_action_<名字>(tag, nxt)`。
动作完全相同时，可共用动作体。
薄包装最后一行固定为：

```python
self._force_switch_to(self._find_teammate('<下一个类名>'), '<下个节点模式>')
```

分发器、`_entry_mode`、`_startup_done`、`reset_state` 按骨架实现。
节点注释标出轴原文、视频区间和时序节点编号。
动作体落实前置、触发、完成、取消和依赖判据。
不得只按记号顺序拼接函数。

## 3 记号与判据到代码

| 动作 | 实现选择 |
|---|---|
| E 单击 | 优先 `click_resonance(time_out=<正数>)`，核对返回语义 |
| E/Q 长按 | 用配置键和已确认的按住或松开判据；按需确认并 `record_*_use()` |
| 多段及强化 E/R | 按语义卡确认目标段；不进冷却的段不得循环按到出现冷却 |
| R | 优先 `click_liberation(...)`，区分发送、生效、演出结束 |
| Q | 按 rules.md 1-1 选择 `click_echo(...)` 或 `send_echo_key()` |
| A 段 | 先确认作用；固定时长用 `continues_normal_attack(duration)`，条件等待优先复用框架函数 |
| Z | 消耗回路用 `heavy_click_forte(check_fun)`；已确认固定时长用 `heavy_attack(duration)` |
| 闪 | `self.task.send_key(self.task.key_config.get('Dodge Key'))` |
| 跳 | `self.task.jump()` |
| ↓ 或节点出口 | 按 `node.exit` 的类型、完成判据和超时处理切人 |

- `ready` 触发：满足可用判据即执行，不加保险等待。
- `state` 触发：用 `wait_until` 等明确的状态变化。
- `delay` 触发：使用模型规定的锚点和时钟，不从日志 `ok` 擅自改算。
- `immediate` 触发：前置条件满足后直接执行。
- `timing: condition` 不得改成固定时长。
- 按住操作用 try/finally，finally 中松开，遵守 rules.md 5-4。

**切人**：

- 原轴要求变奏时，按已确认的协奏和结束判据离场。
- 只有 `allow_fill: true` 才能额外补协奏。
- 原轴要求普通切人时，完成最后动作即切，不加补资源动作。
- `↓` 只表示原轴的延奏意图，不能独立决定补满策略。
- 特殊机制和目标切人冷却按模型与 rules.md 3-7、3-12 处理。
- 证据不足时退回建模，不得默认补满。

## 4 时限与未就绪

参考耗时、按住时长和超时保护分别确定。
不得统一使用“视频时长 × 1.5、至少 1 秒”。
每个等待必须记录条件、正数时限、依据和超时处理。
时限宜参考已核实的动作范围、框架语义和实测波动。
条件成立后即继续，不得等满保护时限。
游戏持续时间与真实循环上限按 rules.md 2-5 区分。
超过 1 秒的等待，加 `pre_action=self.check_combat`。

技能未就绪时，先核对 `precondition` 和 `trigger`。
只有模型允许补资源时，才能一边普攻一边等。
超时后按 `wait.on_timeout` 处理，并记录 fallback。
跳过、重试和离场不得自动采用统一策略。
关键处理没有依据时，退回 G2。
战斗结束、角色死亡异常不捕获，交给框架处理。

## 5 日志与实现交接

按 logging.md、骨架和 [日志 Skill](../skills/okww-logging/SKILL.md) 记录：

- 节点 `enter`、`exit`；
- 技能 `cast X: ok|fail`，没有确认信号的发键写 `send X`；
- 分支 `decide`；
- 兜底 `fallback`；
- 上限 ≥2s 的条件等待前打 `wait`。

核对日志与实际事件的关系。
不得用 `ok` 直接替代所有生效时刻。
整队骨架日志处理遵守 rules.md 6-6、6-7。
局部修改保留已有诊断字段，按动作阶段适配。
实现选择、借用来源及待测项写入 `notes.md`。
参考耗时保留在 timeline，不复制成无来源常量。

## 6 verify_chain

复制 [verify_chain.py](../templates/verify_chain.py) 到版本目录。
按模型填 `FILES`、`EXPECTED`、`STARTUP_END`。
运行并确认通过。
在临时副本中改错一条边，确认报错。
最终候选必须恢复正确边并再次通过。

检查只覆盖静态交场链。
这项检查不能证明协奏、技能效果或耗时符合。

## 7 自检清单

适用项必须通过后才能交付。
局部任务不适用的项目，记录原因。

- [ ] 只编译本次角色文件：`python -I -B -m py_compile <文件>`。
- [ ] 交场链正常通过，变异时确实失败，最终候选再次通过。
- [ ] `self.X()`、`self.task.X()` 均能在源码或本文件定义中定位。
- [ ] 每个动作的触发、完成和切人处理与模型一致。
- [ ] 普通切人没有被补协奏或保险等待改成变奏。
- [ ] 没有把参考总时长直接作为等待时长。
- [ ] 依赖、延迟锚点和时钟与模型一致。
- [ ] 无写死按键，无 `time.sleep`。
- [ ] `wait_until` 与 `click_resonance` 有正数时限。
- [ ] 手写循环有真实时间上限，每轮调用 `sleep` 或 `next_frame`。
- [ ] 不吞战斗异常；日志 helper 按规则处理自身异常。
- [ ] 3 个文件的共用协议与日志 helper 逐字一致。
- [ ] 节点日志齐全；fallback 用 warning；日志不额外读状态。
- [ ] `scripts/check_logs.py` 报 0 条问题，或剩下的问题已在 README 写明原因。
- [ ] 待测项均有预期、验证办法和失败处理。

## 8 打包交付

1. 从已有确认读取 `name`、`description`、`author`、`version`。缺少时集中提问。
2. 在新的 `<队名>/harness-v<N>/` 放置 3 个角色文件、`verify_chain.py` 和 `team.json`。
3. 写 README，列出交场链、轴与视频节点对应、参考耗时入口、试验假设和未实测项。
4. 写 `notes.md`，记录来源、实现选择及实际检查结果。
5. 用配置的 Python 执行 `scripts/pack_team.py <版本目录> <ok-ww运行目录>`。
6. 核对 zip 与声明的打包源逐字节一致。
7. 交付 zip 路径、检查结果及待实测项，进入 [iterate.md](iterate.md)。

`team.json.team` 用逗号分隔的英文显示名，按不区分大小写的字母序排列。
显示名以运行目录 `CustomCharLoader.py` 的 `CHARACTER_DISPLAY_NAMES` 为准。

项目要求清洗时，先生成清洗后的 3 个 `.py`。
使用 `--src <清洗结果目录>`，并把该目录记为实际打包源。
字节一致检查针对实际打包源；清洗前后的行为另行核对。

zip 平铺 `team.json` 和 3 个角色文件。
文件名为 `<类名>_<类名>_<类名>_<author>_<version>.zip`。
`inspect_team_archive` 输出 `OK` 才通过。
`REFUSE` 表示同名包已存在，必须使用新版本号。
`FAIL` 时按报错修正，再运行同一打包脚本。
不得另写打包脚本。

交付 README 的出处引用原视频、文字轴和本案 timeline。
迭代证据的路径与分析记录写入 notes，见 iterate.md §4。
