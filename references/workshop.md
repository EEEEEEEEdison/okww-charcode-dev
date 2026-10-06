# 工坊配队与循环轴骨架

**基线**：上游 `2243d465`。骨架来自工坊队“今弗坎 3.6.7 v1”（坎特蕾拉 + 今汐 + 弗洛洛）的实测写法，去掉了队伍专属的内容。

工坊模式的自由度高，本篇的骨架只用来加快开发；交付说明里要标出自实现的部分。

## 目录

1. [工坊 zip 格式（事实）](#1-工坊-zip-格式)
2. [何时用循环轴骨架（6-1）](#2-何时用循环轴骨架)
3. [命名与动作体（6-2）](#3-命名与动作体)
4. [强切协议（6-3）与 NB-1](#4-强切协议)
5. [分发器（6-4）](#5-分发器)
6. [日志：降级与作用域过滤（6-6 / 6-7）](#6-日志)
7. [完整骨架代码](#7-完整骨架代码)
8. [交场链自检（6-5）](#8-交场链自检)
9. [可选案例（6-8，不属于骨架）](#9-可选案例)
10. [交付前检查](#10-交付前检查)

---

## 1. 工坊 zip 格式

导入时，`src/char/CustomCharLoader.py:521` 的 `inspect_team_archive` 会强制校验以下各项。

**zip 结构**

- 平铺，不能有子目录；
- 内容**恰好**是 `team.json` 加队伍 3 个角色的 `<ClassName>.py`；多一个、少一个文件都会被拒；
- 单个文件不超过 2,000,000 字节。

**team.json**

- `name`、`description`、`author`、`version`、`team` 五个字段都必须是非空字符串；
- `team` 是逗号分隔的英文角色名，必须按字母序排列（不区分大小写），并且每个名字都必须是已注册的角色。
  - 名字用**英文显示名**，不是 `char_xxx` 这种 key。大多数角色的显示名就是类名，少数有映射（`CustomCharLoader.py:25-34`）：例如类 `Linnai` 写 `Lynae`，类 `Xiangliyao` 写 `Xiangli Yao`，类 `Luhesi` 写 `Luuk Herssen`。排序按显示名比较。
  - 逗号两侧的空格会被去掉，例如 `"Cantarella, Jinhsi, Phrolova"`。
  - zip 里的 `.py` 文件名用**类名**（`Linnai.py`），不是显示名。

**每个 .py 文件**

- UTF-8 编码；
- 顶层必须定义同名类 `class <ClassName>`；
- 必须能编译（`_validate_character_code`，`:610`）；
- 加载时类必须继承 `BaseChar`（`:776`）；
- CRLF 换行会被归一化。

**能力边界**

- **不能携带图片模板**。识别只能用颜色占比，或项目里已有的模板名（5-5）。
- 可以 `from src.char.BaseChar import BaseChar, SwitchPriority, forte_white_color`，也可以 import 框架里的其他模块。
- 三个文件各自独立加载，**不能互相 import**。所以共用的 helper 每个文件各带一份，内容保持一致。
- 直接继承 `BaseChar` 的工坊类和内置类没有继承关系：`isinstance(char, src.char.Jinhsi.Jinhsi)` 判断不到，`task.has_char(cls)` 也一样。要按类名查找（`_find_teammate`）。

**实例替换（事实）**

- 队伍三人都识别到之后，`apply_team_char_classes`（`src/char/CharFactory.py:215`）会先建内置类实例，再新建工坊类实例替换它，并执行 `replacement.__dict__.update(char.__dict__)`（`:240`）。
- 后果一：工坊类在 `__init__` 里给**内置实例也有的属性**赋的值，会被内置实例的值覆盖。最典型的是 `logger`：`BaseChar.__init__` 给它赋了值（`BaseChar.py:107`）。所以改这类属性要用类上的 property，见第 6 节。
  - 实测：今弗坎在 `__init__` 里替换 `self.logger`，结果在 2026-10-04 的实机日志里，`click_liberation end` 照常输出。
  - 只属于工坊类的新字段（协议字段等）不受影响。
- 后果二：直接继承 `BaseChar` 时，`get_char_by_pos` 的 `isinstance(old_char, 内置类)` 不成立（`CharFactory.py:188`），每次 `load_chars` 都会重建实例。
  - `load_chars` 在每次脱战状态的战斗检查里都会被调用（`CombatCheck.py:166/182`），所以**每场开战时，工坊实例都是新建的**：`__init__` 重新执行，`last_res` / `last_liberation` 等框架时间戳也回到初始值。
  - 需要跨场保存的状态不能放在实例上。

## 2. 何时用循环轴骨架

6-1：骨架**只用于脚本化交场链**的工坊队，也就是每个节点都写明“下一个上场的人 + 它执行哪个动作体”。

没有固定交场链的工坊角色，照普通写法：`do_perform` 加 `get_switch_priority`，遵守第 1～5 组规则。

## 3. 命名与动作体

6-2：

- **f 族 = 启动轴**：每场战斗只跑一遍。
- **s 族 = 循环轴**：启动轴跑完后重复执行，并且首尾闭环。
- 每个角色**各自**从 1 开始编号（`perform_f1`、`perform_f2`……`perform_s1`……）。
- 同一个角色的 f 节点即使在链里被反复指定，也仍然属于启动轴。曾经出过错：把链条中段的 f 节点叫成循环轴，结果注释、trace 和自检全都写错了。
- 启动轴和循环轴之间**只有一条 f→s 交接边**（`STARTUP_END`）。

**动作体与薄包装**

- f 和 s 共用的动作抽成 `_action_xx(tag, nxt)`：
  - `tag` 是日志节点（`'f2'` / `'s1'`）；
  - `nxt` 是 exit 行的去向（`'Phrolova.f4'`）。
- `perform_fN` / `perform_sN` 是**薄包装**，最后一句固定写成字面形式：

  ```python
  self._force_switch_to(self._find_teammate('X'), 'mode')
  ```

  `verify_chain.py` 靠 AST 扫描这个写法，所以不要换成变量，也不要包进 helper。

## 4. 强切协议

6-3：队里**每个类**都带同一套协议，缺一个就失效（那个类仍会按自己的 MUST 抢人）。协议有四部分：

1. `__init__` 里的协议字段：`_force_switch_me`、`_entry_mode`、`_node`、`started`、`_startup_done`。
2. `get_switch_priority` 头部拦截：
   - 自己被标记，返回 `MUST`；
   - 别人被标记，返回 `NO`；
   - 其余情况调用 `super()`。
3. `_find_teammate(class_name)`：按类名查找队友。
4. `_force_switch_to(target, mode)`：
   1. 写 `target._entry_mode = mode`；
   2. 只给 target 打 `_force_switch_me` 标记；
   3. 在 `try` 里调用 `self.switch_next_char()`；
   4. 在 `finally` 里清掉全队的标记。

**NB-1（已知漏洞，骨架本身绕不开）**

- **原因**：框架的 `_choose_switch_target` 在调用 `get_switch_priority` **之前**，先把处于满协奏锁定期（16 秒，扣冻结）的治疗角色判成 `NO`（`BaseCombatTask.py:537-542`）。如果强切目标正好是刚满协奏切下场的治疗：
  - 它拿不到 MUST；
  - 其他人又因为拦截都返回 NO。
- **后果**：
  1. 框架打 warning `can't find next char`，普攻 0.2 秒后返回；
  2. 本角色以自然入场再次进入分发器；
  3. 交场链在这里断开。
- **对策**：设计链条时，不要让治疗在满协奏切下场后 16 秒内被强切回来。

## 5. 分发器

6-4：`do_perform` 是分发器，按以下流程处理：

1. 读出 `_entry_mode`，**立即清空**。
2. **自然入场**（`mode is None`）三选一：
   - 本角色本场还没开始（`not self.started`）：走 `f1`；
   - 循环轴已开始（`self._startup_done`）：走 `s1`；
   - 启动轴进行中：**交还框架切人**。既不跳进 s 族（会提前离开启动轴），也不重开 f1（会污染启动轴）。
3. 分发到 s 族时，把**整队**标记为 `_startup_done = True`。这是单向标记：不存在“进了循环轴又回到启动轴”的合法路径。
4. `perform_<mode>` 不存在时**交还框架**，绝不回落到 f1。
5. `reset_state` 清 `started`、`_startup_done`、`_entry_mode` 三个字段。

**注意**：战斗中如果框架重新读取队伍（`load_chars`），也会触发 `reset_state`，启动轴就会**重新播放**。

为什么门控要用整队的 `_startup_done`：如果用每个角色自己的 `started`，启动轴中途发生自然入场时，会提前跳进循环轴。

## 6. 日志

日志模板与词表见 logging.md。循环轴层在模板前加 `[F1]` / `[S2]` 标签。

**6-6 降级与过滤**

- **按实例降级**：在类上把 `logger` 定义成 property。
  - setter 接住 `BaseChar.__init__` 赋的 Logger，存成 `_raw_logger`，同时包一层 `_InfoAsDebug`；getter 返回这层包装。
  - 框架通过 `self.logger` 打的 info 行（`click_liberation end`、`In lock with`、`switch_out at full con`……）就降为 debug，正式版看不到，`main_debug` 里仍然能看到。
  - **不要在 `__init__` 里直接赋值 `self.logger = ...`**：会被 CharFactory 的 `__dict__.update` 覆盖回去（第 1 节“实例替换”）。property 是数据描述符，查找时优先于实例 `__dict__`，所以不受影响。
  - warning 和 error 原样输出。
  - 模板行走 `_raw_logger`，见 `_trace`。
- **任务层过滤**：`BaseCombatTask` 的切人 info 行用的是模块级 logger，没法按实例降级。改为在共享的 `logging.getLogger("ok")` 上挂一个 `logging.Filter`，按前缀丢弃两种行：
  - `BaseCombatTask:switch selection result`；
  - `BaseCombatTask:switch_next_char end`。
- **过滤器的作用范围**：
  - 由轴角色在 `__init__` 里安装，靠标记属性 `okww_axis_switch_filter` 去重，**只装一次**；
  - 只在 `executor.current_task` 的队伍里含轴角色（`_axis_char = True`）时生效。换成别的队伍后，框架行自动恢复，不用重启 ok-ww；
  - 只过滤 info，**warning 和 error 一律不过滤**；
  - 过滤器内部吞掉自己的异常，返回 True（放行）。这是日志 helper 的例外（5-6）；
  - 已装的过滤器会一直留到 ok-ww 重启。重新导入 zip 后，如果改了前缀列表，要重启才生效。

**6-7 exit 行与框架行**

- `exit` 行不读协奏（L-8）。
- 框架的 `switch_next_char A -> B … has_intro … current_con …` 行**保留**，不过滤。它自带协奏读数和是否带变奏，而且这是框架本来就要读的值。

## 7. 完整骨架代码

下面是 `Alpha.py` 的骨架，三人队为 Alpha、Beta、Gamma。

- `Beta.py` / `Gamma.py`：复制同一份“模块级日志部件”和“协议 / 分发器 / `_trace`”区，只改类名和节点、动作体。
- 节点内容（`_action_*`）是占位示例，要按实际轴来写。写的时候遵守第 1～5 组规则。

```python
import logging

from src.char.BaseChar import BaseChar, SwitchPriority

# ---------------- 模块级日志部件（三个文件各带一份，内容保持一致） ----------------
_RATIO_FIELDS = ('con', 'res_pct')
_FILTERED_SWITCH_LINES = (
    'BaseCombatTask:switch selection result',
    'BaseCombatTask:switch_next_char end',
)


def _fmt_value(key, v):
    if isinstance(v, float):
        return f'{v:.3f}' if key in _RATIO_FIELDS else f'{v:.2f}'
    return str(v)


class _InfoAsDebug:
    """Per-instance logger: framework info lines become debug; everything else passes through."""

    def __init__(self, inner):
        self._inner = inner

    def info(self, message):
        self._inner.debug(message)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class _AxisSwitchFilter(logging.Filter):
    """Drops the task-level switch info lines while the running task's team has an axis char."""

    okww_axis_switch_filter = True

    def __init__(self, executor):
        super().__init__()
        self._executor = executor

    def filter(self, record):
        try:
            if record.levelno != logging.INFO or not record.getMessage().startswith(_FILTERED_SWITCH_LINES):
                return True
            chars = getattr(self._executor.current_task, 'chars', None) or []
            return not any(getattr(char, '_axis_char', False) for char in chars)
        except Exception:
            return True


def _install_axis_switch_filter(task):
    try:
        ok_logger = logging.getLogger('ok')
        if not any(getattr(f, 'okww_axis_switch_filter', False) for f in ok_logger.filters):
            ok_logger.addFilter(_AxisSwitchFilter(task.executor))
    except Exception:
        pass


class Alpha(BaseChar):
    """Workshop axis team Alpha / Beta / Gamma: Alpha opens the startup axis."""

    _axis_char = True

    # A property, not an __init__ assignment: CharFactory copies the built-in instance's __dict__
    # over this one on team load, and a data descriptor wins over the instance __dict__.
    @property
    def logger(self):
        return self._quiet_logger

    @logger.setter
    def logger(self, value):
        self._raw_logger = value
        self._quiet_logger = _InfoAsDebug(value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _install_axis_switch_filter(self.task)
        self._force_switch_me = False
        self._entry_mode = None
        self._node = None
        self.started = False
        self._startup_done = False

    def reset_state(self):
        super().reset_state()
        self.started = False
        self._startup_done = False
        self._entry_mode = None

    # ---------------- 强切协议（队里每个类都带同一份） ----------------
    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        if self._force_switch_me:
            return SwitchPriority.MUST
        for char in self.task.chars:
            if char is not None and char is not self and getattr(char, '_force_switch_me', False):
                return SwitchPriority.NO
        return super().get_switch_priority(current_char, has_intro, target_low_con)

    def _find_teammate(self, class_name):
        # Workshop classes are loaded standalone, so isinstance() against src.char.* never matches.
        for char in self.task.chars:
            if char is not None and char.__class__.__name__ == class_name:
                return char
        return None

    def _force_switch_to(self, target, mode):
        if target is None:
            self._raw_logger.warning(f'[{self._node.upper()}] fallback: framework_switch reason=teammate_missing')
            return self.switch_next_char()
        target._entry_mode = mode
        for char in self.task.chars:
            if char is not None:
                char._force_switch_me = char is target
        try:
            return self.switch_next_char()
        finally:
            for char in self.task.chars:
                if char is not None:
                    char._force_switch_me = False

    # ---------------- 分发器 ----------------
    def _mark_startup_done(self):
        for char in self.task.chars:
            if char is not None:
                char._startup_done = True

    def do_perform(self):
        mode = self._entry_mode
        self._entry_mode = None
        if mode is None:
            if not self.started:
                mode = 'f1'
            elif self._startup_done:
                mode = 's1'
            else:
                self._trace(None, 'interrupt', reason='startup_in_progress', next='framework')
                return self.switch_next_char()
            entry = 'intro' if self.has_intro else 'natural'
        else:
            entry = 'forced'
        if mode.startswith('s'):
            self._mark_startup_done()
        self.started = True
        func = getattr(self, f'perform_{mode}', None)
        if func is None:
            self._trace(mode, 'interrupt', reason='unknown_mode', next='framework')
            return self.switch_next_char()
        self._node = mode
        self._trace(mode, 'enter', mode=entry)
        return func()

    # ---------------- 日志 ----------------
    def _trace(self, tag, event, ok=None, reason=None, **data):
        """Write one template line: [TAG] event[: ok|fail] [reason=code] [key=value ...]."""
        try:
            line = f'[{tag.upper()}] {event}' if tag else event
            if ok is not None:
                line += ': ok' if ok else ': fail'
            if reason:
                line += f' reason={reason}'
            for key, value in data.items():
                line += f' {key}={_fmt_value(key, value)}'
            self._raw_logger.info(line)
        except Exception:
            pass

    # ---------------- 节点：f = 启动轴，s = 循环轴（薄包装，最后一句保持字面写法） ----------------
    def perform_f1(self):
        self._action_opener('f1', 'Beta.f1')
        self._force_switch_to(self._find_teammate('Beta'), 'f1')

    def perform_f2(self):
        self._action_burst('f2', 'Gamma.f2')
        self._force_switch_to(self._find_teammate('Gamma'), 'f2')

    def perform_s1(self):
        self._action_burst('s1', 'Beta.s1')
        self._force_switch_to(self._find_teammate('Beta'), 's1')

    # ---------------- 动作体（f/s 共用；tag = 日志节点，nxt = exit 行去向） ----------------
    def _action_opener(self, tag, nxt):
        if self.has_intro:
            self.wait_down()
        clicked = self.click_resonance(time_out=1.0)[0]
        self._trace(tag, 'cast E', ok=clicked, reason=None if clicked else 'not_ready')
        self._trace(tag, 'exit', reason='done', next=nxt)

    def _action_burst(self, tag, nxt):
        if self.has_intro:
            self.wait_down()
        self.continues_normal_attack(1.2)
        self._trace(tag, 'exit', reason='done', next=nxt)
```

**和今弗坎原版的差别**

这些差别都是按 6-x 的结论改的：

- 日志改成英文模板；`_FilteredLogger` 改为 info 降级（`_InfoAsDebug`），并加了作用域过滤器；
- logger 包装从 `__init__` 赋值改为类上的 property。原版的写法会被 CharFactory 覆盖，实际没有生效（第 1 节“实例替换”）；
- 交场时不再读协奏（6-7）；
- `exit` 行由动作体用 `nxt` 输出；`_force_switch_to` 只在找不到队友时打 `fallback`；
- 自然入场的 enter 行带 `mode=intro|natural`，强切入场带 `mode=forced`。

## 8. 交场链自检

6-5：使用 [templates/verify_chain.py](../templates/verify_chain.py)。

1. 把它复制到队伍目录（不打进 zip）。
2. 填写：
   - `FILES`：三个类名；
   - `EXPECTED`：每条交接边 `(源类, 源mode, 目标类, 目标mode)`；
   - `STARTUP_END`：唯一的 f→s 边；
   - `PENDING`：尚未实现的端点，可以留空。
3. 运行 `python verify_chain.py [队伍目录]`。不传目录时，默认使用脚本所在目录。退出码 0 表示通过，1 表示不一致。

脚本用 AST 扫描每个 `perform_*` 里的 `_force_switch_to(self._find_teammate('X'), 'mode')`，检查以下各项：

- `EXPECTED` 的每条边都存在；
- 没有多余的边；
- f→s 的边只有一条，并且等于 `STARTUP_END`；
- 从 s 节点出发的边和 `EXPECTED` 里的对应边逐条一致；
- s 族首尾闭环：每个有 s 入边的节点都有 s 出边；
- 每个目标 `perform_<mode>` 都存在。

**要求**：

- 每次重新打包前都要跑一遍。
- 新增断言后，先**故意改错一条边**，确认退出码为 1，证明这条断言真能拦住错误。

起因：2026-09-11 实测发现，某个节点交场时用错了 mode，结果整圈一直在重复 f1，后续节点一次都没被调用。当时只有“目标方法存在”的检查，查不出这类接线错误。

## 9. 可选案例

6-8：以下两处覆写来自今弗坎这一队实测后的裁定。它们改变了框架的脱战判定或处决行为，**不属于骨架**，其他队按需评估。

### 9a skip_combat_check：队伍界面 5 秒保持窗口

- **起因**（今弗坎第 57 轮，2026-09-20）：交场链中途出现过 `target lost try retarget 3` → `combat check not in combat`，整场战斗被中断。大招演出（实测 3.35 秒）之后紧跟切人特写（2～3 秒），这段时间里框架找不到目标。用户要求判据不和任何技能挂钩，只用 `in_team` 当证据。
- **做法**：
  - 覆写 `skip_combat_check()`；
  - `task.in_team()[0]` 为真时，刷新共享时间戳（挂在 `self.task` 上，三人共用），并返回 True；
  - 读不到时，距上次读到不足 `HUD_GRACE = 5.0` 秒，仍返回 True；
  - 连续 5 秒读不到才返回 False，把判定交还框架；每次交还只打一条 `interrupt reason=out_of_combat`，再次读到队伍后重置；
  - 从没读到过队伍时，以首次调用的时刻起算，同样先给 5 秒窗口。今弗坎原版的注释写的是“首次调用只起算，不直接放行”，但代码起算后紧接着做窗口判断，实际返回 True。
- **原理**：`in_team()` 在收场和切人特写时都读成 False，所以它只能作为正向证据。读不到不构成结论，靠保持窗口把短暂的读不到吃掉。
- **代价**：真正收场时，脱战判定会多等约 5 秒，之后才轮到框架自己的检查。

### 9b f_break：只放行显式 force

- **起因**：沿用同作者之前的工坊队“弗坎嘉 v1”，三人都把 `f_break` 覆写成恒 `False`，切人前不自动按 F 处决。框架 `BaseChar.f_break` 的注释写明：击破动画带全局时停，目前无法识别，可能出现计时问题。今弗坎第 49 轮（2026-09-14）改为放行动作体里显式写 `force=True` 的那一次调用。
- **做法**：

  ```python
  def f_break(self, check_f_on_switch=False, force=False):
      if force:
          return self.task.f_break()
      return False
  ```

- **注意**：
  - `task.f_break()`（`CombatCheck.py:96`）内部还会再判断一次 `can_break or check_f_break()`，没命中就不会硬按 F。命中时会连按 F 加左键：至少 0.5 秒，图标还在的话最长 5 秒。
  - 和基类 `f_break(force=True)` 不同：基类会先无条件补按一次 F（`BaseChar.py:1008-1009`），这个覆写不补按。

## 10. 交付前检查

- [ ] 三个 `.py` 都能 `py_compile`。
- [ ] 每个类都带完整的协议（6-3）：`__init__` 字段、拦截、`_find_teammate`、`_force_switch_to`。
- [ ] `verify_chain.py` 返回 PASS；新增断言做过变异测试（6-5）。
- [ ] zip 内容恰好是 `team.json` 加 3 个 `.py`；`team.json` 的 `team` 按字母序排列（第 1 节）。
- [ ] 交付说明里标出自实现的部分（工坊模式要求）。
