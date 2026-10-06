# BaseChar API 参考

**基线**

- 上游 `ok-oldking/ok-wuthering-waves` master `2243d465`，行号均指 `src/char/BaseChar.py`，除非另有注明。
- 框架 ok-script `v2.0.8`。
- 源码与本文不一致时以源码为准，并修正本文（0-1）。

**调用频次**

括号里的“N 次 / M 文件”是该方法在上游 `src/char/*.py` 角色文件中的调用统计，不含 BaseChar 自身，用来说明这种写法有多常见。

## 目录

- [常量与枚举](#常量与枚举)
- [实例字段（状态与时间戳）](#实例字段)
- [生命周期：perform / do_perform / switch_out / reset_state](#生命周期)
- [切人：switch_next_char / get_switch_priority / need_fast_perform / wait_switch](#切人)
- [放技能：click_resonance / click_liberation / click_echo / send_*_key / record_*_use](#放技能)
- [技能可用判断：*_available / current_* / has_cd](#技能可用判断)
- [资源：协奏 is_con_full / get_current_con；回路 is_forte_full 系列](#资源)
- [普攻与重击：click / continues_normal_attack / heavy_attack / heavy_click_forte](#普攻与重击)
- [等待与计时：sleep / wait_down / wait_intro / time_elapsed_accounting_for_freeze](#等待与计时)
- [其他：flying / f_break / check_outro / is_first_engage / buff / cycle](#其他)
- [全量成员索引](#全量成员索引)

---

## 常量与枚举

| 名称 | 值 | 位置 |
|---|---|---|
| `SKILL_TIME_OUT` | `15` | `:11`，`click_resonance(time_out=0)` 的默认上限、各 click 的硬上限 |
| `SwitchPriority` | `NO=0 / LOW=100 / NORMAL=200 / HIGH=300 / MUST=400` | `:21`，间隔 100，可以返回 `HIGH + 1` 这类值 |
| `CharType` | `MAIN_DPS / SUB_DPS / HEALER` | `:14`；属性 `is_main_dps` / `is_sub_dps` / `is_healer` |
| `Elements` | `SPECTRO=0 … HAVOC=5` | `:29`；`ring_index` 用它的值 |
| `HEALER_FULL_CON_SWITCH_LOCKOUT` | `16.0` | `:66`，治疗满协奏切出后的锁定秒数 |
| `forte_white_color` | 颜色范围 dict | `:1015`，`is_forte_full` 使用；工坊可 `from src.char.BaseChar import forte_white_color` |
| `text_white_color` | 颜色范围 dict | `src/__init__.py`，`current_*` / `box_highlighted` 使用 |

## 实例字段

在 `__init__`（`:68`）中初始化。

| 字段 | 初值 | 写入者 | 含义 |
|---|---|---|---|
| `task` | — | 构造 | 所属 `BaseCombatTask` |
| `index` | — | 构造 | 队伍位置 0/1/2；切人键 = `index + 1` |
| `char_name` | — | 构造 | 如 `'char_jinhsi'` |
| `last_perform` | `0` | `perform()` | 本次 `do_perform` 开始时间。每次 `perform()` 都会刷新，包括 `switch_next_char` 没切走、`perform` 再次执行的时候，所以它不一定等于上场时刻 |
| `last_res` / `last_echo` / `last_liberation` | `-1` | `record_*_use()` | 各技能最近一次使用时间 |
| `last_switch_time` | `-1` | `switch_out()` | 最近一次下场时间 |
| `last_switch_in_time` | `-1` | task 切人成功时（`BaseCombatTask.py:677`） | 最近一次被切上场的时间。开战首发角色没有经过切人，所以仍是 `-1`；`reset_state` 不清这个值 |
| `last_outro_time` | `-1` | task（带 intro 切出时） | 最近一次出延奏的时间 |
| `last_full_con_switch_time` | `-1` | `switch_out()`（仅治疗） | 治疗锁定的起点 |
| `has_intro` / `has_sub_dps_intro` | `False` | task 切人时 | 本次上场是否带入场（变奏） |
| `is_current_char` | `False` | task | 是否在场 |
| `current_con` | `0` | `get_current_con()` | 协奏缓存，读到 1 后粘住，直到 `switch_out` |
| `intro_motion_freeze_duration` | `0.9` | — | 入场动作冻结时长，`wait_down` 和 task 冻结记账使用 |
| `check_f_on_switch` | `not is_healer` | — | 切人时是否自动按 F 处决 |
| `logger` | `Logger.get_logger(self.name)` | — | 输出自动带 `类名:` 前缀 |
| `_liberation_available` / `_resonance_available` / `_echo_available` | `False` | `send_*_key`、`switch_next_char` | 内部快照 |

## 生命周期

### perform / do_perform（`:220` / `:280`）

- `perform()` 由 `AutoCombatTask.run` 对在场角色调用。它先写 `last_perform = time.time()`，再调 `do_perform()`。不要覆写 `perform`；50 个上游角色覆写的都是 `do_perform`。
- 默认 `do_perform` 依次执行：
  1. `wait_intro(1.2)`；
  2. `click_echo(time_out=0)`；
  3. `click_liberation()`；
  4. `click_resonance()[0]`，失败则 `heavy_click_forte(self.is_mouse_forte_full)`；
  5. `switch_next_char()`。
- 3-1：以 `return self.switch_next_char()` 结尾，后面不再接动作。

### switch_out(con_full=False)（`:318`）

由 task 在切人确认成功后调用（`BaseCombatTask.py:675`）。它做这些事：

- 写 `last_switch_time`；
- 清 `is_current_char` / `has_intro` / `has_sub_dps_intro`；
- 如果满协奏切出（`con_full` 或 `current_con == 1`）：
  - 写 `last_buff_time`（当 `buff_time > 0`）；
  - 把 `current_con` 归 0；
  - 治疗角色还要写 `last_full_con_switch_time`；
  - 打 info `switch_out at full con set current_con to 0`。

覆写（3-8）：`super().switch_out(con_full)` 放在第一行，然后清理“每次上场”的状态。上游有 4 处覆写。

### reset_state（`:575`）

由 `combat_end()`（`BaseCombatTask.py:758`）和 `load_chars()`（`:842`，重新读队伍时）对全队调用。

- 它会清：`has_intro`、`current_con`、`last_full_con_switch_time`、工具箱标记、`_*_available`；
- 它不清：`last_res`、`last_liberation` 等时间戳。

覆写（3-8）：先调 `super().reset_state()`，再清“每场战斗”的状态；`__init__` 里的初值要和它一致。上游有 13 处覆写。

### on_combat_end(chars)（`:673`）

战斗结束时，由 `combat_end` 对**当时在场**的角色调用。默认 `pass`。3-6：`switch_other_char` 只在这里用。

---

## 切人

### switch_next_char(post_action=None, free_intro=False, target_low_con=False)（`:337`，130 次 / 50 文件）

**角色侧**（`:337-356`）：

1. 调 `self.is_forte_full()`，返回值丢弃；
2. 清 `has_intro`；
3. 快照 `_liberation_available`；
4. `use_tool_box()`；
5. 转给 `task.switch_next_char(self, ...)`。

**task 侧**（`BaseCombatTask.py:585-688`）：

1. `free_intro` 为 False 时读 `current_char.get_current_con()`。读数在 (0.8, 1) 之间时，sleep 0.05 再读一次；等于 1 就 `has_intro=True`。
2. `_choose_switch_target`：
   - 对每个候选人：处于治疗满协奏锁定期的，直接给 `NO`，**不调用**它的 `get_switch_priority`；其余调用 `get_switch_priority(current_char, has_intro, target_low_con)`；
   - 取最高优先级那一档；
   - `has_intro` 且最高档 ≥ MUST 时，取最久没上场的；否则按 buff、角色类型规则挑选；
   - 无 intro 时，排除 1 秒内刚下场的候选人（switch cd）；
   - 打 info `switch selection result ...`。
3. **没有候选人**（全是 NO，或选回自己）：打 warning `can't find next char ... add a normal attack`，然后 `continues_normal_attack(0.2)` 并 `return`。此时没有切人，`AutoCombatTask` 会再次调用当前角色的 `perform`。
4. 打 info `switch_next_char A(type) -> B(type) has_intro ... current_con ...`。
5. 循环直到切人成功：
   - 每轮 `check_combat()`；目标是 ShoreKeeper 且带 intro 时除外；
   - 若 `switch_to.wait_switch()` 为真，则点击 + sleep 0.1 后 continue。**这一支没有超时**；
   - 每 0.1s 发一次数字键 `index+1` 并点击；
   - `in_team()` 为假时立即 `raise_not_in_combat('not in_team while switching')`。所以在大招演出中切人会中断整场战斗；
   - 10 秒没切成：`raise_not_in_combat('failed switch chars')`；
   - 成功后：`in_liberation=False`，F 处决检查，`current_char.switch_out(con_full=has_intro)`，写目标的 `is_current_char` / `last_switch_in_time`；带 intro 时登记入场冻结（`intro_motion_freeze_duration`，freeze_time=-100）。
6. 有 `post_action` 时调用 `post_action(switch_to, has_intro)`。
7. 打 info `switch_next_char end {秒}s`。

**规则**：3-1、3-7。不带参数调用；只有今汐这类机制才用 `free_intro=True`；不用 `post_action`。

**覆写**：上游有 5 处覆写 `switch_next_char`，都是在调用 `super()` 前做准备工作。新代码优先用 `get_switch_priority`（3-2）。

### get_switch_priority(current_char=None, has_intro=False, target_low_con=False)（`:701`，覆写 25 处）

- 默认返回 `NO`（治疗锁定期）或 `NORMAL`。
- 它是**目标角色**的方法：A 切出时，框架问 B 和 C“你想不想上”。
- 调用时机：每次切人对每个候选人各调一次；`need_fast_perform()` 也会对所有非在场角色调用它（`has_intro=False`）。
- 3-3 规定它在不在场时运行，只读时间戳、已存状态和 `*_available()`。不在场时 `*_available()` 走的是 CD 推算，不读 HUD。

上游例子：

```python
# Camellya.py:23 —— 带入场就必须上
def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
    if has_intro:
        return SwitchPriority.MUST
    return super().get_switch_priority(current_char, has_intro, target_low_con)

# Brant.py:108-116 节选 —— 时间戳驱动：刚上过场 4 秒内不上；大招持续中必须上
def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
    ...  # 原文这里调用 self.decide_teammate()，见下方反例
    if self.time_elapsed_accounting_for_freeze(self.perform_anchor, True) < 4:
        return SwitchPriority.NO
    if self.still_in_liberation():
        return SwitchPriority.MUST
    ...
    return super().get_switch_priority(current_char, has_intro, target_low_con)
```

反例：Brant 在这里调用了 `self.decide_teammate()`，Carlotta 也在这里做初始化。新代码不要在此改状态（3-3）。

### healer_full_con_switch_locked()（`:712`）

治疗角色满协奏切出后 16 秒内（扣冻结）为 True。task 在调用 `get_switch_priority` **之前**先做这项判断，所以覆写 `get_switch_priority` 返回 MUST 也绕不过锁定（工坊 NB-1）。

### need_fast_perform()（`:825`，12 次 / 9 文件）

遍历非在场队友，只要有人的 `get_switch_priority(...) >= MUST` 就返回 True，并打 info `In lock with {char}`。

默认的 `get_switch_priority` 只返回 NORMAL 或 NO（`:701-710`），所以只有队里有人覆写成不带 intro 也返回 MUST 时，它才可能为真。上游 9 个文件、12 处调用，多数用来给 R 或重击当门控，例如 `Brant.py:32`。

用法（3-4）：放在可以跳过的动作之前（R、重击、填充普攻），为真就跳过、直接切人，exit 行写 `reason=fast_switch`。不要在紧凑循环里调用：每次调用都会触发全部队友的优先级计算并打 info。上游 `Zhezhi.py` 就在循环里调用，这是反例。

### wait_switch()（`:959`，覆写 2 处）

默认返回 False。它在**目标角色**上调用：task 切人循环中，只要它返回 True，就一直普攻等待，没有超时。3-5：覆写必须自带时间上限，并且只读时间戳和已存状态。

### switch_other_char(allow_auto_combat=False)（`:963`）

- 战斗结束后切到治疗，或切到下一位。`AutoCombatTask` 下默认直接 return。
- 最多 6 秒，每 0.2 秒发一次数字键。
- 3-6：只在 `on_combat_end` 中使用。

---

## 放技能

### click_resonance(post_sleep=0, has_animation=False, send_click=True, animation_min_duration=0, check_cd=False, time_out=0, click_f=True)（`:369`，78 次 / 42 文件）

**行为**（`:384-458`）：

- 上限：`time_out=0` 时为 `SKILL_TIME_OUT=15` 秒，否则为 `time_out`。
- 每轮先 `check_combat()`。`not resonance_available()` 成立时（有动画时还要求超过 `animation_min_duration`）退出循环。
- 每 0.1 秒操作一次。`send_click=True` 时**点击和 E 交替**：上一次按了 E，这一次就先点普攻。
- 第一次真正发 E 时调用 `record_resonance_use()`。注意这是在**按键时**记录，不是确认之后。
- `has_animation=True` 时：
  - 发 E 后 sleep 0.2；
  - `in_team()[0]` 为假视为进入动画，置 `task.in_liberation=True`；
  - 动画超过 `animation_min_duration` 后，`click_f` 为真则每 0.1 秒按 F；
  - 回到队伍界面后退出；
  - 动画时长会记入冻结。
- `check_cd` 参数在函数体中**没有使用**。
- 结束时 `clicked` 为真才 `sleep(post_sleep)`。

**返回**：`(clicked: bool, duration: float, animated: bool)`。

**坑**：

- 返回值是**元组，永远为真**，所以 `if self.click_resonance():` 恒成立。判断是否按出要用 `[0]`（默认 `do_perform` 就是 `self.click_resonance()[0]`）。
- E 一直亮着时（强化 E、多段 E、识别不稳）会连按到上限。1-4 规定必须传正数 `time_out`。上游有 4 处写 `time_out=0`，实际都是 15 秒。
- `continues_normal_attack(..., click_resonance_if_ready_and_return=True)` 内部调用的是**不带参数**的 `click_resonance()`，上限同样是 15 秒。

**对比**：

- `send_resonance_key()`：只发一次，不等、不记录时间戳。
- `wait_until(lambda: not self.resonance_available(), post_action=self.send_resonance_key, time_out=N)`：反复按直到进 CD，不插普攻（1-6）。上游 `Brant.py:136`、`Changli.py:169` 就是这样写的；`Luhesi.py:52-54`（条件换成动作识别）和 `Augusta.py:54`（R，条件换成 `not liberation_available()`）是同一模式的变体。

### click_liberation(con_less_than=-1, send_click=False, wait_if_cd_ready=0.1, animation_min_duration=0, click_f=True)（`:591`，71 次 / 45 文件）

**行为**（`:605-671`）：

1. 依次检查前置条件：
   - `task.use_liberation` 为 False 时直接返回 False（大世界“不使用大招”配置）；
   - `con_less_than > 0` 且 `get_current_con() > con_less_than` 时返回 False。注意这会写入 `current_con`。
2. 大招可用时：只要 `liberation_available()` 为真，就每 0.1 秒发一次 R（`send_click` 为真时附带点击）。超过 15 秒则报 `alert_skill_failed` 并 `raise_not_in_combat`。
3. 发过 R 后用 `wait_until(not in_team, time_out=0.4)` 确认进入演出。没确认到就打 **error** `clicked liberation but no effect`，并 `return False`。这时不记录 `last_liberation`，也不等演出结束。
4. 一开始就不可用时：在 `wait_if_cd_ready` 秒内，只要还没进 CD 就补按；仍然没进演出则返回 False。
5. 演出阶段：只要 `not in_team()[0]`，就置 `in_liberation=True`，`click_f` 为真时每 0.1 秒按 F。超过 7 秒则 `raise_not_in_combat`（boss 被大招打死）。
6. 演出结束后依次：
   - 记冻结；
   - `record_liberation_use()`；
   - 复位 `in_liberation`；
   - 打 info `click_liberation end {duration}`。

**返回**：bool。返回 False **不等于**没放出来（1-5）：

- 没有动画的大招会走第 3 步，返回 False；
- 演出比 0.4 秒窗口晚出现时也返回 False，而且这时切人会撞进演出，在 `switch_next_char` 里判为脱战。工坊实测过演出晚约 0.6 秒出现的情况。

要确认是否放出，看 CD 是否出现，或者 `in_team` / 图标是否变化。

### click_echo(duration=0, sleep_time=0, time_out=1)（`:517`，70 次 / 45 文件）

**两种模式**：

- **单发模式**：`time_out=0` 且 `echo_available()` 为真时，发一次声骸键，`record_echo_use()`，返回 True。召唤型声骸用这种。
- **循环模式**（其余情况）：
  1. 大世界自动战斗且 `ring_index == FIRE` 时返回 False（不用摩托声骸）。
  2. `has_cd('echo')` 时返回 False。
  3. 每 0.1 秒发一次声骸键，第一次发送时记录。
  4. `duration > 0` 时持续按满 `duration`；否则 `echo_available()` 一变为假就退出。
  5. 超过 `time_out + duration` 时打 info `click_echo time out`，返回 **False，即使已经按出去了**。

**坑**：

- `time_out=0` 但声骸不可用时，会掉进循环模式：上限为 0，基本立即超时，返回 False。
- `sleep_time` 参数没有使用。

### send_resonance_key / send_echo_key / send_liberation_key（`:460` / `:471` / `:494`）

```
send_resonance_key(post_sleep=0, interval=-1, down_time=0.01)
send_echo_key(after_sleep=0, interval=-1, down_time=0.01)
send_liberation_key(after_sleep=0, interval=-1, down_time=0.01)
```

- 只发一次键（键位取 `get_*_key()`），并把对应的 `_*_available` 置 False。
- **不**记录时间戳，**不**确认是否生效。
- 注意参数名不统一：resonance 叫 `post_sleep`，另外两个叫 `after_sleep`。

规则：

- 1-1：只有 `click_*` 明确不合适时才用，并写注释说明原因。
- 1-2：长按用 `self.task.send_key(self.get_resonance_key(), down_time=秒)`，见 `Chisa.py:90`。
- 1-3：需要计时就调用 `record_*_use()`，并且放在确认之后。
- 1-8：不要传 `interval`，否则可能被节流静默丢弃。

### get_resonance_key / get_echo_key / get_liberation_key（`:697` / `:693` / `:689`）

代理到 task，读取用户在 ok-ww 设置里配置的键位。1-2：不要写死。

### record_resonance_use / record_liberation_use / record_echo_use（`:505-515`）

分别写 `last_res` / `last_liberation` / `last_echo = time.time()`。

| 函数 | 何时会自动记录 |
|---|---|
| `click_resonance` | 第一次发 E 时 |
| `click_echo` | 发送时 |
| `click_liberation` | 演出结束后（返回 False 时不记录） |

手动发键后的记录时机见 1-3 / 5-3。

---

## 技能可用判断

### resonance_available() / echo_available() / liberation_available(check_color=True)（`:720` / `:739` / `:807`）

它们都走 `available(box, check_color, check_cd)`（`:733`）：

- **在场**：调用 `task.available(box, check_color, check_cd)`（`BaseCombatTask.py:350`）。
  - `check_color`：读 `box_{name}` 的白色像素比，大于 0 才算亮；
  - `check_cd`：同时要求 `not has_cd(name)`。
- **不在场**：`not task.has_cd(box, self.index)`，用上次在场时 OCR 到的 CD 减去扣冻结的经过时间来推算。

| 函数 | check_color | 含义 |
|---|---|---|
| `resonance_available()` | False | 只看 CD 数字 |
| `echo_available()` | False | 只看 CD 数字 |
| `liberation_available()` | True（默认） | 图标亮 + 没有 CD |
| `extra_action_available()` | True，check_cd=False | 只看图标 |

1-7：要确认 E 图标是亮的，写 `self.current_resonance() > 0 and self.resonance_available()`，见 `Brant.py:135`、`Changli.py:168`。

### current_resonance() / current_echo() / current_liberation()（`:912` / `:917` / `:922`）

返回对应技能格的 `text_white_color` 像素占比（0~1），**不是**能量进度。0 表示暗或灰；大于 0 表示有白色（亮，或者 CD 数字本身也是白色）。只对在场角色有意义（4-4）。

### has_cd(box_name)（`:295`）→ task.has_cd

- 判断条件是 `get_cd(box) > 0.2`。
- `get_cd` 先调用 `refresh_cd()`：**每帧（scene）最多做一次 OCR**，识别技能栏的 3 个 CD 数字并存进 `task.cds[index]`。
- L-8：打日志时不要为了取数而额外调用 `has_cd`。

### is_available(percent, box_name)（`:306`）

旧接口：`percent == 0 or not has_cd(box)`。新代码不用。

---

## 资源

### is_con_full()（`:761`，27 次 / 15 文件）

- `current_con == 1` 时直接返回 True；
- 否则调用 `task.is_con_full()`，即 `task.get_current_con() == 1`。
- **注意**：角色侧的 `is_con_full()` **不写** `current_con`。

4-3：判断“满没满”用它。

### get_current_con()（`:767`）

- `current_con == 1` 时直接返回 1；
- 否则调用 `task.get_current_con()` 并**写入** `current_con`。

**task 侧**（`BaseCombatTask.py:972`）：

- 读协奏环区域；环色索引首次通过 `_ensure_ring_index` 确定；
- 用连通域判断是否为整环。满环时把面积存进 `con_full_size`，这个值持久化在 Config `_con_full_size` 中；
- 非满时的比例 = 当前面积 / 满环面积（上限 0.99）。

**坑**：

- 读到 1 后一直是 1，直到 `switch_out` 才归 0（4-3）。
- `switch_next_char` 自己会调用它。
- L-8：不要为了打日志去调用它。

### is_forte_full()（`:784`，38 次 / 14 文件；覆写 3 处）

- 固定区域 `(2251,1993)-(2311,2016)@3840x2160`，水平居中。
- `forte_white_color` 白色像素比大于 **0.08** 时为 True。
- 它是通用的“回路条亮”判断，很多角色不准。

**谁会调用它**：默认 `do_perform` 间接调用；`heavy_click_forte` 的默认 `check_fun`；角色侧 `switch_next_char()` 的第一行（返回值丢弃）。

4-1：不准时可以覆写它，或者新增 `is_forte_full_<char>_<what>()`。新增的函数要显式传给 `heavy_click_forte(check_fun=...)` 等调用方。

### is_mouse_forte_full() / is_e_forte_full()（`:774` / `:781`）

- 分别对应 `task.find_mouse_forte()` / `find_e_forte()`（`BaseCombatTask.py:690/694`）。
- 方法是在二值化后的画面上做模板匹配（`mouse_forte` / `e_forte`，threshold 0.6）：前者找重击强化标记，后者找 E 强化标记。
- 比颜色占比更精确，但只适用于有这类标记的角色。

---

## 普攻与重击

### click(*args, **kwargs)（`:275`，52 次 / 29 文件）/ click_with_interval(interval=0.1)（`:267`）/ normal_attack()（`:892`）

- `click`：强制 `down_time=0.01`，再转给 `task.click`。不带坐标时点屏幕中心，也就是普攻。
- `click_with_interval`：等于 `click(interval=0.1)`，常用作 `wait_until(post_action=...)`。
- `normal_attack`：先 `check_combat()`，再点击一次。

1-8：带 `interval>0` 的点击和 `send_key` 共用节流时间戳。

### continues_normal_attack(duration, interval=0.1, after_sleep=0, click_resonance_if_ready_and_return=False, until_con_full=False)（`:843`，89 次 / 38 文件）

在**真实时间**的 `duration` 内循环：

1. 如果 `click_resonance_if_ready_and_return` 且 `resonance_available()`，就 `return self.click_resonance()`。注意这是不带参数的调用，上限 15 秒。
2. 如果 `until_con_full` 且 `is_con_full()`，就 return。这意味着每轮都读一次协奏。
3. `task.click()`，然后 `self.sleep(interval)`；sleep 里会做战斗检查。

循环结束后 `sleep(after_sleep)`。

规则：2-8。固定时长普攻用它，不要手写循环。

### continues_right_click(duration, interval=0.1, direction_key=None)（`:875`）/ continues_click(key, duration, interval=0.1)（`:863`）

- `continues_right_click`：持续右键点击（闪避、瞄准等），可以同时按住方向键。
- `continues_click`：持续发送某个键。

两者**都不调用 sleep，也不做战斗检查**，只靠 `interval` 节流空转。

### heavy_attack(duration=0.6)（`:898`，26 次 / 18 文件）

依次 `check_combat`、`mouse_down`、`sleep(duration)`、`mouse_up`、`sleep(0.01)`，即固定时长的重击（4-2）。

**坑**：中间的 `sleep` 在战斗检查失败时会抛异常，这时 `mouse_up` 不会执行。手写按住要按 5-4 放进 try/finally。

### heavy_click_forte(check_fun=None)（`:482`，17 次 / 12 文件）

- `check_fun` 默认是 `self.is_forte_full`。
- `check_fun()` 为真时：`mouse_down` → `wait_until(lambda: not check_fun(), time_out=2)` → `mouse_up` → `sleep(0.05)`。

返回三态：

| 返回值 | 含义 |
|---|---|
| `None` | 进入时 `check_fun()` 为假，根本没按 |
| 真值 | 2 秒内回路被消耗 |
| `None`（超时） | 按满 2 秒仍未消耗 |

注意：`wait_until` 超时返回 None，所以“没按”和“超时”都返回 None。

4-2：长按直到回路耗尽用它；`check_fun` 显式传入（4-1）。

---

## 等待与计时

### sleep(sec, check_combat=True)（`:358`，112 次 / 38 文件）

- `check_combat=False` 时，在 sleep 期间置 `task.skip_combat_check=True`。
- 执行链：`task.sleep` → `BaseWWTask.sleep`（会扣掉月卡检查的耗时）→ `executor.sleep`：
  - 期间距上次检查满 `sleep_check_interval=0.4` 秒，就抓一帧并调用 `task.sleep_check()`；
  - `sleep_check()` 发现已脱战时 `raise_not_in_combat`。
- `sec <= 0` 时立即返回：不抓帧，也不做检查。

2-1：不要用 `time.sleep()`，它既不抓帧，也不响应暂停和停止。

### wait_down(click=True)（`:231`，33 次 / 22 文件）

- **没有控物**（`task.has_lavitator` 为假）且 `has_intro`：普攻（`continues_normal_attack`）或 sleep `intro_motion_freeze_duration=0.9` 秒。
- **其他情况**：只要 `flying()` 为真且不超过 2.5 秒，就 `click(interval=0.2)`（或 sleep 0.2），并且每轮调用 `next_frame()`。

2-7：等入场动作或落地用它。

### wait_intro(time_out=1.2, click=True)（`:248`）/ down()（`:258`）

- 只有 `has_intro` 时，才 `wait_until(self.down, post_action=click_with_interval, time_out)`。
- `down()` 的判断是：E 亮且无 CD，或者 R 亮且无 CD。

2-7：只在要等 E/R 变得可用时才用 `wait_intro`。

### time_elapsed_accounting_for_freeze(start, intro_motion_freeze=False)（`:685`，67 次 / 30 文件）

转给 task（`BaseCombatTask.py:100`）：

- `start < 0` 时返回 10000（视为“很久以前”）；
- 否则返回 `time.time() - start - Σ(start 之后登记的冻结时长 - freeze_time)`；
- 入场冻结（`freeze_time=-100`）只有在 `intro_motion_freeze=True` 时才扣除。它由带 intro 的切人登记，时长取目标角色的 `intro_motion_freeze_duration`（默认 0.9 秒，`BaseCombatTask.py:680`）。

**冻结的来源**：

- `click_liberation` 和 `click_resonance(has_animation=True)` 的演出时长；
- 切人 intro 的入场动作；
- 手动调用的 `add_freeze_duration`。

2-5 / 2-6：游戏内时长用它，锚点按含义选。

### add_freeze_duration(start, duration=-1.0, freeze_time=0.1)（`:681`）

- 登记一段冻结；`duration < 0` 时取 `now - start`。
- 只登记 `duration > freeze_time` 的；超过 60 秒的旧记录会被清掉。
- 手写演出等待之后，要调用它来记账（见 `Augusta.py:85`、`Hiyuki.py:175`）。

### wait_switch_cd()（`:837`）/ normal_attack_until_can_switch()（`:819`）

- `wait_switch_cd`：距本次上场不足 1 秒时，普攻补足剩余时间。
- `normal_attack_until_can_switch`：扣冻结后，普攻到上场满 1.1 秒为止。它是**忙等**，循环里没有 sleep 也没有 `next_frame`，是 2-9 的反例。

---

## 其他

| 成员 | 行 | 说明 |
|---|---|---|
| `flying()` | `:926` | 有控物（`task.has_lavitator`）时，控物边框白色比例小于 0.1 即为在空中；没有控物时恒为 False。上游 51 次调用 |
| `flying_based_on_resonance()` | `:187` | E 无 CD 且 E 格不亮时，视为在空中 |
| `f_break(check_f_on_switch=False, force=False)` | `:1003` | F 处决。`force=True` 先补按一次 F；`check_f_on_switch=True` 且本角色 `check_f_on_switch` 为假时返回 False；然后调用 `task.f_break()`（检测到可处决时连按 F，最长 5 秒）。切人时 task 会自动调用 |
| `check_outro()` | `:933` | 带入场时，返回最近下场的队友 `char_name`（视为延奏来源），否则返回 `'null'`；会打 info |
| `is_first_engage()` | `:952` | 本次上场是否就是开战时的首发（`last_perform - combat_start < 0.4`）；会打 info |
| `has_buff()` / `has_all_buff()` / `buff_time` | `:154` / `:158` / `:151` | 由 `CharFactory` 按定位配置；task 选人时使用 |
| `char_type` / `is_healer` / `is_main_dps` / `is_sub_dps` | `:124-145` | 定位来自配置，不要写死 |
| `skip_combat_check()` | `:191` | 默认 False；返回 True 时，task 的战斗检查直接视为在战斗中（`CombatCheck.py:147`）。工坊可选案例见 workshop.md |
| `use_tool_box()` | `:199` | 有工具箱标记时按工具键 |
| `has_long_action()` / `has_long_action2()` / `has_short_action()` | `:989-1001` | 在目标框里找长/短动作条模板 |
| `cycle()` / `do_cycle()` / `cycle_start()` / `cycle_sleep(duration=0.1)` | `:165-185` | 固定节拍循环框架：在 `cycle_time_out + cycle_intro_time` 内反复调用 `do_cycle()`，结束后切人。上游有 9 个文件使用 |
| `alert_skill_failed()` | `:364` | 报错、截图、通知用户检查键位，属于框架内部 |
| `is_open_world_auto_combat()` | `:568` | 是否为大世界自动战斗 |

---

## 全量成员索引

`src/char/BaseChar.py`@`2243d465`，按行号排列。

```
66   HEALER_FULL_CON_SWITCH_LOCKOUT = 16.0
68   __init__(task, index, char_name=None, confidence=1, ring_index=-1, char_type=CharType.MAIN_DPS, buff_time=None)
114  set_char_type(char_type=CharType.MAIN_DPS)
120  get_char_type()
124  char_type            (property)
127  set_buff_time(buff_time=None)
132  type                 (property)
136  is_healer / 140 is_main_dps / 144 is_sub_dps   (property)
147  get_buff_time()
151  buff_time            (property)
154  has_buff()
158  has_all_buff()
165  cycle()
176  do_cycle()
179  cycle_start()
182  cycle_sleep(duration=0.1)
187  flying_based_on_resonance()
191  skip_combat_check()
199  use_tool_box()
206  name                 (property, 类名)
214  __eq__(other)        (类名 + index)
220  perform()
231  wait_down(click=True)
248  wait_intro(time_out=1.2, click=True)
258  down()
267  click_with_interval(interval=0.1)
275  click(*args, **kwargs)
280  do_perform()
295  has_cd(box_name)
306  is_available(percent, box_name)
318  switch_out(con_full=False)
337  switch_next_char(post_action=None, free_intro=False, target_low_con=False)
358  sleep(sec, check_combat=True)
364  alert_skill_failed()
369  click_resonance(post_sleep=0, has_animation=False, send_click=True, animation_min_duration=0, check_cd=False, time_out=0, click_f=True)
460  send_resonance_key(post_sleep=0, interval=-1, down_time=0.01)
471  send_echo_key(after_sleep=0, interval=-1, down_time=0.01)
482  heavy_click_forte(check_fun=None)
494  send_liberation_key(after_sleep=0, interval=-1, down_time=0.01)
505  record_resonance_use() / 509 record_liberation_use() / 513 record_echo_use()
517  click_echo(duration=0, sleep_time=0, time_out=1)
568  is_open_world_auto_combat()
571  check_combat()
575  reset_state()
591  click_liberation(con_less_than=-1, send_click=False, wait_if_cd_ready=0.1, animation_min_duration=0, click_f=True)
673  on_combat_end(chars)
681  add_freeze_duration(start, duration=-1.0, freeze_time=0.1)
685  time_elapsed_accounting_for_freeze(start, intro_motion_freeze=False)
689  get_liberation_key() / 693 get_echo_key() / 697 get_resonance_key()
701  get_switch_priority(current_char=None, has_intro=False, target_low_con=False)
712  healer_full_con_switch_locked()
720  resonance_available()
733  available(box, check_color=True, check_cd=True)
739  echo_available()
750  extra_action_available()
761  is_con_full()
767  get_current_con()
774  is_mouse_forte_full()
781  is_e_forte_full()
784  is_forte_full()
807  liberation_available(check_color=True)
819  normal_attack_until_can_switch()
825  need_fast_perform()
837  wait_switch_cd()
843  continues_normal_attack(duration, interval=0.1, after_sleep=0, click_resonance_if_ready_and_return=False, until_con_full=False)
863  continues_click(key, duration, interval=0.1)
875  continues_right_click(duration, interval=0.1, direction_key=None)
892  normal_attack()
898  heavy_attack(duration=0.6)
912  current_resonance() / 917 current_echo() / 922 current_liberation()
926  flying()
933  check_outro()
952  is_first_engage()
959  wait_switch()
963  switch_other_char(allow_auto_combat=False)
989  has_long_action() / 993 has_long_action2() / 997 has_short_action()
1003 f_break(check_f_on_switch=False, force=False)
```
