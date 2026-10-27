# okwwcharcode

用于 [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves)（ok-ww，鸣潮自动战斗脚本）的角色代码开发 Skill。
仓库名为 `okww-charcode-dev`，安装后的 Skill 名为 `okwwcharcode`。
输入文字作战轴、教程视频或已有代码，交付工坊配队代码和 zip。
也支持根据实测日志与录屏修改角色代码。
也可直接测试已有角色代码的战斗逻辑，不必先生成新代码。

项目按工作流分为总入口 `okwwcharcode`、六个阶段 Skill、日志 Skill `logging`、MCP 辅助 Skill `mcp` 和知识提议 Skill `proposal`。
[总入口 SKILL.md](SKILL.md) 按任务和已有产物选择阶段。
各阶段共用证据、代码、时间测量和验收规则。
已有确认仍适用时，直接沿用；缺少前提时，返回对应阶段补齐。
版本号见 [VERSION](VERSION)。指定版本通过 `v<版本号>` 标签安装，例如 `v0.3.0`。各版本的变化见 [版本记录](#版本记录)。
普通开发只读取随版本提供的知识；知识维护由独立入口处理。

## 准备

- Agent 宿主：Claude Code、pi，或支持 Agent Skills 的其他宿主。
- Git：按版本标签安装。
- ok-ww：本机已安装。Skill 用其运行目录 `working` 查框架源码、显示名和 zip 校验器。
- Python：ok-ww 自带的 `python.exe`。视频处理需能 `import cv2`。
- ok-ww 上游仓库的本地克隆：收集角色代码基线。
- gh：可选。知识反馈时可由 Agent 安装，见 [用 gh 自动反馈](#用-gh-自动反馈)。

所选阶段需要本机路径且尚未记录时，Agent 会询问，并保存在工作区根目录的 `okww-harness.local.md`。

## 安装

GitHub 的正式版本标签固定指向对应提交。
例如，“安装 0.3.0 版本”表示安装 `v0.3.0` 标签的内容。
安装不依赖专用 zip，不能用默认分支代替指定版本。

可向 Agent 提出：

> 安装 EEEEEEEEdison/okww-charcode-dev 的 v0.3.0。
> 按该标签的 README 安装，并核对版本、加载路径和重复副本。

安装目录名必须为 `okwwcharcode`，与总入口的 `name` 一致。
全新安装时，目标目录必须不存在。
以下命令按宿主选择一条，并保留完整目录结构：

```sh
# Claude Code
git clone --branch v0.3.0 --depth 1 https://github.com/EEEEEEEEdison/okww-charcode-dev.git "$HOME/.claude/skills/okwwcharcode"

# pi
git clone --branch v0.3.0 --depth 1 https://github.com/EEEEEEEEdison/okww-charcode-dev.git "$HOME/.pi/agent/skills/okwwcharcode"
```

其他宿主克隆到宿主的 Skill 目录，目录名同样用 `okwwcharcode`。

### Claude Code

仓库含 `.claude-plugin/plugin.json`。
新开会话后，Claude Code 把安装目录加载为插件 `okwwcharcode@skills-dir`：

- 总入口注册为 `okwwcharcode`；
- 六个阶段、日志 Skill、MCP 辅助 Skill `mcp` 和知识提议 Skill 注册为 `okwwcharcode:<阶段名>`。

该方式不经过 marketplace。
运行 `claude plugin details okwwcharcode@skills-dir` 核对，结果应列出 9 个 Skill。

### pi

pi 扫描到含 `SKILL.md` 的目录后便停止递归。
因此，上述安装只注册总入口；阶段、日志、MCP 和知识提议 Skill 由总入口读取。
需要分别调用阶段 Skill 时，在 `~/.pi/agent/settings.json` 中添加：

```json
{
  "skills": [
    "~/.pi/agent/skills/okwwcharcode/skills"
  ]
}
```

已有 `skills` 数组时，追加该路径并保留其他配置。
仓库安装在其他位置时，数组需同时列出仓库根目录和其 `skills/` 子目录。
保存后在 pi 运行 `/reload`。

### 其他宿主

- 总入口和各阶段的 `name` 与所在目录名一致，符合 Agent Skills 规范。
- 宿主只注册总入口时，总入口读取 `skills/<阶段名>/SKILL.md`。
- 宿主不加命名空间时，`materials`、`logging` 等阶段名可能与其他 Skill 重名。重名时只注册总入口。
- 阶段目录必须保留在仓库内，以便读取 `../../` 下的共用文件。

### 已有安装与升级

0.0.1 的安装目录名为 `okww-charcode-dev`，0.1.0 起改为 `okwwcharcode`。
旧目录留在 Skill 目录时，宿主会同时加载新旧两份。

先核对旧安装的实际路径、链接目标及未提交改动。
从 0.0.1 升级时：

1. 将旧目录完整移到宿主不扫描的位置，例如 `~/.claude/okww-charcode-dev-v0.0.1`。
2. 按全新安装步骤安装到 `okwwcharcode`。
3. pi 的 `settings.json` 中，把 `.../okww-charcode-dev/skills` 改为 `.../okwwcharcode/skills`。

不得删除或覆盖旧安装中的用户改动。
目录名已是 `okwwcharcode` 且为干净的 Git 仓库时，在实际仓库中切换版本：

```sh
git fetch origin tag v0.3.0 --no-tags
git switch --detach v0.3.0
```

安装后核对：

- `HEAD` 与 `refs/tags/v0.3.0^{commit}` 指向同一提交；
- 实际安装目录中的 `VERSION` 为 `0.3.0`；
- `git status --porcelain --untracked-files=all` 没有输出；
- 宿主加载的是该安装目录，不存在同名旧副本。

更新到其他版本时，显式指定新的标签，并重复核对。
已发布标签不得移动；修复通过新版本发布。

## 用法

| 宿主 | 总入口 | 阶段与日志 Skill |
|---|---|---|
| Claude Code | `/okwwcharcode` | `/okwwcharcode:materials`、`/okwwcharcode:logging` 等 |
| pi | `/skill:okwwcharcode` | 按 [pi 安装](#pi) 注册后，用 `/skill:materials`、`/skill:logging` 等 |
| 其他宿主 | 按宿主的 Skill 命令调用 `okwwcharcode` | 总入口读取 `skills/<阶段名>/SKILL.md` |

不确定从哪个阶段开始时，调用总入口，由总入口按已有产物选择阶段。
在 Claude Code 中，总入口用 Skill 工具切换到 `okwwcharcode:<阶段名>`。
显示当前 Skill 的状态栏，例如 ccstatusline 的 skills 组件，随之显示所在阶段。
直接描述需求时，宿主也可按 Skill 描述自动调用。

请求示例：

- `/okwwcharcode 把这个视频的作战轴做成工坊配队：<视频链接>`：从素材获取开始，依次推进到验证交付。
- `/okwwcharcode 文字轴如下，视频在 <路径>：<文字轴>`：素材齐全时从轴解析开始。
- `/okwwcharcode:implementation 修改 <角色 .py> 的 <函数>：<改法与依据>`：局部修改，从代码实现开始。
- `/okwwcharcode:iteration <队名> harness-v<N> 的实测日志在 <路径>，<现象>`：实测迭代，按根因退回对应阶段。
- `/okwwcharcode 测试 <代码路径> 在 <队伍与关卡> 中的 <战斗行为>`：直接测试，由 Agent 准备场景并采证。
- `/okwwcharcode:logging 检查 <角色 .py> 的日志`：单独的日志任务。
- `/okwwcharcode:proposal <队名> harness-v<N>`：把本案可入卡的发现整理成知识提议。

检查日志调用：

```text
<ok-ww python.exe> -I -B scripts/check_logs.py <角色 .py> [<角色 .py> ...]
```

### 工作区

队伍素材和产物放在独立工作区：

```text
<工作区>/<队名>/
  media/           原视频、音频或字幕、info.md、截图、取证脚本
  harness-v<N>/    timeline.json、baseline.md、notes.md、角色代码、检查文件、team.json、README.md、zip
  proposals/       知识提议文件
```

每次迭代新建版本目录，不得覆盖旧版。
媒体、角色产物和本地配置不得提交到本仓库。

## 六个阶段 Skill

| 阶段 | Skill 名 | 职责 | 主要交付物 |
|---|---|---|---|
| [素材获取](skills/materials/SKILL.md) | `materials` | 收集文字、视频、字幕与作者说明，记录素材条件 | 原素材、`media/info.md`、质量限制 |
| [轴解析](skills/rotation/SKILL.md) | `rotation` | 确认所选轴，解释动作、资源与跨步依赖 | G1 确认、动作解释、代码基线、缺项 |
| [时序建模](skills/timeline/SKILL.md) | `timeline` | 标记输入、状态变化和切人事件，测量参考耗时 | `timeline.json`、参考耗时表、G2 结果 |
| [代码实现](skills/implementation/SKILL.md) | `implementation` | 选用框架 API，实现动作、判据与交场链 | 角色代码、`verify_chain.py`、实现说明 |
| [验证交付](skills/delivery/SKILL.md) | `delivery` | 定向检查代码，校验并打包工坊文件 | 检查结果、zip、README、待实测项 |
| [实测迭代](skills/iteration/SKILL.md) | `iteration` | 测试已有代码，或对照日志和录屏定位差异，修改并复验 | 测试证据、差异表、根因、下一版或验收记录 |

整队生成按上述顺序推进。
局部修改可从代码实现或实测迭代进入。
已有待测代码与测试目标，或有可定位版本的日志或录屏时，可从实测迭代进入。
直接测试已有代码不必先补文字轴或整队时序。
局部任务只补受影响的依据和验证，不必重建整队时序。

[日志 Skill](skills/logging/SKILL.md)（`logging`）跨阶段使用：代码实现时写日志，验证交付时用 `scripts/check_logs.py` 检查，实测迭代时按日志定位卡点。

[MCP Skill](skills/mcp/SKILL.md)（`mcp`）跨阶段辅助运行与测试。
Agent 按任务发现并读取当前 ok-ww 运行时的内置技能。
覆盖以下操作：

- 启动 ok-ww 与游戏。
- 准备矩阵或深塔测试起点。
- 入场选队：目标明确时，在进入副本前选择队伍或槽位，并读回核对。
- 开战并核对首位角色。
- 识别异常并将结果用于测试判断。

具体流程见 [MCP Skill](skills/mcp/SKILL.md) 和 [MCP 测试参考](references/mcp-testing.md)。
实际操作路径必须按当前游戏界面与源码验证，不保证任意页面均已支持。
未知界面需基于当前截图编写有界 Task。
未实机验证的路径不得称为全自动可用。

[知识提议 Skill](skills/proposal/SKILL.md)（`proposal`）在实测迭代后使用，把可入卡的发现整理成提议。经用户同意后，提议反馈给维护者，见 [贡献知识](#贡献知识)。

## 贡献知识

使用者在本地实测得到的新结论，可反馈给维护者审核，不经过服务器。
实测迭代得到可入卡的发现时，Agent 进入 [知识提议 Skill](skills/proposal/SKILL.md)：

1. 按 [提议模板](templates/knowledge-proposal.md) 起草提议，保存到 `<工作区>/<队名>/proposals/`。
2. 用 `scripts/submit_proposal.py` 检查格式。含本机路径、邮箱或令牌时不能提交。
3. 给出提议全文，问用户一次是否反馈。
4. 按用户的选择提交。gh 已登录时，选项为“反馈”“用邮件反馈”“不反馈”。gh 未安装或未登录时，增加“安装 gh 后反馈”和“用浏览器反馈”。

| 选项 | 提交方式 | 用户操作 |
|---|---|---|
| 反馈 | gh 已登录时用 `gh issue create` 创建 Issue；否则同“用浏览器反馈” | 无 |
| 安装 gh 后反馈 | 安装并登录 gh，再创建 Issue | 管理员确认点“是”；在授权页粘贴验证码，点 Authorize |
| 用浏览器反馈 | 打开预填的新建 Issue 页面 | 在页面点提交；正文过长时先粘贴剪贴板内容 |
| 用邮件反馈 | 在资源管理器中选中提议文件 | 把文件作为附件发到 476676559@qq.com |

除邮件外都需要 GitHub 账号。Issue 公开可见。提交即同意按 MIT 许可收录提议内容。
手动提交时，复制提议模板，在本仓库新建 Issue 填写。
维护者按 [外部提议](maintainer/knowledge-maintenance.md#6-外部提议) 审核，写入的条目随新版本发布。

### 用 gh 自动反馈

经常反馈时，宜安装并登录 gh。之后每次反馈由 Agent 直接创建 Issue。
选“安装 gh 后反馈”时，`submit_proposal.py --setup-gh` 依次执行：

1. 没装 gh 时，用 winget 安装 GitHub CLI。没有 winget 时，打开 https://cli.github.com 由用户下载安装。
2. 运行 `gh auth login --web --clipboard`。验证码复制到剪贴板，脚本打开授权页。
3. 登录后提交本次提议。安装或登录失败时，本次改用浏览器反馈。

gh 已安装但未登录时，该选项名为“登录 gh 后反馈”，跳过安装。
gh 登录后的最低权限为 `repo`、`read:org` 和 `gist`，能读写本账号的仓库。
令牌存在系统凭据管理器中。撤销时运行 `gh auth logout`，或在 GitHub 的 Settings → Applications 撤销 GitHub CLI 的授权。

用户有该选项而改选浏览器或邮件时，工作区的 `okww-harness.local.md` 记下 `gh 引导：不再推荐`，之后不再提供。删掉这一行即可恢复。
不提交提议也可先安装并登录：

```text
<ok-ww python.exe> -I -B scripts/submit_proposal.py --setup-gh
```

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

## 知识维护

角色代码开发仍可根据日志与录屏迭代队伍代码。
新证据与知识冲突时，先记录在用户工作区。
普通开发流程不自动补卡、不发起补卡确认、不改写安装目录。
可入卡的发现按 [贡献知识](#贡献知识) 反馈给维护者。
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
| [.claude-plugin/plugin.json](.claude-plugin/plugin.json) | Claude Code 插件清单；阶段注册为 `okwwcharcode:<阶段名>` |
| [SKILL.md](SKILL.md) | 总入口、阶段路由、工作区与提问约定 |
| `skills/*/SKILL.md` | 六个阶段、日志、MCP 和知识提议 Skill 的输入、任务、交付与退回条件 |
| [skills/mcp/SKILL.md](skills/mcp/SKILL.md) | 跨阶段发现和使用 ok-ww 内置技能，准备测试与采证 |
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
| [references/mcp-testing.md](references/mcp-testing.md) | ok-ww 内置技能发现、测试场景准备和证据采集流程 |
| [references/workshop.md](references/workshop.md) | 工坊格式、循环轴骨架与案例 |
| [templates/verify_chain.py](templates/verify_chain.py) | 静态交场链检查模板 |
| [templates/knowledge-proposal.md](templates/knowledge-proposal.md) | 知识提议模板 |
| [scripts/pack_team.py](scripts/pack_team.py) | 打包 zip，并调用 ok-ww 的校验器 |
| [scripts/check_logs.py](scripts/check_logs.py) | 按 logging.md 的词表和规则检查日志调用 |
| [scripts/submit_proposal.py](scripts/submit_proposal.py) | 检查知识提议，用 gh、浏览器或邮件反馈；可安装并登录 gh |

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

## 版本记录

- 未发布：新增 MCP 辅助技能与直接测试已有代码入口。
- 0.3.0：知识提议在 gh 未安装或未登录时提供“安装 gh 后反馈”，由 `submit_proposal.py --setup-gh` 安装并登录 gh。
- 0.2.0：新增知识提议 Skill `proposal`。实测得到可入卡的发现时起草提议，经用户同意后用 gh、预填 Issue 页面或邮件反馈给维护者。
- 0.1.0：总入口改名为 `okwwcharcode`，拆分出六个阶段 Skill；新增日志 Skill 和 `scripts/check_logs.py`；语义卡改为精简写法。Claude Code 以插件形式注册阶段。
- 0.0.1：首个版本，Skill 名为 `okww-charcode-dev`。

## 许可证

本项目采用 [MIT License](LICENSE)。
上游项目及引用内容沿用各自的许可。
