# okww-charcode-dev

用于编写 [ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves)（ok-ww，鸣潮自动战斗脚本）角色代码的 agent skill。

它要求 AI：

- 优先调用框架内置函数，并在相近的函数之间选对；
- 内置函数不够用时，按项目已有的经验自己实现；
- 按统一的英文模板写日志；
- 写工坊脚本化配队时，套用统一的循环轴骨架。

入口文件是 [SKILL.md](SKILL.md)。

## 基线

- ok-ww 上游 master `2243d465`（2026-10-05）
- ok-script `v2.0.8`

所有 `File.py:N` 引用都以这两个版本为准。上游改动后，以源码为准修正条目（SKILL.md 0-1）。

## 目录

```
SKILL.md                      规则（1-1 … 6-8、L-1 … L-10）、决策阶梯、迭代工作流
references/basechar-api.md    BaseChar 函数详条 + 成员索引
references/task-api.md        角色代码用到的 self.task.* 与战斗检查机制
references/self-impl-patterns.md  自实现套路
references/logging.md         日志模板、词表、_trace 参考实现
references/workshop.md        工坊 zip 格式、循环轴骨架、可选案例
templates/verify_chain.py     交场链静态自检模板
```

## 安装

把仓库克隆或链接到 agent 的 skills 目录，目录名用 `okww-charcode-dev`：

- Claude Code：`~/.claude/skills/okww-charcode-dev`
- pi：`~/.pi/agent/skills/okww-charcode-dev`

## 与上游 `.agents/skills/ok-ww-characters` 的关系

上游仓库自带的 `ok-ww-characters` skill 覆盖新角色接入流程，本 skill 不重复这部分。它包括：

- 在 `src/char/CharFactory.py` 注册；
- `Labels` 特征名；
- 技能描述的中英术语对照。

**注意**：在 `2243d465` 里，它的示例代码用了源码中不存在的 `Priority` 和 `do_get_switch_priority`。实际的 API 是 `SwitchPriority` 和 `get_switch_priority`，详见 references/basechar-api.md。
