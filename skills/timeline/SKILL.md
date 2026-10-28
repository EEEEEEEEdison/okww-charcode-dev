---
name: timeline
description: okwwcharcode（ok-ww 角色代码开发）的时序建模阶段。用于把已确认的轴对应到视频事件，建立节点链、动作条件、切人状态和参考耗时表；检查阻断项及 G2，输出可用于实现和实测比较的 timeline.json。
---

# 时序建模

## 输入

G1 确认、动作解释、代码基线、素材和问题清单。

## 执行

1. 读取 [总入口](../../SKILL.md) 和 [evidence.md](../../guides/evidence.md)。
2. 按 [step1.md §4–5、§7–8](../../guides/step1.md) 建立事件与节点。
3. 按 [timing.md](../../guides/timing.md) 整理参考耗时。
4. 按 [timeline.md](../../guides/timeline.md) 维护字段并检查 G2。
5. 按 evidence.md §5 更新阶段交接。

## 输出与通过条件

- `timeline.json` 记录动作判据、切人类型和跨步依赖。
- 整轮、节点和关键动作段有参考记录或测量缺项。
- 每个时长能追溯起止事件、口径和原始观察。
- G2 已逐项检查，阻断项已解决。
- 试验假设和未验证内容已交给实现与实测阶段。

动作解释有误时，退回 [轴解析](../rotation/SKILL.md)。
缺少可用画面时，退回 [素材获取](../materials/SKILL.md)。
通过后进入 [代码实现](../implementation/SKILL.md)。

进入、退回或交给其他阶段时，按 [总入口的阶段切换](../../SKILL.md#阶段切换) 加载。
