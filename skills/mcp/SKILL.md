---
name: mcp
description: okwwcharcode 的 MCP 自动实测 Skill：通过 ok-ww MCP 的 run_task 提交仓库 templates/mcp 的 Task 模板，全自动完成一局实测并取证。流程包括登录回大世界、导入工坊 zip 并核对代码生效。随后导航到终焉矩阵编队详情页，核对编队与开场角色。再交互回音之钥开战、锁敌、自动战斗并实时录像。结算页不保存成绩。用 mcp_report.py 汇总日志，并给每个问题行配录像帧。适用于 run_task、自动实测、终焉矩阵、重新挑战、战斗逻辑排错、证据采集和自主迭代。不提供 MCP 安装或连接配置教程。
---

# MCP 自动实测

直接测试已有代码时，可从本 Skill 进入。
其他阶段宜读取本文件，不宜调用，以保留当前阶段。

## 输入

- 待测代码：已装队伍，或待导入的工坊 zip。
- 队伍 3 个类名、开场角色、矩阵模式和队伍槽位。
- 本机 `working` 目录和 Python 路径，见工作区的 `okwwcharcode.local.md`。
- 本轮测试目标、运行局数上限和停止条件。

已有日志、录像或报告能回答测试目标时，不必重新实测。

## 执行

1. 读取 [总入口](../../SKILL.md) 和 [实测操作指引](../../references/mcp-testing.md)。
2. 按指引 §2 检查 MCP 连接，读取 ok-ww 内置的 `develop` 技能。
3. 按指引 §3 把 `templates/mcp/` 复制到 `<工作区>/<队名>/media/mcp/`，填写 `mcp_test.json`。
4. 按指引 §4 依次运行 `preflight.py`、`team_import.py`、`matrix_nav.py` 和 `matrix_run.py`。
5. 用 `scripts/mcp_report.py --frames` 生成报告，按指引 §6 判读。
6. 把报告和结论交给 [实测迭代](../iteration/SKILL.md)。

## 内置技能

按 `list_skills()` 的当前结果选用，不得依赖固定清单。

| 当前任务 | 内置技能 |
|---|---|
| 写 Task、核对框架 API | `develop` |
| 修改 ok-ww 已注册任务后运行 | `reload-tasks` |
| 写测试 | `write-test` |

内置技能不含导航、开战和取证。
这些步骤用本仓库的模板，不得复制内置战斗逻辑另写执行器。

## 使用边界

- MCP 不可用时，记录缺口；不得把连接配置教程加入本流程。
- MCP 连接可用不表示已获游戏操作授权。沿用已有授权，不重复审批。
- 消耗结晶单质和覆盖已装队伍代码前，必须已有用户授权。
- `save_result` 必须保持 `false`，用户要求保存成绩时除外。
- 只测试时，不得修改角色逻辑、配装或战斗配置。
- 重启 ok-ww 需要用户以管理员身份启动，见指引 §7。
- 外来工坊代码的运行边界沿用 [evidence.md](../../guides/evidence.md)。

## 输出与通过条件

- 每局的 `run_id`、运行目录、代码 sha256 和 `report.md` 可复查。
- 任务成功、进入战斗、代码生效和战斗行为分别判定。
- 已回答测试目标，或写明阻断原因和未验证项。
- 测试结束时游戏停在编队详情页或大世界，矩阵原记录未被覆盖。

改代码进入 [代码实现](../implementation/SKILL.md)。
打包与静态检查由 [验证交付](../delivery/SKILL.md) 负责。
