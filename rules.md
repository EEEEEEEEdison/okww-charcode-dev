# 代码规则

okww-charcode-dev Skill 的代码规则。代码实现和实测修改都依照本文件。入口见 [SKILL.md](SKILL.md)。

## 这是什么

教 AI 写 ok-ww 的角色代码（`BaseChar` 子类）：

1. 宜调用框架现成函数，并在相近函数之间选对（`click_*` vs `send_*_key`、`is_con_full` vs `get_current_con`……）。
2. 没有现成函数时，按项目已有经验自实现（时间推算或画面识别）。
3. 日志统一用英文模板，规定何时打、打什么。
4. 工坊脚本化配队使用统一的循环轴骨架。

日常工作流：用户给游戏日志和录像，AI 定位出招或切人问题后修改代码（见“迭代工作流”）。

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

0. **先看前人怎么写**：改动涉及某个角色时，先读它的语义卡和代码基线（[harness/baseline.md](harness/baseline.md)）。
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
- **1-5** 不得直接相信返回值：
  - `click_liberation` 遇到没有动画的大招会返回 False；
  - `click_echo` 循环模式超时一律返回 False，即使已经按了出去。

  要确认技能是否放出，看 CD 是否出现、资源或图标是否变化。
- **1-6** 反复按某技能直到它进入 CD，用 `self.task.wait_until(lambda: not self.resonance_available(), post_action=self.send_resonance_key, time_out=N)`，不手写 while。这是 1-1 认可的例外，不需要另写注释。
- **1-7** 分清看的是什么：
  - `resonance_available()` / `echo_available()` 只看 CD 数字；要确认图标是亮的，再加 `current_resonance() > 0`；
  - `liberation_available()` 同时看图标和 CD；
  - 不在场角色的“可用”是用上次看到的 CD 推算的。
- **1-8** 带 `interval>0` 的 `click` 和 `send_key` 共用同一个节流时间戳，挨得太近的后一次会被静默丢弃，所以必须发出去的键不得传 `interval`。另外，发键和点击都会清空当前帧缓存，紧接着的画面判断会重新截图，截到的可能是动作刚开始时的画面。

### 2 等待与计时

- **2-1** 一律用 `self.sleep()`，不用 `time.sleep()`。要跳过战斗检查时传 `check_combat=False`。
- **2-2** 等条件用 `self.task.wait_until`，并且必须传正数 `time_out`（`0` 表示默认 10 秒）。
- **2-3** 只有可能单帧闪烁的识别才传 `settle_time=0.1~0.2`（条件需要连续成立这么久）；其他等待不传。
- **2-4** `time_out` 超过 1 秒的等待，传 `pre_action=self.check_combat`。不得把 `check_combat` 写进条件函数里，它返回 None。
- **2-5** 游戏内时长（buff、技能持续、冷却）用 `time_elapsed_accounting_for_freeze(anchor)` 计算；循环的时间上限用真实时间 `time.time() - start`。
- **2-6** 按含义选锚点：
  - `last_perform`：本次上场；
  - `last_res` / `last_liberation` / `last_echo`：对应技能；
  - 局部 `start`：本次动作。

  不得新建和已有时间戳重复的变量。
