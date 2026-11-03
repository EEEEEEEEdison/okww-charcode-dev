"""从《鸣潮数据汇总》xlsx 生成 knowledge/frames/ 下的角色帧数据。

维护者拿到新版本数据汇总时运行：

    <ok-ww 的 python.exe> -I -B maintainer/build_frames.py <xlsx 路径>

只用标准库读取 xlsx，因为 ok-ww 自带的 Python 没有 openpyxl。
读取的是单元格缓存值；公式错误值按空格处理。
生成的文件第一行带 GENERATED_MARK，重新生成时只删除带该标记的文件。
"""
import argparse
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

M = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'

FPS = 60
CHAR_SHEETS = ('角色-女', '角色-男')
APPENDIX_SHEET = '附页2'
INDEX_SHEET = '索引'
GENERATED_MARK = '<!-- 由 maintainer/build_frames.py 生成，不得手改 -->'

# 数据汇总中的名称 → 输出文件名。文件名用框架类名；漂泊者按属性拆分，与语义卡一致。
CHAR_FILES = {
    '白芷': 'Baizhi', '长离': 'Changli', '坎特蕾拉': 'Cantarella', '赞妮': 'Zani',
    '奥古斯塔': 'Augusta', '嘉贝莉娜': 'Galbrena', '绯雪': 'Hiyuki', '洛瑟菈': 'Lucilla',
    '清宵': 'Qingxiao', '应世心': 'Hsin', '照世心': 'Hsin', '心': 'Hsin',
    '光主': 'SpectroRover', '暗主': 'HavocRover', '风主': 'AeroRover', '雷主': 'ElectroRover',
    '秧秧': 'Yangyang', '炽霞': 'Chixia', '散华': 'Sanhua', '桃祈': 'Taoqi', '桃祁': 'Taoqi',
    '丹瑾': 'Danjin', '鉴心': 'Jianxin', '吟霖': 'Yinlin', '今汐': 'Jinhsi', '折枝': 'Zhezhi',
    '守岸人': 'ShoreKeeper', '椿': 'Camellya', '夏空': 'Ciaccona', '露帕': 'Lupa',
    '弗洛洛': 'Phrolova', '尤诺': 'Iuno', '千咲': 'Chisa', '琳奈': 'Linnai',
    '爱弥斯': 'Aemeath', '机兵爱弥斯': 'Aemeath', '露西': 'Lucy', '秧秧·玄翎': 'YangYangSp',
    '穗穗': 'Suisui', '灯灯': 'Lumi', '珂莱塔': 'Carlotta', '菲比': 'Phoebe',
    '卡提希娅': 'Cartethyia', '芙露德莉斯': 'Cartethyia', '卜灵': 'Douling', '莫宁': 'Mornye',
    '西格莉卡': 'Xigelika', '达妮娅': 'Denia', '丽贝卡': 'Rebecca', '维里奈': 'Verina',
    '安可': 'Encore', '釉瑚': 'Youhu', '洛可可': 'Roccia', '锁暝': 'Suoming',
    '卡卡罗': 'Calcharo', '忌炎': 'Jiyan', '秋水': 'Aalto', '渊武': 'Yuanwu',
    '莫特斐': 'Mortefi', '莫特菲': 'Mortefi', '布兰特': 'Brant', '仇远': 'Qiuyuan', '陆·赫斯': 'Luhesi',
    '相里要': 'Xiangliyao', '景燃': 'JingRan', '凌阳': 'Lingyang',
}
# 有数据但不生成的名称及原因。
SKIP_CHARS = {'旧椿': '框架没有对应的类'}
# 名称列里的导航标签，不是角色名。
LABELS = {'技能类型', '伤害计算', '输入缓存', '牵引', '偏谐机制', '同奏体系', '快速反应'}
COMMON_PREFIX = '通用'
COMMON_FILE = '_common'
INDEX_FILE = '_index'

