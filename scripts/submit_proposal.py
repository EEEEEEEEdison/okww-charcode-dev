"""把知识提议文件反馈给本仓库维护者。

用法（用 ok-ww 自带的 Python，带 -I -B）：
    python.exe -I -B submit_proposal.py <提议 .md> [--method auto|gh|browser|email] [--setup-gh] [--dry-run]
    python.exe -I -B submit_proposal.py --setup-gh [--dry-run]

- 先检查格式和隐私：首行必须是 `# [知识提议] ...`，必须有标记行和 MIT 同意行；
  出现本机绝对路径、邮箱或令牌时拒绝提交，逐行列出。
- 输出 `gh: 已登录|未登录|未安装`，供调用方决定是否提供安装或登录 gh 的选项。
- auto：gh 已登录时用 gh 直接创建 Issue，否则用 browser。
- browser：打开预填标题和正文的新建 Issue 页面，由用户点提交；链接超长时正文复制到剪贴板。
- email：在资源管理器中选中提议文件，输出收件邮箱和邮件主题，由用户发送。
- --setup-gh：先安装并登录 gh，再用 gh 提交，忽略 --method；安装或登录失败时本次改用 browser。
  未安装时用 winget 安装 GitHub.cli，Windows 可能弹出管理员确认；
  登录时验证码复制到剪贴板并打开授权页，由用户粘贴验证码、点 Authorize，最多等 9 分钟。
  不带提议文件时只安装并登录。
- --dry-run 只输出将要执行的动作，不安装、不登录、不创建 Issue、不打开页面、不改剪贴板。
- 退出码：0 完成；1 提交或登录失败；2 文件检查未通过；3 没有 winget，需用户手动安装 gh 后重新运行。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from urllib.parse import quote

REPO = 'EEEEEEEEdison/okww-charcode-dev'
EMAIL = '476676559@qq.com'
TITLE_PREFIX = '# [知识提议] '
MARKER = '<!-- okwwcharcode-proposal v1 -->'
CONSENT = '提交即同意按 MIT 许可收录本提议内容。'
# 未登录时 GitHub 先跳转登录页，链接超过约 7000 字符会返回 500；取 6000 留余量，超出时正文改走剪贴板
URL_LIMIT = 6000
GH_DEFAULT = os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'GitHub CLI', 'gh.exe')
GH_DOWNLOAD = 'https://cli.github.com'
# 等用户授权的上限：短于宿主常见的 10 分钟命令超时，也短于验证码的 15 分钟有效期
LOGIN_TIMEOUT = 540
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


def find_gh():
    # 刚用 winget 装完时，当前进程的 PATH 还没刷新，再查默认安装位置
    path = shutil.which('gh')
    if path:
        return path
    return GH_DEFAULT if os.path.isfile(GH_DEFAULT) else None


def gh_state(gh):
    if not gh:
        return '未安装'
    result = subprocess.run([gh, 'auth', 'status', '--hostname', 'github.com'], capture_output=True)
    return '已登录' if result.returncode == 0 else '未登录'


def install_gh(dry_run):
    winget = shutil.which('winget')
    if not winget:
        print('没有 winget。打开 %s，由用户下载安装 gh 后重新运行。' % GH_DOWNLOAD)
        if not dry_run:
            webbrowser.open(GH_DOWNLOAD)
        return None, 3
    print('将执行：winget install --id GitHub.cli -e --source winget')
    if dry_run:
        return None, 0
    result = subprocess.run([winget, 'install', '--id', 'GitHub.cli', '-e', '--source', 'winget',
                             '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity'],
                            capture_output=True)
    gh = find_gh()
    if not gh:
        tail = result.stdout.decode('utf-8', 'replace').strip().splitlines()[-3:]
        print('安装 gh 失败（winget 退出码 %d）：%s' % (result.returncode, ' / '.join(tail)))
        return None, 1
    print('已安装 gh：%s' % gh)
    return gh, 0


def login_gh(gh, dry_run):
    print('将执行：gh auth login --hostname github.com --git-protocol https --web --clipboard')
    if dry_run:
        return 0
    # stdin 为空时 gh 按非交互运行：不配置 git 凭据，也不自己打开浏览器，只打印授权页链接
    proc = subprocess.Popen([gh, 'auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https',
                             '--web', '--clipboard'],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace')
    reasons = []

    def stop(reason):
        reasons.append(reason)
        proc.kill()

    timer = threading.Timer(LOGIN_TIMEOUT, stop, args=('超过 %d 秒未授权' % LOGIN_TIMEOUT,))
    timer.start()
    try:
        for line in proc.stdout:
            line = line.rstrip()
            print(line, flush=True)
            if 'Failed to copy one-time code' in line:
                # 命令结束前用户看不到输出，验证码不在剪贴板就无法授权
                stop('验证码没能复制到剪贴板')
            match = re.search(r'https://github\.com/login/device\S*', line)
            if match:
                webbrowser.open(match.group(0))
        proc.wait()
    finally:
        timer.cancel()
    if proc.returncode != 0 or gh_state(gh) != '已登录':
        print('gh 登录未完成（退出码 %d）%s。' % (proc.returncode, '：' + reasons[0] if reasons else ''))
        return 1
    return 0


def setup_gh(dry_run):
    gh = find_gh()
    if not gh:
        gh, code = install_gh(dry_run)
        if code:
            return None, code
    if gh and gh_state(gh) == '已登录':
        print('gh 已登录。')
        return gh, 0
    return gh, login_gh(gh or 'gh', dry_run)


def write_temp(body):
    fd, path = tempfile.mkstemp(suffix='.md')
    with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
        f.write(body)
    return path


def submit_gh(gh, title, body, dry_run):
    if dry_run:
        print('将执行：gh issue create --repo %s --title "%s" --body-file <正文>' % (REPO, title))
        return 0
    path = write_temp(body)
    try:
        result = subprocess.run([gh, 'issue', 'create', '--repo', REPO, '--title', title, '--body-file', path],
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
    parser.add_argument('proposal', nargs='?')
    parser.add_argument('--method', choices=['auto', 'gh', 'browser', 'email'], default='auto')
    parser.add_argument('--setup-gh', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not args.proposal and not args.setup_gh:
        parser.error('需要提议文件，或 --setup-gh')

    if args.proposal:
        path = os.path.abspath(args.proposal)
        with open(path, encoding='utf-8-sig') as f:
            text = f.read()
        problems = check(text)
        if problems:
            print('提议文件检查未通过，改正后重新运行：')
            for problem in problems:
                print('- ' + problem)
            return 2

    gh = find_gh()
    if args.setup_gh:
        gh, code = setup_gh(args.dry_run)
        if not args.proposal or code == 3:
            return code
        method = 'gh'
        if code:
            print('本次改用 browser。')
            method = 'browser'
    else:
        state = gh_state(gh)
        print('gh: %s' % state)
        method = args.method
        if method == 'auto':
            method = 'gh' if state == '已登录' else 'browser'
        elif method == 'gh' and state != '已登录':
            print('gh %s，可加 --setup-gh 安装并登录。' % state)
            return 1

    title = text.splitlines()[0][2:].strip()
    body = text.split('\n', 1)[1].lstrip('\n')
    print('method: %s' % method)
    if method == 'gh':
        return submit_gh(gh or 'gh', title, body, args.dry_run)
    if method == 'browser':
        return submit_browser(title, body, args.dry_run)
    return submit_email(path, title, args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
