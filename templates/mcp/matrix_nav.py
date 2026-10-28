"""从大世界或矩阵相关页面导航到终焉矩阵编队详情页（有“前往”的页面），找到要测试的队伍，不点“前往”。

队伍和开场角色取自 team.json：mcp_test.json 填了 zip 时读包内 team.json，否则按 team（3 个类名）读已装队伍的 team.json。
开场角色取 description 里的“一号位<中文名>”；没写时用 mcp_test.json 的 opener。模式取 mode（默认奇点扩张）。
测试队伍由用户事先在矩阵里编好，1 号位放开场角色。本任务只读编队，不改编队。
找队：逐个打开可挑战的队伍，在编队编辑器里读 1 号位和 2、3 号角标格的名字，再按 ESC 丢弃改动。
找到后写同目录 target.json（slot、team、opener），matrix_run.py 读它。
路径：大世界 → 索拉指南 → 周期挑战 → 终焉矩阵 → 模式“前往” → 矩阵主页 → 选队 → 重新挑战或开始挑战 → 编队详情页。
上一局的结算页：返回 → 成绩确认 → 取消（保留原记录）→ 编队详情页。
安全：save_result 为 true 时只允许最后一个有记录的队伍；保存成绩会清空其后所有队伍的记录。
"""
import json
import re
from pathlib import Path

import cv2
from ok import BaseTask

from src.char import CustomCharLoader as loader
from src.task.AutoCombatTask import AutoCombatTask

CONFIG = json.loads(Path(__file__).with_name('mcp_test.json').read_text(encoding='utf-8'))
TARGET = Path(__file__).with_name('target.json')
MAX_STEPS = 40
MAX_ESC = 3
BOOK_TABS_Y = [0.427, 0.178, 0.302, 0.547, 0.676, 0.8]  # 左侧分页图标，0.427 为本版周期挑战
ROW_Y0, ROW_DY, ROWS = 0.27, 0.107, 5  # 矩阵主页队伍行 01 的纵坐标、行距、行数
SCORE_RE = re.compile(r'^\+\d{3,}$')
OPENER_RE = re.compile(r'一号位[:：\s]*([^\s，。、,.;；（(]+)')
SLOT1 = (0.599, 0.702)  # 详情页编队 1 号位头像；点 2、3 号头像打开的编辑器焦点也在 1 号位
BADGE_Y0, BADGE_DY = 0.197, 0.177  # 编辑器角色格角标的首行纵坐标与行距
BADGE_TO_CELL = (-0.033, 0.069)  # 角标到所在格中心


