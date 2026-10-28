"""从大世界或矩阵相关页面导航到终焉矩阵编队详情页（有“前往”的页面），不点“前往”。

参数读同目录 mcp_test.json：mode（奇点扩张 / 稳态协议）、slot_label（如 "04"）、save_result（默认 false）。
路径：大世界 → 索拉指南 → 周期挑战 → 终焉矩阵 → 模式“前往” → 矩阵主页 → 选队 → 重新挑战 → 确认 → 编队详情页。
上一局的结算页：返回 → 成绩确认 → 取消（保留原记录）→ 编队详情页。
安全：只重测最后一个有记录的队伍；保存成绩会清空其后所有队伍的记录。空槽位需要编队，暂不支持。
"""
import json
import re
from pathlib import Path

import cv2
from ok import BaseTask

from src.task.AutoCombatTask import AutoCombatTask

CONFIG = json.loads(Path(__file__).with_name('mcp_test.json').read_text(encoding='utf-8'))
MAX_STEPS = 20
MAX_ESC = 2
BOOK_TABS_Y = [0.427, 0.178, 0.302, 0.547, 0.676, 0.8]  # 左侧分页图标，0.427 为本版周期挑战
ROW_Y0, ROW_DY = 0.27, 0.107  # 矩阵主页队伍行 01 的纵坐标与行距
SCORE_RE = re.compile(r'^\+\d{3,}$')


class Task(BaseTask):
    def reset_to_start(self):
        self.log_info('matrix_nav: navigation is its own recovery')

    def verify_start_state(self):
        assert self.executor.next_frame(time_out=6) is not None, 'no frame'

    def _snap(self, tag):
        cv2.imwrite(str(self.artifact_directory / f'{self.n:02d}_{tag}.jpg'), self.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

    def _texts(self):
        h, w = self.frame.shape[:2]
        return [(b.name, (b.x + b.width / 2) / w, (b.y + b.height / 2) / h, b) for b in (self.ocr(log=False) or [])]

    def _page(self, texts, combat, last_action):
        names = [t[0] for t in texts]
        joined = ' '.join(names)
        title = ' '.join(t[0] for t in texts if t[1] < 0.3 and t[2] < 0.1)
        if '成绩确认' in names and '是否覆盖' in joined and '取消' in names:
            return 'score_confirm'
        if '提示' in joined and '重新挑战并保存' in joined and '确认' in names:
            return 'confirm'
        if '终焉矩阵' in title and '队伍得分' in names and '战绩详情' in joined:
            return 'result'
        if '终焉矩阵' in title and '角色编队' in joined:
            return 'detail'
        if '终焉矩阵' in title and '当前累计积分' in joined:
            return 'matrix_main'
        if '周期挑战' in title:
            return 'cycle'
        # 指南默认分页随版本和进度变化，只按“刚按过指南键或刚切过分页、左上有标题”判定
        if title and last_action in ('book_key', 'tab'):
            return 'book'
        if combat.in_team_and_world():
            return 'world'
        return 'unknown'

    def _click_text(self, texts, text, pick=lambda c: c[0]):
        cands = [t for t in texts if t[0] == text]
        assert cands, f'{text} not found'
        self.click(pick(cands)[3], after_sleep=2)

    def run(self):
        combat = self.get_task_by_class(AutoCombatTask)
        mode, slot = CONFIG.get('mode', '奇点扩张'), int(CONFIG['slot_label'])
        trace, esc_count, tab_index, action = [], 0, 0, None
        try:
            for self.n in range(MAX_STEPS):
                self.next_frame()
                texts = self._texts()
                page = self._page(texts, combat, action)
                action = page
                trace.append({'step': self.n, 'page': page,
                              'texts': [t[0] for t in texts if not t[0].startswith('特征码')][:30]})
                self._snap(page)
                self.log_info(f'matrix_nav step={self.n} page={page}')
                if page == 'detail':
                    slot_texts = [b.name for b in (self.ocr(0.44, 0.64, 0.56, 0.76, log=False) or [])]
                    assert any(CONFIG['slot_label'] in t for t in slot_texts), f'detail page of wrong slot {slot_texts}'
                    return True
                if page == 'world':
                    book_key = combat.key_config.get('Guidebook Key', combat.key_config.get('索拉指南', 'f2'))
                    self.send_key(book_key, after_sleep=3)
                    action = 'book_key'
                elif page == 'book':
                    assert tab_index < len(BOOK_TABS_Y), 'cycle challenge tab not found'
                    self.click_relative(0.039, BOOK_TABS_Y[tab_index], after_sleep=2)
                    tab_index += 1
                    action = 'tab'
                elif page == 'result':
                    # 结算页的总积分只是预览，点“返回”后才弹“成绩确认”
                    self._click_text(texts, '返回')
                elif page == 'score_confirm':
                    # 取消 = 保留原记录、回到编队详情页；确认会覆盖本队并清空其后各队记录
                    save = bool(CONFIG.get('save_result', False))
                    trace[-1]['save_result'] = save
                    self._click_text(texts, '确认' if save else '取消')
                elif page == 'cycle':
                    heads = [t for t in texts if t[0].startswith(mode[:2]) and t[1] > 0.35]
                    if not heads:
                        self._click_text(texts, '终焉矩阵')
                        continue
                    head_y = min(t[2] for t in heads)
                    gos = sorted((t for t in texts if t[0] == '前往' and t[2] > head_y), key=lambda t: t[2])
                    assert gos, f'前往 under {mode} not found'
                    self.click(gos[0][3], after_sleep=4)
                elif page == 'matrix_main':
                    assert any(t[0].startswith(mode[:2]) for t in texts if t[2] < 0.15), f'matrix mode is not {mode}'
                    scores = {round((t[2] - ROW_Y0) / ROW_DY) + 1: t[0] for t in texts
                              if SCORE_RE.match(t[0]) and t[1] > 0.85}
                    last = max(scores, default=0)
                    trace[-1]['recorded'] = scores
                    assert slot <= last, f'slot {slot} has no record (last recorded {last}); team setup is not supported'
                    assert slot == last, f'slot {slot} is before last recorded {last}; retry would wipe later records'
                    self.click_relative(0.48, ROW_Y0 + (slot - 1) * ROW_DY, after_sleep=2)
                    self.next_frame()
                    retry = [t for t in self._texts() if t[0] == '重新挑战' and t[2] > 0.85]
                    assert retry, '重新挑战 button not shown after selecting slot'
                    self.click(retry[0][3], after_sleep=2)
                elif page == 'confirm':
                    self._click_text(texts, '确认')
                    self.sleep(1)
                else:
                    assert esc_count < MAX_ESC, f'unknown page after {esc_count} esc'
                    esc_count += 1
                    self.send_key('esc', after_sleep=2)
            raise AssertionError(f'not on detail page after {MAX_STEPS} steps')
        finally:
            (self.artifact_directory / 'nav.json').write_text(json.dumps(trace, ensure_ascii=False, indent=1),
                                                              encoding='utf-8')
