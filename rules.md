# 代码规则

okww-charcode-dev harness 的代码规则部分：步骤 2 生成代码时依照本文件，直接写或改角色代码时也依照本文件。入口见 [SKILL.md](SKILL.md)。

## 这是什么

教 AI 写 ok-ww 的角色代码（`BaseChar` 子类）：

1. 尽量调用框架现成函数，并在相近函数之间选对（`click_*` vs `send_*_key`、`is_con_full` vs `get_current_con`……）。
2. 没有现成函数时，按项目已有经验自实现（时间推算或画面识别）。
3. 日志统一用英文模板，规定何时打、打什么。
4. 工坊脚本化配队使用统一的循环轴骨架。

日常工作流：用户给游戏日志和录像，AI 定位出招或切人问题后修改代码（见「迭代工作流」）。

## 基线

- 上游 `ok-oldking/ok-wuthering-waves` master `2243d465`（2026-10-05），引用写作 `src/char/BaseChar.py:369`。
- 框架 ok-script `v2.0.8`，引用写作 `ok/task/task.py:508`。
- **0-1 源码为准**：本规则或 references 的条目与源码不一致时，以源码为准，并在当次会话里修正对应条目。

## 两种模式（按文件位置判定）

| 模式 | 判定 | 规则 |
|---|---|---|
| 内置模式 | 改 `src/char/*.py`（包括只部署到本地运行目录的改动） | 造新轮子要谨慎：任何新 helper、状态机、循环，先和用户讨论——说明内置函数为什么不行、影响范围、怎么回滚。改 `BaseChar`/`BaseCombatTask` 本身是单独的讨论项。 |
| 工坊模式 | 工坊配队 zip（`team.json` + 3 个角色 `.py`） | 自由度高，本规则只用来加快开发；交付说明里标出哪些是自实现的部分。 |

提交、测试、部署等开发纪律以项目自己的 AGENTS.md / spec 为准（项目规则优先）。

## 决策阶梯

1. **先找内置函数**：查 [references/basechar-api.md](references/basechar-api.md)（角色侧）和 [references/task-api.md](references/task-api.md)（`self.task.*`）。
2. **内置不够**时（内置模式先讨论），按 **5-1** 的顺序自实现：
   1. 内置 HUD 识别（`*_available`、`current_*`、`in_team`、回路、协奏）；
   2. 自定义区域识别（颜色占比；内置 PR 还可以加模板）；
   3. 时间戳推算。

   写法见 [references/self-impl-patterns.md](references/self-impl-patterns.md)。
3. **日志**按 [references/logging.md](references/logging.md) 写。
4. **工坊脚本化交场链**按 [references/workshop.md](references/workshop.md) 的循环轴骨架写，并用 [templates/verify_chain.py](templates/verify_chain.py) 自检。

## 规则

编号与讨论记录一致，详细依据见各 reference。

### 1 放技能

- **1-1** 放 E、R、声骸默认用 `click_resonance` / `click_liberation` / `click_echo`。只有当它们的等待、超时或返回值判定明确不合适时，才改用 `send_*_key`，并在注释里写明原因。
- **1-2** 技能键一律经 `send_*_key()` 或 `self.get_*_key()` 发送，不写死 `'e'/'q'/'r'`（用户可能改过键位）。长按写成 `self.task.send_key(self.get_resonance_key(), down_time=秒数)`。
- **1-3** 用 `send_*_key` 手动放技能后，如果后续要用 `last_res` / `last_liberation` / `last_echo` 计时，必须调用对应的 `record_*_use()`。记录时机优先放在确认技能生效之后；确认不了才在按键时记录，并在注释里说明。
- **1-4** E 可能一直亮着时（强化 E、多段 E、识别不稳），`click_resonance` 必须传正数 `time_out`。注意它的 `time_out=0` 表示默认 15 秒，和 `click_echo(time_out=0)`（只按一次）意思相反。
- **1-5** 不要直接相信返回值：
  - `click_liberation` 遇到没有动画的大招会返回 False；
  - `click_echo` 循环模式超时一律返回 False，即使已经按了出去。

  要确认技能是否放出，看 CD 是否出现、资源或图标是否变化。