# 输出列：(列名, 取值方式)。取值方式为表头名，或 ('frames', 表头名) 表示附秒数。
COLUMNS = [
    ('ID', 'ID'),
    ('动作', '动作'),
    ('备注', '备注'),
    ('发生帧', '发生帧'),
    ('持续帧', '持续帧'),
    ('无敌', 'invincible'),
    ('派生帧', ('frames', '派生帧')),
    ('派生持续帧', ('frames', '派生持续帧')),
    ('动作结束帧', ('frames', '动作结束帧')),
    ('中断优先级', '中断优先级'),
    ('优先级改变', '优先级改变'),
    ('位置状态', '位置状态'),
    ('时停', 'timestop'),
    ('大招回收', '大招回收'),
    ('协奏回收', '协奏回收'),
    ('核心回收', 'core'),
]
INPUT_KEYS = ['A', 'E', 'R', '声骸', '闪避', '跳跃']
HOLD_KEYS = {'长按A': 'A', '长按E': 'E', '长按R': 'R', '长按跳': '跳跃', '长按闪': '闪避', '长按移动': '移动'}
INPUT_COLUMNS = INPUT_KEYS + ['移动']


def col_index(ref):
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def load_shared_strings(z):
    if 'xl/sharedStrings.xml' not in z.namelist():
        return []
    out = []
    root = ET.parse(z.open('xl/sharedStrings.xml')).getroot()
    for si in root.iter(M + 'si'):
        parts = []
        for child in si:
            if child.tag == M + 't':
                parts.append(child.text or '')
            elif child.tag == M + 'r':
                parts.extend(t.text or '' for t in child.iter(M + 't'))
        out.append(''.join(parts))
    return out


def sheet_paths(z):
    wb = ET.parse(z.open('xl/workbook.xml')).getroot()
    rels = ET.parse(z.open('xl/_rels/workbook.xml.rels')).getroot()
    targets = {r.get('Id'): r.get('Target') for r in rels.iter(PKG + 'Relationship')}
    paths = {}
    for s in wb.iter(M + 'sheet'):
        target = targets[s.get(R_ID)].lstrip('/')
        paths[s.get('name')] = target if target.startswith('xl/') else 'xl/' + target
    return paths


def read_rows(z, path, shared):
    """逐行产出 (Excel 行号, {列序号: 值})。"""
    for _, el in ET.iterparse(z.open(path), events=('end',)):
        if el.tag != M + 'row':
            continue
        cells = {}
        for c in el.findall(M + 'c'):
            t = c.get('t')
            v = c.find(M + 'v')
            if t == 'inlineStr':
                val = ''.join(x.text or '' for x in c.iter(M + 't'))
            elif v is None or v.text is None or t == 'e':
                continue
            elif t == 's':
                val = shared[int(v.text)]
            elif t in ('str', 'b'):
                val = v.text
            else:
                val = float(v.text)
            if isinstance(val, str) and not val.strip():
                continue
            cells[col_index(c.get('r'))] = val
        yield int(el.get('r')), cells
        el.clear()


def fmt_num(x):
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return f'{x:.3f}'.rstrip('0').rstrip('.')
    s = str(x).strip()
    # 部分 ID 单元格是文本型公式结果，如 "17.0"
    return re.sub(r'^(-?\d+)\.0+$', r'\1', s)


def fmt_text(x):
    s = fmt_num(x)
    s = s.replace('\r\n', '\n').replace('\r', '\n').strip('\n')
    return s.replace('|', '\\|').replace('\n', '<br>')


def with_seconds(x):
    s = fmt_num(x)
    try:
        f = float(s)
    except ValueError:
        return fmt_text(x)
    return f'{s} ({f / FPS:.2f}s)' if f > 0 else s


