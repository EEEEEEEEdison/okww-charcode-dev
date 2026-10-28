"""汇总一次 MCP 实测运行：截取本次运行的 ok-script.log，列节点链、技能结果、问题行及其录像时刻。

用法：python -I -B scripts/mcp_report.py <运行目录> [--frames]
运行目录是 run_task 返回的 artifact_directory，须含 status.json 和 templates/mcp/matrix_run.py 写的 summary.json。
日志取 <working>/logs/ok-script.log 中本次运行时段的行（毫秒时间戳，不含 pythonw 控制台噪声）。
输出写到 <运行目录>/report/：run.log（日志切片）、events.json、report.md。
--frames：在每个问题行的录像时刻取 -0.5、0、+0.5、+1.0 秒 4 帧拼成一张图，写到 report/frames/。
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LINE_RE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) (\w+) \S+ (.*)$')
CHAR_RE = re.compile(r'^(\w+):\[(\w+)\] (.*)$')
ISSUE_RE = re.compile(r": fail\b|^fallback\b|^interrupt\b|clicked liberation but no effect|not in team while switching"
                      r"|can't find next char|not in combat")
FRAME_OFFSETS = (-0.5, 0.0, 0.5, 1.0)


def parse_log(log_path, start, end):
    """返回 [start, end] 内的日志行；无时间戳的续行（如 Traceback）并入上一行。"""
    rows = []
    for raw in log_path.read_text(encoding='utf-8', errors='replace').splitlines():
        m = LINE_RE.match(raw)
        if not m:
            if rows:
                rows[-1]['extra'].append(raw)
            continue
        ts = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S').timestamp() + int(m.group(2)) / 1000
        if start <= ts <= end:
            rows.append({'ts': ts, 'level': m.group(3), 'msg': m.group(4), 'extra': []})
        elif rows and ts > end:
            break
    return rows


def classify(rows, t0):
    nodes, issues, casts = [], [], {}
    for r in rows:
        r['t'] = round(r['ts'] - t0, 3)
        m = CHAR_RE.match(r['msg'])
        if m:
            char, node, text = m.groups()
            if text.startswith('enter'):
                nodes.append({'t': r['t'], 'char': char, 'node': node, 'event': text})
            cm = re.match(r'(?:cast|retry) (\w+): (ok|fail)', text)
            if cm:
                casts.setdefault(f'{char} {cm.group(1)}', {'ok': 0, 'fail': 0})[cm.group(2)] += 1
        else:
            task, _, body = r['msg'].partition(':')
            char, node, text = task, None, body.strip()
        if r['level'] in ('WARNING', 'ERROR', 'CRITICAL') or ISSUE_RE.search(text):
            issues.append({'t': r['t'], 'ts': r['ts'], 'level': r['level'], 'char': char, 'node': node,
                           'text': text, 'extra': r['extra'][:6]})
    return nodes, issues, casts


def loop_stats(nodes):
    """启动轴到第一个 S 节点为止；循环轮按第一个 S 节点的再次进入切分。墙钟，含冻结。"""
    loop = [n for n in nodes if n['node'].startswith('S')]
    if not nodes or not loop:
        return {'loop_start': None, 'startup_s': None, 'rounds': []}
    first = (loop[0]['char'], loop[0]['node'])
    starts = [n['t'] for n in loop if (n['char'], n['node']) == first]
    return {'loop_start': f'{first[0]}.{first[1]}', 'startup_s': round(loop[0]['t'] - nodes[0]['t'], 2),
            'rounds': [round(b - a, 2) for a, b in zip(starts, starts[1:])]}


def extract_frames(mp4, fps, items, out_dir):
    import cv2
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(mp4))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for k, item in enumerate(items):
        tiles = []
        for off in FRAME_OFFSETS:
            idx = min(max(round((item['video_s'] + off) * fps), 0), total - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            frame = cv2.resize(frame, (640, 360))
            cv2.putText(frame, f'{idx / fps:.2f}s ({off:+.1f})', (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            tiles.append(frame)
        if len(tiles) == 4:
            name = f"{k:02d}_{item['video_s']:.1f}s.jpg"
            cv2.imwrite(str(out_dir / name), cv2.vconcat([cv2.hconcat(tiles[:2]), cv2.hconcat(tiles[2:])]))
            item['frames'] = f'frames/{name}'
    cap.release()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir', type=Path)
    ap.add_argument('--frames', action='store_true')
    args = ap.parse_args()
    run_dir = args.run_dir
    status = json.loads((run_dir / 'status.json').read_text(encoding='utf-8'))
    summary = json.loads((run_dir / 'summary.json').read_text(encoding='utf-8'))
    steps_path = run_dir / 'steps.json'
    steps = json.loads(steps_path.read_text(encoding='utf-8')) if steps_path.is_file() else []
    start, end = status['created_at'], status.get('finished_at') or datetime.now().timestamp()
    working = run_dir.parents[2]  # <working>/logs/mcp/<run_id>
    rows = parse_log(working / 'logs' / 'ok-script.log', start, end)
    if not rows:
        sys.exit(f'no ok-script.log lines between {start} and {end}')

    day = datetime.fromtimestamp(start).strftime('%Y-%m-%d ')

    def clock_ts(clock):
        return datetime.strptime(day + clock, '%Y-%m-%d %H:%M:%S.%f').timestamp()

    rec = summary.get('recorder', {})
    fps = rec.get('fps', 15)
    video_t0 = clock_ts(rec['video_start']) if rec.get('video_start') else None
    gaps = [(clock_ts(a), g) for a, g in rec.get('gaps_over_0_5s', [])]
    fight_start = next((clock_ts(s['clock']) for s in steps if s['step'] == 'fight1_start'), start)
    nodes, issues, casts = classify(rows, fight_start)
    for item in issues:
        item['video_s'] = round(item['ts'] - video_t0, 2) if video_t0 else None
        # 落在采集空档里的时刻，录像帧是空档前的旧画面
        item['stale_frame'] = any(a <= item['ts'] <= a + g for a, g in gaps)

    out = run_dir / 'report'
    out.mkdir(exist_ok=True)
    if args.frames and video_t0 and (run_dir / 'record.mp4').is_file():
        extract_frames(run_dir / 'record.mp4', fps, [i for i in issues if i['video_s'] is not None], out / 'frames')
    (out / 'run.log').write_text('\n'.join(
        f"{datetime.fromtimestamp(r['ts']).strftime('%H:%M:%S.%f')[:-3]} {r['level']} {r['msg']}"
        + ''.join('\n    ' + e for e in r['extra']) for r in rows) + '\n', encoding='utf-8')
    stats = loop_stats(nodes)
    for item in issues:
        item.pop('ts')
    events = {'run_id': status['run_id'], 'state': status['state'], 'error': status.get('error'),
              'manifest': summary.get('manifest'), 'team': summary.get('team'), 'code': summary.get('code'),
              'team_score': summary.get('team_score'), 'fights': summary.get('fights'),
              'timeout': summary.get('timeout', False), 'recorder': rec, 'loop': stats, 'casts': casts,
              'issues': issues, 'nodes': nodes, 'steps': steps}
    (out / 'events.json').write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding='utf-8')

    codes = [f"{c['class']}:{c['sha256_16']}" for c in summary.get('code') or [] if c]
    lines = [f"# 运行 {status['run_id']}", '',
             f"- 状态：{status['state']}；错误：{status.get('error') or '无'}；战斗上限超时：{summary.get('timeout', False)}",
             f"- 队伍：{summary.get('team')}；版本：{summary.get('manifest')}；代码：{codes}",
             f"- 队伍得分：{summary.get('team_score')}；战斗段数：{summary.get('fights')}",
             f"- 录像：{rec.get('written')} 帧 / {fps} fps，补齐 {rec.get('padded')} 帧，"
             f"最大采集空档 {rec.get('max_gap')} 秒（>0.5 秒共 {len(gaps)} 处）",
             f"- 启动轴 {stats['startup_s']} 秒；循环起点 {stats['loop_start']}；各轮墙钟 {stats['rounds']}",
             f"- 节点 {len(nodes)} 个；问题行 {len(issues)} 条", '', '## 技能结果', '']
    lines += [f'- {k}: ok {v["ok"]} / fail {v["fail"]}' for k, v in sorted(casts.items())]
    lines += ['', '## 问题行（t 从 fight1_start 起算；video 为录像秒）', '']
    lines += [f"- t={i['t']:.2f} video={i['video_s']}{' 旧帧' if i['stale_frame'] else ''} {i['level']} "
              f"{i['char']}[{i['node']}] {i['text']}" + (f" → {i['frames']}" if i.get('frames') else '')
              for i in issues]
    lines += ['', '## 节点步骤', ''] + [f"- t={s['t']} {s['clock']} {s['step']}" for s in steps]
    (out / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
    print(f'\nreport: {out}')


if __name__ == '__main__':
    main()