- **1-6** 反复按某技能直到它进入 CD，用 `self.task.wait_until(lambda: not self.resonance_available(), post_action=self.send_resonance_key, time_out=N)`，不手写 while。这是 1-1 认可的例外，不需要另写注释。
- **1-7** 分清看的是什么：
  - `resonance_available()` / `echo_available()` 只看 CD 数字；要确认图标是亮的，再加 `current_resonance() > 0`；
  - `liberation_available()` 同时看图标和 CD；
  - 不在场角色的“可用”是用上次看到的 CD 推算的。
- **1-8** 带 `interval>0` 的 `click` 和 `send_key` 共用同一个节流时间戳，挨得太近的后一次会被静默丢弃，所以必须发出去的键不要传 `interval`。另外，发键和点击都会清空当前帧缓存，紧接着的画面判断会重新截图，截到的可能是动作刚开始时的画面。

### 2 等待与计时

- **2-1** 一律用 `self.sleep()`，不用 `time.sleep()`。要跳过战斗检查时传 `check_combat=False`。
- **2-2** 等条件用 `self.task.wait_until`，并且必须传正数 `time_out`（`0` 表示默认 10 秒）。
- **2-3** 只有可能单帧闪烁的识别才传 `settle_time=0.1~0.2`（条件需要连续成立这么久）；其他等待不传。
- **2-4** `time_out` 超过 1 秒的等待，传 `pre_action=self.check_combat`。不要把 `check_combat` 写进条件函数里，它返回 None。
- **2-5** 游戏内时长（buff、技能持续、冷却）用 `time_elapsed_accounting_for_freeze(anchor)` 计算；循环的时间上限用真实时间 `time.time() - start`。
- **2-6** 按含义选锚点：
  - `last_perform`：本次上场；
  - `last_res` / `last_liberation` / `last_echo`：对应技能；
  - 局部 `start`：本次动作。

  不要新建和已有时间戳重复的变量。
- **2-7** 等入场动作或落地用 `wait_down()`，不要用固定秒数普攻代替。只有要等 E/R 变得可用时才用 `wait_intro()`。
- **2-8** 固定时长普攻用 `continues_normal_attack(duration)`，配合它的 `click_resonance_if_ready_and_return` / `until_con_full` 参数。`duration` 是真实时间，不扣冻结。
- **2-9** 手写的轮询循环必须有真实时间上限，每轮必须调用 `self.sleep()` 或 `self.task.next_frame()`。反例：上游 `normal_attack_until_can_switch` 是忙等。

### 3 切人

- **3-1** `do_perform` 以 `return self.switch_next_char()` 结尾，后面不再接动作。不要假设切人一定发生：没有候选人时它只普攻 0.2 秒就返回，随后 `perform` 会再次执行。
- **3-2** 想决定下一个上场的人，覆写**目标角色**的 `get_switch_priority`，返回 `MUST` / `NO` / `HIGH + 1`，其余情况返回 `super()`。不要写死数字键。
- **3-3** `get_switch_priority` 在角色**不在场**时被调用：每次切人对每个候选人各调一次，`need_fast_perform` 也会调用它。里面只能读时间戳、已存状态和 `*_available()`。不做 HUD 识别、不 sleep、不改状态、不打 info 日志。
- **3-4** 只有队里有人会**不带 intro 也返回 MUST**（例如按时间戳返回 MUST 的覆写）时，才需要检查 `need_fast_perform()`；默认的 `get_switch_priority` 从不返回 MUST，其他情况下它恒为 False。检查点放在可以跳过的动作之前（R、重击、填充普攻），为真就提前切人，exit 行写 `reason=fast_switch`。不要在紧凑循环里调用它（反例：上游 Zhezhi）。
- **3-5** 覆写 `wait_switch()` 时必须自带时间上限（框架那一支没有超时），并且只读时间戳和已存状态。
- **3-6** `switch_other_char()` 只在 `on_combat_end` 里用；战斗中切人一律用 `switch_next_char()`。
- **3-7** `switch_next_char()` 不带参数调用。只有当游戏机制允许不满协奏也能出延奏时（例如今汐）才传 `free_intro=True`。不要用 `post_action`；切人后要做的事放进目标角色的 `do_perform`，根据 `has_intro` 判断。
- **3-8** 状态清理分两处，两处都先调用 `super()`，并且 `__init__` 里的初始值要和 `reset_state` 一致：
  - 每次上场的状态，在覆写的 `switch_out(con_full)` 里清；
  - 每场战斗的状态，在覆写的 `reset_state()` 里清（战斗结束和重新读队伍时都会调用）。