class SheetLayout:
    def __init__(self, header):
        self.idx = {}
        for i, name in sorted(header.items()):
            self.idx.setdefault(str(name).strip(), i)
        missing = [h for h in ('名称', 'ID', '动作', '备注', '派生帧', '动作结束帧', '中断优先级') if h not in self.idx]
        if missing:
            raise SystemExit(f'表头缺少列：{missing}')

    def get(self, cells, name):
        i = self.idx.get(name)
        return None if i is None else cells.get(i)

    def expansion(self, cells, prefix):
        """膨胀系数后面依次是“膨胀发生”“膨胀持续”，表头重名，只能按位置取。"""
        i = self.idx.get(prefix + '膨胀系数')
        return None if i is None else cells.get(i + 2)

    def value(self, cells, spec):
        if isinstance(spec, tuple):
            v = self.get(cells, spec[1])
            return '' if v is None else with_seconds(v)
        if spec == 'invincible':
            start, dur = self.get(cells, '无敌启动帧'), self.get(cells, '无敌持续帧')
            if start is None and dur is None:
                return ''
            return f'{fmt_num(start) if start is not None else "?"}+{fmt_num(dur) if dur is not None else "?"}'
        if spec == 'timestop':
            kind = self.get(cells, '时间膨胀类型')
            if kind not in ('时停', '全局时停'):
                return ''
            dur = next((d for d in (self.expansion(cells, p) for p in ('敌', '友', '自')) if d is not None), None)
            return f'{kind} {fmt_num(dur)}' if dur is not None else kind
        if spec == 'core':
            vals = [self.get(cells, f'核心回收{i}') for i in (1, 2, 3)]
            return '/'.join(fmt_num(v) for v in vals if v is not None)
        v = self.get(cells, spec)
        return '' if v is None else fmt_text(v)


def read_blocks(z, paths, shared):
    blocks = []
    for sheet in CHAR_SHEETS:
        rows = read_rows(z, paths[sheet], shared)
        _, header = next(rows)
        layout = SheetLayout(header)
        current = None
        for rnum, cells in rows:
            name = layout.get(cells, '名称')
            if isinstance(name, str) and name.strip() and name.strip() not in LABELS:
                current = {'sheet': sheet, 'name': name.strip(), 'start': rnum, 'end': rnum, 'rows': []}
                blocks.append(current)
            if current is None:
                continue
            row = [layout.value(cells, spec) for _, spec in COLUMNS]
            if any(row[1:]):
                current['rows'].append(row)
                current['end'] = rnum
    return blocks


def read_input_cache(z, paths, shared):
    """附页2 的“输入缓存时间(s)”表：({名称: {'buffer': {...}, 'hold': {...}}}, [未识别的名称])。"""
    rows = read_rows(z, paths[APPENDIX_SHEET], shared)
    header = None
    for _, cells in rows:
        vals = {str(v).strip(): i for i, v in cells.items()}
        if '角色' in vals and '长按A' in vals:
            header = vals
            break
    if header is None:
        raise SystemExit(f'{APPENDIX_SHEET} 中找不到输入缓存表头')
    role = header['角色']
    out, unknown, blank = {}, [], 0
    for _, cells in rows:
        name = cells.get(role)
        if name is None:
            blank += 1
            if blank > 5:
                break
            continue
        blank = 0
        name = str(name).strip()
        if name not in CHAR_FILES and name not in SKIP_CHARS:
            unknown.append(name)
            continue
        norm = lambda v: '' if v is None else fmt_num(v).replace('，', ', ')
        out[name] = {
            'buffer': {k: norm(cells.get(header[k])) for k in INPUT_KEYS if k in header},
            'hold': {HOLD_KEYS[k]: norm(cells.get(header[k])) for k in HOLD_KEYS if k in header},
        }
    return out, unknown


def read_version(z, paths, shared):
    for _, cells in read_rows(z, paths[INDEX_SHEET], shared):
        for v in cells.values():
            m = re.search(r'Resource Version\s*([\d.]+)', str(v))
            if m:
                return m.group(1)
    return None


def render_table(rows):
    keep = [i for i in range(len(COLUMNS)) if any(r[i] for r in rows)]
    lines = ['| ' + ' | '.join(COLUMNS[i][0] for i in keep) + ' |',
             '|' + '---|' * len(keep)]
    lines += ['| ' + ' | '.join(r[i] for i in keep) + ' |' for r in rows]
    return lines


def render_input_cache(entries):
    lines = ['## 输入缓存（秒）', '',
             '| 名称 | 项目 | ' + ' | '.join(INPUT_COLUMNS) + ' |',
             '|' + '---|' * (len(INPUT_COLUMNS) + 2)]
    for name, e in entries:
        lines.append(f'| {name} | 指令缓存（按下, 抬起, 长按） | '
                     + ' | '.join(e['buffer'].get(k, '') for k in INPUT_COLUMNS) + ' |')
        lines.append(f'| {name} | 长按触发 | '
                     + ' | '.join(e['hold'].get(k, '') for k in INPUT_COLUMNS) + ' |')
    return lines