- **2-7** 等入场动作结束或角色回到地面，用 `wait_down()`，不得用固定秒数普攻代替。只有要等 E/R 变得可用时才用 `wait_intro()`。
- **2-8** 固定时长普攻用 `continues_normal_attack(duration)`，配合它的 `click_resonance_if_ready_and_return` / `until_con_full` 参数。`duration` 是真实时间，不扣冻结。
- **2-9** 手写的轮询循环必须有真实时间上限，每轮必须调用 `self.sleep()` 或 `self.task.next_frame()`。反例：上游 `normal_attack_until_can_switch` 是忙等。
- **2-10** `click_liberation` 在 `in_team()` 第一次为真的那一帧返回，那一帧 HUD 可能还在淡入（队伍编号已过阈值、技能栏图标还没亮全）。R 后紧接着判 HUD 图标时，用 `wait_until(图标出现, time_out=0.3)` 从下一帧开始判，不在当前帧上做单帧判定，也不拿一次没认出就当“状态已结束”。案例：弗坎嘉 v7 test_1621，爆发图标在那一帧只有 0.62，两场都判成没进爆发。
- **2-11** `click_liberation` 和 `click_resonance(has_animation=True)` 默认 `click_f=True`，演出期间（`in_team()` 为假）每 0.1 秒按一次 F。敌人韧性已空时，演出一结束就会触发击破。击破演出是全局时停：挑战计时器、技能冷却都停 1.3–1.5 秒，冻结记账（2-5）也算不进去。演出后紧跟按真实时间计时的动作（2-8 的固定时长普攻、按秒分组的爆发）时，传 `click_f=False`，击破留给切人时的 `f_break(check_f_on_switch=True)`（它的代价见 3-9）。注意治疗位 `check_f_on_switch` 为假，切人时不按 F。案例：弗坎嘉 v10 test_2142、v11 首版 test_2257，嘉贝莉娜 R 后爆发第 1 组被时停吃掉约 1.3 秒，协奏不满、无延奏切人。
- **2-12** 日志 `cast … ok` 的含义由当前实现决定。先核对发送、生效、冷却和函数返回的对应关系，再选计时锚点，见 [timing.md §2](harness/timing.md)。历史案例中，弗洛洛 E 冷却首帧比 ok 早 0.16–0.34 秒；该值来自 v8 test_1644、v10 test_2142、v11 test_2257，用户于 2026-10-13 确认。不得把该偏移用于所有技能，也不得统一从参考时长扣除。

### 3 切人

- **3-1** `do_perform` 以 `return self.switch_next_char()` 结尾，后面不再接动作。不得假设切人一定发生：没有候选人时它只普攻 0.2 秒就返回，随后 `perform` 会再次执行。
- **3-2** 想决定下一个上场的人，覆写**目标角色**的 `get_switch_priority`，返回 `MUST` / `NO` / `HIGH + 1`，其余情况返回 `super()`。不得写死数字键。
- **3-3** `get_switch_priority` 在角色**不在场**时被调用：每次切人对每个候选人各调一次，`need_fast_perform` 也会调用它。里面只能读时间戳、已存状态和 `*_available()`。不做 HUD 识别、不 sleep、不改状态、不打 info 日志。
- **3-4** 只有队里有人会**不带 intro 也返回 MUST**（例如按时间戳返回 MUST 的覆写）时，才需要检查 `need_fast_perform()`；默认的 `get_switch_priority` 从不返回 MUST，其他情况下它恒为 False。检查点放在可以跳过的动作之前（R、重击、填充普攻），为真就提前切人，exit 行写 `reason=fast_switch`。不得在紧凑循环里调用它（反例：上游 Zhezhi）。
- **3-5** 覆写 `wait_switch()` 时必须自带时间上限（框架那一支没有超时），并且只读时间戳和已存状态。
- **3-6** `switch_other_char()` 只在 `on_combat_end` 里用；战斗中切人一律用 `switch_next_char()`。
- **3-7** `switch_next_char()` 不带参数调用。只有当游戏机制允许不满协奏也能出延奏时（例如今汐）才传 `free_intro=True`。不得用 `post_action`；切人后要做的事放进目标角色的 `do_perform`，根据 `has_intro` 判断。
- **3-8** 状态清理分两处，两处都先调用 `super()`，并且 `__init__` 里的初始值要和 `reset_state` 一致：
  - 每次上场的状态，在覆写的 `switch_out(con_full)` 里清；
  - 每场战斗的状态，在覆写的 `reset_state()` 里清（战斗结束和重新读队伍时都会调用）。