### 4 资源判断

- **4-1** 内置回路判断不准时，有两种做法：
  - 覆写 `is_forte_full()`；
  - 新增函数，命名为“内置函数名 + `_<角色名>_<含义>`”，例如 `is_forte_full_cantarella_bar`。

  注意框架里的调用方仍然调原函数，包括默认 `do_perform`、`heavy_click_forte` 的默认 `check_fun`、`switch_next_char`，所以新函数要显式传进去。
- **4-2** 长按重击直到回路耗尽用 `heavy_click_forte(check_fun)`；固定时长的重击用 `heavy_attack(duration)`。
- **4-3** 判断“协奏满了没有”用 `is_con_full()`。只有需要部分比例时才用 `get_current_con()`。它会写入 `current_con`，而且一旦读到 1 就一直是 1，直到下场。
- **4-4** 资源识别只对**在场角色**有效。不在场的自己和队友，只能用在场时存下的值或时间戳。

### 5 自实现

- **5-1** 没有合适的内置函数时，按以下顺序选：
  1. 内置 HUD 识别；
  2. 自定义区域识别；
  3. 时间戳推算。
- **5-2** 时间推算的状态写成按游戏含义命名的小谓词（如 `still_in_liberation()`），内容是：已确认的时间戳 + 扣冻结的经过时间 + 时长常量。时间戳只在确认之后记录。
- **5-3** 手动发键遵循“发送 → `wait_until` 确认 → 记录”。最多尝试 2 次，同 Rover 的 `for attempt in range(2)`；失败就打日志并返回 False。标准确认信号：

  | 动作 | 确认信号 |
  |---|---|
  | E | `not resonance_available()` |
  | R | `not in_team()[0]` |
  | 回到可操作 | `in_team()[0]` + `settle_time=0.1` |
  | 声骸 | `not echo_available()` |
- **5-4** 手写的按住操作（`mouse_down`、`send_key_down`）放进 try/finally，在 finally 里松开。
- **5-5** 自定义识别自由度高，有两种做法：
  - 颜色占比：`box_of_screen_scaled(...)` + `calculate_color_percentage` + 阈值。比例打 debug 日志，颜色优先复用框架已有的；
  - 模板：只限内置代码 PR，按项目的模板流程提交。

  工坊 zip 无法携带模板，所以工坊只能用颜色占比或已有模板。
- **5-6** 角色代码不捕获异常。`NotInCombatException` / `CharDeadException` 要一路抛给 `AutoCombatTask`。唯一的例外是日志 helper 吞掉它自己的异常。
- **5-7** 从日志或视频量出的时长、阈值，按模式决定写法：
  - 工坊代码随意。可以写成类常量，并配测试式备注（如“视频实测 R 1.8s”）；
  - 内置 PR 代码要正式：用上游风格的简洁注释说明游戏机制或原因，不写测试和实测记录。实测数据放进 PR 描述。
- **5-8** 根据日志和视频迭代：
  1. 在日志里定位节点、ok/fail 和 reason；
  2. 对照视频里的对应时刻；
  3. 确认根因后再改；
  4. 一次只改一个变量；
  5. 原因不明时不加兜底。

### 日志（摘要，全文见 references/logging.md）

- **L-1** 级别：
  - 实机要看的打 `info`；
  - 走兜底分支打 `warning`；
  - 高频细节打 `debug`（正式版不写入日志文件）；
  - 角色代码不用 `error`。
- **L-2** 模板：`[TAG] event[: ok|fail] [reason=code] [key=value ...]`。通用层不带 `[TAG]`；只有工坊循环轴层加 `[F1]`/`[S2]` 这样的节点标签。Logger 会自动加 `类名:` 前缀，所以消息里不写角色名。
- **L-3** 必打的时机：
  - `enter`：带入场方式，同时作为和视频对齐的锚点；
  - `decide`；
  - `cast X: ok|fail`；
  - `fallback`；
  - `exit`：带原因和下一个上场的人；
  - 中断。
