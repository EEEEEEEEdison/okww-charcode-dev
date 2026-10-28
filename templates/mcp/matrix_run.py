"""终焉矩阵单局实测：编队详情页 → 前往 → 大厅核对队伍与代码 → 交互回音之钥开战 → 切开场角色 → 锁敌 → 自动战斗 → 结算页停下。

参数读同目录 mcp_test.json。全程后台录像（record.mp4，实时），节点留帧写 steps.json，汇总写 summary.json。
结算页不点任何按钮；离开结算页和是否保存成绩由 matrix_nav.py 处理。
"""
import hashlib
import inspect
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
from ok import BaseTask

from src.char import CustomCharLoader as loader
from src.task.AutoCombatTask import AutoCombatTask

CONFIG = json.loads(Path(__file__).with_name('mcp_test.json').read_text(encoding='utf-8'))


def local_time(ts):
    return datetime.fromtimestamp(ts).strftime('%H:%M:%S.%f')[:-3]


class Recorder:
    """后台线程把画面写成实时 mp4：视频第 i 帧对应 video_start + i / fps。

    主要读执行器的帧快照，不与任务抢采集。任务超过 FILL_AFTER 秒没取帧（sleep、长等待）时，
    非阻塞地向采集后端补取一帧；后端正忙就跳过，不拖慢任务。两帧之间的空档用上一帧补齐。
    """
    FILL_AFTER = 0.2

    def __init__(self, executor, out_dir, fps, size):
        self.executor, self.fps, self.size = executor, fps, tuple(size)
        self.path = out_dir / 'record.mp4'
        self.writer = cv2.VideoWriter(str(self.path), cv2.VideoWriter_fourcc(*'mp4v'), fps, self.size)
        self.t0, self.last_img, self.written, self.padded, self.fills = None, None, 0, 0, 0
        self.seen = []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def _grab(self):
        grab = getattr(self.executor.method, 'do_get_frame_wait', None)
        if grab is None:
            return None
        try:
            return grab(0)
        except Exception:
            return None

    def _push(self, frame, ts):
        self.seen.append(ts)
        if self.t0 is None:
            self.t0 = ts
        slot = int((ts - self.t0) * self.fps)
        if slot < self.written:
            return
        while self.written < slot:
            self.writer.write(self.last_img)
            self.written += 1
            self.padded += 1
        self.last_img = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)
        self.writer.write(self.last_img)
        self.written += 1

    def _loop(self):
        last_seen, last_try = None, 0.0
        while not self.stop_event.is_set():
            snap = self.executor.get_frame_snapshot()
            now = time.time()
            if snap is not None and snap[1] != last_seen:
                last_seen = snap[1]
                self._push(snap[0], snap[1])
            elif self.t0 is not None and now - max(self.seen[-1], last_try) > self.FILL_AFTER:
                last_try = now
                frame = self._grab()
                if frame is not None:
                    self.fills += 1
                    self._push(frame, now)
            time.sleep(0.01)

    def start(self):
        assert self.writer.isOpened(), 'VideoWriter not opened'
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)
        self.writer.release()
        gaps = [(a, b - a) for a, b in zip(self.seen, self.seen[1:]) if b - a > 0.5]
        return {'mp4': str(self.path), 'fps': self.fps, 'video_start': local_time(self.t0) if self.t0 else None,
                'written': self.written, 'padded': self.padded, 'seen': len(self.seen), 'fills': self.fills,
                'max_gap': round(max((g for _, g in gaps), default=0), 3),
                'gaps_over_0_5s': [[local_time(a), round(g, 2)] for a, g in gaps]}


