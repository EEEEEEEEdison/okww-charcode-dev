---
name: iteration
description: okwwcharcode（ok-ww 角色代码开发）的实测迭代阶段。用于核对实际代码版本与运行条件，对照日志、参考视频和实测录屏，比较动作、触发、协奏切人、整轮及节点耗时；定位根因并验证下一版或记录未验证项。
---

> If the Chinese text below looks garbled (replacement characters or unrelated symbols), read this SKILL.md with a file-read tool and follow that copy.

# 实测迭代

## 输入

可定位到代码版本的日志或录屏，以及该版模型和待测项。

## 执行

1. 读取 [总入口](../../SKILL.md) 和 [iterate.md](../../harness/iterate.md)。
2. 按 [evidence.md](../../harness/evidence.md) 核对运行条件与证据。
3. 读取 [日志 Skill](../logging/SKILL.md)，用 `wait` 行和 probe 行定位卡点。
4. 按 [timing.md](../../harness/timing.md) 比较参考与实测耗时。
5. 解释偏差，按根因选择退回阶段。
6. 按 iterate.md §5–6 更新案例证据和验收状态。

## 输出与通过条件

- 动作、触发、切人和时间差异有证据或明确缺项。
- 本段差值与累计差值已分别记录。
- 根因结论区分观测、解释和待验证假设。
- 新版本的改动目标和验证办法可复查。
- 已查清问题的 probe 行在新版本删除。
- 完成声明满足 iterate.md §6；缺视频时写明验证限制。

来源缺失或片段不可读时，退回 [素材获取](../materials/SKILL.md)。
意图错误退回 [轴解析](../rotation/SKILL.md)。
测量或模型错误退回 [时序建模](../timeline/SKILL.md)。
实现错误退回 [代码实现](../implementation/SKILL.md)。
复验与打包交给 [验证交付](../delivery/SKILL.md)。

进入、退回或交给其他阶段时，按 [总入口的阶段切换](../../SKILL.md#阶段切换) 加载。
