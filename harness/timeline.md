# timeline.json 格式与关口 G2

每个案例一份：`cases/<队名>/harness-v<N>/timeline.json`。由 AI 按本文件手写、维护，不依赖校验工具。

## 1 结构

```json
{
  "case": {"team": "弗坎嘉", "version": "harness-v1", "chars": ["Cantarella", "Galbrena", "Phrolova"]},
  "sources": {
    "video": {"ref": "BV1nAC6BRETp", "file": "<媒体目录>/video.m4s", "width": 768, "height": 480, "fps": 30},
    "axis_text": {"raw": "启动轴\n坎 RQ\n...", "from": "video_frame", "confirmed": true},
    "legend": {"from": "description", "entries": {"A": "普攻", "红字": "强化技"}},
    "constellations": {"Cantarella": {"author": 0, "user": 0}}
  },
  "nodes": [
    {
      "id": "Cantarella.f1", "char": "Cantarella", "axis": "f", "line": "坎 RQ",
      "t_start": 0.0, "t_end": 5.3, "next": "Galbrena.f1",
      "steps": [
        {"token": "R", "enhanced": false, "op": "tap", "hold_s": null,
         "t_start": 1.2, "t_end": null, "timing": "fixed",
         "evidence": {"grade": "B", "frames": ["frames/c_f1_r.png"]},
         "decided_by": "video", "note": "大招动画 1.5–4.5s"}
      ]
    }
  ],
  "issues": [
    {"id": "I1", "refs": ["Galbrena.s1#0"], "kind": "low_confidence",
     "question": "嘉贝莉娜循环轴开头的 Z 是长按多久？", "answer": null, "status": "open"}
  ]
}
```

## 2 字段约定

| 字段 | 取值 |
|---|---|
| `case.chars` | 3 个角色的类名 |
| `sources.axis_text.from` | `user` / `video_frame` / `description` / `comment` |
| `sources.constellations.<类名>` | `author`（作者）与 `user`（用户）的共鸣链，0–6；还不知道时填 null |
| `nodes[].id` | `<类名>.<f|s><序号>`。f 是启动轴，s 是循环轴，每个角色各自从 1 开始编号 |
| `nodes[].next` | 下一个节点的 id。启动轴最后一个节点接到循环轴，循环轴首尾相接 |
| `steps[].token` | `A` `Z` `E` `R` `Q` `闪` `跳` `↓` |
| `steps[].count` | 只用于 A，表示连续几段 |
| `steps[].enhanced` | 是否强化技（按作者的记号说明判断，例如红字） |
| `steps[].op` | `tap` / `hold` / `unknown` / `n/a`（↓ 之类没有按法的记号） |
| `steps[].hold_s` | op 为 `hold` 时的按住秒数 |
| `steps[].timing` | `fixed`（固定时长）/ `condition`（满足条件才触发，条件写在 note 里） |
| `steps[].evidence.grade` | A 按键显示 / B HUD 变化 / C 动作画面 / D 时间推断 / none |
| `steps[].decided_by` | `video` / `card` / `user` / `text`（照抄文字轴） |
| `issues[].kind` | `axis_text` / `notation` / `conflict` / `low_confidence` / `missing` / `constellation` / `other` |
| `issues[].refs` | 涉及的步骤，写成 `<节点id>#<步骤序号>` |
| `issues[].status` | `open` / `resolved`；resolved 时必须填 `answer` |

时间一律是视频里的秒数。

## 3 关口 G2：进入步骤 2 前逐条确认

以下全部满足才能生成代码。有任何一条不满足，回到步骤 1 补齐，或者继续问用户。

- [ ] `sources.axis_text.confirmed` 为 true（用户确认过文字轴）。
- [ ] 每个角色的 `constellations` 中，`author` 和 `user` 都已知；两者不同时，受影响的步骤已经问过用户。
- [ ] `issues` 里没有 `open`。
- [ ] 没有 `op: unknown` 的步骤。
- [ ] 凡是 C/D 级证据得出的结论，`decided_by` 都是 `user` 或 `card`，不是 `video`。
- [ ] 节点链正确：启动轴的 f 节点只有一条边接到循环轴，s 节点首尾相接，并且覆盖全部 s 节点；所有 `next` 都指向存在的节点。

检查完后，把 timeline 渲染成一张 markdown 对照表给用户看。表的列为：节点 / 轴原文 / 视频区间 / 步骤（记号、按法、时刻、证据等级与来源）/ 下一个节点。
