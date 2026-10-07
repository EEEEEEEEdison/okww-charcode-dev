# 步骤 2：由时序数据生成角色代码

前提：关口 G2 全部通过（[timeline.md](timeline.md) §3）。

代码遵守 [../rules.md](../rules.md)。骨架和日志的完整写法见 [../references/workshop.md](../references/workshop.md) 和 [../references/logging.md](../references/logging.md)，函数签名查 [../references/basechar-api.md](../references/basechar-api.md) 和 [../references/task-api.md](../references/task-api.md)。

## 1 目标代码形式

- 工坊循环轴骨架：3 个直接继承 `BaseChar` 的类，按 f/s 节点组织成状态机（rules.md 第 6 组）。
- 每个文件带同一套协议和日志 helper，内容逐字一致（workshop.md）。
- 动作体里只用框架里已有的函数（BaseChar、`self.task.*`），以及本文件里自己定义的 helper。不引入 DSL。

## 2 节点映射

- timeline 的一个节点生成一对方法：
  - `perform_<f|s><序号>()`：薄包装；
  - `_action_<名字>(tag, nxt)`：动作体。

  几个节点的动作完全相同时，可以共用同一个 `_action_`。
- 薄包装的最后一行固定写成 `self._force_switch_to(self._find_teammate('<下一个类名>'), '<下一个节点的模式>')`（rules.md 6-2）。
- 分发器、`_entry_mode`、`_startup_done`、`reset_state` 照骨架原样写（6-4）。
- 每个节点上方用注释写明它对应文字轴的哪一行，以及视频区间。

## 3 记号到代码

| 记号 | 生成的代码 |
|---|---|
| E 单击 | `self.click_resonance(time_out=<正数>)`（1-1、1-4） |
| E/Q 长按 | `self.task.send_key(self.get_resonance_key(), down_time=<hold_s>)`，Q 用 `get_echo_key()`。然后用 `wait_until` 确认放出，按需调用 `record_*_use()`（1-2、1-3、5-3） |
| 多段 E/R、强化 E/R | 按语义卡逐段生成。放完不进冷却的那一段，用卡里写的图标变化或条件来确认，不要用"进入冷却"去确认 |
| R | `self.click_liberation(...)`（1-1、1-5） |
| Q | `self.click_echo(...)` 或 `self.send_echo_key()`，按 1-1 来选 |
| A 段 | `self.continues_normal_attack(<视频时长>)`。注释写"待专题：普攻段数，暂按视频时长" |
| Z | 消耗回路的重击用 `self.heavy_click_forte(...)`，固定时长的用 `self.heavy_attack(<时长>)`，具体看语义卡（4-2） |
| 闪 | `self.task.send_key(self.task.key_config.get('Dodge Key'))`。用用户设置的闪避键，不写死按键 |
| 跳 | `self.task.jump()` |
| ↓ | 协奏满了直接走出口切人。没满就普攻等协奏满（`continues_normal_attack(<时限>, until_con_full=True)`），超时也照样切人 |

- `timing: condition` 的步骤，用 `self.task.wait_until(<条件>, time_out=<时限>, ...)` 等条件成立，不用固定时长。
- 按住类操作（`mouse_down`、`send_key_down`）放进 try/finally，在 finally 里松开（5-4）。

## 4 时限与未就绪

- 所有等待都带时限：时限 = 视频里量到的时长 × 1.5，最少 1 秒。
- 超过 1 秒的等待，加 `pre_action=self.check_combat`（2-4）。
- 轴上该放某个技能但它还没就绪时，一边普攻一边等。超时就跳过这一步继续往下走，并打一条 fallback warning（rules.md L-1，reason 按 logging.md 的词表取）。
- 战斗结束、角色死亡等异常一律不捕获，让它抛给框架（5-6）。

## 5 日志

按 logging.md 和骨架写：
- 每个节点打 `enter` 和 `exit`；
- 每次放技能打 `cast X: ok|fail`；
- 有分支判断就打 `decide`；
- 走兜底时打 `fallback`；
- 框架的 info 降为 debug，任务层的切人行用过滤器去掉（6-6）。

## 6 verify_chain

把 [../templates/verify_chain.py](../templates/verify_chain.py) 复制到输出目录，按 timeline 的节点链填好 `FILES`、`EXPECTED`、`STARTUP_END`，然后运行并确认通过。再临时改错一条边，确认它会报错，最后改回去（6-5）。

## 7 自检清单

以下逐条确认，有一条不过就修改后重查，不能交付：

- [ ] 3 个文件都能编译：`python -I -B -m py_compile <文件>`。
- [ ] verify_chain 通过，变异测试也确实会报错。
- [ ] 用到的每个 `self.X()` 和 `self.task.X()`，都在 references 或上游源码里存在，或者是本文件自己定义的。
- [ ] 没有写死的按键字符串（1-2）。
- [ ] 没有 `time.sleep`（2-1）。
- [ ] 每个 `wait_until` 和 `click_resonance` 都传了正数 `time_out`（2-2、1-4）。
- [ ] 每个手写循环都有真实时间上限，并且每轮都调用 `self.sleep()` 或 `self.task.next_frame()`（2-9）。
- [ ] 没有会吞掉战斗异常的 except；日志 helper 除外（5-6）。
- [ ] 3 个文件里共用的协议和日志 helper 逐字一致（workshop.md）。
- [ ] 每个节点都打了 enter/exit；fallback 都用 warning；日志不另外读状态（L-3、L-8）。

## 8 打包交付

1. **先问用户** team.json 的四个字段：`name`、`description`、`author`、`version`。
2. **写输出目录** `E:\GameAutoScript\workspace\okww-test\ok-ww-char\<队名>\harness-v<N>\`，必须是新目录，已存在就把 N 加 1：
   - 3 个角色 `<类名>.py`；
   - `verify_chain.py`；
   - `team.json`。它的 `team` 字段用逗号分隔的英文显示名，按不区分大小写的字母序排列。显示名大多等于类名，例外以运行目录 `src/char/CustomCharLoader.py` 里的 `CHARACTER_DISPLAY_NAMES` 为准；
   - `README.md`，写清：
     - 交场链表；
     - 每个节点对应文字轴的哪一行和视频区间；
     - 用了临时方案或属于待专题的地方；
     - 未经验证的地方（尚未实测）；
     - 出处：视频、文字轴来源、本案 timeline 的路径。
3. **打 zip**：
   - 平铺结构，内容恰好是 `team.json` 加 3 个角色 `.py`，不放 verify_chain 和 README；
   - 文件名为 `<类名>_<类名>_<类名>_<author>_<version>.zip`，类名按 team 的顺序，放在输出目录里；
   - 同名文件已存在时不覆盖，请用户换一个版本号。
4. **校验 zip**：把运行目录 `E:\GameAutoScript\ok-ww\data\apps\ok-ww\working` 加进 `sys.path`，调用 `src.char.CustomCharLoader.inspect_team_archive(<zip路径>)`。不报错，并且返回的 `team` 是这 3 个角色，才算通过。在 scratchpad 里运行，避免在其他目录留下 `configs/`。
5. **交付说明**：告诉用户 zip 的路径、自检结果、待专题和未验证的地方，请用户实机测试，然后进入 [iterate.md](iterate.md)。