- **L-4** 不按帧、不按点击打日志；只在状态翻转时打，或在循环结束时打一条汇总。
- **L-5** 日志里不写耗时，看两行时间戳的差。
- **L-6 / L-7** 字段名和 `reason` 码都用固定的 snake_case 词表，新词先加进词表再用。格式：布尔写 True/False，比例保留 3 位小数，其他浮点保留 2 位。fail 行分不出原因时（又不能额外读状态，L-8），省略 `reason`。
- **L-8** 不为打日志额外读状态，失败路径也一样；需要的值在做判断时就存进变量。两个坑：`get_current_con()` 会写 `current_con`，`has_cd()` 会触发 OCR。
- **L-9 / L-10** 两种模式的写法不同：
  - 内置模式：保留框架日志、不重复打，直接内联写 `self.logger.info(f'...')`；
  - 工坊模式：可以用 `_trace` helper。循环轴角色还要把框架 info 降为 debug，并过滤两行切人日志（见 workshop.md）。

### 6 工坊循环轴（摘要，全文见 references/workshop.md）

- **6-1** 只用于脚本化交场链的工坊队，即每个节点写明下一个上场的人和他要执行的动作体。其他工坊角色用普通的 `do_perform` + `get_switch_priority`。
- **6-2** f 是启动轴（每场只跑一遍），s 是循环轴，每个角色从 1 开始编号。动作体写成 `_action_xx(tag, nxt)`；`perform_fN` / `perform_sN` 薄包装的最后一行固定写成 `self._force_switch_to(self._find_teammate('X'), 'mode')`。
- **6-3** 队里每个类都带同一套协议：`__init__` 字段、`get_switch_priority` 头部拦截、`_find_teammate`，以及带 try/finally 的 `_force_switch_to`。注意 NB-1：处于满协奏锁定期的治疗目标无法被强切。
- **6-4** 分发器的规则：
  - 先读取并清空 `_entry_mode`；
  - 自然入场三选一：f1 / s1 / 交还框架；
  - 进入任一 s 模式时置整队 `_startup_done`（单向）；
  - 未知模式交还框架，绝不重开 f1；
  - `reset_state` 清 3 个字段。
- **6-5** 每次重打包前跑 `verify_chain.py`；新增断言后先做变异测试，确认它会失败。
- **6-6 / 6-7** 日志处理：
  - 降级：框架 info 降为 debug；
  - 过滤：两行任务层切人 info 用作用域过滤器滤掉，warning/error 不过滤；
  - exit 行不读协奏；
  - 框架的 `switch_next_char A -> B ... current_con` 行保留。
- **6-8** `skip_combat_check` 保持窗口和只放行 force 的 `f_break` 不属于骨架，只作为可选案例。

## 迭代工作流（日志 + 视频）

1. 读日志，找到出问题的节点（`enter` 行即视频锚点），看 `cast X: ok|fail` 和 `reason=`。
2. 用相邻两行的时间戳差换算出视频时刻，对照画面确认根因。
3. 只改一个变量（时长、阈值、分支），重新实机验证。
4. 原因不明时不加兜底（5-8）。

## references

| 文件 | 内容 |
|---|---|
| [references/basechar-api.md](references/basechar-api.md) | BaseChar 常用函数详条（签名、行为、副作用、坑、对比、何时用、上游例子）+ 全量成员索引 |
| [references/task-api.md](references/task-api.md) | 角色代码用到的 `self.task.*`（BaseCombatTask / BaseWWTask / ok-script）+ 异常与战斗检查机制 |
| [references/self-impl-patterns.md](references/self-impl-patterns.md) | 自实现套路：时间谓词、发送-确认-记录、按住、颜色识别、模板流程 |
| [references/logging.md](references/logging.md) | 日志模板、级别、必打时机、字段词表、reason 词表、`_trace` 参考实现 |
| [references/workshop.md](references/workshop.md) | 工坊 zip 格式、循环轴骨架完整代码、日志过滤器、可选案例 |
| [templates/verify_chain.py](templates/verify_chain.py) | 交场链静态自检模板（填 `FILES` / `EXPECTED` / `STARTUP_END`） |
