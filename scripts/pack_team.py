"""打包工坊配队 zip，并用 ok-ww 自己的 inspect_team_archive 校验。

用法（用 ok-ww 自带的 Python，带 -I -B）：
    python.exe -I -B pack_team.py <版本目录> <ok-ww 的 working 目录> [--src <代码目录>]

- team.json 取自版本目录。3 个角色 .py 默认也取自版本目录；项目要求先清洗代码时，用 --src 指向清洗结果。
- zip 写进版本目录，文件名 <类名>_<类名>_<类名>_<author>_<version>.zip，类名按 team 字段的顺序。
- 同名 zip 已存在时不覆盖，退出码 2。校验不通过时删掉本次打的 zip，退出码 1。
- 导入 ok-ww 会在当前目录生成 configs/，所以校验在临时目录里跑。
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

FIELDS = ('name', 'description', 'author', 'version', 'team')


def safe(value):
    return re.sub(r'[<>:"/\\|?*\s]+', '_', value).strip(' .')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('version_dir')
    parser.add_argument('working_dir')
    parser.add_argument('--src')
    args = parser.parse_args()
    version_dir = os.path.abspath(args.version_dir)
    working_dir = os.path.abspath(args.working_dir)
    src_dir = os.path.abspath(args.src or version_dir)

    manifest_path = os.path.join(version_dir, 'team.json')
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)
    missing = [k for k in FIELDS if not isinstance(manifest.get(k), str) or not manifest[k].strip()]
    if missing:
        print(f'FAIL: team.json 缺少字段 {missing}')
        return 1

    old_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp(prefix='okww-pack-')
    os.chdir(temp_dir)
    try:
        sys.path.insert(0, working_dir)
        from src.char.CustomCharLoader import CHARACTER_DISPLAY_NAMES, inspect_team_archive

        class_by_display = {v: k for k, v in CHARACTER_DISPLAY_NAMES.items()}
        displays = [n.strip() for n in manifest['team'].split(',') if n.strip()]
        class_names = [class_by_display.get(n, n) for n in displays]
        sources = [os.path.join(src_dir, f'{c}.py') for c in class_names]
        absent = [p for p in sources if not os.path.isfile(p)]
        if absent:
            print(f'FAIL: 找不到角色代码 {absent}')
            return 1

        zip_name = '_'.join(class_names + [safe(manifest['author']), safe(manifest['version'])]) + '.zip'
        zip_path = os.path.join(version_dir, zip_name)
        if os.path.exists(zip_path):
            print(f'REFUSE: {zip_path} 已存在，不覆盖；请换版本号')
            return 2
        with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED) as z:
            z.write(manifest_path, 'team.json')
            for c, p in zip(class_names, sources):
                z.write(p, f'{c}.py')

        try:
            info = inspect_team_archive(zip_path)
        except ValueError as e:
            print(f'FAIL: inspect_team_archive: {e}')
            os.remove(zip_path)
            return 1
        if sorted(info['team'], key=str.casefold) != sorted(class_names, key=str.casefold):
            print(f'FAIL: 校验得到的队伍 {info["team"]} 与 team.json {class_names} 不一致')
            os.remove(zip_path)
            return 1
        with zipfile.ZipFile(zip_path) as z:
            members = z.namelist()
        print(f'OK: {zip_path}')
        print(f'members: {members}')
        print(f'team: {list(info["team"])}')
        return 0
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
