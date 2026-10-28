# timeline.json 格式与关口 G2

每个案例维护 `<队名>/skilltest-v<N>/timeline.json`。
该文件交接动作模型、证据、参考耗时和未知。
由 Agent 维护并按本文件检查。

## 1 结构示例

以下片段演示字段，不代表完整节点链或已通过 G2。
数值仅用于展示记录方式。

```json
{
  "case": {
    "team": "示例队", "version": "skilltest-v1",
    "chars": ["Cantarella", "Galbrena", "Phrolova"],
    "goal": "复现选定启动轴与循环轴"
  },
  "sources": {
    "video": {
      "ref": "用户提供的参考视频", "file": "../media/video.mp4",
      "width": 1920, "height": 1080, "fps": 30, "frame_count": 900,
      "duration_s": 30.0, "playback_rate": null, "edits": "unknown",
      "coverage": [[0.0, 30.0]], "timer": "可读倒计时"
    },
    "axis_text": {"raw": "坎 RQ", "from": "user", "confirmed": true},
    "legend": {"from": "用户确认", "entries": {"R": "共鸣解放", "Q": "声骸"}},
    "constellations": {"Cantarella": {"author": 0, "user": 0}},
    "conditions": {
      "game_version": null, "framework_commit": null,
      "author": {"initial_resources": "未确认"},
      "user": {"initial_resources": "未确认"}
    }
  },
  "decisions": [
    {
      "id": "D1", "refs": ["Cantarella.f1#0"],
      "observation": "R 后出现演出，随后 HUD 恢复",
      "conclusion": "该次 R 已生效",
      "implementation": "按框架返回语义及 HUD 恢复确认",
      "evidence": [{"source": "video", "grade": "B", "at": 1.2, "frames": ["../media/frames/r.png"]}],
      "conditions": "本次片段及对应共鸣链",
      "unknowns": ["I1"], "impact": "R 后下一步的发键时机",
      "verify": "实测核对 R 演出结束与后续动作"
    }
  ],
  "nodes": [
    {
      "id": "Cantarella.f1", "char": "Cantarella", "axis": "f", "line": "坎 RQ",
      "t_start": 0.0, "t_end": 5.3, "next": "Galbrena.f1",
      "entry": {"kind": "initial", "evidence_refs": []},
      "exit": {
        "kind": "normal", "con_full": false,
        "completion": "声骸已生效且可切人", "allow_fill": false,
        "on_timeout": "记录 fallback 后普通切人", "evidence_refs": ["D2"]
      },
      "steps": [
        {
          "token": "R", "enhanced": false, "op": "tap", "hold_s": null,
          "t_start": 1.2, "t_end": 4.0, "timing": "condition",
          "precondition": "入场动作结束且共鸣能量满足",
          "trigger": {"kind": "ready", "condition": "R 可用", "anchor": null, "delay_s": null, "clock": null},
          "completion": "演出结束，恢复可操作", "cancel": "按角色已确认规则",
          "depends_on": [],
          "wait": {"timeout_s": 5.0, "basis": "示例保护时限，实测待核对", "on_timeout": "记录 fallback 后跳过"},
          "evidence": {"grade": "B", "frames": ["../media/frames/r.png"]},
          "decision_refs": ["D1"], "decided_by": "video", "note": "示例动作"
        }
      ]
    }
  ],
  "reference_timings": [
    {
      "id": "T1", "level": "node", "refs": ["Cantarella.f1"],
      "start_event": "Cantarella 确认入场", "end_event": "Galbrena 确认入场",
      "observations": [
        {
          "run": 1, "t_start": 0.0, "t_end": 5.3,
          "video_s": 5.3, "real_s": null, "game_s": 3.5,
          "timer_start": "00:30.00", "timer_end": "00:26.50",
          "freeze_intervals": [[1.5, 3.3]],
          "frames": ["../media/frames/entry.png", "../media/frames/exit.png"],
          "precision_s": 0.1
        }
      ],
      "sample_status": "single", "conditions": "示例片段，速度未核实",
      "tolerance": null, "issue_refs": ["I1"]
    }
  ],
  "issues": [
    {
      "id": "I1", "refs": ["T1", "D1"], "kind": "timing", "impact": "trial",
      "question": "视频是否加速？", "status": "open", "answer": null,
      "assumption": "不从该视频换算真实等待时长",
      "verify": "获取原视频速度说明，并核对实测事件",
      "on_failure": "保留游戏时间比较，重新量真实时间"
    }
  ]
}
```

