# okww-charcode-dev

用于 [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves)（ok-ww，鸣潮自动战斗脚本）的角色代码开发 Skill。
输入文字作战轴、教程视频或已有代码，交付工坊配队代码和 zip。
也支持根据实测日志与录屏修改角色代码。

项目包含一个总入口和六个阶段 Skill。
[总入口 SKILL.md](SKILL.md) 按任务和已有产物选择阶段。
各阶段共用证据、代码、时间测量和验收规则。
已有确认仍适用时，直接沿用；缺少前提时，返回对应阶段补齐。

## 六个阶段 Skill

| 阶段 | 职责 | 主要交付物 |
|---|---|---|
| [素材获取](skills/okww-materials/SKILL.md) | 收集文字、视频、字幕与作者说明，记录素材条件 | 原素材、`media/info.md`、质量限制 |
| [轴解析](skills/okww-rotation/SKILL.md) | 确认所选轴，解释动作、资源与跨步依赖 | G1 确认、动作解释、代码基线、缺项 |
| [时序建模](skills/okww-timeline/SKILL.md) | 标记输入、状态变化和切人事件，测量参考耗时 | `timeline.json`、参考耗时表、G2 结果 |
| [代码实现](skills/okww-implementation/SKILL.md) | 选用框架 API，实现动作、判据与交场链 | 角色代码、`verify_chain.py`、实现说明 |
| [验证交付](skills/okww-delivery/SKILL.md) | 定向检查代码，校验并打包工坊文件 | 检查结果、zip、README、待实测项 |
| [实测迭代](skills/okww-iteration/SKILL.md) | 对照日志和录屏定位差异，修改并复验 | 差异表、根因、下一版或验收记录 |

整队生成按上述顺序推进。
局部修改可从代码实现或实测迭代进入。
局部任务只补受影响的依据和验证，不必重建整队时序。

## 信息如何贯穿流程

关键判断交接六项：结论、依据、适用条件、未知、影响范围、验证办法。
原素材、源码和日志必须能定位到时刻、原文或版本。
口播、字幕及简介可能影响操作时，必须核对对应内容。
证据冲突先检查版本、资源和事件定义，再决定是否补证。

动作模型分别记录前置状态、按法、触发、生效、结束和切人条件。
例如，技能可用、图标变化和固定延迟是不同的触发策略。
每次切人都记录普通或变奏入场、协奏状态和是否允许补资源。
跨角色效果、延迟生效和跨轮资源也要保留依赖。

缺项分为阻断项、待测项和非关键项。
阻断项必须解决后才能确定受影响的实现。
待测项可进入试验版本，但必须有假设、验证办法和失败处理。
用户确认操作意图后，机制和数值仍需按证据验证。
详见 [信息获取与交接规则](harness/evidence.md)。

## 参考耗时与实测验收

素材阶段保留帧率、速度、剪辑和计时器信息。
建模阶段记录整轮、全部角色节点及关键动作段的参考耗时。
每条记录保留起止事件、各遍结果、计时口径和测量精度。

实测视频沿用相同事件定义，分别比较视频、真实和游戏时间。
差异表保留本段差值与累计差值，逐层定位延迟来源。
时间变化还要结合动作效果、协奏切人和场景干扰解释。
参考耗时用于比较，代码等待仍由动作判据确定。

G1 确认所选文字轴、角色对应、记号和双方共鸣链。
G2 检查模型、动作判据、切人、依赖、参考耗时和开放缺项。
静态交场链与 zip 检查的结果单独记录。
整队实测完成还需动作和耗时复验，以及用户认可。
缺少录屏或参考数据时，明确列出未验证项。
详见 [时间测量](harness/timing.md) 和 [实测迭代](harness/iterate.md)。

## 使用与安装

把仓库克隆或链接到 Agent 的 skills 目录。
目录名使用 `okww-charcode-dev`，并保留完整目录结构：

- Claude Code：`~/.claude/skills/okww-charcode-dev`
- pi：`~/.pi/agent/skills/okww-charcode-dev`

从总入口加载，再按路由读取相应阶段。
共用规则、知识和脚本使用仓库内的相对路径。

队伍素材和产物放在独立工作区：

```text
<工作区>/<队名>/
  media/           原视频、音频或字幕、info.md、截图、取证脚本
  harness-v<N>/    timeline.json、baseline.md、notes.md、角色代码、检查文件、team.json、README.md、zip
```

每次迭代新建版本目录，不得覆盖旧版。
本机路径按总入口保存在工作区的 `okww-harness.local.md`。
媒体、角色产物和本地配置不得提交到本仓库。

## 目录与工具

| 路径 | 内容 |
|---|---|
| [SKILL.md](SKILL.md) | 总入口、阶段路由、工作区与提问约定 |
| `skills/*/SKILL.md` | 六个阶段的输入、任务、交付与退回条件 |
| [harness/evidence.md](harness/evidence.md) | 信息获取、证据、缺项分级和阶段交接 |
| [harness/timing.md](harness/timing.md) | 计时口径、参考耗时、差值和时间验收 |
| [harness/step1.md](harness/step1.md) | 素材、文字轴确认、画面取证与事件标记 |
| [harness/baseline.md](harness/baseline.md) | 上游、工坊和历史代码基线 |
| [harness/timeline.md](harness/timeline.md) | 时序字段、示例和 G2 清单 |
| [harness/step2.md](harness/step2.md) | 节点实现、定向检查和打包交付 |
| [harness/iterate.md](harness/iterate.md) | 日志录像比较、根因、修改和复验 |
| [knowledge/basics.md](knowledge/basics.md) | 游戏操作、记号和画面识别知识 |
| [knowledge/cards/README.md](knowledge/cards/README.md) | 按角色和共鸣链维护语义卡 |
| [rules.md](rules.md) | 代码规则、API 选择、日志和循环轴约束 |
| [references/basechar-api.md](references/basechar-api.md) | `BaseChar` API 与成员索引 |
| [references/task-api.md](references/task-api.md) | `self.task.*` 与战斗检查 |
| [references/self-impl-patterns.md](references/self-impl-patterns.md) | 框架函数不足时的实现经验 |
| [references/logging.md](references/logging.md) | 英文日志模板与参考实现 |
| [references/workshop.md](references/workshop.md) | 工坊格式、循环轴骨架与案例 |
| [templates/verify_chain.py](templates/verify_chain.py) | 静态交场链检查模板 |
| [scripts/pack_team.py](scripts/pack_team.py) | 打包 zip，并调用 ok-ww 的校验器 |

下载、抽帧和分析脚本按任务编写，放在媒体目录或 scratchpad。
交场链检查使用模板，打包固定使用 `scripts/pack_team.py`。

## 代码基线

现有 API 与行号引用基于：

- ok-ww 上游 master `2243d465`（2026-10-05）；
- ok-script `v2.0.8`。

实际开发必须核对当前框架源码与所用版本。
上游变化后，按 rules.md 0-1 修正受影响的引用。

## 与上游角色接入 Skill 的关系

上游 `.agents/skills/ok-ww-characters` 覆盖新角色接入流程，包括：

- 在 `src/char/CharFactory.py` 注册；
- `Labels` 特征名；
- 技能描述的中英术语对照。

本项目负责作战轴、角色实现、工坊配队和实测迭代。
上游 `2243d465` 的 Skill 示例使用了不存在的 `Priority` 和 `do_get_switch_priority`。
该版源码实际使用 `SwitchPriority` 和 `get_switch_priority`。
对应说明见 [BaseChar API](references/basechar-api.md)。
