---
name: okww-charcode-dev
description: ok-ww（ok-wuthering-waves，鸣潮自动战斗脚本）角色代码 harness。两种用法。一是根据文字作战轴和实机视频（B 站链接或本地文件）理解出招，发现问题向用户确认，信息齐全后生成工坊循环轴角色代码并打包 zip。二是直接编写、修改、调试 ok-ww 角色代码与工坊配队代码（内置函数优先、自实现套路、统一英文日志模板、循环轴骨架、根据日志和录像迭代）。Triggers：ok-ww, okww, ok-wuthering-waves, 鸣潮, Wuthering Waves, 文字轴, 作战轴, 战斗轴, 配队轴, 启动轴, 循环轴, 轴转代码, 视频, 实机视频, 教程视频, B站, BV, 生成角色代码, harness, 角色代码, 写角色, char code, src/char, BaseChar, do_perform, switch_next_char, get_switch_priority, click_resonance, click_liberation, click_echo, heavy_click_forte, wait_until, 协奏, 回路, 切人, 出招, 工坊, 工坊配队, workshop, team zip, team.json, 强切, 交场链, 日志模板, log template, 根据日志改代码, 根据视频改代码.
---

# okww-charcode-dev

ok-ww 角色代码 harness。

## 两种用法

| 用法 | 什么时候用 | 读什么 |
|---|---|---|
| A 轴 → 代码 | 用户给了文字轴和/或视频，要生成一队角色代码 | 本文件的流程 + `harness/*.md` |
| B 直接写或改代码 | 改已有角色代码，或者根据日志、录像修问题 | [rules.md](rules.md) |

用法 A 的步骤 2（生成代码）同样遵守 rules.md。

## 总原则（用法 A）

- **只做匹配，不做挑剔**：忠实地把轴翻译成代码，不评价轴的好坏，也不擅自优化。
- **先自己识别，不确定再问**：只靠动作画面或时间推断得出的结论（C/D 级证据），也算不确定，要问。
- **尽量全自动，但以下三处必须停下来问用户**：
  - 文字轴要经用户确认；
  - 属于角色本身的结论，存入语义卡之前要用户同意；
  - 实测迭代时，改代码之前先向用户说明方案。
- **不自备工具**：抽帧、下载、打包之类的脚本，按文档当场写，放在会话 scratchpad 或本案的媒体目录里，不进仓库。
- **不上网查 wiki**：角色知识只来自视频简介和评论、视频画面、用户提供的攻略和用户的回答。

## 位置（本机）

| 内容 | 位置 |
|---|---|
| 案例数据（timeline.json、记录） | 本仓库 `cases/<队名>/harness-v<N>/` |
| 媒体（视频、截图、临时脚本） | `E:\GameAutoScript\okww-charcode-dev-media\<队名>\harness-v<N>\`，不进仓库 |
| 生成的代码与 zip | `E:\GameAutoScript\workspace\okww-test\ok-ww-char\<队名>\harness-v<N>\`，新建目录，不覆盖已有版本 |
| Python | `E:\GameAutoScript\ok-ww\data\apps\ok-ww\python\python.exe`，带 `-I -B` 运行。环境里有 cv2，机器上没有 ffmpeg |
| ok-ww 运行目录（校验 zip 用） | `E:\GameAutoScript\ok-ww\data\apps\ok-ww\working` |

`<N>` 从 1 开始，每次迭代加 1。

## 流程（用法 A）

| 步骤 | 做什么 | 详见 |
|---|---|---|
| S1 收集素材 | 下载视频，获取简介和评论，截出画面里的轴表 | [harness/step1.md](harness/step1.md) §1 |
| S2 确认文字轴（关口 G1） | 拼出候选文字轴和作者的记号说明，**单独**请用户确认；同时问双方的共鸣链 | step1.md §2 |
| S3 识别与对齐 | 拆分记号，建立 HUD 时间线，把轴和视频对齐，再推断其余记号 | step1.md §3–7 |
| S4 集中提问 | 把问题清单一次问完；属于角色的结论，问过用户后存入语义卡 | step1.md §8 |
| S5 生成前检查（关口 G2） | 按清单检查 timeline.json，全部满足才能生成代码 | [harness/timeline.md](harness/timeline.md) §3 |
| S6 生成代码并自检 | 按骨架生成 3 个角色文件和 verify_chain，然后自检 | [harness/step2.md](harness/step2.md) §1–7 |
| S7 打包交付 | 先问 team.json 的字段，再打 zip 并校验，写 README | step2.md §8 |
| S8 实测迭代 | 读日志、对比视频，先说明方案，用户同意后再出下一版 | [harness/iterate.md](harness/iterate.md) |

常识见 [knowledge/basics.md](knowledge/basics.md)，角色语义卡见 [knowledge/cards/](knowledge/cards/README.md)。

## 怎么问用户

- 用 AskUserQuestion 提问，每题只问一个点，每次调用最多 4 题。
- 涉及视频的问题，附上截图路径和视频时刻。
- 第一个问题永远是确认文字轴（G1），单独问；其余问题等 S3 全部做完后再集中问。