`D2` 及后续节点需在完整案例中补齐。
不得把示例值复制成真实队伍的结论。
路径相对当前 `timeline.json`，或使用明确的原素材绝对路径。

## 2 字段约定

### 来源与判断

| 字段 | 约定 |
|---|---|
| `case.chars` | 3 个角色类名 |
| `sources.axis_text.from` | `user` / `video_frame` / `description` / `comment` |
| `sources.constellations.<类名>` | `author` 与 `user` 的共鸣链，0–6；未知填 `null` |
| `sources.video.playback_rate` | 1 秒视频对应的真实秒数；未知填 `null` |
| `sources.video.edits` | `none` / `known` / `unknown`；`known` 时在 `info.md` 列剪辑区间 |
| `sources.conditions` | 影响本案的版本、装备、资源和场景条件；未知及影响写入 `issues` |
| `decisions[].refs` | 受判断影响的节点、步骤或时间区间编号 |
| `decisions[].evidence` | 来源位置；视频带时刻和帧路径，代码带版本与行号 |
| `decisions[]` 其余字段 | 观测、结论、实现选择、适用条件、未知、影响范围、验证办法，按 [evidence.md](evidence.md) |

### 节点与动作

| 字段 | 约定 |
|---|---|
| `nodes[].id` | `<类名>.<f或s><序号>`；f 为启动轴，s 为循环轴，各角色分别编号 |
| `nodes[].next` | 下个节点 id；全部存在，启动接循环，循环首尾相接 |
| `nodes[].entry.kind` | `initial` / `intro` / `normal` / `unknown` |
| `nodes[].exit.kind` | 目标的入场方式：`intro` / `normal` / `unknown` |
| `nodes[].exit.con_full` | 出场协奏是否满；未知为 `null`，机制例外写入判断 |
| `nodes[].exit.completion` | 最后动作的结束和可切人判据 |
| `nodes[].exit.allow_fill` | 是否允许补协奏；必须有依据，不得默认补满 |
| `nodes[].exit.on_timeout` | 未满足离场条件时的处理 |
| `entry/exit.evidence_refs` | 支持入场或切人判断的 `decisions` 编号 |
| `steps[].token` | `A` `Z` `E` `R` `Q` `闪` `跳` `↓` |
| `steps[].count` | A 的连续段数；只表示已知段数 |
| `steps[].enhanced` | 是否强化，依据本案记号说明 |
| `steps[].op` | `tap` / `hold` / `unknown` / `n/a` |
| `steps[].hold_s` | 已确认的按住秒数；条件松开时可为 `null` |
| `steps[].timing` | `fixed` / `condition` / `unknown`；表示实现选择，不能由波动自动推断 |
| `steps[].precondition` | 动作前必须满足的状态和资源 |
| `steps[].trigger.kind` | `immediate` / `ready` / `state` / `delay` / `unknown` |
| `trigger.condition` | 立即、就绪或状态触发的明确含义 |
| `trigger.anchor/delay_s/clock` | 延迟触发的起点、秒数及 `real` 或 `game` 口径 |
| `steps[].completion/cancel` | 生效与结束判据、取消或中断时机；不同信号分别描述 |
| `steps[].depends_on` | 依赖的节点、步骤或判断编号；无依赖为 `[]` |
| `steps[].wait` | 正数 `timeout_s`、依据 `basis`、超时处理 `on_timeout` |
| `steps[].evidence.grade` | A/B/C/D/none，含义见 evidence.md §3 |
| `steps[].decided_by` | `video` / `card` / `user` / `text`；决定来自何处，不表示机制已实测 |
| `steps[].decision_refs` | 解释该动作的 `decisions` 编号 |

