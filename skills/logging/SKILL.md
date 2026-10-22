---
name: logging
description: okwwcharcode 的日志 Skill：ok-ww 角色代码的游戏内日志写法与检查。用于给角色代码或工坊循环轴写 logger / _trace 日志行，选事件、字段、reason 与 info/debug/warning 级别；在长等待前打 wait 行定位卡点；按需加 probe 取证行并在问题查清后删除；交付前用 check_logs.py 检查日志模板、字段词表、耗时字段和不额外读状态。适用于日志模板、字段词表、reason 词表、耗时字段、降级过滤、卡点定位、取证行。
---

# 日志

单独写或改日志时，可直接调用本 Skill。其他阶段宜读取本文件，不宜调用。

## 输入

要写或要改日志的角色代码，以及它所属的模式：内置或工坊；工坊模式下是否为循环轴。

## 执行

1. 读取 [logging.md](../../references/logging.md)。工坊循环轴另读 [workshop.md §6](../../references/workshop.md)。
2. 按 L-3 列出每个节点必打的行：`enter`、`decide`、`cast X: ok|fail`、`fallback`、`exit`、`interrupt`。
3. 上限 ≥2s 的条件等待前加 `wait` 行。
4. 只能发键、没有确认信号的技能写 `send`，不写 ok/fail。
5. 判断用到的值先存进变量，判断和日志行共用这个变量（L-8）。
6. 动作内耗时按 L-5 用 `time.time()` 之差写 `_s` 字段。
7. 需要的事件、字段或 reason 不在词表时，记进本版 README 的新词表并写明含义。维护本仓库时再补进 logging.md。
8. 为查问题加的行写成 `probe`（L-11）。问题查清后的下一版删掉。
9. 交付前对本次改动的角色文件运行检查：

   ```text
   <ok-ww python.exe> -I -B scripts/check_logs.py <角色 .py> [<角色 .py> ...]
   ```

## 输出与通过条件

- 每个节点的必打行齐全，级别符合 L-1。
- `check_logs.py` 报 0 条问题。剩下的问题在 README 逐条写明原因。
- README 列出本版开着的 probe 行和各自要回答的问题。
- 手写轮询循环不在检查范围内，人工确认循环前有 `wait` 行。

实测迭代时，先按 `wait` 行和 probe 行定位卡点，再看录屏。
