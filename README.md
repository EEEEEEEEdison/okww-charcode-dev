# okww-charcode-dev

用于 [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves)（ok-ww，鸣潮自动战斗脚本）的角色代码开发 Skill。
输入文字作战轴、教程视频或已有代码，交付工坊配队代码和 zip。
也支持根据实测日志与录屏修改角色代码。

项目包含一个总入口、六个阶段 Skill 和一个日志 Skill。
[总入口 SKILL.md](SKILL.md) 按任务和已有产物选择阶段。
各阶段共用证据、代码、时间测量和验收规则。
已有确认仍适用时，直接沿用；缺少前提时，返回对应阶段补齐。
版本号见 [VERSION](VERSION)。指定版本通过 `v<版本号>` 标签安装，例如 `v0.0.1`。
普通开发只读取随版本提供的知识；知识维护由独立入口处理。

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

[日志 Skill](skills/okww-logging/SKILL.md) 跨阶段使用：代码实现时写日志，验证交付时用 `scripts/check_logs.py` 检查，实测迭代时按日志定位卡点。

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

GitHub 的正式版本标签固定指向对应提交。
例如，“安装 0.0.1 版本”表示安装 `v0.0.1` 标签的内容。
安装不依赖专用 zip，不能用默认分支代替指定版本。

可向 Agent 提出：

> 安装 EEEEEEEEdison/okww-charcode-dev 的 v0.0.1。
> 按该标签的 README 安装，并核对版本、加载路径和重复副本。

全新安装时，目标目录必须不存在。
以下命令按宿主选择一条，并保留完整目录结构：

```sh
# pi
git clone --branch v0.0.1 --depth 1 https://github.com/EEEEEEEEdison/okww-charcode-dev.git "$HOME/.pi/agent/skills/okww-charcode-dev"

# Claude Code
git clone --branch v0.0.1 --depth 1 https://github.com/EEEEEEEEdison/okww-charcode-dev.git "$HOME/.claude/skills/okww-charcode-dev"
```

已有安装时，先核对实际路径、链接目标及未提交改动。
已有安装不是 Git 仓库或含本地改动时，不执行切换命令。
先将旧安装完整移到宿主不扫描的位置保存，再按全新安装步骤安装。
不得删除或覆盖旧安装中的用户改动。
已有安装是干净的 Git 仓库时，在实际仓库中执行：

```sh
git fetch origin tag v0.0.1 --no-tags
git switch --detach v0.0.1
```

安装后核对：

- `HEAD` 与 `refs/tags/v0.0.1^{commit}` 指向同一提交；
- 实际安装目录中的 `VERSION` 为 `0.0.1`；
- `git status --porcelain --untracked-files=all` 没有输出；
- 宿主加载的是该安装目录，不存在同名旧副本。

更新到其他版本时，显式指定新的标签，并重复核对。
已发布标签不得移动；修复通过新版本发布。

默认从总入口加载，再按路由读取相应阶段。
共用规则、知识和脚本使用仓库内的相对路径。

在当前 pi 中，扫描到含 `SKILL.md` 的目录后便停止递归。
因此，上述安装方式只注册总入口；六个阶段和日志 Skill 仍可由总入口读取。

需要分别调用阶段 Skill 时，在 `~/.pi/agent/settings.json` 中添加：

```json
{
  "skills": [
    "~/.pi/agent/skills/okww-charcode-dev/skills"
  ]
}
```

已有 `skills` 数组时，追加该路径并保留其他配置。
仓库安装在其他位置时，数组需同时列出仓库根目录和其 `skills/` 子目录。
保存后在 pi 运行 `/reload`；Claude Code 重新开启会话。
默认启用 Skill 命令时，可用 `/skill:okww-charcode-dev` 调用总入口。
六个阶段和日志 Skill 可分别用 `/skill:okww-materials`、`/skill:okww-logging` 等命令调用。
阶段目录必须保留在仓库内，以便读取 `../../` 下的共用文件。

队伍素材和产物放在独立工作区：

```text
<工作区>/<队名>/
  media/           原视频、音频或字幕、info.md、截图、取证脚本
  harness-v<N>/    timeline.json、baseline.md、notes.md、角色代码、检查文件、team.json、README.md、zip
```

每次迭代新建版本目录，不得覆盖旧版。
本机路径按总入口保存在工作区的 `okww-harness.local.md`。
媒体、角色产物和本地配置不得提交到本仓库。