`t_start`、`t_end`、`evidence.at` 及 `freeze_intervals` 均为原视频秒数。
步骤 `t_start/t_end` 的事件定义必须写入 `note` 或关联判断。
输入、生效、结束与返回时刻必须分别记录。
可用 `decisions[].evidence.at` 或关键动作区间记录各事件。
无法观测的时刻填 `null`，并登记缺项。
其他时长必须带字段规定的口径。
固定时长没有依据时，登记缺项，不得从参考总时长反推等待。

### 参考耗时与缺项

| 字段 | 约定 |
|---|---|
| `reference_timings[].level` | `cycle` / `node` / `segment` |
| `start_event/end_event` | 可复现的起止事件定义 |
| `observations[]` | 每遍保留原始时刻、三个口径的时长、读数、帧路径、精度 |
| `sample_status` | `single` / `repeated` / `unavailable` |
| `conditions/tolerance` | 适用条件和可接受偏差依据；尚不能确定时填 `null` 并关联缺项 |
| `issue_refs` | 测量或适用条件未知时关联缺项；不可测区间保留空 `observations` |
| `issues[].refs` | 节点、`<节点id>#<从0开始的步骤序号>`、判断或时间区间编号 |
| `issues[].kind` | `axis_text` / `notation` / `conflict` / `low_confidence` / `missing` / `constellation` / `timing` / `state` / `trigger` / `dependency` / `other` |
| `issues[].impact` | `blocking` / `trial` / `noncritical`，判定见 evidence.md §4 |
| `issues[].status` | `open` / `resolved`；暂存、迁入及状态回写遵守 [evidence.md §4](evidence.md) |
| `issues[].assumption/verify/on_failure` | 试验采用的假设或数值、验证办法、失败处理 |

未知用 `null` 或明确的 `unknown`，不得填造值。
时间测量和差值计算遵守 [timing.md](timing.md)。

## 3 关口 G2

以下适用项全部通过，才能生成整队代码。
不适用项必须写原因。

- [ ] G1 已确认，所选片段、角色和轴原文可追溯。
- [ ] 各角色的作者与用户共鸣链已知，差异影响已处理。
- [ ] 适用条件、初始资源和场景依赖已检查。
- [ ] 没有未解决的 `blocking` 缺项。
- [ ] 开放的 `trial` 缺项有假设、验证办法和失败处理。
- [ ] 开放的 `noncritical` 缺项有不影响本次行为的理由。
- [ ] 按法、触发、生效、完成和切人判据明确。
- [ ] 没有影响行为的 `op/timing/trigger.kind: unknown`。
- [ ] C/D 推断的关键行为有用户意图确认或已确认知识支撑。
- [ ] 资源、后台效果、延迟和跨轮依赖有记录。
- [ ] 出场切人类型、协奏状态与下个节点入场一致。
- [ ] 每次补协奏均有原轴依据，普通切人没有被改成变奏。
- [ ] `next` 全部存在；仅一条 f→s，s 覆盖全部循环节点并闭合。
- [ ] 整轮、每个节点和关键动作段有参考耗时记录或缺项。
- [ ] 步骤起止事件已定义，输入、生效、结束与返回没有混用。
- [ ] 参考耗时的事件、口径、各遍观察和精度可复查。
- [ ] 所有判断、步骤、时间和缺项引用均能定位。

检查结果写入 `notes.md`，并输出两张表：

1. 节点 / 轴原文 / 视频区间 / 动作与触发判据 / 切人方式 / 下个节点。
2. 参考耗时表，按 timing.md 列各遍、口径和待测项。

未通过时，退回 [轴解析](../skills/rotation/SKILL.md) 或 [时序建模](../skills/timeline/SKILL.md) 补证。
