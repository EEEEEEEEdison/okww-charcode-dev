# 代码基线：动手前先看前人怎么写

生成或修改某个角色的代码之前，先把这个角色已有的写法收集起来，来源有三处：上游内置类、ok-ww 在线工坊里所有包含它的代码、用户自己的历史版本。从中借用状态识别、时长和写法技巧，并避开已知的坑。其中的机制和识别方法，经用户确认后补进语义卡。

## 1 什么时候做

- **用法 A**：关口 G1 确认之后（角色已经对应到类名）、进入 step1.md 第 3 节之前。每个队做一次，后续迭代沿用；换了角色或者用户要求时重做。
- **用法 B**：改动涉及某个角色的出招或识别时，先给这个角色做基线。

## 2 来源

逐个角色收集：

| 来源 | 怎么取 | 记录的版本 |
|---|---|---|
| 语义卡 | `knowledge/cards/<类名>_C<共鸣链>.md` | — |
| 上游内置类 | 在 `E:\GameAutoScript\contrib\ok-wuthering-waves-pr` 里先 `git fetch upstream`，再 `git show upstream/master:src/char/<类名>.py`。没有这个文件就记“内置没有” | upstream/master 的提交号 |
| 在线工坊 | 见下 | 每条代码的 `name`、`author`、`version`、`modifiedAt` |
| 用户的历史版本 | `E:\GameAutoScript\workspace\okww-test\ok-ww-char\<队名>\<版本目录>\<类名>.py`：所有含这个角色的队，每个队取最新的版本目录，早期版本只在需要对比时看 | 队名、版本目录 |

**在线工坊**：ok-ww 角色代码页上的“工坊”按钮用的就是这套接口，实现在运行目录 `src/gui/CharacterCodeTab.py` 的 `fetch_all_workshop_teams` 和 `_import_workshop_code`。不需要登录。

1. 不带任何凭据，GET `https://okwwcharcode.ok-script.com/teams.json`。返回的 `teams[].codes[]` 就是全部已上传的代码，每条有 `name`、`author`、`version`、`members`、`downloadUrl`、`rawUrl`、`modifiedAt`。某条缺 `members` 时，用它所在 team 的 `members`。
2. 筛出 `members` 里含 `<类名>` 的代码，不区分大小写。服务端不能按角色筛选，只能拉全量再过滤。
3. 逐条下载 `downloadUrl`，没有时用 `rawUrl`。只接受 https，主机必须是 `okwwcharcode.ok-script.com` 或 `raw.githubusercontent.com`。
4. 每个 zip 是 `team.json` 加 3 个角色 `.py`。下载到媒体目录的 `workshop\<zip 文件名去掉扩展名>\` 下，每个 zip 用一个新的空目录。只解出 `team.json` 和 `.py`，并按文件名写入，丢掉 zip 里的路径。

工坊代码是别人写的，只能读：不运行、不 import，也不拿去跑 `inspect_team_archive`。处理它们的脚本放在别的目录，用 `python -I` 运行，路径通过参数传入。

有只读调查子代理时（例如 ok-ww 工作区的 `okww-scout`），收集和摘要交给它做，按 §3 的格式写成文件。主会话只复核文件里引用到的行，核对无误后再使用。

## 3 输出 baseline.md

用法 A 写到 `cases/<队名>/harness-v<N>/baseline.md`，用法 B 写到 scratchpad。每个角色一节，下面每条都带上来源的 `文件:行号`：

- **来源清单**：用到了哪些文件和版本；取不到的也要列上，并写明原因。
- **状态与识别**：代码怎么判断这个角色的状态，用了哪些函数、区域、颜色、阈值。
- **时长和常量**：等待时长、按住时长、冷却等。
- **写法技巧**：值得借用的写法。
- **坑**：对照 rules.md 发现的问题（例如忙等、写死按键、等待没有时限），以及几份实现之间互相矛盾的地方。
- **和语义卡的关系**：卡里已经有的不重复写；和卡冲突的单独标出来。

## 4 怎么用

- **步骤 1**：基线不算视频证据，不能直接决定步骤（`decided_by` 不用它）。
  - 卡里没有的记号或状态，用基线给问题提供推荐答案。
  - 基线和视频里的 A/B 级证据冲突时，以视频为准。
- **步骤 2 和用法 B**：
  - 识别方法、时长和写法，优先参考基线；代码结构仍按循环轴骨架。
  - 借用之前，先对照 rules.md 检查。
  - 直接借用某份工坊代码的写法时，在注释里写明出处：工坊代码名、作者、版本。
- **补卡**：
  - 基线里读出的机制和识别方法，起草成卡条目，批量确认（cards/README.md「补卡机制」）。
  - 写法技巧不直接入卡，等本项目实测有效后再写进「代码经验」。