class Task(BaseTask):
    def reset_to_start(self):
        self.log_info('matrix_run: start page is prepared by matrix_nav, no reset')

    def verify_start_state(self):
        texts = [b.name for b in (self.ocr(log=False) or [])]
        joined = ' '.join(texts)
        assert '终焉矩阵' in joined and '角色编队' in joined, f'not on matrix team detail page: {texts[:20]}'
        # 方括号大号槽位编号全屏 OCR 读不出，裁到编队栏左侧才能读出“(04)”
        slot_texts = [b.name for b in (self.ocr(0.44, 0.64, 0.56, 0.76, log=False) or [])]
        assert any(CONFIG['slot_label'] in t for t in slot_texts), \
            f"team slot {CONFIG['slot_label']} not shown: {slot_texts}"
        assert self._go_button(), 'no 前往 button'

    def _go_button(self):
        boxes = self.ocr(match='前往', log=False) or []
        boxes = [b for b in boxes if b.y > self.height * 0.8]
        return boxes[0] if boxes else None

    def _mark(self, name, **kw):
        self.next_frame()
        now = time.time()
        cv2.imwrite(str(self.out / f'{len(self.steps):02d}_{name}.jpg'), self.frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        self.steps.append({'t': round(now - self.t0, 2), 'clock': local_time(now), 'step': name, **kw})
        self.log_info(f'mcp_mark t={now - self.t0:.2f} {name} {kw}')
        (self.out / 'steps.json').write_text(json.dumps(self.steps, ensure_ascii=False, indent=1), encoding='utf-8')

    def _on_field(self, combat):
        ok, idx, _ = combat.in_team()
        if not ok or not (0 <= idx < len(combat.chars)) or combat.chars[idx] is None:
            return None, idx
        return type(combat.chars[idx]).__name__, idx

    @staticmethod
    def _code_info(char):
        """取类自身定义的方法所在文件；继承来的方法会指向 BaseChar.py。"""
        if char is None:
            return None
        cls = type(char)
        own = [v for v in vars(cls).values() if inspect.isfunction(v)]
        path = own[0].__code__.co_filename if own else ''
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16] if path and Path(path).is_file() else None
        return {'class': cls.__name__, 'module': cls.__module__, 'source': path, 'sha256_16': digest}

    def run(self):
        self.out, self.steps, self.t0 = Path(self.artifact_directory), [], time.time()
        combat = self.get_task_by_class(AutoCombatTask)
        rec_cfg = CONFIG.get('record', {})
        recorder = Recorder(self.executor, self.out, rec_cfg.get('fps', 15), rec_cfg.get('size', [960, 540]))
        recorder.start()
        manifest = loader.read_team_manifest(CONFIG['team']) or {}
        summary = {'config': CONFIG, 'started': local_time(self.t0),
                   'manifest': {k: manifest.get(k) for k in ('version', 'code_mode')}}
        try:
            self.click(self._go_button(), after_sleep=1)
            self._mark('click_go')
            combat.wait_in_team_and_world(time_out=60)
            # 清空旧角色对象再识别，导入的新代码才会生效
            combat.chars = [None, None, None]
            combat.load_chars()
            name, idx = self._on_field(combat)
            names = [type(c).__name__ if c else None for c in combat.chars]
            summary['team'] = names
            summary['code'] = [self._code_info(c) for c in combat.chars]
            self._mark('lobby', on_field=name, slot=idx, team=names)
            assert set(names) == set(CONFIG['team']), f"team mismatch {names} != {CONFIG['team']}"

            # 大厅里正前方是回音之钥，走到出现 F 提示再交互开战
            combat.walk_until_f(direction='w', time_out=CONFIG.get('walk_time_out', 4))
            self._mark('f_found')
            self.send_key('f')
            opener = CONFIG.get('opener')
            if opener and name != opener:
                self.sleep(CONFIG.get('switch_delay', 0.15))
                self.send_key(str(names.index(opener) + 1))
                self.sleep(0.5)
                name2, _ = self._on_field(combat)
                self._mark('switched', on_field=name2, ok=name2 == opener)
            else:
                self._mark('f_pressed', on_field=name)
            locked = combat.wait_combat(target=True, time_out=15, raise_if_not_found=False)
            self._mark('lock', in_combat=bool(locked))
            assert locked, 'lock-on failed'

            # MCP 运行期间触发器暂停，必须显式调用自动战斗；队伍 HUD 消失超过 end_out_of_team 秒视为进入结算
            fights, out_since = 0, None
            while time.time() - self.t0 < CONFIG.get('fight_cap', 260):
                if not combat.in_team_and_world():
                    out_since = out_since or time.time()
                    if time.time() - out_since > CONFIG.get('end_out_of_team', 8):
                        break
                    self.sleep(0.3)
                    continue
                out_since = None
                if combat.wait_combat(target=True, time_out=3, raise_if_not_found=False):
                    fights += 1
                    self._mark(f'fight{fights}_start')
                    ret = combat.run()
                    self._mark(f'fight{fights}_end', ret=ret)
            else:
                summary['timeout'] = True
            summary['fights'] = fights
            self._mark('end', fights=fights)
            texts = [b.name for b in (self.ocr(log=False) or []) if not b.name.startswith('特征码')]
            summary['result_texts'] = texts[:40]
            if '队伍得分' in texts and texts.index('队伍得分') + 1 < len(texts):
                summary['team_score'] = texts[texts.index('队伍得分') + 1]
        finally:
            summary['recorder'] = recorder.stop()
            summary['finished'] = local_time(time.time())
            (self.out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')
        assert not summary.get('timeout'), 'fight cap reached'
