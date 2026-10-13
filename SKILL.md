---
name: okww-charcode-dev
description: ok-ww（ok-wuthering-waves，鸣潮自动战斗脚本）角色代码 harness。两种用法。一是根据文字作战轴和实机视频（B 站链接或本地文件）理解出招，发现问题向用户确认，信息齐全后生成工坊循环轴角色代码并打包 zip。二是直接编写、修改、调试 ok-ww 角色代码与工坊配队代码（内置函数优先、自实现套路、统一英文日志模板、循环轴骨架、根据日志和录像迭代）。Triggers：ok-ww, okww, ok-wuthering-waves, 鸣潮, Wuthering Waves, 文字轴, 作战轴, 战斗轴, 配队轴, 启动轴, 循环轴, 轴转代码, 视频, 实机视频, 教程视频, B站, BV, 生成角色代码, harness, 角色代码, 写角色, char code, src/char, BaseChar, do_perform, switch_next_char, get_switch_priority, click_resonance, click_liberation, click_echo, heavy_click_forte, wait_until, 协奏, 回路, 切人, 出招, 工坊, 工坊配队, workshop, team zip, team.json, 强切, 交场链, 日志模板, log template, 根据日志改代码, 根据视频改代码, 语义卡, 补卡, 代码基线, 工坊代码.
---

# okww-charcode-dev

ok-ww 角色代码 harness。

## 两种用法

| 用法 | 什么时候用 | 读什么 |
|---|---|---|
| A 轴 → 代码 | 用户给了文字轴和/或视频，要生成一队角色代码 | 本文件的流程 + `harness/*.md` |
| B 直接写或改代码 | 改已有角色代码，或者根据日志、录像修问题 | [rules.md](rules.md)，以及涉及角色的语义卡和代码基线（[harness/baseline.md](harness/baseline.md)） |

用法 A 的步骤 2（生成代码）同样遵守 rules.md。

两种用法都要补卡：按 [knowledge/cards/README.md](knowledge/cards/README.md) 的「补卡机制」，在触发点主动起草语义卡条目，批量请用户确认后写入。用法 B 里，用户纠正了某个角色的出招、时长或写法，就是触发点之一。

## 总原则（用法 A）

- **只做匹配，不做挑剔**：忠实地把轴翻译成代码，不评价轴的好坏，也不擅自优化。
- **先自己识别，不确定再问**：只靠动作画面或时间推断得出的结论（C/D 级证据），也算不确定，要问。
- **尽量全自动，但以下三处必须停下来问用户**：
  - 文字轴要经用户确认；
  - 语义卡条目写入之前要用户确认（起草后批量确认）；
  - 实测迭代时，改代码之前先向用户说明方案。
- **不自备工具**：打 zip 和校验固定用 `scripts/pack_team.py`；抽帧、下载之类的脚本按文档当场写，放在会话 scratchpad 或本案的媒体目录里，不进仓库。
- **不上网查 wiki**：上网只用来取 B 站素材和 ok-ww 在线工坊的代码。角色知识只来自视频简介和评论、视频画面、用户提供的攻略、用户的回答、实测日志和录屏，以及已有代码（上游内置类、在线工坊、用户的历史版本）。

## 工作区

本仓库只放流程、规则、常识和语义卡，不放本机路径和某个队的数据。每个队的产物都放在会话的当前目录，即工作区：

```
<工作区>/<队名>/
  harness-v<N>/   timeline.json、notes.md、baseline.md、3 个角色 .py、verify_chain.py、team.json、README.md、zip
  media/          视频、截图、临时脚本（文档里的“媒体目录”）
```

- 开始前必须先读工作区里的 AGENTS.md 和 CLAUDE.md。项目对目录、分支、打包有约定时按项目约定；和本文件冲突时，以项目约定为准。
- 工作区是本仓库或 ok-ww 的安装目录，或者看不出是用户要的目录时，必须先问用户工作区放在哪。
- `harness-v<N>` 必须是新目录。`<N>` 从 1 开始，每次迭代加 1，不得覆盖已有版本。
- `media/` 和本地配置文件不得提交到 git。

**本地配置**：本机路径写在工作区根目录的 `okww-harness.local.md`。没有这个文件或缺少某一项时，必须先问用户，再写进去。

| 项 | 用途 |
|---|---|
| ok-ww 运行目录（`working`） | 校验 zip，查 `CHARACTER_DISPLAY_NAMES` 和框架源码 |
| Python | ok-ww 自带的 `python.exe`，带 `-I -B` 运行，要能 `import cv2`；抽帧用 cv2 |
| 上游仓库 | 有 `upstream` 远端的 ok-wuthering-waves 克隆，收集代码基线用 |
| 用户历史版本目录 | 用户以前写的配队代码，收集代码基线用；没有就写“无” |

## 流程（用法 A）

| 步骤 | 做什么 | 详见 |
|---|---|---|
| S1 收集素材 | 下载视频，获取简介和评论，截出画面里的轴表 | [harness/step1.md](harness/step1.md) §1 |
| S2 确认文字轴（关口 G1） | 拼出候选文字轴和作者的记号说明，**单独**请用户确认；同时问双方的共鸣链。确认后给每个角色收集代码基线 | step1.md §2、[harness/baseline.md](harness/baseline.md) |
| S3 识别与对齐 | 拆分记号，建立 HUD 时间线，把轴和视频对齐，再推断其余记号 | step1.md §3–7 |
| S4 集中提问 | 把问题清单一次问完；问完后起草语义卡条目，批量确认后写入 | step1.md §8 |
| S5 生成前检查（关口 G2） | 按清单检查 timeline.json，全部满足才能生成代码 | [harness/timeline.md](harness/timeline.md) §3 |
| S6 生成代码并自检 | 按骨架生成 3 个角色文件和 verify_chain，然后自检 | [harness/step2.md](harness/step2.md) §1–7 |
| S7 打包交付 | 先问 team.json 的字段，再打 zip 并校验，写 README | step2.md §8 |
| S8 实测迭代 | 读日志、对比视频，先说明方案，用户同意后再出下一版；每轮分析完补卡 | [harness/iterate.md](harness/iterate.md) |

常识见 [knowledge/basics.md](knowledge/basics.md)，角色语义卡见 [knowledge/cards/](knowledge/cards/README.md)。

## 怎么问用户

- 用 AskUserQuestion 提问，每题只问一个点，每次调用最多 4 题。
- 涉及视频的问题，附上截图路径和视频时刻。
- 第一个问题永远是确认文字轴（G1），单独问；其余问题等 S3 全部做完后再集中问。