## 知识维护

角色代码开发仍可根据日志与录屏迭代队伍代码。
新证据与知识冲突时，先记录在用户工作区。
普通开发流程不自动补卡、不发起补卡确认、不改写安装目录。
详见 [知识使用边界](knowledge/cards/README.md#使用边界)。

维护源码保存在 `maintainer/`，随仓库源码可见。
该目录独立于六阶段的 `skills/`，默认安装不注册维护 Skill。
维护者明确需要补卡或修正规则时，可单独加载
[知识维护 Skill](maintainer/okww-knowledge-maintenance/SKILL.md)。
在 pi 中，可将该文件的实际路径追加到 `settings.json` 的 `skills` 数组。
运行 `/reload` 后，手动调用 `/skill:okww-knowledge-maintenance`。
该 Skill 设置 `disable-model-invocation: true`，仅供显式调用。
审核后的知识随新版本交付，旧版本保持原内容。

## 目录与工具

| 路径 | 内容 |
|---|---|
| [VERSION](VERSION) | 发布版本号；对应 `v<版本号>` 标签 |
| [SKILL.md](SKILL.md) | 总入口、阶段路由、工作区与提问约定 |
| `skills/*/SKILL.md` | 六个阶段和日志 Skill 的输入、任务、交付与退回条件 |
| [harness/evidence.md](harness/evidence.md) | 信息获取、证据、缺项分级和阶段交接 |
| [harness/timing.md](harness/timing.md) | 计时口径、参考耗时、差值和时间验收 |
| [harness/step1.md](harness/step1.md) | 素材、文字轴确认、画面取证与事件标记 |
| [harness/baseline.md](harness/baseline.md) | 上游、工坊和历史代码基线 |
| [harness/timeline.md](harness/timeline.md) | 时序字段、示例和 G2 清单 |
| [harness/step2.md](harness/step2.md) | 节点实现、定向检查和打包交付 |
| [harness/iterate.md](harness/iterate.md) | 日志录像比较、根因、修改和复验 |
| [knowledge/basics.md](knowledge/basics.md) | 游戏操作、记号和画面识别知识 |
| [knowledge/cards/README.md](knowledge/cards/README.md) | 语义卡读取、适用条件与知识使用边界 |
| [maintainer/knowledge-maintenance.md](maintainer/knowledge-maintenance.md) | 维护者的补卡、确认与知识审核规则 |
| [rules.md](rules.md) | 代码规则、API 选择、日志和循环轴约束 |
| [references/basechar-api.md](references/basechar-api.md) | `BaseChar` API 与成员索引 |
| [references/task-api.md](references/task-api.md) | `self.task.*` 与战斗检查 |
| [references/self-impl-patterns.md](references/self-impl-patterns.md) | 框架函数不足时的实现经验 |
| [references/logging.md](references/logging.md) | 英文日志模板、词表与参考实现 |
| [references/workshop.md](references/workshop.md) | 工坊格式、循环轴骨架与案例 |
| [templates/verify_chain.py](templates/verify_chain.py) | 静态交场链检查模板 |
| [scripts/pack_team.py](scripts/pack_team.py) | 打包 zip，并调用 ok-ww 的校验器 |
| [scripts/check_logs.py](scripts/check_logs.py) | 按 logging.md 的词表和规则检查日志调用 |

下载、抽帧和分析脚本按任务编写，放在媒体目录或 scratchpad。
交场链检查使用模板，打包固定使用 `scripts/pack_team.py`。

## 代码基线

现有 API 与行号引用基于：

- ok-ww 上游 master `2243d465`（2026-10-05）；
- ok-script `v2.0.8`。

实际开发必须核对当前框架源码与所用版本。
上游变化后，按 rules.md 0-1 在案例中记录差异和正确来源。

## 与上游角色接入 Skill 的关系

上游 `.agents/skills/ok-ww-characters` 覆盖新角色接入流程，包括：

- 在 `src/char/CharFactory.py` 注册；
- `Labels` 特征名；
- 技能描述的中英术语对照。

本项目负责作战轴、角色实现、工坊配队和实测迭代。
上游 `2243d465` 的 Skill 示例使用了不存在的 `Priority` 和 `do_get_switch_priority`。
该版源码实际使用 `SwitchPriority` 和 `get_switch_priority`。
对应说明见 [BaseChar API](references/basechar-api.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。
上游项目及引用内容沿用各自的许可。
