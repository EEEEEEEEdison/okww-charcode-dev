"""测试前置：把游戏推进到大世界可操作状态。

- 登录页、公告、月卡、开始游戏：每帧调用一次 AutoLoginTask.wait_login()。
- 已登录但停在菜单或挑战页面：wait_login() 连续 2 帧认不出登录元素时按 ESC，最多 MAX_ESC 次。
- 游戏未运行时，run_task 的设备准备阶段会先启动游戏（ok-ww 须以管理员身份运行）。
结果写 steps.json，每次画面变化留帧。
"""
import json
import re
import time

import cv2
from ok import BaseTask

from src.task.AutoLoginTask import AutoLoginTask

TIME_OUT = 180
MAX_ESC = 5
LOADING_RE = re.compile(r'^\d{1,3}%$')


class Task(BaseTask):
    def reset_to_start(self):
        self.log_info('preflight: observe and advance only')

    def verify_start_state(self):
        frame = self.executor.next_frame(time_out=10)
        assert frame is not None and frame.size > 0, 'no game frame'

    def _shot(self, name):
        cv2.imwrite(str(self.artifact_directory / f'{len(self.steps):02d}_{name}.jpg'), self.frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 80])

    def run(self):
        login = self.get_task_by_class(AutoLoginTask)
        self.steps, t0 = [], time.time()
        last_texts, idle, esc = None, 0, 0
        try:
            while time.time() - t0 < TIME_OUT:
                login.next_frame()
                if login.in_team_and_world():
                    login.logged_in = True
                    self.steps.append({'t': round(time.time() - t0, 1), 'state': 'in_world', 'esc': esc})
                    self._shot('in_world')
                    return True
                boxes = [b for b in (login.ocr(log=False) or []) if not b.name.startswith('特征码')]
                texts = [b.name for b in boxes][:12]
                if texts != last_texts:
                    self.steps.append({'t': round(time.time() - t0, 1), 'texts': texts})
                    self._shot('screen')
                    last_texts = texts
                if any(LOADING_RE.match(t) for t in texts):  # 加载画面只等，不计入 idle
                    idle = 0
                    self.sleep(1)
                    continue
                # 矩阵等挑战区域在 ESC 到底后弹“是否确认返回大世界”，确认后加载回大世界
                if any('返回大世界' in t for t in texts) and (ok := [b for b in boxes if b.name == '确认']):
                    self.steps.append({'t': round(time.time() - t0, 1), 'action': 'confirm_return_world'})
                    self.click(ok[0], after_sleep=5)
                    idle = 0
                    continue
                login.logged_in = False  # 缓存可能来自上一次运行；以本帧为准
                idle = idle + 1 if login.wait_login() is None else 0
                if idle >= 2:
                    assert esc < MAX_ESC, f'still not in world after {esc} esc: {texts}'
                    esc += 1
                    self.steps.append({'t': round(time.time() - t0, 1), 'action': 'esc'})
                    self.send_key('esc', after_sleep=2)
                    idle = 0
                    continue
                self.sleep(1)
            self._shot('timeout')
            raise AssertionError(f'not in world after {TIME_OUT}s')
        finally:
            (self.artifact_directory / 'steps.json').write_text(
                json.dumps(self.steps, ensure_ascii=False, indent=1), encoding='utf-8')
