# task API 参考（`self.task.*`）

**基线**

| 类 | 文件 | 版本 |
|---|---|---|
| `BaseCombatTask` | `src/task/BaseCombatTask.py` | 上游 `2243d465` |
| `CombatCheck` | `src/combat/CombatCheck.py` | 上游 `2243d465` |
| `BaseWWTask` | `src/task/BaseWWTask.py` | 上游 `2243d465` |
| `ExecutorOperation` / `FindFeature` / `BaseTask` | `ok/task/task.py` | ok-script `v2.0.8` |
| `TaskExecutor` | `ok/task/TaskExecutor.py` | ok-script `v2.0.8` |

继承链：`BaseCombatTask` → `CombatCheck` → `BaseWWTask` → ok-script `BaseTask`，`BaseTask` 再混入 `ExecutorOperation` / `FindFeature`。

**调用频次**：括号里的“N 次 / M 文件”是 `self.task.<name>` 在上游 `src/char/*.py` 中出现的统计。

能用 BaseChar 包装的就用包装：

- `self.sleep` 而不是 `self.task.sleep`；
- `self.click` 而不是 `self.task.click`；
- `self.check_combat`；
- `self.time_elapsed_accounting_for_freeze`。

只有 BaseChar 没有包装的能力，才直接用 `self.task.*`。

## 目录