def render_file(stem, blocks, cache, version):
    names = list(dict.fromkeys(b['name'] for b in blocks))
    title = '通用动作' if stem == COMMON_FILE else f'{" / ".join(names)}（{stem}）'
    lines = [GENERATED_MARK, f'# {title}帧数据', '',
             f'数据版本 {version}。列含义、术语和用法见 [README](README.md)。', '']
    for b in blocks:
        lines += [f'## {b["name"]}（{b["sheet"]} 第 {b["start"]}–{b["end"]} 行）', '']
        lines += render_table(b['rows']) + ['']
    entries = [(n, cache[n]) for n in cache if CHAR_FILES.get(n) == stem]
    if entries:
        lines += render_input_cache(entries) + ['']
    return '\n'.join(lines)


def render_index(files, skipped, version, sha):
    lines = [GENERATED_MARK, '# 帧数据索引', '',
             f'数据版本 {version}。数据汇总 xlsx 的 SHA-256：`{sha}`。', '',
             '| 文件 | 数据汇总中的名称 |', '|---|---|']
    for stem in sorted(files, key=lambda s: (s != COMMON_FILE, s.lower())):
        names = ' / '.join(dict.fromkeys(b['name'] for b in files[stem]))
        lines.append(f'| [{stem}.md]({stem}.md) | {names} |')
    if skipped:
        lines += ['', '未生成：', '']
        lines += [f'- {n}：{why}' for n, why in skipped.items()]
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('xlsx', type=Path)
    ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parent.parent / 'knowledge' / 'frames')
    args = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    sha = hashlib.sha256(args.xlsx.read_bytes()).hexdigest()
    with zipfile.ZipFile(args.xlsx) as z:
        shared = load_shared_strings(z)
        paths = sheet_paths(z)
        missing = [s for s in (*CHAR_SHEETS, APPENDIX_SHEET, INDEX_SHEET) if s not in paths]
        if missing:
            raise SystemExit(f'找不到工作表：{missing}')
        version = read_version(z, paths, shared)
        if not version:
            raise SystemExit(f'{INDEX_SHEET} 中找不到 Resource Version')
        blocks = read_blocks(z, paths, shared)
        cache, cache_unknown = read_input_cache(z, paths, shared)

    files, skipped, unknown = {}, {}, []
    for b in blocks:
        if b['name'].startswith(COMMON_PREFIX):
            stem = COMMON_FILE
        elif b['name'] in CHAR_FILES:
            stem = CHAR_FILES[b['name']]
        elif b['name'] in SKIP_CHARS:
            skipped[b['name']] = SKIP_CHARS[b['name']]
            continue
        else:
            unknown.append(f'{b["sheet"]} 第 {b["start"]} 行：{b["name"]}')
            continue
        files.setdefault(stem, []).append(b)
    if unknown:
        raise SystemExit('名称不在 CHAR_FILES、SKIP_CHARS 或 LABELS 中，先补映射：\n' + '\n'.join(unknown))

    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob('*.md'):
        with old.open(encoding='utf-8') as f:
            generated = f.readline().strip() == GENERATED_MARK
        if generated:
            old.unlink()
    for stem, bs in files.items():
        (args.out / f'{stem}.md').write_text(render_file(stem, bs, cache, version), encoding='utf-8', newline='\n')
    (args.out / f'{INDEX_FILE}.md').write_text(render_index(files, skipped, version, sha), encoding='utf-8', newline='\n')

    no_cache = sorted(s for s in files if s != COMMON_FILE and not any(CHAR_FILES.get(n) == s for n in cache))
    print(f'数据版本 {version}，SHA-256 {sha}')
    print(f'生成 {len(files)} 个文件和 {INDEX_FILE}.md，共 {len(blocks)} 个区块，未生成 {len(skipped)} 个：{list(skipped)}')
    print(f'输入缓存匹配 {len(cache)} 个名称；没有输入缓存的文件：{no_cache}')
    if cache_unknown:
        print(f'警告：输入缓存表中有未识别的名称，未写入：{cache_unknown}')


if __name__ == '__main__':
    main()
