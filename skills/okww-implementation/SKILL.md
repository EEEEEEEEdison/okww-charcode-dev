---
name: okww-implementation
description: ok-ww 开发的代码实现阶段。用于从通过 G2 的时序模型生成工坊角色代码，或按明确依据局部修改 BaseChar 子类；复用框架函数，落实触发、完成、切人和等待判据，记录实现假设。
---

# 代码实现

## 输入

通过 G2 的 `timeline.json`，或有明确依据的局部修改任务。

## 执行

1. 读取 [总入口](../../SKILL.md) 和 [rules.md](../../rules.md)。
2. 读取涉及角色的语义卡和 [代码基线](../../harness/baseline.md)。
3. 整队生成按 [step2.md §1–6](../../harness/step2.md) 实现。
4. 局部修改检查直接调用者，核对函数判据和副作用。
5. 按 [evidence.md §5](../../harness/evidence.md) 记录实现与假设。

## 输出与通过条件

- 候选代码实现已确认的动作、依赖和切人要求。
- 工坊循环轴有对应的 `verify_chain.py`。
- 等待、按住和退出均能追溯到模型或修改依据。
- 新增判据及待测项已列出验证办法。
- 参考耗时与超时保护已分别处理。

关键行为仍不明确时，退回 [轴解析](../okww-rotation/SKILL.md) 或 [时序建模](../okww-timeline/SKILL.md)。
通过后进入 [验证交付](../okww-delivery/SKILL.md)。