- **3-9** 切人时框架会调出场角色的 `f_break(check_f_on_switch=True)`：有变奏时在发切人键**之前**（`BaseCombatTask.py:642-643`），无变奏时在认到换人**之后**（`:673-674`）。命中击破时 `task.f_break` 连按 F 加左键，直到认不到击破图标才返回，这时击破时停已近结束：v12 切人键在计时器恢复后约 0.1 秒发出，v13 坎 s1 开局的 `decide: break` 在恢复前 0.14–0.32 秒。所以有变奏的切人要等完整段演出：实测从切人日志行到技能栏换人约 1.8 秒，其中时停约 1.5 秒；没有击破时约 0.1 秒。出场节点靠切人取消最后一下的后摇（合轴）时，合轴会被这一段打断。不想在某个节点离场时击破，就覆写出场角色的 `f_break`，对该节点 `check_f_on_switch=True` 的调用返回 False（9b 是不分节点的版本）。案例：弗坎嘉 v12 test_0043 T1、T3。
- **3-10** `task.can_break` 是粘滞标记：`check_f_break` 在战斗检查（`CombatCheck.py:145`）和 `cycle_sleep`（`BaseChar.py:184`）里认到 `f_break_full`（boss 血条左边的击破环满了）或击破图标就置真，之后只有 `task.f_break` 按过 F、或者战斗状态重置才清。认到以后如果没人按 F，比如离场的 `f_break` 被覆写跳过（3-9），或者 boss 没被击破就死了、换了场，这个旧标记会一直留到下一次 `f_break`。那时对着击破环是空的新 boss，照样连按 F 加左键至少 0.5 秒。节点里主动击破之前，先 `self.task.can_break = False`，只认当下的图标。切人流程中的击破调用遵守 3-9。真击破不受影响：`f_break_full` 每轮都能实时认到。案例：弗坎嘉 v13 test_0110 t2、t3。
- **3-11** 生成代码前，按 [timeline.md](harness/timeline.md) 记录每次切人的类型、协奏状态、完成判据和 `allow_fill`。切人实现遵守 [step2.md §3](harness/step2.md)，不得默认补满协奏。实测按 `switch_next_char` 日志的 `has_intro`、`current_con` 逐条核对。案例：弗坎嘉 25 秒轴 v2 test_2304，弗洛洛强化重击后至少按住 1.0 秒再切，离场协奏 1，坎特蕾拉变奏入场，没打出普攻。参考视频第 6 音符到切人约 0.35 秒，用户于 2026-10-13 确认。
- **3-12** 节点要“打到能切某人就切”时，宜按框架选人的同一判据等：`self.task.wait_until(lambda: not self.task._target_has_switch_cd(target), post_action=self.click_with_interval, time_out=N)`，N 取 1.5–2.0 秒，超时记 fallback 照切。框架选人会滤掉离场不到 1 秒（扣冻结）的角色（`BaseCombatTask.py:456`），切早了认不到候选，只普攻 0.2 秒就返回（3-1）；改用固定时长普攻又要留余量，会多等。案例：弗坎嘉 25 秒轴坎特蕾拉 s2。v5 固定普攻 1.0 秒，切回时嘉贝莉娜已过切人冷却 0.41 秒和 1.64 秒。2.0.7 改成条件等，`attack_s` 1.02–1.04 秒，节点游戏时长 1.25 秒，参考 1.19 秒（test_2358；用户确认 2026-10-15）。

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

  E 的确认信号只适用于放完必进冷却的技能。放完后图标变成另一个无冷却可用技能的（多段、终结后回到普通技能），连按到冷却出现会把下一个也放出来，这类只按一次。案例：弗坎嘉 25 秒轴 v1 test_2216，坎特蕾拉终结技能放完图标回到普通 E，连按多放了一个普通 E（用户确认 2026-10-13）。
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
  - `enter`：带入场方式；作为视频候选锚点前，按 timing.md §2 核对事件边界；
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

流程与完成标准见 [harness/iterate.md](harness/iterate.md)。
按同一事件核对日志和录屏，先确认根因再改代码。
每次试验隔离因果影响，未知保留缺项。
语义卡候选按 [补卡机制](knowledge/cards/README.md#补卡机制) 批量确认。

## references

| 文件 | 内容 |
|---|---|
| [references/basechar-api.md](references/basechar-api.md) | BaseChar 常用函数详条（签名、行为、副作用、坑、对比、何时用、上游例子）+ 全量成员索引 |
| [references/task-api.md](references/task-api.md) | 角色代码用到的 `self.task.*`（BaseCombatTask / BaseWWTask / ok-script）+ 异常与战斗检查机制 |
| [references/self-impl-patterns.md](references/self-impl-patterns.md) | 自实现套路：时间谓词、发送-确认-记录、按住、颜色识别、模板流程 |
| [references/logging.md](references/logging.md) | 日志模板、级别、必打时机、字段词表、reason 词表、`_trace` 参考实现 |
| [references/workshop.md](references/workshop.md) | 工坊 zip 格式、循环轴骨架完整代码、日志过滤器、可选案例 |
| [templates/verify_chain.py](templates/verify_chain.py) | 交场链静态自检模板（填 `FILES` / `EXPECTED` / `STARTUP_END`） |