- [等待与帧](#等待与帧)
- [输入：点击、按键、按住](#输入)
- [画面识别](#画面识别)
- [队伍与战斗状态](#队伍与战斗状态)
- [战斗检查与异常](#战斗检查与异常)
- [CD 与冻结](#cd-与冻结)
- [杂项属性](#杂项属性)

---

## 等待与帧

### wait_until(condition, time_out=0, pre_action=None, post_action=None, settle_time=-1, raise_if_not_found=False)

位置：`task.py:508` → `TaskExecutor.wait_condition`（`TaskExecutor.py:409`）。调用频次：61 次 / 23 文件。

**每一轮依次执行**：

1. `pre_action()`；
2. `next_frame()`：抓新帧，并检查任务是否被禁用；
3. `condition()`。为真就返回结果，或者进入 settle；为假就重置 settle 计时；
4. 条件为假时执行 `post_action()`；
5. 超时检查。

**参数含义**：

| 参数 | 含义 |
|---|---|
| `time_out=0` | 使用 `wait_scene_timeout`，ok-ww 未配置时为 **10 秒** |
| `settle_time=-1` | 使用 `wait_until_settle_time`。ok-ww `config.py:181` 设为 `0`，所以默认**不做 settle**：条件第一次为真就返回 |
| `settle_time>0` | 条件要**连续**为真超过这个时长才返回。settle 期间直接 `continue`，不执行 `post_action`，也不检查超时 |

**返回**：条件的结果（真值），超时返回 `None`。超时还会打一行 info：`wait_until timeout <condition> N seconds`。

**注意**：它**自身不做战斗检查**，抓帧也不会检查是否脱战。等待时间长时要传 `pre_action=self.check_combat`（2-4）。

相关规则：2-2、2-3、2-4、1-6、5-3。

### next_frame()

位置：`task.py:531` → `TaskExecutor.next_frame(time_out=6)`（`TaskExecutor.py:250`）。调用频次：60 次 / 24 文件。

- 先清空场景缓存，抓一帧新画面；
- 只检查 `check_enabled`（任务是否被禁用或暂停），**不做战斗检查**；
- 手写循环里每轮至少调用它或 `self.sleep`（2-9），否则识别函数会反复读同一帧。

### frame（property）

位置：`task.py:545` → `TaskExecutor.frame`。调用频次：14 次 / 10 文件。

当前帧（numpy BGR）。没有帧时会先调用 `next_frame()`。

### sleep(timeout)

`BaseWWTask.py:675`：`super().sleep(timeout - self.check_for_monthly_card())`。

角色代码用 `self.sleep(sec, check_combat=True)`。行为见 basechar-api.md。

---

## 输入

### click(x=-1, y=-1, move_back=False, name=None, interval=-1, move=False, down_time=0.01, after_sleep=0, key='left')

位置：`BaseWWTask.py:347`，覆写了 `task.py:140`。调用频次：21 次 / 9 文件。

- **不带坐标**：点屏幕中心，`down_time=0.01`，即普攻；
- **带坐标**：`down_time` 被改成 0.2；
- `interval>0`：通过 `check_interval`（`task.py:188`）节流。它和 `send_key` 共用同一个 `last_click_time`，被节流掉时返回 False，并且同样清空场景缓存（1-8）；
- 点击后会 `reset_scene()`，紧接着的识别会重新截图。

### send_key(key, down_time=0.02, interval=-1, after_sleep=0)

位置：`task.py:463`。调用频次：16 次 / 8 文件。

- 发一次键。`interval` 的语义和 `click` 相同，共用节流时间戳；
- 发送前会 `reset_scene()`；
- 技能键一律用 `self.get_*_key()` 取，不写死（1-2）；
- 长按例子：`self.task.send_key(self.get_resonance_key(), down_time=1.2)`（`Chisa.py:90`）。

### send_key_down(key, after_sleep=0) / send_key_up(key, after_sleep=0)

位置：`task.py:494` / `:501`。调用频次：各 9 次 / 9 文件。

按下与松开分开发送。手写按住必须放进 try/finally，在 finally 里 `send_key_up`（5-4）。

### mouse_down(x=-1, y=-1, name=None, key='left') / mouse_up(name=None, key='left')

位置：`task.py:206` / `:214`。调用频次：26 / 31 次，19 文件。

鼠标按住与松开，要求同上（5-4）。上游例子：

- `Hsin.py:82-86`：`mouse_down` → `try: wait_until(...) finally: mouse_up`；
- `Lucilla.py:126-130`、`Lucilla.py:147-151`：按键或鼠标按住的 try/finally 写法。

### jump(after_sleep=0.01)

位置：`BaseWWTask.py:1243`。调用频次：14 次 / 10 文件。

用用户配置的 `Jump Key` 跳跃。

### middle_click_relative(x, y, move_back=False, down_time=0.01)

位置：`task.py:386`。中键点击（锁定目标）。

---

## 画面识别

### box_of_screen_scaled(original_screen_width, original_screen_height, x_original, y_original, to_x=0, to_y=0, width_original=0, height_original=0, name=None, hcenter=False, vcenter=False, confidence=1.0)

位置：`task.py:346`。调用频次：23 次 / 13 文件。

- 按参考分辨率（ok-ww 统一用 `3840, 2160`）给出坐标，换算成当前分辨率下的 `Box`；
- `hcenter=True`：位于 HUD 水平居中区域，在超宽屏上按中心对齐，技能栏、协奏环都这么设置；
- 例子：`self.task.box_of_screen_scaled(3840, 2160, 2251, 1993, 2311, 2016, name='forte_full', hcenter=True)`（`BaseChar.py:790`）。

### calculate_color_percentage(color, box)

位置：`task.py:555`。调用频次：17 次 / 9 文件。

- 返回 `box` 内符合 `color` 范围的像素占比（0~1）；
- `box` 可以是 `Box`，也可以是已注册的 box 名；
- 会把结果写进 `box.confidence` 并绘制 debug 框。

颜色字典格式：`{'r': (lo, hi), 'g': (lo, hi), 'b': (lo, hi)}`。框架已有的颜色：

| 颜色 | 来源 |
|---|---|
| `text_white_color` | `from src import text_white_color` |
| `forte_white_color` | `from src.char.BaseChar import forte_white_color` |

### get_box_by_name(name)

位置：`task.py:610`。调用频次：9 次 / 5 文件。

取已注册的 HUD 区域，例如 `'box_resonance'`、`'box_echo'`、`'box_liberation'`、`'box_char_1'`、`'edge_levitator'`。

### find_one(feature_name=None, horizontal_variance=0, vertical_variance=0, threshold=0, use_gray_scale=False, box=None, canny_lower=0, canny_higher=0, frame_processor=None, template=None, mask_function=None, frame=None, match_method=cv2.TM_CCOEFF_NORMED, screenshot=False, limit=1, target_height=0)

位置：`task.py:684`。调用频次：46 次 / 14 文件。

- 模板匹配，返回命中的 `Box` 或 `None`；
- `feature_name` 是 `assets/coco_annotations.json` 里登记的模板名，例如 `'mouse_forte'`、`Labels.hsin_h2`；
- `template=` 可以直接传 numpy 模板（见 `Cartethyia.py:192`）；
- 工坊代码只能用项目里**已有**的模板名，或者在代码里现场构造的 `template`（5-5）。

### find_best_match_in_box(box, to_find, threshold, ...) / find_feature(...)

位置：`task.py:706` / `:585`。

- `find_best_match_in_box`：在多个模板里取最佳的一个；
- `find_feature`：返回全部命中。

### draw_boxes(feature_name=None, boxes=None, color='red', debug=True) / screenshot(name=None, ...)

位置：`task.py:549` / `:283`。只用于调试：

- `draw_boxes`：在调试叠加层上画框；
- `screenshot`：保存截图（debug 模式下）。

---

## 队伍与战斗状态

### in_team() → (in_team: bool, current_index: int, count: int)

位置：`BaseWWTask.py:930`。调用频次：22 次 / 9 文件。

- 在底部 3 个头像位找 `char_N_text` 模板，阈值 0.8；
- **在场角色那一格没有文字**，所以“没找到的那一格”就是 `current_index`；
- 命中 1~2 个时 `in_team=True`；否则返回 `(False, -1, …)`；
- **大招、E 演出期间返回 False**，这是 `click_liberation` 确认演出的依据；
- 收场特写、切人特写同样读成 False，所以只能作为“仍在队伍界面”的正向证据（工坊 `skip_combat_check` 案例）。

### in_team_and_world() / wait_in_team_and_world(time_out=10, raise_if_not_found=True, esc=False)

位置：`BaseWWTask.py:796` / `:678`。

- `in_team_and_world()` 等于 `in_team()[0]`；
- `wait_in_team_and_world` 等到它为真后再 sleep 0.5。

### chars（属性）/ has_char(char_cls) / get_current_char(raise_exception=False)

- `chars`：长度 2~3 的角色实例列表，可能含 `None`。调用频次：14 次 / 11 文件。
- `has_char(char_cls)`：`BaseCombatTask.py:837`，用 `isinstance` 判断。**直接继承 `BaseChar` 的工坊类和内置类没有继承关系，用 isinstance 判断不到**，要按类名查找（workshop.md 的 `_find_teammate`）。
- `get_current_char(raise_exception=False)`：`BaseCombatTask.py:741`，返回 `is_current_char` 为真的那个角色。

### load_chars()

位置：`BaseCombatTask.py:842`。

- 从屏幕重新识别队伍，并对每个角色调用 `reset_state()`，同时重置 `combat_start`；
- 进入战斗时，以及队伍变化时调用；
- 战斗中如果被重新调用，角色的每场状态会被清掉。

### combat_start（属性）

本场战斗开始时间，在 `load_chars` 中写入。`is_first_engage()` 用它判断首发。

### has_lavitator（属性）

进战时检测是否装备了控物（`edge_levitator` 模板）。`flying()` 和 `wait_down()` 依赖它。

### is_open_world_auto_combat()

位置：`BaseWWTask.py:49`。是否为大世界自动战斗（不在副本中）。

### use_liberation（属性）

来自 `AutoCombatTask` 的配置 `Use Liberation`，只在大世界生效。为 False 时 `click_liberation` 直接返回 False。

---

## 战斗检查与异常

### 异常

位置：`BaseCombatTask.py:22-35`。

| 异常 | 含义 |
|---|---|
| `NotInCombatException` | 脱战 |
| `CharDeadException(NotInCombatException)` | 角色死亡 |
| `CharRevivedException(CharDeadException)` | 复活成功，非自动战斗任务使用 |

**处理方式**：`AutoCombatTask.run`（`AutoCombatTask.py:48-75`）捕获这些异常后 `break`，再调用 `combat_end()`，后者会对全队调用 `on_combat_end` 和 `reset_state`。

5-6：角色代码不捕获异常，让它们一路抛上去。

### check_combat()

位置：`BaseCombatTask.py:796`。

- `skip_combat_check` 为真时直接返回；
- 否则，在已进战（`_in_combat`）但 `in_combat()` 为假时，`raise_not_in_combat('combat check not in combat')`。

返回值是 `None`，所以不能放进 `wait_until` 的条件函数里（2-4）。

### in_combat()

位置：`CombatCheck.py:185` → `do_check_in_combat`（`:139`）。已进战时按以下顺序判断：

1. `in_liberation` 为真：**直接返回在战斗中**。
2. 场景缓存命中：直接返回缓存结果。
3. 调用 `check_f_break()`，检查是否可以处决。
4. 当前角色 `skip_combat_check()` 为真：视为在战斗中。
5. 有目标：在战斗中。
6. 结束条件已满足：判为脱战。
7. `target_enemy(wait=True)` 重新锁定：成功则在战斗中。
8. 否则打 error `target_enemy failed ...` 并 `reset_to_false`，判为脱战。

### raise_not_in_combat(message)

位置：`BaseCombatTask.py:310`。

- 先打 **error** `message`；
- 再检查是否弹出复活框，据此决定抛 `CharDeadException` / `CharRevivedException` 还是 `NotInCombatException`。

框架内部用它中断战斗，角色代码一般不需要调用。

### skip_combat_check（属性）

为 True 时，`check_combat` 和 `sleep_check` 都直接返回。

`self.sleep(sec, check_combat=False)` 就是靠它实现的：sleep 期间置 True，结束后复位。不要手动长时间置 True。

### in_liberation（属性，带 setter）

位置：`CombatCheck.py:46`。

- 为 True 时，`in_combat()` 直接视为在战斗中，所以演出期间不会因为看不到目标而判脱战。
- 写入它的地方：
  - 框架：`click_liberation` 和 `click_resonance(has_animation=True)` 在演出期间置 True，结束后复位；切人成功后也会复位；
  - 上游角色：手写演出等待时，自己置 True / False，例如 `Augusta.py:73`、`Hiyuki.py:171-174`、`Jinhsi.py:50-72`。
- 置 True 后一定要复位，否则会一直判定为在战斗中。

### sleep_check_interval（属性）

值为 `0.4`（`CombatCheck.py:26`）。`executor.sleep` 每过这么久，就抓帧并调用 `sleep_check()` 一次。

---

## CD 与冻结

### has_cd(box_name, char_index=None) / get_cd(box_name, char_index=None) / refresh_cd()

位置：`BaseCombatTask.py:730` / `:192` / `:156`。

- `refresh_cd()`：每个场景（帧）最多执行一次。它 OCR 技能栏的 3 个 CD 数字，存进 `cds[当前角色 index]`，并带上时间戳。
- `get_cd()`：返回存下的 CD 减去扣冻结后的经过时间。查询不在场角色时（传入 `char_index`），用的就是这份推算值。
- `has_cd()`：等于 `get_cd() > 0.2`。

调用者：

- 角色侧 `self.has_cd(name)` 只查当前角色；
- `available()` 查不在场角色时传入 `index`。

L-8：它会触发 OCR，不要为了打日志去调用它。

### available(name, check_color=True, check_cd=True) / box_highlighted(name)

位置：`BaseCombatTask.py:350` / `:366`。

- `box_highlighted`：`box_{name}` 的白色像素比大于 0 时返回 1，否则返回 0；
- `available`：图标亮，并且（不查 CD，或者没有 CD）。

角色侧用 `self.*_available()` 调用（见 basechar-api.md）。

### add_freeze_duration(start, duration=-1.0, freeze_time=0.1) / time_elapsed_accounting_for_freeze(start, intro_motion_freeze=False)

位置：`BaseCombatTask.py:85` / `:100`。见 basechar-api.md 的“等待与计时”。

### get_current_con() / is_con_full()

位置：`BaseCombatTask.py:972` / `:934`。

task 侧**不写** `char.current_con`。角色代码用 `self.get_current_con()` / `self.is_con_full()`，区别见 basechar-api.md 的“资源”和规则 4-3。

### find_mouse_forte() / find_e_forte()

位置：`BaseCombatTask.py:690` / `:694`。对应 `is_mouse_forte_full()` / `is_e_forte_full()`。

---

## 杂项属性

| 名称 | 说明 |
|---|---|
| `key_config` | 用户键位 dict，例如 `'Jump Key'`、`'Tool Key'`、`'Resonance Key'` |
| `debug`（property） | 是否为 debug 模式（`main_debug`） |
| `executor` | ok-script `TaskExecutor`；`executor.current_task` 是当前正在运行的任务 |
| `log_error(message, exception=None, notify=False, ...)` / `log_info` | 任务级日志，会显示在 GUI 中。**角色代码用 `self.logger`**，不用这两个 |
| `info_set(key, value)` | 往 GUI 信息面板写值 |
| `char_config` | 角色配置 |
| `f_break()` / `check_f_break()` / `can_break` | 处决检测与执行（`CombatCheck.py:81-103`） |
| `get_target_names()` | 有目标 / 无目标模板名，会按云游戏和 1600 宽度调整 |
