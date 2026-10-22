---
name: okww-delivery
description: ok-ww 开发的验证交付阶段。用于定向语法检查、交场链验证、模型与代码核对、工坊 zip 打包及 inspect_team_archive 校验；检查包内外一致，交付 README、验证结果和待实测项。
---

# 验证交付

## 输入

候选代码、模型或修改依据、实现说明和待测项。

## 执行

1. 读取 [总入口](../../SKILL.md) 的产物位置要求。
2. 按 [step2.md §7](../../harness/step2.md) 检查候选代码。日志按 [日志 Skill](../okww-logging/SKILL.md) 检查。
3. 工坊交付按 step2.md §8 打包与校验。
4. 局部代码交付只运行改动目标的检查。
5. 按 [evidence.md §5](../../harness/evidence.md) 记录结果。

## 输出与通过条件

- 适用的静态检查已通过，并记录实际结果。
- 工坊 zip 的上游校验器输出 `OK`。
- 包内代码与本次声明的打包源逐字节一致。
- README 列出来源、参考耗时入口和未实测项。
- 局部任务记录不适用的整队检查及原因。

检查失败时，退回 [代码实现](../okww-implementation/SKILL.md)。
模型与代码不一致时，先核对模型依据。
交付后进入 [实测迭代](../okww-iteration/SKILL.md)。
静态通过后，动作效果和耗时仍按实测结果验收。
