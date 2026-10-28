"""把工坊 zip 导入 ok-ww：先备份已装队伍目录，导入后读回核对。不发按键。

参数读同目录 mcp_test.json：zip（绝对路径）；team（3 个类名）可留空，填了就须与包内 team.json 一致。
结果写 import.json：旧/新 team.json、各文件 sha256 前 16 位、备份路径。
新装文件的 sha256 与 matrix_run 记录的 summary.json code[].sha256_16 用同一算法，可直接比对。
"""
import hashlib
import json
import shutil
from pathlib import Path

from ok import BaseTask

from src.char import CustomCharLoader as loader

CONFIG = json.loads(Path(__file__).with_name('mcp_test.json').read_text(encoding='utf-8'))


def digest(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            for p in sorted(Path(folder).iterdir()) if p.is_file()}


class Task(BaseTask):
    def reset_to_start(self):
        self.log_info('team_import: no reset')

    def verify_start_state(self):
        assert Path(CONFIG['zip']).is_file(), f"zip missing: {CONFIG['zip']}"

    def run(self):
        info = loader.inspect_team_archive(CONFIG['zip'])
        assert not CONFIG.get('team') or set(info['team']) == set(CONFIG['team']), \
            f"zip team {info['team']} != {CONFIG['team']}"
        folder = loader.get_custom_team_folder(info['team'])
        # 加载器导入时会删除同名 .backup；该目录已存在说明上次导入中断，留给人处理
        assert not folder.with_name(folder.name + '.backup').exists(), 'stale .backup folder exists'
        result = {'zip': CONFIG['zip'], 'folder': str(folder), 'old': None}
        if folder.exists():
            backup = Path(self.artifact_directory) / ('backup_' + folder.name)
            shutil.copytree(folder, backup)
            result['old'] = {'manifest': loader.read_team_manifest(info['team']), 'files': digest(backup),
                             'backup': str(backup)}
        loader.import_custom_team(info)
        result['new'] = {'manifest': loader.read_team_manifest(info['team']), 'files': digest(folder),
                         'state': loader.team_code_state(info['team'])}
        # 加载器按文本写文件（Windows 下换行变 CRLF），所以按文本比对，不比字节
        same = {n: (folder / f'{n}.py').read_text(encoding='utf-8') == info['codes'][n] for n in info['team']}
        result['code_equals_zip'] = same
        (Path(self.artifact_directory) / 'import.json').write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
        old_v = ((result['old'] or {}).get('manifest') or {}).get('version')
        self.log_info(f"team_import old={old_v} new={result['new']['manifest'].get('version')} "
                      f"state={result['new']['state']} same={same}")
        assert all(same.values()), f'installed code differs from zip: {same}'
        assert result['new']['state'] == 'import', f"code_mode not import: {result['new']['state']}"
