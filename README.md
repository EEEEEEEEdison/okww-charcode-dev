# okww-charcode-dev

为 [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves)（ok-ww，鸣潮自动战斗脚本）生成角色代码的 harness：输入文字作战轴和实机视频，AI 对照理解出招，信息不全时向用户确认，最后生成角色代码。

harness 只由流程文档组成，不带工具：需要的脚本（抽帧、下载、打包）由 AI 按文档当场写。它以 agent skill 的形式加载，入口是 [SKILL.md](SKILL.md)，有两种用法：

- **轴 → 代码**：按 `harness/` 的流程，从文字轴和视频生成一队工坊角色代码并打包。
- **直接写或改代码**：按 [rules.md](rules.md) 来。代码规则要求 AI：
  - 优先调用框架内置函数，并在相近的函数之间选对；
  - 内置函数不够用时，按项目已有的经验自己实现；
  - 按统一的英文模板写日志；
  - 写工坊脚本化配队时，套用统一的循环轴骨架。

## 基线

- ok-ww 上游 master `2243d465`（2026-10-05）
- ok-script `v2.0.8`

所有 `File.py:N` 引用都以这两个版本为准。上游改动后，以源码为准修正条目（rules.md 0-1）。

## 目录

```
SKILL.md                      入口：两种用法、总原则、本机位置、流程总表、提问方式
harness/step1.md              步骤 1：收集素材、确认文字轴、HUD 时间线、对齐、集中提问
harness/timeline.md           timeline.json 格式与关口 G2 清单
harness/step2.md              步骤 2：节点映射、记号到代码、时限、自检清单、打包交付
harness/iterate.md            实测迭代：读日志、两段视频对比、先说明再改
knowledge/basics.md           游戏常识：按键与操作、记号、画面识别
knowledge/cards/README.md     角色语义卡的规则与模板（一角色一命座一张卡）
cases/                        每个案例的 timeline.json（视频等媒体不进仓库）
rules.md                      代码规则（1-1 … 6-8、L-1 … L-10）、决策阶梯、迭代工作流
references/basechar-api.md    BaseChar 函数详条 + 成员索引
references/task-api.md        角色代码用到的 self.task.* 与战斗检查机制
references/self-impl-patterns.md  自实现套路
references/logging.md         日志模板、词表、_trace 参考实现
references/workshop.md        工坊 zip 格式、循环轴骨架、可选案例
templates/verify_chain.py     交场链静态自检模板
```

## 安装

把仓库克隆或链接到 agent 的 skills 目录，目录名 `okww-charcode-dev`：

- Claude Code：`~/.claude/skills/okww-charcode-dev`
- pi：`~/.pi/agent/skills/okww-charcode-dev`

## 与上游 `.agents/skills/ok-ww-characters` 的关系

上游仓库自带的 `ok-ww-characters` skill 覆盖新角色接入流程，本仓库不重复这部分。它包括：

- 在 `src/char/CharFactory.py` 注册；
- `Labels` 特征名；
- 技能描述的中英术语对照。

**注意**：在 `2243d465` 里，它的示例代码用了源码中不存在的 `Priority` 和 `do_get_switch_priority`。实际的 API 是 `SwitchPriority` 和 `get_switch_priority`，详见 references/basechar-api.md。
