---
name: okwwcharcode
description: okwwcharcode：ok-ww（ok-wuthering-waves，鸣潮自动战斗脚本）角色代码开发与实测 Skill 总入口。三种用法：按文字轴、教程视频从头制作工坊配队代码；提交 zip 只测稳定性；提交 zip 按 MCP 实测结果迭代。按任务选择 6 个阶段：materials 素材获取、rotation 轴解析、timeline 时序建模、implementation 代码实现、delivery 验证交付、iteration 实测迭代。mcp 通过 ok-ww MCP 全自动实测：回大世界、导入代码、导航到终焉矩阵、开战、录像和生成报告。logging 负责日志写法与检查。proposal 把实测发现整理成知识提议。适用于作战轴转代码、BaseChar、src/char、协奏切人和技能触发。支持循环轴、工坊代码、team.json、日志录像排错与测试结果分析。
---

# okwwcharcode

ok-ww 角色代码开发 Skill，可生成角色代码，也可直接测试现有代码。
按任务和已有产物选择阶段。
安装版本见 [VERSION](VERSION)，固定版本安装见 [README](README.md#安装)。

## 三种用法

| 用法 | 入口 | 迭代依据 |
|---|---|---|
| 从头制作 | [`materials`](skills/materials/SKILL.md) | 参考视频；MCP 报告作为参考 |
| 提交 zip 只测稳定性 | [`iteration`](skills/iteration/SKILL.md) | 不迭代 |
| 提交 zip 按 MCP 结果迭代 | [`iteration`](skills/iteration/SKILL.md) | MCP 报告的问题行 |

用户提交 zip 但没说要改代码时，按“只测稳定性”执行。
各用法的做法和通过条件见 [iterate.md §1.1](guides/iterate.md#11-三种用法)。

## 阶段选择

| 阶段 Skill | 进入条件 | 交付物 | 细则 |
|---|---|---|---|
| [`materials`](skills/materials/SKILL.md) 素材获取 | 有视频、文字轴或待整理来源 | `media/info.md`、原素材、质量限制 | [step1.md §1](guides/step1.md) |
| [`rotation`](skills/rotation/SKILL.md) 轴解析 | 素材能覆盖选定片段 | G1 确认、动作解释、代码基线、问题清单 | [step1.md §2–3、§6](guides/step1.md) |
| [`timeline`](skills/timeline/SKILL.md) 时序建模 | 已确认文字轴和动作意图 | `timeline.json`、参考耗时表、G2 结果 | [step1.md §4–5、§7–8](guides/step1.md)、[timeline.md](guides/timeline.md) |
| [`implementation`](skills/implementation/SKILL.md) 代码实现 | G2 通过，或已有明确的局部修改任务 | 角色代码、`verify_chain.py`、实现说明 | [step2.md §1–6](guides/step2.md) |
| [`delivery`](skills/delivery/SKILL.md) 验证交付 | 候选代码和来源齐全 | 检查结果、zip、README、待实测项 | [step2.md §7–8](guides/step2.md) |
| [`iteration`](skills/iteration/SKILL.md) 实测迭代 | 已有待测代码与测试目标，或有可定位版本的日志或录屏 | 测试证据、差异表、根因、下一版依据或验收结果 | [iterate.md](guides/iterate.md) |
| [`proposal`](skills/proposal/SKILL.md) 知识提议 | 实测得到可入卡的发现，或与现有卡冲突的已验证证据 | 提议文件、反馈结果 | [knowledge-maintenance.md §2–3](maintainer/knowledge-maintenance.md) |

- 从中间阶段进入时，检查该阶段的输入和通过条件。
- 缺少前提时，退回负责该前提的阶段。
- 直接改代码时，可从代码实现或实测迭代进入。
- 直接测试已有代码时，可从实测迭代进入。不必先补文字轴或整队时序。
- 局部任务不必创建整队时序。必须记录修改依据和影响范围。
- 已有确认且仍适用时，不必重复提问。

## 阶段切换

进入、退回或交给其他阶段时，按宿主能力加载该阶段：

- 宿主提供 Skill 调用工具，且已注册本仓库的阶段 Skill 时，必须用该工具调用阶段。Claude Code 中的阶段名为 `okwwcharcode:<阶段名>`，例如 `okwwcharcode:materials`。
- 其他情况读取 `skills/<阶段名>/SKILL.md`。
- 加载阶段后，再读取阶段引用的细则。
- 阶段内用到 [日志 Skill](skills/logging/SKILL.md) 或 [MCP Skill](skills/mcp/SKILL.md) 时，宜读取文件，不宜调用。两者不增加阶段，宿主显示的当前 Skill 保持为所在阶段。

## 共用规范

- 信息来源、证据、缺项分级和阶段交接见 [evidence.md](guides/evidence.md)。
- 计时口径、参考耗时和实测差值见 [timing.md](guides/timing.md)。
- 代码遵守 [rules.md](rules.md)。涉及角色时，先读语义卡和 [代码基线](guides/baseline.md)。
- 写或改游戏内日志时，按 [日志 Skill](skills/logging/SKILL.md) 写和检查。
- 需要运行、采证或测试时，读取 [MCP Skill](skills/mcp/SKILL.md)，用 `templates/mcp/` 的模板自动实测。
- 实测得到可入卡的发现时，按 [知识提议 Skill](skills/proposal/SKILL.md) 起草提议，由用户决定是否反馈。
- 游戏常识见 [knowledge/basics.md](knowledge/basics.md)。
- 语义卡的读取、冲突记录和安装目录边界见 [knowledge/cards/README.md](knowledge/cards/README.md)。

## 执行原则

- 忠实复现已确认的轴。不得擅自改变动作意图。
- G1 确认和关键歧义，按各阶段的要求提问。
- 实测改动前说明根因和改法。已有明确授权时，直接执行授权范围内的修改。
- 打包固定用 `scripts/pack_team.py`。
- 下载、抽帧和比较脚本放在媒体目录或会话 scratchpad。
- 素材来源范围按 evidence.md。不得查第三方 wiki 补角色机制。

## 工作区

本仓库保存 Skill、共用规范、知识、模板和打包脚本。
每个队的素材与产物放在独立工作区：

```text
<工作区>/<队名>/
  skilltest-v<N>/ timeline.json、notes.md、baseline.md、角色代码、检查文件、team.json、README.md、zip
  media/          info.md、原视频、口播或字幕、截图、取证脚本
  media/mcp/      templates/mcp/ 的副本和 mcp_test.json
```

- 开始前读取工作区的 `AGENTS.md` 和 `CLAUDE.md`。
- 工作区是本仓库或 ok-ww 安装目录时，先确认队伍产物的位置。
- 版本目录必须新建。`<N>` 从 1 开始，迭代时加 1。
- 不得覆盖已有版本。
- 媒体和本地配置不得提交到本仓库。

本机路径保存在工作区根目录的 `okwwcharcode.local.md`。
只在所选阶段需要且无法从已有配置确定时提问。

| 配置项 | 用途 |
|---|---|
| ok-ww 运行目录 `working` | 查框架源码、显示名和 zip 校验器 |
| Python | ok-ww 的 `python.exe`；取证用 `-I -B`，视频处理需能 `import cv2` |
| 上游仓库 | 收集角色代码基线，记录提交号 |
| 用户历史版本目录 | 收集已有配队代码；没有时记“无” |
| gh 引导 | 记为“不再推荐”后，知识提议不再提供安装或登录 gh 的选项 |

## 提问

- 使用宿主提供的结构化提问工具。
- 一个问题只问一个决策点，互相关联的问题合并在一次调用中。
- 视频问题附截图路径、视频时刻和缺项影响。
- G1 单独确认所选文字轴，见 step1.md §2。
- 其他问题在完成可独立执行的取证后集中提出。
