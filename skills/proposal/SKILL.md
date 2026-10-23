---
name: proposal
description: okwwcharcode（ok-ww 角色代码开发）的知识提议阶段。用于实测迭代得到可入卡的新结论，或与现有语义卡冲突的已验证证据时。把本案证据整理成知识提议文件，脱敏后问用户一次是否反馈。同意后用 gh 创建 GitHub Issue、打开预填的新建 Issue 页面或改发邮件，交仓库维护者审核。适用于知识反馈、补卡提议、语义卡纠错、贡献知识。
---

# 知识提议

## 输入

本案 `notes.md`、`timeline.json.issues`、当前语义卡，以及本轮实测结论。

## 执行

1. 读取 [knowledge-maintenance.md §2–3](../../maintainer/knowledge-maintenance.md) 的入卡条件和条目写法。
2. 从本案挑出候选。候选必须满足入卡条件，并有可定位的证据。
3. 没有候选时，说明原因并结束，不生成文件，不提问。
4. 按 [提议模板](../../templates/knowledge-proposal.md) 逐条填写。原文照抄当前卡片，版本号取 [VERSION](../../VERSION)。
5. 脱敏：本机路径改为 `<工作区>`、`<ok-ww>` 等占位，删除用户名、账号、邮箱和令牌。视频只写链接和时刻。
6. 写入 `<工作区>/<队名>/proposals/<YYYYMMDD>-<短名>.md`，不得写入本 Skill 安装目录。
7. 用 [submit_proposal.py](../../scripts/submit_proposal.py) 检查，未通过时按输出改正：

   ```text
   <ok-ww python.exe> -I -B <本仓库>/scripts/submit_proposal.py <提议 .md> --dry-run
   ```

8. 给出提议全文，用宿主的结构化提问工具问一次。题干写明条数、反馈后公开在 GitHub Issue、同意按 MIT 许可收录。选项为“反馈”“用邮件反馈”“不反馈”。
9. 按回答处理：
   - 反馈：去掉 `--dry-run` 运行，脚本自动选 gh 或浏览器。
   - 用邮件反馈：加 `--method email` 运行，告诉用户收件邮箱、邮件主题和附件路径。
   - 不反馈：保留文件，结束。

## 输出与通过条件

- 提议文件通过 `submit_proposal.py` 的格式和隐私检查。
- 每条提议有类型、位置、原文、提议、背景、证据、运行条件和验证状态。
- 用户只被问一次，且回答前没有提交任何内容。
- 反馈后告诉用户 Issue 链接，或页面已打开待提交，或邮件发送信息。
- 未经维护者审核的提议不得写入语义卡。

需要补证据时，退回 [实测迭代](../iteration/SKILL.md)。

进入、退回或交给其他阶段时，按 [总入口的阶段切换](../../SKILL.md#阶段切换) 加载。