def resolve_team():
    """返回 team（类名）、opener（类名）、zh（类名 → 游戏内中文名）。"""
    if CONFIG.get('zip'):
        info = loader.inspect_team_archive(CONFIG['zip'])
        team, manifest = list(info['team']), info['manifest']
        assert not CONFIG.get('team') or set(CONFIG['team']) == set(team), f"zip team {team} != {CONFIG['team']}"
    else:
        team = list(loader.normalize_team(CONFIG['team']))
        manifest = loader.read_team_manifest(team)
    po = Path(loader.__file__).parents[2] / 'i18n' / 'zh_CN' / 'LC_MESSAGES' / 'ok.po'
    names = dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.+)"$', po.read_text(encoding='utf-8'), re.M))
    zh = {c: names.get(loader.get_english_char_name(c), loader.get_english_char_name(c)) for c in team}
    m = OPENER_RE.search(manifest.get('description', ''))
    opener = next((c for c, n in zh.items() if m and m.group(1).startswith(n)), None) or CONFIG.get('opener')
    assert opener in team, f'opener unknown: write 一号位<中文名> in team.json description or set opener; {zh}'
    return {'team': team, 'opener': opener, 'zh': zh}


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
        # 赛季页：从详情页按 ESC 可能退到这里，右侧是各模式卡片，没有“前往”
        if '周期规则' in names and any(self.mode[:2] in t[0] and t[1] > 0.6 for t in texts):
            return 'season'
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

    def _slot_label(self):
        # 方括号大号槽位编号全屏 OCR 读不出，裁到编队栏左侧才能读出
        joined = ' '.join(b.name for b in (self.ocr(0.44, 0.64, 0.56, 0.76, log=False) or []))
        m = re.search(r'\d{2}', joined)
        return int(m.group()) if m else None

    @staticmethod
    def _editor_name(texts):
        return ''.join(t[0] for t in texts if 0.38 < t[1] < 0.65 and 0.11 < t[2] < 0.16)

    def _read_members(self):
        """在编队编辑器里读当前队伍成员的中文名，读完按 ESC 回详情页。

        打开时右上显示 1 号位；点带角标的格子会显示其名字，同时把该成员移出编队。
        不点“确定”时 ESC 丢弃全部改动，编队保持原样（已实机验证）。
        """
        self.click_relative(*SLOT1, after_sleep=2.5)
        self.next_frame()
        texts = self._texts()
        self._snap('editor1')
        assert any(t[0] == '角色编队' and t[2] < 0.1 for t in texts) and any(t[0] == '确定' for t in texts), \
            'formation editor not opened'
        try:
            members = [self._editor_name(texts)]
            badges = {t[0]: t for t in texts if t[0] in ('2', '3') and t[1] < 0.4
                      and min((t[2] - BADGE_Y0) % BADGE_DY, BADGE_DY - (t[2] - BADGE_Y0) % BADGE_DY) < 0.03}
            for k in ('2', '3'):
                if k not in badges:
                    break
                self.click_relative(badges[k][1] + BADGE_TO_CELL[0], badges[k][2] + BADGE_TO_CELL[1], after_sleep=1.5)
                self.next_frame()
                self._snap(f'editor{k}')
                members.append(self._editor_name(self._texts()))
        finally:
            self.send_key('esc', after_sleep=2.5)
        return members

    def run(self):
        combat = self.get_task_by_class(AutoCombatTask)
        self.mode = CONFIG.get('mode', '奇点扩张')
        save = bool(CONFIG.get('save_result', False))
        info = resolve_team()
        want = sorted(info['zh'].values())
        opener_zh = info['zh'][info['opener']]
        self.log_info(f"matrix_nav team={info['team']} opener={info['opener']} want={want}")
        # 旧 target.json 可能指向别的队伍，没找到队伍时不得留给 matrix_run.py
        TARGET.unlink(missing_ok=True)
        trace, checked, last, row = [], {}, None, None
        esc_count, tab_index, action = 0, 0, None
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
                    slot = self._slot_label() or row
                    assert slot, 'slot label not read on detail page'
                    # 要保存成绩时须先在主页确认本队是最后一个有记录的队伍
                    if slot not in checked and not (save and last is None):
                        members = self._read_members()
                        checked[slot] = members
                        trace[-1]['members'] = members
                        self.log_info(f'matrix_nav slot={slot:02d} members={members}')
                        if members and members[0] == opener_zh and sorted(members) == want:
                            assert not save or slot == last, \
                                f'save_result needs slot {slot} to be the last recorded {last}; later records would be wiped'
                            TARGET.write_text(json.dumps(
                                {'slot': slot, 'slot_label': f'{slot:02d}', 'team': info['team'],
                                 'opener': info['opener'], 'members': members}, ensure_ascii=False), encoding='utf-8')
                            return True
                    self.send_key('esc', after_sleep=2)
                    action = 'leave_detail'
                elif page == 'world':
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
                    trace[-1]['save_result'] = save
                    self._click_text(texts, '确认' if save else '取消')
                elif page == 'cycle':
                    heads = [t for t in texts if self.mode[:2] in t[0] and t[1] > 0.35]
                    if not heads:
                        self._click_text(texts, '终焉矩阵')
                        continue
                    head_y = min(t[2] for t in heads)
                    gos = sorted((t for t in texts if t[0] == '前往' and t[2] > head_y), key=lambda t: t[2])
                    assert gos, f'前往 under {self.mode} not found'
                    self.click(gos[0][3], after_sleep=4)
                elif page == 'season':
                    card = [t for t in texts if self.mode[:2] in t[0] and t[1] > 0.6]
                    self.click(card[0][3], after_sleep=3)
                elif page == 'matrix_main':
                    # 模式标题前常被读出图标杂字（如“风奇点护张”），按包含判断
                    assert any(self.mode[:2] in t[0] for t in texts if t[2] < 0.15), f'matrix mode is not {self.mode}'
                    scores = {round((t[2] - ROW_Y0) / ROW_DY) + 1: t[0] for t in texts
                              if SCORE_RE.match(t[0]) and t[1] > 0.85}
                    last = max(scores, default=0)
                    trace[-1]['recorded'] = scores
                    # 可挑战的是已有记录的队伍和其后第一个空位
                    rows = [r for r in range(1, min(last + 1, ROWS) + 1) if r not in checked]
                    assert rows, f'no slot has team {want} with {opener_zh} at position 1: {checked}'
                    row = rows[0]
                    self.click_relative(0.48, ROW_Y0 + (row - 1) * ROW_DY, after_sleep=2)
                    self.next_frame()
                    btns = [t for t in self._texts() if t[0] in ('重新挑战', '开始挑战') and t[2] > 0.85]
                    assert btns, f'challenge button not shown after selecting slot {row}'
                    self.click(btns[0][3], after_sleep=2)
                elif page == 'confirm':
                    # 进入重新挑战不改记录，只有结算后保存成绩才会重置
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
