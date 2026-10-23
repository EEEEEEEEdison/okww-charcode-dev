"""把知识提议文件反馈给本仓库维护者。

用法（用 ok-ww 自带的 Python，带 -I -B）：
    python.exe -I -B submit_proposal.py <提议 .md> [--method auto|gh|browser|email] [--dry-run]

- 先检查格式和隐私：首行必须是 `# [知识提议] ...`，必须有标记行和 MIT 同意行；
  出现本机绝对路径、邮箱或令牌时拒绝提交，逐行列出。
- auto：gh 已安装并登录时用 gh 直接创建 Issue，否则用 browser。
- browser：打开预填标题和正文的新建 Issue 页面，由用户点提交；链接超长时正文复制到剪贴板。
- email：在资源管理器中选中提议文件，输出收件邮箱和邮件主题，由用户发送。
- --dry-run 只输出将要执行的动作，不创建 Issue、不打开页面、不改剪贴板。
- 退出码：0 完成；1 提交失败；2 文件检查未通过。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from urllib.parse import quote

REPO = 'EEEEEEEEdison/okww-charcode-dev'
EMAIL = '476676559@qq.com'
TITLE_PREFIX = '# [知识提议] '
MARKER = '<!-- okwwcharcode-proposal v1 -->'
CONSENT = '提交即同意按 MIT 许可收录本提议内容。'
# GitHub 新建 Issue 链接的长度上限按 8000 字符算，超出时正文改走剪贴板
URL_LIMIT = 8000
PRIVATE_PATTERNS = [
    ('本机绝对路径', re.compile(r'(?<![A-Za-z])[A-Za-z]:[\\/]|/(?:Users|home)/|/[a-z]/Users/')),
    ('邮箱', re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')),
    ('令牌', re.compile(r'\b(?:ghp|gho|ghu|ghs)_\w+|github_pat_\w+|sk-ant-\w+')),
]


def check(text):
    problems = []
    lines = text.splitlines()
    if not lines or not lines[0].startswith(TITLE_PREFIX):
        problems.append('第 1 行必须以“%s”开头' % TITLE_PREFIX)
    if MARKER not in text:
        problems.append('缺少标记行 %s' % MARKER)
    if CONSENT not in text:
        problems.append('缺少同意行“%s”' % CONSENT)
    if not any(line.startswith('## ') for line in lines):
        problems.append('没有任何条目（## 开头的节）')
    for no, line in enumerate(lines, 1):
        for kind, pattern in PRIVATE_PATTERNS:
            if pattern.search(line):
                problems.append('第 %d 行含%s：%s' % (no, kind, line.strip()))
    return problems


def gh_ready():
    if not shutil.which('gh'):
        return False
    return subprocess.run(['gh', 'auth', 'status'], capture_output=True).returncode == 0


def write_temp(body):
    fd, path = tempfile.mkstemp(suffix='.md')
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(body)
    return path


def submit_gh(title, body, dry_run):
    if dry_run:
        print('将执行：gh issue create --repo %s --title "%s" --body-file <正文>' % (REPO, title))
        return 0
    path = write_temp(body)
    try:
        result = subprocess.run(['gh', 'issue', 'create', '--repo', REPO, '--title', title, '--body-file', path],
                                capture_output=True, text=True, encoding='utf-8')
    finally:
        os.remove(path)
    if result.returncode != 0:
        print('gh 创建 Issue 失败，可改用 --method browser：%s' % (result.stderr or result.stdout).strip())
        return 1
    print('issue: %s' % result.stdout.strip().splitlines()[-1])
    return 0


def copy_to_clipboard(body):
    path = write_temp(body)
    try:
        command = "Get-Content -LiteralPath '%s' -Raw -Encoding UTF8 | Set-Clipboard" % path.replace("'", "''")
        return subprocess.run(['powershell', '-NoProfile', '-Command', command]).returncode == 0
    finally:
        os.remove(path)


def submit_browser(title, body, dry_run):
    base = 'https://github.com/%s/issues/new?title=%s' % (REPO, quote(title))
    url = base + '&body=' + quote(body)
    if len(url) <= URL_LIMIT:
        print('将打开预填页面（链接 %d 字符），由用户点提交。' % len(url))
        if not dry_run:
            webbrowser.open(url)
        return 0
    print('正文过长（链接 %d 字符），正文复制到剪贴板，打开只预填标题的页面，由用户粘贴正文后提交。' % len(url))
    if dry_run:
        return 0
    if not copy_to_clipboard(body):
        print('复制到剪贴板失败，改用 --method email。')
        return 1
    webbrowser.open(base)
    return 0


def submit_email(path, title, dry_run):
    print('to: %s' % EMAIL)
    print('subject: %s' % title)
    print('attach: %s' % path)
    if not dry_run and os.name == 'nt':
        subprocess.Popen('explorer /select,"%s"' % path)
    return 0


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('proposal')
    parser.add_argument('--method', choices=['auto', 'gh', 'browser', 'email'], default='auto')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    path = os.path.abspath(args.proposal)
    with open(path, encoding='utf-8-sig') as f:
        text = f.read()
    problems = check(text)
    if problems:
        print('提议文件检查未通过，改正后重新运行：')
        for problem in problems:
            print('- ' + problem)
        return 2

    title = text.splitlines()[0][2:].strip()
    body = text.split('\n', 1)[1].lstrip('\n')
    method = args.method
    if method == 'auto':
        method = 'gh' if gh_ready() else 'browser'
    print('method: %s' % method)
    if method == 'gh':
        if not gh_ready():
            print('gh 未安装或未登录。')
            return 1
        return submit_gh(title, body, args.dry_run)
    if method == 'browser':
        return submit_browser(title, body, args.dry_run)
    return submit_email(path, title, args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
